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
    """
    Converts data frame containing unique value pairs and counts
    into a counts matrix.
    """
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
    """
    Normalize counts matrix along each row.
    """
    cm_df = counts_matrix_df

    for i, row in cm_df.iterrows():
        r_sum = sum(row)
        if r_sum and r_sum >= 20:
            cm_df.loc[i, :] = cm_df.loc[i, :] / r_sum
        else:
            cm_df.loc[i, :] = 0
    return cm_df


class LinearRegressionMetric:
    """
    Metric for comparing target and deidentified data using linear
    regression model. Linear regression is performed between features
    EDU and PINCP_DECILE, where EDU is input and PINCP_DECILE output.
    Also, creates density grid plots these two features. Density
    plots have counts of  records for each unique value pair of EDU-PINCP_DECILE.
    For density plots, counts in cell are normalized along each EDU value.
    """

    NAME = 'Linear Regression'

    def __init__(self,
                 target: pd.DataFrame,
                 synthetic: pd.DataFrame,
                 data_dictionary: Dict,
                 output_directory: Path):
        self.tar = target
        self.syn = synthetic
        self.d_dict = data_dictionary
        self.o_path = output_directory  # linear regression report output path
        self.xc = 'EDU'  # input for regression
        self.yc = 'PINCP_DECILE'  # output for regression

        # subset of target data
        self.ts = None
        # subset of deidentified data
        self.ss = None

        # outputs
        self.tcm = None  # target data density counts
        self.scm = None  # synthetic data density counts
        self.diff = None

        self.t_reg = None  # target data regression instance
        self.s_reg = None  # deidentified data regression instance

        # slope and intercept found for target data regression line
        self.t_slope = 0
        self.t_intercept = 0
        # slope and intercept found for deidentified data regression line
        self.s_slope = 0
        self.s_intercept = 0

        # regression metric statistics for json report
        self.report_data = None

        self._setup()

    def _setup(self):
        """
        Creates paths for the linear regression report output
        """
        create_path(self.o_path)

    def compute(self):
        """
        Compute linear regression of target and deidentified data.
        Compute density metrices for target and deidentified data.
        """
        t = self.tar
        s = self.syn
        xc = self.xc  # x axis feature or input feature
        yc = self.yc  # y axis feature or output feature

        # take subset of target and deidentified data
        self.ts = t[[xc, yc]]
        self.ss = s[[xc, yc]]

        # Records counts xc and yc value pairs in target and deidentified data
        t_xy_counts = self.ts.groupby([xc, yc]).size().reset_index(name='count')
        s_xy_counts = self.ss.groupby([xc, yc]).size().reset_index(name='count')

        # unique x feature values
        x_values = [int(v) for v in self.d_dict[xc]['values'] if v != 'N'] + [0]
        # unique y feature values
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

        # calculated difference of density distribution
        # between target and deindentifed data
        self.diff = self.tcm - self.scm

        # calculate regression lines for target and synthetic data
        if self.ts.shape[0] > 1 and len(self.ts[xc].unique()) > 1:
            self.t_reg = stats.linregress(self.ts[xc].astype(float), self.ts[yc].astype(float))
            self.t_slope = round(self.t_reg.slope, 2)
            self.t_intercept = round(self.t_reg.intercept, 2)

        if self.ss.shape[0] > 1 and len(self.ss[xc].unique()) > 1:
            self.s_reg = stats.linregress(self.ss[xc].astype(float), self.ss[yc].astype(float))
            self.s_slope = round(self.s_reg.slope, 2)
            self.s_intercept = round(self.s_reg.intercept, 2)

    def plots(self) -> List[Path]:
        """
        Create plots for target and deidentified data's density distribution and
        overlay regression lines on the density grid.
        Also saves the plots to the regression metric report output directory.
        Saves regression metric statistics to the json report data dictionary.
        """

        # -------- Creates and saves plots for target and deidentified data
        fig, ax = plt.subplots(1, 2, figsize=(10, 3.3))
        plt.subplots_adjust(wspace=0.9)
        ax0 = ax[0]
        ax1 = ax[1]

        apc0 = ax0.pcolor(self.tcm, cmap='rainbow', vmin=0, vmax=0.5)
        fig.colorbar(apc0, ax=ax0)

        apc1 = ax1.pcolor(self.diff, cmap='PuOr', vmin=-0.3, vmax=0.3)
        fig.colorbar(apc1, ax=ax1)

        tx = self.ts[self.xc].values

        r_tx_df = pd.DataFrame([[_ + 0.5, self.t_intercept + self.t_slope * (_ + 0.5)]
                                for _ in tx], columns=['x', 'y'])
        r_tx_df = r_tx_df[(r_tx_df['y'] >= 0) & (r_tx_df['y'] <= 10)]
        r_sx_df = pd.DataFrame([[_ + 0.5, self.s_intercept + self.s_slope * (_ + 0.5)]
                                for _ in tx], columns=['x', 'y'])
        r_sx_df = r_sx_df[(r_sx_df['y'] >= 0) & (r_sx_df['y'] <= 10)]

        ax0.plot(r_tx_df['x'],
                 r_tx_df['y'], color='red', label='Target')
        ax1.plot(r_tx_df['x'],
                 r_tx_df['y'], color='red')
        ax1.plot(r_sx_df['x'],
                 r_sx_df['y'], color='green', label='Deid.')

        ax0.set_xlabel(self.xc)
        ax0.set_ylabel(self.yc)
        ax1.set_xlabel(self.xc)

        ax0.set_title('Target Distribution Density')
        ax1.set_title('Diff. Between Target and Deid. Density')
        fig.legend(loc=7, title='Regression')
        plt.tight_layout()
        fig.subplots_adjust(right=0.88)
        file_path = Path(self.o_path, 'density_plot.svg')
        plt.savefig(file_path, bbox_inches='tight', dpi=100)
        plt.suptitle('Comparison between ')
        plt.close()

        # --------- saves regression metric statistics to json report dictionary
        self.report_data = {
            "target_counts": relative_path(save_data_frame(self.tcm,
                                                           self.o_path,
                                                           'target_counts'), level=3),
            "target_deidentified_counts_difference": relative_path(save_data_frame(self.diff,
                                                                self.o_path,
                                                                "target_deidentified_counts_difference"),
                                                                   level=3),
            "target_deidentified_difference_plot": relative_path(file_path, level=3),
            "target_regression_slope_and_intercept": (self.t_slope, self.t_intercept),
            "deidentified_regression_slope_and_intercept": (self.s_slope, self.s_intercept)
        }

        return [file_path]
