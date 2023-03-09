import os
from pathlib import Path
import pandas as pd

from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA

import numpy as np

import matplotlib.pyplot as plt

from sdnist.utils import *

plt.style.use('seaborn-deep')


class PCAMetric:
    def __init__(self, target: pd.DataFrame, synthetic: pd.DataFrame,):
        self.tar = target
        self.syn = synthetic
        self.t_pdf = None
        self.s_pdf = None

        # loadings for the data features
        self.t_comp_data = []

        # target data components eigen basis
        self.comp_df = None

    def compute_pca(self):
        cc = 5
        t_pca = PCA(n_components=cc)

        tdf_v = self.tar.values
        sdf = self.syn.apply(lambda x: x - x.mean())
        sdf_v = sdf.values

        tdf_v = StandardScaler().fit_transform(tdf_v)
        sdf_v = StandardScaler().fit_transform(sdf_v)

        t_pc = t_pca.fit_transform(tdf_v)

        t_ev = np.array(t_pca.components_)
        s_pc = np.matmul(sdf_v, t_ev.T)

        self.t_comp_data = []
        for i, comp in enumerate(t_pca.components_):
            qc = [[n, round(v, 2)] for n, v in zip(self.tar.columns.tolist(), comp)]
            qc = sorted(qc, key=lambda x: x[1], reverse=True)
            qc = [f'{v[0]} ({v[1]})' for v in qc]
            self.t_comp_data.append({"Principal Component": f"PC-{i}",
                                     "Features Contribution: "
                                     "feature-name (contribution ratio)": ','.join(qc[:5])})

        self.comp_df = pd.DataFrame(t_pca.components_,
                                    columns=self.tar.columns,
                                    index=[i for i in range(cc)])

        self.t_pdf = pd.DataFrame(data=t_pc,
                                  columns=[f'PC-{i}'
                                           for i in range(cc)],
                                  index=self.tar.index)

        self.s_pdf = pd.DataFrame(data=s_pc,
                                  columns=[f'PC-{i}'
                                           for i in range(cc)],
                                  index=self.syn.index)

    def plot(self, output_directory: Path):
        o_path = output_directory
        tar_path = Path(o_path, 'target.jpg')
        syn_path = Path(o_path, 'deidentified.jpg')

        plot_pca('Target Dataset', self.t_pdf, tar_path, color='#5373d8')
        plot_pca('Deidentified Dataset', self.s_pdf, syn_path, color='#4eb07a')

        return [tar_path, syn_path]


def plot_pca(title: str, data: pd.DataFrame, out_file, color='b'):
    cc = len(data.columns)
    fig, ax = plt.subplots(cc, cc, figsize=(6, 6))

    fig.set_dpi(200)

    for i, pc_i in enumerate(data.columns):
        for j, pc_j in enumerate(data.columns):
            if pc_i == pc_j:
                ax_t = ax[i, j]
                ax_t.text(0.5, 0.5, pc_i,
                          ha='center', va='center', color='black', fontsize=30)
            else:
                df_ij = data[[pc_i, pc_j]]
                ax_t = ax[i, j]
                df_ij.plot(ax=ax_t, kind='scatter',
                           x=pc_j, y=pc_i, c='none',
                           facecolor='none', edgecolors=color)
            ax_t.set_xlabel('')
            ax_t.set_ylabel('')
            ax_t.set_xticklabels([])
            ax_t.set_yticklabels([])
            ax_t.tick_params(length=0)
    plt.suptitle(title)
    plt.tight_layout()
    plt.savefig(out_file, bbox_inches='tight')
    plt.close()
