import os
import json
from typing import Dict
from pathlib import Path
import pandas as pd
import networkx as nx

from sdnist.metrics.edit_distance_graph.communities import EditDistanceGraph


def compute_graph(data, feats, dataset_type, metadata, output_path, puma=None):
    dp = metadata
    edg = EditDistanceGraph(data, feats, dataset_type, output_path)
    dp['edges'] = edg.edge_count()
    dp['nodes'] = len(edg.g.nodes())

    # edg.remove_small_components()
    edg.louvain()
    dp['communities'] = edg.communities_count()
    dp['path'] = str(dp['path'])
    dp['schema_path'] = str(dp['schema_path'])
    with open(Path(output_path, 'meta.json'), 'w') as f:
        json.dump(dp, f, indent=4)

    print('Save community dist')
    edg.communities_dist()
    print('Save edit distance plot')
    edg.plot_ed_dist()
    # print('Save diversity plot')
    # edg.plot_diversity()
    # print('Save dominant_features')
    # edg.dominant_features()
    print('Save graph')
    edg.dump()


def community_edit_distance_graph(data1, data2):
    edges = []
    dom_edges = []
    for c1, fv1 in data1.items():
        for c2, fv2 in data2.items():
            feats = list(fv1.keys())
            net_diff = 0
            dom_f = []
            for f in feats:
                vals1, vals2 = fv1[f], fv2[f]
                vals1 = sorted(vals1, key=lambda x: (x[0], x[1]))
                vals2 = sorted(vals2, key=lambda x: (x[0], x[1]))

                oval1 = [v[0] for v in vals1]
                oval2 = [v[0] for v in vals2]

                all_vals = set(oval1)
                all_vals.update(oval2)
                intersect = set(oval1).intersection(set(oval2))
                rest_vals = all_vals.difference(intersect)

                diff = len(rest_vals)

                for v in intersect:
                    vf1 = [vf[1] for vf in vals1 if vf[0] == v][0]
                    vf2 = [vf[1] for vf in vals2 if vf[0] == v][0]
                    diff += abs(vf1 - vf2)

                if diff/len(all_vals) > 0.5:
                    dom_f.append([f, round(diff/len(all_vals), 1)])

                net_diff += diff/len(all_vals)

            net_diff = net_diff/len(feats)
            dom_f = sorted(dom_f, reverse=True, key=lambda x: x[1])

            if net_diff < 0.6:
                edges.append((f'd1_{c1}', f'd2_{c2}', net_diff))
                dom_edges.append(((f'd1_{c1}'
                                   , f'd2_{c2}'
                                   , ' | '.join([f'{f[0]}({f[1]})' for f in dom_f]))))

    g = nx.Graph()
    g.add_weighted_edges_from(edges)

    for e in dom_edges:
        g.edges[e[0], e[1]]['data'] = e[2]

    for n in g.nodes():
        g.nodes[n]['type'] = 0 if n.startswith('d1') else 1
    return g


if __name__ == "__main__":
    THIS_DIR = Path(__file__).parent
    OUT_DIR = Path(THIS_DIR, 'edit_dist_output')

    if not OUT_DIR.exists():
        os.mkdir(OUT_DIR)

    samples = 5000
    orig_sna = ['HOUSING_TYPE', 'OWN_RENT', 'NPF', 'SEX', 'NOC', 'MSP', 'AGEP', 'EDU', 'PINCP_DECILE']
    race_split = ['AGEP', 'RAC1P', 'MSP', 'SEX', 'HOUSING_TYPE', 'OWN_RENT', 'DVET', 'DEYE']
    sector_split = ['AGEP', 'INDP_CAT', 'RAC1P', 'SEX', 'HOUSING_TYPE', 'OWN_RENT', 'DVET', 'DEYE', 'PINCP_DECILE']

    features = race_split
    f_set = 'race_split'
    T_DATA_PATH = Path(THIS_DIR, '..', '..', '..', 'sdnist_toy_data')
    S_DATA_PATH = Path(THIS_DIR, '..', '..', '..', 'toy_synthetic_data', 'syn')

    dataset_paths = [
        # {
        #     "path": Path(T_DATA_PATH, 'ma2019.csv'),
        #     "schema_path": Path(T_DATA_PATH, 'ma2019.json'),
        #     "type": "target",
        #     "pair_id": 0,
        #     "pair_name": f"{f_set}_ma_orig"
        # },
        # {
        #     "path": Path(T_DATA_PATH, 'tx2019.csv'),
        #     "schema_path": Path(T_DATA_PATH, 'tx2019.json'),
        #     "type": "target",
        #     "pair_id": 0,
        #     "pair_name": f"{f_set}_tx_orig"
        # },
        # {
        #     "path": Path(T_DATA_PATH, 'national2019.csv'),
        #     "schema_path": Path(T_DATA_PATH, 'national2019.json'),
        #     "type": "target",
        #     "pair_id": 0,
        #     "pair_name": f"{f_set}_national_orig_ed_1"
        # },
        # {
        #     "path": Path(S_DATA_PATH, 'censyn', 'Race', 'syn_ma.csv'),
        #     "schema_path": Path(T_DATA_PATH, 'ma2019.json'),
        #     "type": "synthetic",
        #     "pair_id": 1,
        #     "pair_name": f"{f_set}_ma_censyn_inc",
        #     "synthesizer": "censyn"
        # },
        # {
        #     "path": Path(S_DATA_PATH, 'censyn', 'Race', 'syn_tx.csv'),
        #     "schema_path": Path(T_DATA_PATH, 'tx2019.json'),
        #     "type": "synthetic",
        #     "pair_id": 1,
        #     "pair_name": f"{f_set}_tx_censyn_inc",
        #     "synthesizer": "censyn"
        # },
        # {
        #     "path": Path(S_DATA_PATH, 'censyn', 'Race', 'syn_na.csv'),
        #     "schema_path": Path(T_DATA_PATH, 'national2019.json'),
        #     "type": "synthetic",
        #     "pair_id": 1,
        #     "pair_name": f"{f_set}_national_censyn_inc",
        #     "synthesizer": "censyn"
        # },
        # {
        #     "path": Path(S_DATA_PATH, 'censyn', 'nist0829', 'syn_ma.csv'),
        #     "schema_path": Path(T_DATA_PATH, 'ma2019.json'),
        #     "type": "synthetic",
        #     "pair_id": 2,
        #     "pair_name": f"{f_set}_ma_censyn_latest_ed_1",
        #     "synthesizer": "censyn"
        # },
        # {
        #     "path": Path(S_DATA_PATH, 'censyn', 'nist0829', 'syn_tx.csv'),
        #     "schema_path": Path(T_DATA_PATH, 'tx2019.json'),
        #     "type": "synthetic",
        #     "pair_id": 2,
        #     "pair_name": f"{f_set}_tx_censyn_latest_ed_1",
        #     "synthesizer": "censyn"
        # },
        # {
        #     "path": Path(S_DATA_PATH, 'censyn', 'nist0829', 'syn_na.csv'),
        #     "schema_path": Path(T_DATA_PATH, 'national2019.json'),
        #     "type": "synthetic",
        #     "pair_id": 2,
        #     "pair_name": f"{f_set}_national_censyn_latest_ed_1",
        #     "synthesizer": "censyn"
        # },
        {
            "path": Path(S_DATA_PATH, 'cell_supression', 'syn_national.csv'),
            "schema_path": Path(T_DATA_PATH, 'national2019.json'),
            "type": "synthetic",
            "pair_id": 2,
            "pair_name": f"{f_set}_national_cell_supression_ed_1_r_10_to_0",
            "synthesizer": "censyn"
        },
        # {
        #     "path": Path(S_DATA_PATH, 'sdv_copula', 'syn_na.csv'),
        #     "schema_path": Path(T_DATA_PATH, 'national2019.json'),
        #     "type": "synthetic",
        #     "pair_id": 2,
        #     "pair_name": f"{f_set}_national_sdv_copula_ed_1",
        #     "synthesizer": "censyn"
        # },
        # {
        #     "path": Path(S_DATA_PATH, 'sdv', 'syn_na.csv'),
        #     "schema_path": Path(T_DATA_PATH, 'national2019.json'),
        #     "type": "synthetic",
        #     "pair_id": 2,
        #     "pair_name": f"{f_set}_national_sdv_ed_1",
        #     "synthesizer": "censyn"
        # },
        # {
        #     "path": Path(S_DATA_PATH, 'subsample', 'syn_na_33.csv'),
        #     "schema_path": Path(T_DATA_PATH, 'national2019.json'),
        #     "type": "synthetic",
        #     "pair_id": 2,
        #     "pair_name": f"{f_set}_national_subsample_33_ed_1",
        #     "synthesizer": "censyn"
        # }
    ]

    pid_pname_map = {dp['pair_id']: dp['pair_name'] for dp in dataset_paths}
    d_edg: Dict[int, EditDistanceGraph] = dict()

    for i, dp in enumerate(dataset_paths):
        print('Dataset: ', i)
        schema_path = dp['schema_path']
        with open(schema_path, 'r') as f:
            schema = json.load(f)

        dtypes = {f: schema['schema'][f]['dtype']
                  for f in schema['schema'].keys()}

        if str(dp['path']).endswith('parquet'):
            df = pd.read_parquet(dp['path'])
        else:
            df = pd.read_csv(dp['path'], dtype=dtypes)

        pair_id = dp["pair_id"]
        pair_name = dp["pair_name"]

        df_type = dp['type']

        samples = samples if samples < df.shape[0] else df.shape[0]

        tdf_s = df.sample(samples)
        dp['records_complete'] = df.shape[0]
        dp['records_sample'] = tdf_s.shape[0]

        PAIR_ID_PATH = Path(OUT_DIR, f'pair_id_{pair_id}_{pair_name}')

        if not PAIR_ID_PATH.exists():
            os.mkdir(PAIR_ID_PATH)

        TYPE_PATH = Path(PAIR_ID_PATH, df_type)

        if not TYPE_PATH.exists():
            os.mkdir(TYPE_PATH)

        compute_graph(tdf_s, features, df_type, dp, TYPE_PATH)

        # for puma, group in tdf_s.groupby(by=['PUMA']):
        #     print('Dataset: ', i, 'PUMA: ', puma)
        #     puma_out_path = Path(TYPE_PATH, f'{puma}')
        #     if not puma_out_path.exists():
        #         os.mkdir(puma_out_path)
        #     compute_graph(group, features, df_type, dp, puma_out_path)

    # max_pair_id = max([dp['pair_id'] for dp in dataset_paths]) + 1
    # compute community graph

    # for pid in range(max_pair_id):
    #     p_n = pid_pname_map[pid]
    #     p_dir = f'pair_id_{pid}_{p_n}'
    #     t_dom_f_p = Path(OUT_DIR, p_dir, 'target', 'dominant_features_dict.json')
    #     s_dom_f_p = Path(OUT_DIR, p_dir, 'synthetic', 'dominant_features_dict.json')
    #
    #     with open(t_dom_f_p, 'r') as f:
    #         t_dom_f = json.load(f)
    #
    #     with open(s_dom_f_p, 'r') as f:
    #         s_dom_f = json.load(f)
    #
    #     g = community_edit_distance_graph(t_dom_f, s_dom_f)
    #
    #     t_com_dist = pd.read_csv(Path(OUT_DIR, p_dir, 'target', 'comm_nodes_dist.csv'))
    #     s_com_dist = pd.read_csv(Path(OUT_DIR, p_dir, 'synthetic', 'comm_nodes_dist.csv'))
    #
    #     for i, row in t_com_dist.iterrows():
    #         com = row['community']
    #         size = row['record counts']
    #         node_name = f'd1_{com}'
    #         if node_name in g.nodes():
    #             g.nodes[f'd1_{com}']['weight'] = size
    #
    #     for i, row in s_com_dist.iterrows():
    #         com = row['community']
    #         size = row['record counts']
    #         node_name = f'd2_{com}'
    #         if node_name in g.nodes():
    #             g.nodes[f'd2_{com}']['weight'] = size
    #
    #     for c, fv in t_dom_f.items():
    #         dom_f = []
    #         for f, v in fv.items():
    #             if len(v) == 1:
    #                 dom_f.append(f)
    #         dom_f = sorted(dom_f)
    #         if f'd1_{c}' in g.nodes():
    #             g.nodes[f'd1_{c}']['dominant_features'] = ' | '.join(dom_f)
    #
    #     for c, fv in s_dom_f.items():
    #         dom_f = []
    #         for f, v in fv.items():
    #             if len(v) == 1:
    #                 dom_f.append(f)
    #         dom_f = sorted(dom_f)
    #         if f'd2_{c}' in g.nodes():
    #             g.nodes[f'd2_{c}']['dominant_features'] = ' | '.join(dom_f)
    #
    #     nx.write_graphml(g, Path(OUT_DIR, p_dir, 'comm_graph.graphml'))

