import os
import json
from typing import List

from pathlib import Path
import random
import pandas as pd
import numpy as np
from tqdm import tqdm
from multiprocessing import Pool, Array
import itertools
import matplotlib
import matplotlib.pyplot as plt
import networkx as nx
from networkx.algorithms.community.centrality import girvan_newman
from community import community_louvain
from itertools import permutations

# original cmap
o_cmap = list(matplotlib.colors.get_named_colors_mapping().keys())

random.shuffle(o_cmap)
cmap = ['green', 'blue', 'red', 'yellow', 'pink', 'purple', 'grey', 'brown', 'orange', 'teal', 'key lime', 'deep sea blue']
cmap = ['xkcd:'+c for c in cmap]
cmap = cmap + o_cmap


class EditDistanceGraph:
    def __init__(self,
                 data: pd.DataFrame,
                 features: List[str],
                 dataset_type: str,
                 out_dir: Path):
        self.f = features
        self.d = data[self.f]
        self.dataset_type = dataset_type
        self.o_dir = out_dir
        self.e_dist = None  # edit distance distribution
        self.g = None   # graph of small edit distances
        self.pos = None  # position of nodes for plotting purpose
        self.comms = None  # communities in graph
        self.build()

    def build(self):
        edges, ed_dist = process(self.d)
        self.e_dist = ed_dist
        self.g = nx.Graph()
        self.g.add_weighted_edges_from(edges)

        # add feature values as node properties
        for n in self.g.nodes():
            for _ in self.d.columns.tolist():
                self.g.nodes[n][_] = self.d.loc[n, _]

    def edge_count(self) -> int:
        if self.g is not None:
            return len(self.g.edges)

    def remove_small_components(self):
        remove_nodes = []
        for c in nx.connected_components(self.g):
            if len(c) < 10:
                remove_nodes.extend(list(c))
        self.g.remove_nodes_from(remove_nodes)

    def louvain(self):
        partition = community_louvain.best_partition(self.g)
        comms = [[] for _ in sorted(set(partition.values()))]

        for n, c in partition.items():
            comms[c].append(n)
        self.comms = comms
        self.add_communities_to_graph()

    def girvan_newman(self):
        comp = girvan_newman(self.g)
        comms = []
        for comm in itertools.islice(comp, 3):
            com_update = [sorted(c) for c in comm]
            comms = com_update
        self.comms = comms

    def add_communities_to_graph(self):
        for i, c in enumerate(self.comms):
            for n in c:
                self.g.nodes[n]['com'] = i

    def communities_count(self):
        if self.comms is None:
            self.louvain()
        return len(self.comms)

    def communities_dist(self):
        if self.comms is None:
            self.louvain()
        comms = self.comms
        dist_data = []
        for i, c in enumerate(comms):
            dist_data.append([i, len(c)])
        self.comm_nodes_dist = pd.DataFrame(dist_data,
                                            columns=['community', 'record counts'])
        self.comm_nodes_dist.to_csv(Path(self.o_dir, 'comm_nodes_dist.csv'))

    def plot_ed_dist(self):
        if self.e_dist is not None:
            ax = self.e_dist.plot(kind='bar',
                                  title='# of Records in each edit distance bin',
                                  legend=False,
                                  xlabel='Edit Distance', ylabel='# of Records')
            fig = ax.get_figure()
            fig.savefig(Path(self.o_dir, "edit_distance_distribution.jpg"))
            plt.close(fig)

    def layout(self):
        self.pos = nx.fruchterman_reingold_layout(self.g, scale=2)

    def plot_graph(self):
        if self.pos is None:
            self.layout()

        pos = self.pos
        g = self.g
        fig = plt.figure(figsize=(12, 8), dpi=100)
        ax = fig.gca()
        nx.draw_networkx_edges(g, pos, alpha=0.1)

        nx.draw_networkx_nodes(g, pos, node_color=cmap[0], label='Target', ax=ax,
                               node_size=10, alpha=0.5)
        plt.legend(scatterpoints=1)
        fig.savefig(Path(self.o_dir, 'graph_plot.jpg'))
        plt.close(fig)

    def plot_communities(self):
        if self.comms is None:
            self.louvain()
        if self.pos is None:
            self.layout()

        comms = self.comms
        g = self.g
        pos = self.pos
        fig = plt.figure(figsize=(15, 10), dpi=100)
        ax = fig.gca()
        n_colors = nx.get_node_attributes(g, 'com')
        # ec = nx.draw_networkx_edges(g, pos, alpha=0.2)

        for i, c in enumerate(comms):
            color = cmap[i]
            nx.draw_networkx_nodes(g, pos, ax=ax, node_color=color, label=i,
                                   node_size=10, alpha=0.5)

        nx.draw_networkx_edges(g, pos, alpha=0.1)
        fig.savefig('graph_communities.jpg')
        plt.close(fig)

    def plot_diversity(self):
        f_p = set()
        features = self.f
        for p1, p2 in permutations(features, 2):
            if frozenset([p1, p2]) not in f_p:
                f_p.add(frozenset([p1, p2]))

        f_pairs = [list(fs) for fs in f_p]
        p_data = dict()
        for fp in f_pairs:
            f1, f2 = fp[0], fp[1]
            key = f'{f1}-{f2}'
            p_data[key] = None
            dfc_l = []
            for i, c in enumerate(self.comms):
                df_c = self.d.loc[c]
                df_c = df_c[fp]
                df_c['community'] = i
                dfc_l.append(df_c)

            p_data[key] = pd.concat(dfc_l)
        i = 0
        total_keys = len(p_data.keys())
        keys = sorted(list(p_data.keys()))

        key_pairs = [[keys[i], keys[i+1]]
                     for i in range(0, total_keys, 2)]
        tot_key_pairs = len(key_pairs)

        fig, ax = plt.subplots(tot_key_pairs, 2,
                               figsize=(10, tot_key_pairs * 4), dpi=200)
        fig.suptitle(self.dataset_type, fontsize=16)

        for i, kp in enumerate(key_pairs):
            k1, k2 = kp[0], kp[1]
            k1f1, k1f2 = k1.split('-')
            k2f1, k2f2 = k2.split('-')
            ax1 = ax[i, 0]
            ax2 = ax[i, 1]

            k1d = p_data[k1]
            k2d = p_data[k2]

            for cid, group in k1d.groupby('community'):
                group.plot(ax=ax1, kind='scatter', x=k1f1, y=k1f2, color=cmap[cid], alpha=0.5)
            for cid, group in k2d.groupby('community'):
                group.plot(ax=ax2, kind='scatter', x=k2f1, y=k2f2, color=cmap[cid], alpha=0.5)
            i += 1
        plt.tight_layout()
        fig.savefig(Path(self.o_dir, 'diversity_plot.jpg'))
        plt.close(fig)

    def dominant_features(self):
        if self.comms is None:
            self.louvain()
        total_recs = self.d.shape[0]

        com_count = len(self.comms)
        feat_count = len(self.f)
        od_data = [[0 for ci in range(com_count)] for fi in range(feat_count)]
        od_data_complete = {ci: {f: 0 for f in self.f}
                            for ci in range(com_count)}

        for ci, c in enumerate(self.comms):

            o_ndf = self.d.loc[c].copy()
            for fi, feat in enumerate(self.f):
                t_v_count = o_ndf[feat].value_counts(normalize=True)
                t_bundle = []
                c_bundle = []
                for vi in t_v_count.index:
                    v_v = t_v_count[vi]
                    c_bundle.append([vi, round(v_v, 2)])

                    if v_v >= 0.1:
                        t_bundle.append(f'{vi}({round(v_v, 2)})')

                od_data[fi][ci] = " | ".join(t_bundle)
                f = self.f[fi]
                od_data_complete[ci][f] = c_bundle
                # print(v_count)

        oddf = pd.DataFrame(data=od_data,
                            columns=[i for i in range(len(self.comms))],
                            index=[feat for feat in self.f])

        with open(Path(self.o_dir, 'dominant_features_dict.json'), 'w') as f:
            json.dump(od_data_complete, f, indent=4)

        oddf.to_csv(Path(self.o_dir, 'dominant_features.csv'))
        return oddf

    def dump(self):
        nx.write_graphml(self.g, Path(self.o_dir, 'graph.graphml'))


def edit_distance(r1: pd.Series, r2: pd.Series):
    edits = 0
    for v1, v2 in zip(r1, r2):
        if v1 != v2:
            edits += 1
    return edits


def pair_edit_distance(chunk: pd.DataFrame, complete: pd.DataFrame):
    ck = chunk  # chunk of dataset
    cp = complete  # complete dataset
    edges = []
    edit_distance_dist = dict()
    for roi, ro in tqdm(ck.iterrows()):
        for rsi, rs in cp.iterrows():
            if roi == rsi:
                continue
            dist = edit_distance(ro, rs)
            if dist not in edit_distance_dist:
                edit_distance_dist[dist] = 1
            edit_distance_dist[dist] += 1
            if dist < 3:
                edges.append((roi, rsi, dist))
    ed_dist = pd.DataFrame([[k, v] for k, v in edit_distance_dist.items()],
                           columns=['edit-distance', 'records'])
    return edges, ed_dist


def process(data: pd.DataFrame):
    p_size = 12
    pool = Pool(p_size)
    n = 500  # chunk row size
    list_df = [data[i:i + n] for i in range(0, data.shape[0], n)]
    data_chunks = [(t, data) for t in list_df]
    res = pool.starmap(pair_edit_distance, data_chunks)

    edges = [e for r in res for e in r[0]]
    ed_dist = pd.concat([r[1] for r in res]).groupby(['edit-distance']).sum().reset_index()
    return edges, ed_dist
