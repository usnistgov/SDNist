import os
from typing import Dict, List, Optional
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import entropy

from sdnist.report import Dataset
from sdnist.strs import *
from sdnist.utils import *

plt.style.use('seaborn-deep')


def l1(pk: List[int], qk: List[int]):
    pk_max = max(pk)
    qk_max = max(qk)

    if pk_max == 0:
        pk_n = [0 for p in pk]
    else:
        pk_n = [p/pk_max for p in pk]

    if qk_max == 0:
        qk_n = [0 for q in qk]
    else:
        qk_n = [q/qk_max for q in qk]

    div = sum([abs(p-q) for p, q in zip(pk_n, qk_n)])

    return div


class UnivariatePlots:
    def __init__(self,
                 synthetic: pd.DataFrame,
                 target: pd.DataFrame,
                 dataset: Dataset,
                 output_directory: Path,
                 challenge: str = CENSUS,
                 n: int = 3):
        """
        Computes and creates univariate distribution plots of the worst
        performing variables in synthetic data

        Parameters
        ----------
            synthetic : pd.Dataframe
                synthetic dataset
            target : pd.Dataframe
                target dataset
            dataset : Dataset
                dataset object
            output_directory: pd.Dataframe
                path of the directory to which plots will be saved
            challenge: str
                For which challenge type to compute univariates for, CENSUS or TAXI
            n : pd.Dataframe
                n worst performing univariates to save plots for
        """
        self.syn = synthetic
        self.tar = target

        self.schema = dataset.schema
        self.dataset = dataset
        self.o_dir = output_directory
        self.out_path = Path(self.o_dir, 'univariate')
        self.n = n
        self.challenge = challenge
        self.feat_data = dict()
        self._setup()

        self.div_data = None  # feature divergence data
        self.uni_counts = dict()  # univariate counts of target and synthetic data

    def _setup(self):
        if not self.o_dir.exists():
            raise Exception(f'Path {self.o_dir} does not exist. Cannot save plots')
        os.mkdir(self.out_path)

    def report_data(self):
        return {"divergence": relative_path(save_data_frame(self.div_data,
                                                            self.out_path,
                                                            'divergence')),
                "counts": self.uni_counts}

    def save(self) -> Dict:
        if self.challenge == CENSUS:
            ignore_features = ['PUMA', 'YEAR']
        elif self.challenge == TAXI:
            ignore_features = ['pickup_community_area', 'shift', 'company_id']
        else:
            raise Exception(f'Invalid Challenge Name: {self.challenge}. '
                            f'Unable to save univariate plots')
        # divergence dataframe
        div_df = divergence(self.syn,
                            self.tar,
                            self.schema, ignore_features)
        self.div_data = div_df
        # select 3 features with worst divergence
        # div_df = div_df.head(3)

        self.save_distribution_plot(self.dataset,
                                    self.syn,
                                    self.tar,
                                    div_df[FEATURE].tolist(),
                                    self.out_path)
        return self.feat_data

    def save_distribution_plot(self,
                               dataset: Dataset,
                               synthetic: pd.DataFrame,
                               target: pd.DataFrame,
                               features: List,
                               output_directory: Path):
        ds = dataset
        o_path = output_directory
        bar_width = 0.4
        saved_file_paths = []
        INDP = 'INDP'
        INDP_CAT = "INDP_CAT"
        o_tar = ds.target_data.loc[target.index]
        o_syn = ds.synthetic_data.loc[synthetic.index]

        for i, f in enumerate(features):
            self.uni_counts[f] = dict()
            if f == INDP and INDP_CAT in target.columns.tolist():
                all_sectors = o_tar[INDP_CAT].unique().tolist()
                set(all_sectors).update(set(o_syn[INDP_CAT].unique().tolist()))
                selected = []
                for s in all_sectors:
                    if s == 'N':
                        continue
                    st_df = o_tar[o_tar[INDP_CAT].isin([s])]
                    ss_df = o_syn[o_syn[INDP_CAT].isin([s])]

                    unique_ind_codes = st_df[INDP].unique().tolist()
                    set(unique_ind_codes).update(set(ss_df[INDP].unique().tolist()))
                    unique_ind_codes = list(unique_ind_codes)
                    val_df = pd.DataFrame(unique_ind_codes, columns=[f])

                    t_counts_df = st_df.groupby(by=f)[f].size().reset_index(name='count_target')
                    s_counts_df = ss_df.groupby(by=f)[f].size().reset_index(name='count_synthetic')
                    merged = pd.merge(left=val_df, right=t_counts_df, on=f, how='left')\
                        .fillna(0)
                    merged = pd.merge(left=merged, right=s_counts_df, on=f, how='left')\
                        .fillna(0)
                    div = l1(pk=merged['count_target'], qk=merged['count_synthetic'])
                    selected.append([merged, div, s])
                selected = sorted(selected, key=lambda l: l[1], reverse=True)

                for j, data in enumerate(selected):
                    merged = data[0]
                    div = data[1]
                    s = data[2]
                    merged = merged.sort_values(by=f)
                    x_axis = np.arange(merged.shape[0])
                    plt.figure(figsize=(8, 3), dpi=100)
                    plt.bar(x_axis - 0.2, merged['count_target'], width=bar_width, label=TARGET)
                    plt.bar(x_axis + 0.2, merged['count_synthetic'], width=bar_width, label=SYNTHETIC)
                    plt.xlabel('Feature Values')
                    plt.ylabel('Record Counts')
                    plt.gca().set_xticks(x_axis, merged[f].values.tolist())
                    plt.legend(loc='upper right')
                    if merged.shape[0] > 30:
                        plt.xticks(fontsize=6, rotation=90)
                    else:
                        plt.xticks(fontsize=8, rotation=45)
                    plt.tight_layout()
                    title = f'Industries in Industry Category ' \
                            f'{dataset.data_dict["INDP_CAT"]["values"][s]}'
                    plt.title(title,
                              fontdict={'fontsize': 12})

                    file_path = Path(o_path, f'indp_indp_cat_{s}.jpg')
                    plt.savefig(file_path, bbox_inches='tight')

                    plt.close()
                    self.uni_counts[f][f"Industry Category {s}"] = {
                        "divergence": div,
                        "counts": relative_path(save_data_frame(merged,
                                                o_path,
                                                f"Industry Category {s}")),
                        "plot": relative_path(file_path)
                    }
                    if j < 2:
                        saved_file_paths.append(file_path)

                        self.feat_data[title] = {
                            "path": file_path
                        }
            else:
                plt.figure(figsize=(8, 3), dpi=100)
                file_path = Path(o_path, f'{f}.jpg')
                values = set(target[f].unique().tolist()).union(synthetic[f].unique().tolist())
                values = sorted(values)
                val_df = pd.DataFrame(values, columns=[f])
                t_counts_df = target.groupby(by=f)[f].size().reset_index(name='count_target')
                s_counts_df = synthetic.groupby(by=f)[f].size().reset_index(name='count_synthetic')
                merged = pd.merge(left=val_df, right=t_counts_df, on=f, how='left')\
                    .fillna(0)
                merged = pd.merge(left=merged, right=s_counts_df, on=f, how='left')\
                    .fillna(0)
                # merged = merged.sort_values(by=f)
                title = f"{f}: {dataset.data_dict[f]['description']}"
                c_sort_merged = merged.sort_values(by='count_target', ascending=False)
                c_sort_merged = c_sort_merged.reset_index(drop=True)

                c_vals = c_sort_merged['count_target'].head(2).values
                c1, c2 = c_vals[0], c_vals[1]


                self.uni_counts[f] = {
                    "counts": relative_path(save_data_frame(c_sort_merged.copy(),
                                                            o_path,
                                                            f'{f}_counts')),
                    "plot": relative_path(file_path)
                }

                if i < 3:
                    self.feat_data[title] = dict()
                    if c1 >= c2*3 or f in ['PINCP']:
                        f_val = c_sort_merged.loc[0, f]
                        f_tc = c_sort_merged.loc[0, 'count_target']
                        f_sc = c_sort_merged.loc[0, 'count_synthetic']
                        c_sort_merged = c_sort_merged[~c_sort_merged[f].isin([f_val])]
                        self.feat_data[title] = {
                            "excluded": {
                                "feature_value": f_val,
                                "target_counts": int(f_tc),
                                "synthetic_counts": int(f_sc)
                            }
                        }

                merged = c_sort_merged.sort_values(by=f)

                x_axis = np.arange(merged.shape[0])
                plt.bar(x_axis - 0.2, merged['count_target'], width=bar_width, label=TARGET)
                plt.bar(x_axis + 0.2, merged['count_synthetic'], width=bar_width, label=SYNTHETIC)
                plt.xlabel('Feature Values')
                plt.ylabel('Record Counts')
                vals = merged[f].values.tolist()

                if f in ['AGEP', 'POVPIP', 'PINCP']:
                    updated_vals = []
                    for v in vals:
                        mv1 = o_tar[target[f].isin([v])][f].values.tolist()
                        #TODO fix me
                        # t = synthetic[f].isin([v])
                        # mv2 = ds.synthetic_data[synthetic[f].isin([v])][f].values.tolist()
                        mv = mv1
                        if len(mv) and v != -1:
                            nv = min(mv)
                            updated_vals.append(nv)
                        else:
                            updated_vals.append(v)
                    vals = updated_vals

                vals = [str(v) for v in vals]
                if "-1" in vals:
                    idx = vals.index("-1")
                    vals[idx] = "N"

                plt.gca().set_xticks(x_axis, vals)
                plt.legend(loc='upper right')
                plt.xticks(fontsize=8, rotation=45)
                plt.tight_layout()

                plt.title(title,
                          fontdict={'fontsize': 12})

                plt.savefig(Path(o_path, f'{f}.jpg'), bbox_inches='tight')
                plt.close()

                if i < 3:
                    saved_file_paths.append(file_path)
                    self.feat_data[title]['path'] = file_path
        return saved_file_paths


def divergence(synthetic: pd.DataFrame,
               target: pd.DataFrame,
               schema: Dict[str, any],
               ignore_features: Optional[List[str]] = None):
    if not ignore_features:
        ignore_features = []

    div_data = []  # divergence data
    tfeats = target.columns.tolist()
    sfeats = synthetic.columns.tolist()
    for var, var_schema in schema.items():
        if var not in tfeats or var not in sfeats:
            continue
        if var in ignore_features:
            continue
        values = set(target[var].unique().tolist()).union(synthetic[var].unique().tolist())
        values = sorted(values)
        val_df = pd.DataFrame(values, columns=[var])

        s_counts_df = synthetic.groupby(by=var)[var].size().reset_index(name=COUNT)
        t_counts_df = target.groupby(by=var)[var].size().reset_index(name=COUNT)

        s_counts_df = pd.merge(left=val_df, right=s_counts_df, on=var, how='left', sort=True)\
            .fillna(0)
        t_counts_df = pd.merge(left=val_df, right=t_counts_df, on=var, how='left', sort=True)\
            .fillna(0)

        div = l1(pk=s_counts_df[COUNT], qk=t_counts_df[COUNT])
        div_data.append([var, div])

    return pd.DataFrame(div_data, columns=[FEATURE, DIVERGENCE])\
        .sort_values(by=DIVERGENCE, ascending=False)
