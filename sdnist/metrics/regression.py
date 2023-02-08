import os
from typing import List, Dict
from pathlib import Path
import pandas as pd
from scipy import stats

import matplotlib.pyplot as plt
plt.style.use('seaborn-deep')

from sdnist.utils import *


def convert_counts_to_matrix(target_df: pd.DataFrame,
                             counts_df: pd.DataFrame,
                             x_column: str,
                             y_column: str,
                             x_values: List[int],
                             y_values: List[int]) -> pd.DataFrame:
    tar = target_df
    cdf = counts_df
    xc = x_column
    yc = y_column

    xc_u = sorted(x_values)
    yc_u = sorted(y_values)

    # counts matrix
    counts_mat = [[0 for yi in range(len(yc_u))]
                  for xi in range(len(xc_u))]

    for xv in range(len(xc_u)):
        for yv in range(len(yc_u)):
            sub = cdf[(cdf[xc] == xv) & (cdf[yc] == yv)]
            if sub.shape[0]:
                counts_mat[xv][yv] = sub.values[0][2]

    # counts matrix dataframe
    cm_df = pd.DataFrame(counts_mat, columns=yc_u, index=xc_u)
    return cm_df


def normalize_on_x(counts_matrix_df: pd.DataFrame) -> pd.DataFrame:
    cm_df = counts_matrix_df

    for i, row in cm_df.iterrows():
        r_sum = sum(row)
        if r_sum and r_sum > 20:
            cm_df.loc[i, :] = cm_df.loc[i, :] / r_sum
        else:
            cm_df.loc[i, :] = 0
    return cm_df


class LinearRegressionMetric:
    NAME = 'Linear Regression'

    def __init__(self,
                 target: pd.DataFrame,
                 synthetic: pd.DataFrame,
                 data_dictionary: Dict,
                 output_directory: Path):
        self.tar = target
        self.syn = synthetic
        self.d_dict = data_dictionary
        self.o_path = output_directory
        self.xc = 'EDU'
        self.yc = 'PINCP_DECILE'

        self.ts = None
        self.ss = None

        # outputs
        self.tcm = None
        self.scm = None
        self.diff = None

        self.t_reg = None
        self.s_reg = None
        self.t_slope = 0
        self.t_intercept = 0
        self.s_slope = 0
        self.s_intercept = 0

        self.report_data = None

        self._setup()

    def _setup(self):
        create_path(self.o_path)

    def compute(self):
        t = self.tar
        s = self.syn
        xc = self.xc
        yc = self.yc
        self.ts = t[[xc, yc]]
        self.ss = s[[xc, yc]]

        t_xy_counts = self.ts.groupby([xc, yc]).size().reset_index(name='count')
        s_xy_counts = self.ss.groupby([xc, yc]).size().reset_index(name='count')
        x_values = [int(v) for v in self.d_dict[xc]['values'] if v != 'N'] + [0]
        y_values = [int(v) for v in self.d_dict[yc]['values'] if v != 'N']
        # target data x y pair counts matrix
        tcm = convert_counts_to_matrix(self.ts, t_xy_counts, xc, yc, x_values, y_values)

        # synthetic data x y pair counts matrix
        scm = convert_counts_to_matrix(self.ts, s_xy_counts, xc, yc, x_values, y_values)

        # normalize counts per x value
        self.tcm = normalize_on_x(tcm)
        self.scm = normalize_on_x(scm)
        self.tcm = self.tcm.transpose()
        self.scm = self.scm.transpose()

        self.diff = self.tcm - self.scm
        # min_diff = min(self.diff)
        # if min_diff < 0:
        #     self.diff = self.diff - min_diff

        # calculate regression lines for target and synthetic data
        self.t_reg = stats.linregress(self.ts[xc], self.ts[yc])
        self.s_reg = stats.linregress(self.ss[xc], self.ss[yc])
        self.t_slope = round(self.t_reg.slope, 3)
        self.t_intercept = round(self.t_reg.intercept, 3)
        self.s_slope = round(self.s_reg.slope, 3)
        self.s_intercept = round(self.s_reg.intercept, 3)

    def plots(self) -> List[Path]:
        fig, ax = plt.subplots(1, 2, figsize=(10, 3.3))
        plt.subplots_adjust(wspace=0.9)
        ax0 = ax[0]
        ax1 = ax[1]

        apc0 = ax0.pcolor(self.tcm, cmap='rainbow', vmin=0, vmax=0.5)
        fig.colorbar(apc0, ax=ax0)

        apc1 = ax1.pcolor(self.diff, cmap='PuOr', vmin=-0.5, vmax=0.5)
        fig.colorbar(apc1, ax=ax1)
        # ax1.pcolor(self.scm, cmap='rainbow', vmin=0, vmax=0.5)
        tx = self.ts[self.xc].values
        sx = self.ss[self.xc].values
        ax0.plot(tx,
                 self.t_reg.intercept + self.t_reg.slope * tx, color='red', label='Target')
        ax1.plot(tx,
                 self.t_reg.intercept + self.t_reg.slope * tx, color='red')
        ax1.plot(tx,
                 self.s_reg.intercept + self.s_reg.slope * tx, color='green', label='Synthetic')
        ax0.set_xlabel(self.xc)
        ax0.set_ylabel(self.yc)
        ax1.set_xlabel(self.xc)
        # ax1.set_ylabel(self.yc)
        ax0.set_title('Target Data Pair Counts')
        ax1.set_title('Pair Counts Difference From Target')
        fig.legend(loc=7)
        plt.tight_layout()
        fig.subplots_adjust(right=0.88)
        file_path = Path(self.o_path, 'regression.svg')
        plt.savefig(file_path, bbox_inches='tight', dpi=100)
        plt.suptitle('Comparison between ')
        plt.close()
        self.report_data = {
            "target_counts": relative_path(save_data_frame(self.tcm,
                                                           self.o_path,
                                                           'target_counts')),
            "target_synthetic_counts_difference": relative_path(save_data_frame(self.diff,
                                                                self.o_path,
                                                                "target_synthetic_counts_difference")),
            "target_synthetic_difference_plot": relative_path(file_path),
            "target_regression_slope_and_intercept": (self.t_slope, self.t_intercept),
            "synthetic_regression_slope_and_intercept": (self.s_slope, self.s_intercept)
        }

        return [file_path]
