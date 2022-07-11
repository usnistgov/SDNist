import os

from typing import List
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from sdnist.metrics.apparent_match_dist import cellchange

# plt.style.use('seaborn-deep')


def plot_apparent_match_dist(match_percentages: pd.Series,
                             output_directory: Path) -> Path:
    plt.figure(figsize=(8, 6))
    plt.title(
        'Percentage of Matched Records')
    match_percentages.hist()
    plt.xlim(0, 100)
    ax = plt.gca()
    ax.grid(False)
    ax.locator_params(axis='y', integer=True)
    plt.xlabel('Match Percentage', fontsize=14)
    plt.ylabel('Number of Records', fontsize=14)
    out_file = Path(output_directory, f'apparent_match_distribution.jpg')
    plt.savefig(out_file)
    plt.close()
    return out_file


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
        self.quasi_matched_df = pd.DataFrame()
        self._setup()

    def _setup(self):
        if not self.o_dir.exists():
            raise Exception(f'Path {self.o_dir} does not exist. Cannot save plots')

        os.mkdir(self.plots_path)

    def save(self) -> List[Path]:
        percents, u1, u2, mu = cellchange(self.syn, self.tar,
                                          self.quasi_features,
                                          self.exclude_features)
        self.quasi_matched_df = mu
        save_file_path = plot_apparent_match_dist(percents,
                                                  self.plots_path)
        return [save_file_path]
