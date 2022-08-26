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
    def __init__(self, target: pd.DataFrame, synthetic: pd.DataFrame, output_directory: Path):
        self.tar = target
        self.syn = synthetic
        self.t_pdf = None
        self.s_pdf = None
        self.out_dir = output_directory
        self.o_path = Path(self.out_dir, 'pca')
        self.report_data = dict()

        self._setup()

    def _setup(self):
        if not self.out_dir.exists():
            raise Exception(f'Path {self.out_dir} does not exist. Cannot save plots')
        if not self.o_path.exists():
            os.mkdir(self.o_path)

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
            qc = [ f'{v[0]} ({v[1]})' for v in qc]
            self.t_comp_data.append({"Principal Component": f"PC-{i}",
                                      "Features Contribution: "
                                      "feature-name (contribution ratio)": ','.join(qc[:5])})
        comp_df = pd.DataFrame(t_pca.components_,
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

        self.report_data = {
            "components": relative_path(save_data_frame(comp_df,
                                                        self.o_path,
                                                        'components')),
            "target_transformed": relative_path(save_data_frame(self.t_pdf,
                                                                self.o_path,
                                                                'target_transformed')),
            "synthetic_transformed": relative_path(save_data_frame(self.s_pdf,
                                                                   self.o_path,
                                                                   'synthetic_transformed'))
        }

    def plot(self):
        tar_path = Path(self.o_path, 'target.jpg')
        syn_path = Path(self.o_path, 'synthetic.jpg')

        self.report_data['plot_target'] = relative_path(tar_path)
        self.report_data['plot_synthetic'] = relative_path(syn_path)

        plot_pca('Target Dataset', self.t_pdf, tar_path, color='#5373d8')
        plot_pca('Synthetic Dataset', self.s_pdf, syn_path, color='#4eb07a')

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
                           x=pc_i, y=pc_j, c='none',
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


def delete_str_features(data):
    df = data
    cols_to_remove = []

    for col in df.columns:
        try:
            _ = df[col].astype(float)
        except ValueError:
            print('Couldn\'t covert %s to float' % col)
            cols_to_remove.append(col)
            pass

    # keep only the columns in df that do not contain string
    df = df[[col for col in df.columns if col not in cols_to_remove]]
    return df


if __name__ == "__main__":
    THIS_DIR = Path(__file__).parent
    OUT_DIR = Path(THIS_DIR, '')

    TDF = Path(THIS_DIR, '..', 'sdnist_toy_data/TX_ACS_EXCERPT_2019.csv')
    SDF = Path(THIS_DIR, '..', 'syn_data/ma/SYN_TX_ACS_SYNTHPOP.csv')

    tdf = pd.read_csv(TDF)
    sdf = pd.read_csv(SDF)
    tdf = delete_str_features(tdf)
    sdf = delete_str_features(sdf)

    cc = 5
    t_pca = PCA(n_components=cc)
    s_pca = PCA(n_components=cc)

    tdf_v = tdf.values
    sdf = sdf.apply(lambda x: x-x.mean())
    sdf_v = sdf.values

    tdf_v = StandardScaler().fit_transform(tdf_v)

    t_pc = t_pca.fit_transform(tdf_v)
    s_pc = s_pca.fit_transform(sdf_v)

    t_ev = np.array(t_pca.components_)
    s_pc = np.matmul(sdf_v, t_ev.T)

    print(t_pca.components_)
    print(t_pca.explained_variance_)
    print()
    print(s_pca.components_)
    print(s_pca.explained_variance_)

    t_pdf = pd.DataFrame(data=t_pc,
                         columns=[f'PC-{i}'
                                  for i in range(cc)],
                         index=tdf.index)

    s_pdf = pd.DataFrame(data=s_pc,
                         columns=[f'PC-{i}'
                                  for i in range(cc)],
                         index=sdf.index)

    plot_pca(t_pdf, 'pca_tar.png', 'b')
    plot_pca(s_pdf, 'pca_syn.png', 'r')







