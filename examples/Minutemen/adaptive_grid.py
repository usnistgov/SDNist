import numpy as np
import pandas as pd
import json
from util import discretize, undo_discretize, downward_closure
from mbi import FactoredInference, Factor
from scipy import sparse
from autodp import privacy_calibrator
from functools import partial
from pathlib import Path
import typer
from multiprocessing import Pool
from math import ceil

import sdnist


def get_permutation_matrix(cl1, cl2, domain):
    # permutation matrix that maps datavector of cl1 factor to datavector of cl2 factor
    assert set(cl1) == set(cl2)
    n = domain.size(cl1)
    fac = Factor(domain.project(cl1),np.arange(n))
    new = fac.transpose(cl2)
    data = np.ones(n)
    row_ind = fac.datavector()
    col_ind = new.datavector()
    return sparse.csr_matrix((data, (row_ind, col_ind)), shape=(n,n))

def get_aggregate(cl, matrices, domain):
    children = [r for r in matrices if set(r) < set(cl) and len(r)+1 == len(cl)]
    ans = [sparse.csr_matrix((0,domain.size(cl)))]
    for c in children:
        coef = 1.0 / np.sqrt(len(children))
        a = tuple(set(cl)-set(c))
        cl2 = a + c
        Qc = matrices[c]
        P = get_permutation_matrix(cl, cl2, domain)
        T = np.ones(domain.size(a))
        Q = sparse.kron(T, Qc) @ P
        ans.append(coef*Q)
    return sparse.vstack(ans)
    
def get_identity(cl, post_plausibility, domain):
    # determine which cells in the cl marginal *could* have a count above threshold, 
    # based on previous measurements
    children = [r for r in post_plausibility if set(r) < set(cl) and len(r)+1 == len(cl)]
    plausibility = Factor.ones(domain.project(cl))
    for c in children:
        plausibility *= post_plausibility[c]

    row_ind = col_ind = np.nonzero(plausibility.datavector())[0]
    data = np.ones_like(row_ind)
    n = domain.size(cl)
    Q = sparse.csr_matrix((data, (row_ind, col_ind)), (n,n))
    return Q


def adagrid(data, epsilon, delta, threshold, cliques, iters=2500, clip=200):
    # Calibrate noise using Gaussian differential privacy
    # We have an adaptive composistion of K=len(cliques) Gaussian mechanisms, 
    # each applied to a quantity with L2 sensitivty of 1
    # Requried noise is thus sqrt(K) * sigma(epsilon, delta) * 200
    # the 200 can be reduced if clipping is done
    noise = privacy_calibrator.gaussian_mech(epsilon, delta)['sigma']*clip*np.sqrt(len(cliques))
    domain = data.domain
    threshold = noise*threshold
    measurements = []
    post_plausibility = {}
    matrices = {}

    for k in [1,2,3,4]:
        split = [cl for cl in cliques if len(cl) == k]
        print()
        for cl in split:
            I = sparse.eye(domain.size(cl)) 
            Q1 = get_identity(cl, post_plausibility, domain) # get fine-granularity measurements
            Q2 = get_aggregate(cl, matrices, domain) @ (I - Q1) #get remaining aggregate measurements
            Q1 = Q1[Q1.getnnz(1)>0] # remove all-zero rows
            Q = sparse.vstack([Q1,Q2])
            Q.T = sparse.csr_matrix(Q.T) # a trick to improve efficiency of Private-PGM
            # Q has sensitivity 1 by construction
            print('Measuring %s, L2 sensitivity %.6f' % (cl, Q.power(2).sum(axis=0).max())) 
            #########################################
            ### This code uses the sensitive data ###
            #########################################
            mu = data.project(cl).datavector()
            y = Q @ mu + np.random.normal(loc=0, scale=noise, size=Q.shape[0])
            #########################################
            est = Q1.T @ y[:Q1.shape[0]]

            post_plausibility[cl] = Factor(domain.project(cl), est >= threshold)
            matrices[cl] = Q
            measurements.append((Q, y, 1.0, cl))

    print('Post-processing with Private-PGM, will take some time...')
    elim_order = ['trip_seconds', 'payment_type', 'trip_miles', 'trip_total', 'tips', 'fare', 'company_id', 'dropoff_community_area', 'pickup_community_area', 'shift']
    engine = FactoredInference(domain,elim_order=elim_order,log=False,iters=iters,warm_start=True)

    small = [M for M in measurements if len(M[-1]) == 1]
    engine.estimate(small)

    return engine.estimate(measurements, total=engine.model.total)

def assign_taxi_ids(priv):
    gt = pd.read_csv('public_taxiid.zip')
    pair = ['pickup_community_area','shift']
    sizes = priv.groupby(pair).size().unstack().fillna(0).astype(int).stack()

    def assign_identifier(g):
        num = sizes[g.name]
        if num == 0:
            return pd.DataFrame(columns=g.columns)
        g = g.sample(frac=1) # shuffle
        reps = ceil(num/g.shape[0])
        g = pd.concat([g]*reps, ignore_index=True).iloc[:num] # grab correct number of rows
        g['key'] = np.arange(g.shape[0]) # assign key for later join operation
        return g
    gt2 = gt.groupby(pair).apply(assign_identifier).reset_index(drop=True)
    priv2 = priv.groupby(pair).apply(assign_identifier).reset_index(drop=True)
    ans = priv2.merge(gt2, how='left', on=pair+['key']).drop(columns=['key'])
    ans['taxi_id'] = ans.taxi_id.astype('category').cat.codes
    cumct = ans.groupby('taxi_id').cumcount()
    num = (cumct >= 200).sum()
    #new_ids = np.repeat(np.arange(ceil(num/200.0))+ans.taxi_id.max()+1, 200)[:num]
    ans.loc[cumct >= 200,'taxi_id'] = np.arange(num)+ans.taxi_id.max()+1
    return ans

def run_mechanism(df, schema, run):
    epsilon, delta = run['epsilon'], run['delta']
    iters = int(344*epsilon+256)
    threshold = 5
    copies = 8

    if epsilon <= 1:
        clip = 150
    else:
        clip = 200

    data = discretize(df, schema, clip)

    cliques = [('pickup_community_area', 'shift', 'fare', 'trip_total'),
                ('pickup_community_area', 'shift', 'trip_total', 'trip_seconds'),
                ('pickup_community_area', 'shift', 'dropoff_community_area', 'fare'),
                ('pickup_community_area', 'shift', 'payment_type', 'trip_total'),
                ('pickup_community_area', 'shift', 'fare', 'trip_miles'),
                ('pickup_community_area', 'shift', 'company_id'),
                ('pickup_community_area', 'shift', 'tips', 'trip_total')]

    cliques = downward_closure(cliques)
    cliques += [('pickup_community_area', 'dropoff_community_area')]*(copies - 1)

    model = adagrid(data,epsilon,delta,threshold,cliques,iters,clip)

    synth = model.synthetic_data()
    submit = undo_discretize(synth, schema)
    # submit = assign_taxi_ids(submit)
    submit["taxi_id"] = 0
    cols = ['taxi_id', 'shift', 'company_id', 'pickup_community_area', 'dropoff_community_area', 'payment_type', 'fare', 'tips', 'trip_total', 'trip_seconds', 'trip_miles']
    submit = submit[cols]
    return submit


def main():
    df, schema = sdnist.taxi()

    del schema["trip_day_of_week"]
    del schema["trip_hour_of_day"]
    run = {"epsilon": 1, "delta": 2.5e-4}
    synthetic_df = run_mechanism(df, schema, run)
    
    print(sdnist.score(df, synthetic_df, challenge="taxi"))

if __name__ == '__main__':
    typer.run(main) 