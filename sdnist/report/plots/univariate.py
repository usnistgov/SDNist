import os
from typing import Dict, List, Optional
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import entropy

from strs import *

plt.style.use('seaborn-deep')


class UnivariatePlots:
    def __init__(self,
                 synthetic: pd.DataFrame,
                 target: pd.DataFrame,
                 schema: Dict[str, any],
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
            schema : Dict[str, any]
                schema containing description of datasets
            output_directory: pd.Dataframe
                path of the directory to which plots will be saved
            challenge: str
                For which challenge type to compute univariates for, CENSUS or TAXI
            n : pd.Dataframe
                n worst performing univariates to save plots for
        """
        self.syn = synthetic
        self.tar = target
        self.schema = schema
        self.o_dir = output_directory
        self.plots_path = Path(self.o_dir, 'worst_univariates')
        self.n = n
        self.challenge = challenge
        self._setup()

    def _setup(self):
        if not self.o_dir.exists():
            raise Exception(f'Path {self.o_dir} does not exist. Cannot save plots')

        os.mkdir(self.plots_path)

    def save(self) -> List[Path]:
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
        # select 3 features with worst divergence
        div_df = div_df.head(3)

        return save_distribution_plot(self.syn,
                                      self.tar,
                                      div_df[FEATURE].tolist(),
                                      self.plots_path)


def save_distribution_plot(synthetic: pd.DataFrame,
                           target: pd.DataFrame,
                           features: List,
                           output_directory: Path):
    o_dir = output_directory
    bar_width = 0.4
    saved_file_paths = []
    for f in features:
        val_df = pd.DataFrame(target[f].unique().tolist(), columns=[f])
        t_counts_df = target.groupby(by=f)[f].size().reset_index(name='count_target')
        s_counts_df = synthetic.groupby(by=f)[f].size().reset_index(name='count_synthetic')
        merged = pd.merge(left=val_df, right=t_counts_df, on=f, how='left')\
            .fillna(0)
        merged = pd.merge(left=merged, right=s_counts_df, on=f, how='left')\
            .fillna(0)
        merged = merged.sort_values(by=f)

        x_axis = np.arange(merged.shape[0])
        plt.bar(x_axis - 0.2, merged['count_target'], width=bar_width, label=TARGET)
        plt.bar(x_axis + 0.2, merged['count_synthetic'], width=bar_width, label=SYNTHETIC)
        plt.xlabel('Record Counts')
        plt.ylabel(f'{f} Feature Values')
        plt.gca().set_xticks(x_axis, merged[f].values.tolist())
        plt.legend(loc='upper right')
        plt.title(f)
        file_path = Path(o_dir, f'{f}.jpg')
        plt.savefig(Path(o_dir, f'{f}.jpg'))
        plt.close()
        saved_file_paths.append(file_path)
    return saved_file_paths


def divergence(synthetic: pd.DataFrame,
               target: pd.DataFrame,
               schema: Dict[str, any],
               ignore_features: Optional[List[str]] = None):
    if not ignore_features:
        ignore_features = []

    div_data = []  # divergence data
    for var, var_schema in schema.items():
        if VALUES not in var_schema or var in ignore_features:
            continue
        values = var_schema[VALUES]
        val_df = pd.DataFrame(values, columns=[var])

        s_counts_df = synthetic.groupby(by=var)[var].size().reset_index(name=COUNT)
        t_counts_df = target.groupby(by=var)[var].size().reset_index(name=COUNT)

        s_counts_df = pd.merge(left=val_df, right=s_counts_df, on=var, how='left', sort=True)\
            .fillna(0)
        t_counts_df = pd.merge(left=val_df, right=t_counts_df, on=var, how='left', sort=True)\
            .fillna(0)

        div = entropy(pk=s_counts_df[COUNT],
                      qk=t_counts_df[COUNT])
        div_data.append([var, div])

    return pd.DataFrame(div_data, columns=[FEATURE, DIVERGENCE])\
        .sort_values(by=DIVERGENCE, ascending=False)
