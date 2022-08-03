import os
import math
from typing import List, Dict, Tuple
from pathlib import Path

import matplotlib.cm
import matplotlib.pyplot as plt
from matplotlib import colors

import pandas as pd
import numpy as np

plt.style.use('seaborn-deep')


class GridPlot:
    def __init__(self,
                 scores: pd.DataFrame,
                 index_feature: str,
                 pinned_index_features: Dict[str, any],
                 output_directory: Path):
        """
        creates a grid plot where each grid block depicts k-marginal
        score of that block.

        Parameters
        ----------
            scores : pd.DataFrame
                Pandas dataframe containing k-marginal scores along with an index
            index_feature : str
                feature name for which to plot the grid
            pinned_index_features : Dict[str, any]
                dictionary containing feature names (other than the index_feature)
                and a value of the feature on which to pin the scores, i.e. only
                the given value of the feature is included in the index and rest
                all are ignored. This is required mostly if scores is indexed with
                multiple features, otherwise if scores has just a single feature which is
                the index_feature then the pinned_index_features dictionary can be empty.
            output_directory: pd.Dataframe
                path of the directory to which plots will be saved
        """
        self.scores = scores
        self.index_feature = index_feature
        self.pinned_index_features = pinned_index_features
        self.o_dir = output_directory
        self.plots_path = Path(self.o_dir, 'k_marginal_grid')
        self._setup()

    def _setup(self):
        if not self.o_dir.exists():
            raise Exception(f'Path {self.o_dir} does not exist. Cannot save plots')

        os.mkdir(self.plots_path)

    def save(self) -> List[Path]:
        s = self.scores
        for k, v in self.pinned_index_features.items():
            s = s[s[k] == v]
        data_len = len(self.scores[self.index_feature].unique())
        grid_size = np.ceil(np.sqrt(data_len)).astype(int)
        grid_rows = grid_size
        grid_cols = grid_size
        if grid_size ** 2 - data_len >= grid_size:
            grid_rows = grid_size - 1

        grid_data = np.array(s['score'])
        grid_data.resize(grid_rows * grid_cols, refcheck=False)
        grid_data = grid_data.reshape(grid_rows, grid_cols)
        grid_labels = np.array(s[self.index_feature])
        grid_labels.resize(grid_rows * grid_cols, refcheck=False)
        grid_labels = grid_labels.reshape(grid_rows, grid_cols)
        title = f'{self.index_feature} score in '
        title = title + ' '.join([f'{k}: {v}'
                                  for k, v in self.pinned_index_features.items()])
        return save_grid_plots(title, grid_data, grid_labels, self.plots_path)


def save_grid_plots(title: str, grid_data, grid_labels, output_directory: Path) -> List[Path]:
    gd = grid_data
    gl = grid_labels

    fig, ax = plt.subplots(figsize=(4, 4))
    fig.set_dpi(100)
    plt.imshow(gd, cmap='GnBu', vmin=0, vmax=1000)
    im_ratio = gd.shape[0]/gd.shape[1]

    cbar = plt.colorbar(fraction=0.047 * im_ratio,
                        boundaries=np.linspace(0, 1000),
                        ticks=np.arange(0, 1000, 200))
    cbar.ax.tick_params(labelsize=10)
    # Create white grid.
    # ax.set_xticks(np.arange(gd.shape[1] + 1) - .5, minor=True)
    # ax.set_yticks(np.arange(gd.shape[0] + 1) - .5, minor=True)
    ax.grid(which="minor", color="w", linestyle='-', linewidth=2)
    ax.grid(which="major", visible=False)

    # Loop over data dimensions and create text annotations.
    for i in range(gd.shape[0]):
        for j in range(gd.shape[1]):
            if gd[i, j] > 800:
                text = ax.text(j, i, gl[i, j],
                               ha="center", va="center", color="w", fontsize=7)
            else:
                text = ax.text(j, i, gl[i, j],
                               ha="center", va="center", color="k", fontsize=7)

    ax.set_title(title, fontsize=12)
    plt.xticks(fontsize=10)
    plt.yticks(fontsize=10)
    plt.axis('off')
    file_path = Path(output_directory, f'k_marginal_grid.jpg')
    fig.tight_layout()
    plt.savefig(file_path)
    plt.close()

    return [file_path]

