import os

from typing import List
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from sdnist.metrics.apparent_match_dist import \
    cellchange, apparent_match_distribution_plot
from sdnist.report.strs import *

plt.style.use('seaborn-deep')


class ApparentMatchDistributionPlot:
    def __init__(self,
                 synthetic: pd.DataFrame,
                 target: pd.DataFrame,
                 output_directory: Path,
                 quasi_features: List[str],
                 exclude_features: List[str]):
        """
        Computes and plots apparent records match distribution between
        synthetic and target data

        Parameters
        ----------
            synthetic : pd.Dataframe
                synthetic dataset
            target : pd.Dataframe
                target dataset
            output_directory: pd.Dataframe
                path of the directory to which plots will will be saved
            quasi_features: List[str]
                Subset of features for which to find apparent record matches
            exclude_features:
                features to exclude from matching between dataset
        """
        self.syn = synthetic
        self.tar = target
        self.o_dir = output_directory
        self.plots_path = Path(self.o_dir, 'apparent_match_distribution')
        self.quasi_features = quasi_features
        self.exclude_features = exclude_features

        self._setup()

    def _setup(self):
        if not self.o_dir.exists():
            raise Exception(f'Path {self.o_dir} does not exist. Cannot save plots')

        os.mkdir(self.plots_path)

    def save(self) -> List[Path]:
        percents, u1, u2, mu = cellchange(self.syn, self.tar,
                                          self.quasi_features,
                                          self.exclude_features)
        save_file_path = apparent_match_distribution_plot(percents,
                                                          self.plots_path)
        return [save_file_path]
