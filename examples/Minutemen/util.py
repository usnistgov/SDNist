import numpy as np
import pandas as pd
from mbi import Domain, Dataset
import itertools

def powerset(iterable):
    s = list(iterable)
    return itertools.chain.from_iterable(itertools.combinations(s, r) for r in range(1,len(s)+1))

def downward_closure(cliques):
    ans = set()
    for proj in cliques:
        ans.update(powerset(proj))
    return list(sorted(ans, key=len))

BINS = {
    "fare": np.r_[-1, np.arange(0, 100, step=10), 9900],
    "tips": np.r_[-1, np.arange(0, 100, step=10), 407],
    "trip_total": np.r_[-1, np.arange(0, 100, step=10), 9900],
    "trip_seconds": np.r_[-1, np.arange(0, 2000, step=200), 86400],
    "trip_miles": np.r_[-1, np.arange(0, 100, step=10), 1428] }

def discretize(df, schema, clip=None):
    weights = None
    if clip is not None:
        # each individual now only contributes "clip" records
        # achieved by reweighting records, rather than resampling them
        weights = df.taxi_id.value_counts()
        weights = np.minimum(clip/weights, 1.0)
        weights = np.array(df.taxi_id.map(weights).values)

    new = df.copy()
    domain = { }
    for col in schema:
        info = schema[col]
        #print(col)
        if col in BINS:
            new[col] = pd.cut(df[col], BINS[col], right=False).cat.codes
            domain[col] = len(BINS[col]) - 1
        elif 'values' in info:
            new[col] = df[col].astype(pd.CategoricalDtype(info['values'])).cat.codes
            domain[col] = len(info['values'])
        else:
            new[col] = df[col] - info['min']
            domain[col] = info['max'] - info['min'] + 1

    domain = Domain.fromdict(domain)
    return Dataset(new, domain, weights)

def undo_discretize(dataset, schema):
    df = dataset.df
    new = df.copy()

    for col in dataset.domain:
        info = schema[col]
        if col in BINS:
            low = BINS[col][:-1]; 
            high = BINS[col][1:]
            low[0] = low[1]-2
            high[-1] = high[-2]+2
            mid = (low + high) / 2
            new[col] = mid[df[col].values]
        elif 'values' in info:
            mapping = np.array(info['values'])
            new[col] = mapping[df[col].values]
        else:
            new[col] = df[col] + info['min']

        #if 'max' in info:
        #    new[col] = np.minimum(new[col], info['max'])
        #if 'min' in info: 
        #    new[col] = np.maximum(new[col], info['min'])

    dtypes = { col : schema[col]['dtype'] for col in schema }

    return new.astype(dtypes)


def score(real, synth):
    # Replicate the NIST scoring metric
    # Calculates score for *every* 2-way marginal instead of a sample of them
    # performs scoring using the mbi.Dataset representation, which is different from raw data format
    # scores should match exactly 
    # to score raw dataset, call score(discretize(real, schema), discretize(synth, schema))
    assert real.domain == synth.domain
    dom = real.domain
    proj = ('pickup_community_area','shift')
    newdom = dom.project(dom.invert(proj))
    keys = dom.project(proj)
    pairs = list(itertools.combinations(newdom.attrs, 2))

    idx = np.argsort(real.project('pickup_community_area').datavector())

    overall = 0
    breakdown = {}
    breakdown2 = np.zeros(dom.size('pickup_community_area'))

    for pair in pairs:
        #print(pair)
        proj = ('pickup_community_area','shift') + pair
        X = real.project(proj).datavector(flatten=False)
        Y = synth.project(proj).datavector(flatten=False)
        X /= X.sum(axis=(2,3), keepdims=True)
        Y /= Y.sum(axis=(2,3), keepdims=True)

        err = np.nan_to_num( np.abs(X-Y).sum(axis=(2,3)), nan=2.0)
        breakdown[pair] = err.mean()
        breakdown2 += err.mean(axis=1)
        overall += err.mean()

    score = overall / len(pairs)

    nist_score = ((2.0 - score) / 2.0) * 1_000
    breakdown2 /= len(pairs)

    return nist_score, pd.Series(breakdown), (2.0 - breakdown2[idx]) / 2.0

