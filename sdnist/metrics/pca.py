import os
import time
from typing import Dict
from pathlib import Path
import pandas as pd

from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA

import numpy as np

import matplotlib.pyplot as plt
import matplotlib.image as mpimg

import sdnist.strs as strs
from sdnist.utils import *

plt.style.use('seaborn-deep')


class PCAMetric:
    # 0: highlighted type,
    # 1: highlighted name,
    # 2: highlighted caption,
    # 3: filters for the data
    # 4: features involved
    # 5: pca components involved
    pca_highlight_types = [
        ('MSP', 'MSP_N', 'Children (AGEP < 15)', [['MSP', [-1]]], ['MSP'], [0, 1])
    ]

    def __init__(self, target: pd.DataFrame, synthetic: pd.DataFrame,):
        self.tar = target
        self.syn = synthetic
        self.t_pdf = None
        self.s_pdf = None
        self.t_pdf_s = None  # pca target data minmax scaled
        self.s_pdf_s = None  # pca deid data minmax scaled

        # loadings for the data features
        self.t_comp_data = []

        # target data components eigen basis
        self.comp_df = None

    def compute_pca(self):
        cc = 5
        t_pca = PCA(n_components=cc)

        tdf_v = self.tar.values
        sdf_v = self.syn.values
        scaler = StandardScaler().fit(tdf_v)
        sdf_v = scaler.transform(sdf_v)
        tdf_v = scaler.transform(tdf_v)

        t_pc = t_pca.fit_transform(tdf_v)

        t_ev = np.array(t_pca.components_)
        s_pc = np.matmul(sdf_v, t_ev.T)

        self.t_comp_data = []
        for i, comp in enumerate(t_pca.components_):
            qc = [[n, round(v, 2)] for n, v in zip(self.tar.columns.tolist(), comp)]
            qc = sorted(qc, key=lambda x: abs(x[1]), reverse=True)
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

        self.t_pdf_s = self.t_pdf.copy()
        self.s_pdf_s = self.s_pdf.copy()

        for c in self.t_pdf.columns:
            self.t_pdf_s[c] = min_max_scaling(self.t_pdf[c])
        for c in self.s_pdf.columns:
            self.s_pdf_s[c] = min_max_scaling(self.s_pdf[c],
                                              self.t_pdf[c].min(),
                                              self.t_pdf[c].max())

    def plot(self, output_directory: Path) -> Dict[str, any]:
        s = time.time()
        plot_paths = dict()
        o_path = output_directory
        # individual component pair plot output path
        t_cp_o_path = Path(o_path, 'target_individual_components')
        s_cp_o_path = Path(o_path, 'deidentified_individual_components')

        create_path(t_cp_o_path)
        create_path(s_cp_o_path)

        tar_path = Path(o_path, 'target.png')
        syn_path = Path(o_path, 'deidentified.png')

        plot_all_components_pairs('Target Dataset', self.t_pdf_s, tar_path, t_cp_o_path,
                                  color='#5373d8')
        plot_all_components_pairs('Deidentified Dataset', self.s_pdf_s, syn_path, s_cp_o_path,
                                  color='#4eb07a')

        plot_paths[strs.ALL_COMPONENTS_PAIR_PLOT] = [tar_path, syn_path]
        plot_paths[strs.HIGHLIGHTED] = dict()

        cols = self.tar.columns.tolist()
        for t in self.pca_highlight_types:
            h_type = t[0]  # highlighted type
            h_name = t[1]  # highlighted name
            h_caption = t[2]
            h_filters = t[3]  # data filters to use to find record to be highlighted
            hc = t[5]  # component pair to highlight
            hf = t[4]  # features to be highlighted

            if not all(f in cols for f in hf):
                continue

            h_t_cp_o_path = Path(o_path, f'target_highlighted_{h_type}')
            h_s_cp_o_path = Path(o_path, f'deidentified_highlighted_{h_type}')

            create_path(h_t_cp_o_path)
            create_path(h_s_cp_o_path)

            h_tar_path = Path(h_t_cp_o_path, f'{h_name}.png')
            h_syn_path = Path(h_s_cp_o_path, f'{h_name}.png')

            f_tdf = df_filter(self.tar, h_filters)
            f_sdf = df_filter(self.syn, h_filters)
            f_tdf = self.t_pdf_s.loc[f_tdf.index]
            f_sdf = self.s_pdf_s.loc[f_sdf.index]

            plot_single_component_pair(f'Target Dataset: PC{hc[0]}-PC{hc[1]}',
                                       f_tdf, h_tar_path, h_t_cp_o_path, t_cp_o_path, hc)
            plot_single_component_pair(f'Deidentified Dataset: : PC{hc[0]}-PC{hc[1]}',
                                       f_sdf, h_syn_path, h_s_cp_o_path, s_cp_o_path, hc)
            plot_paths[strs.HIGHLIGHTED][(h_type, h_name, h_caption)] = \
                [h_tar_path, h_syn_path]

        # clear temporary data from report data
        remove_path(t_cp_o_path)
        remove_path(s_cp_o_path)

        return plot_paths


def min_max_scaling(series, min_val=None, max_val=None):
    if min_val is None:
        min_val = series.min()
    if max_val is None:
        max_val = series.max()

    return (series - min_val) / (max_val - min_val)


def plot_all_components_pairs(title: str,
                              data: pd.DataFrame,
                              file_path: Path,
                              component_pairs_path: Path,
                              color='b',):

    d = data
    cc = len(d.columns)
    cp_path = component_pairs_path
    f_path = file_path

    for ri, pc_i in enumerate(d.columns):
        for ci, pc_j in enumerate(d.columns):
            fig = plt.figure(figsize=(6, 6))
            ax = fig.add_axes([0, 0, 1, 1])
            ax.scatter(d[pc_j], d[pc_i], s=30, color=color)
            ax.set_xlim([-0.02, 1.02])
            ax.set_ylim([-0.02, 1.02])
            plt.savefig(Path(cp_path, f'{pc_j}_{pc_i}.png'),
                        pad_inches=0.0, dpi=100)
            plt.close(fig)

    fig, ax = plt.subplots(cc, cc, figsize=(6, 6))

    for i, pc_i in enumerate(d.columns):
        for j, pc_j in enumerate(d.columns):
            ax_t = ax[i, j]
            if pc_i == pc_j:
                ax_t.text(0.5, 0.5, pc_i,
                          ha='center', va='center', color='black', fontsize=30)
            else:
                img = mpimg.imread(Path(cp_path, f'{pc_j}_{pc_i}.png'))
                ax_t.imshow(img)
            ax_t.set_xlabel('')
            ax_t.set_ylabel('')
            ax_t.set_xticklabels([])
            ax_t.set_yticklabels([])
            ax_t.tick_params(length=0)

    plt.suptitle(title)
    plt.tight_layout()
    plt.savefig(f_path, bbox_inches='tight', dpi=100)
    plt.close(fig)


def plot_single_component_pair(title: str,
                               data: pd.DataFrame,
                               file_path: Path,
                               highlight_type_path: Path,
                               components_pairs_path: Path,
                               components_involved: List):
    ci = components_involved
    pc_x, pc_y = f'PC-{ci[0]}', f'PC-{ci[1]}'
    d = data
    fig = plt.figure(figsize=(6, 6))
    ax = fig.add_axes([0.05, 0.05, 0.9, 0.9])
    ax.set_xlim([-0.02, 1.02])
    ax.set_ylim([-0.02, 1.02])

    img = plt.imread(Path(components_pairs_path, f'{pc_x}_{pc_y}.png'))
    ax.imshow(img, extent=[-0.02, 1.02, -0.02, 1.02])
    ax.scatter(d[pc_x], d[pc_y], s=30, color='#fa5757')
    ax.set_xlabel(pc_x)
    ax.set_ylabel(pc_y)
    ax.set_xticklabels([])
    ax.set_yticklabels([])
    ax.tick_params(length=0)
    plt.title(title)
    plt.savefig(file_path, dpi=100)
    plt.close(fig)
    return file_path

