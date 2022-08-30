import os
from typing import List
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

from sdnist.utils import *


class PearsonCorrelationPlot:
    def __init__(self,
                 correlation_differences: pd.DataFrame,
                 output_directory: Path):
        self.cd = correlation_differences
        self.o_dir = output_directory
        self.o_path = Path(self.o_dir, 'pearson_correlation')

        self.report_data = dict()
        self._setup()

    def _setup(self):
        if not self.o_dir.exists():
            raise Exception(f'Path {self.o_dir} does not exist. Cannot save plots')
        if not self.o_path.exists():
            os.mkdir(self.o_path)

    def save(self) -> List[Path]:
        file_path = Path(self.o_path, 'pearson_corr_diff.jpg')

        self.report_data = {
            "correlation_difference": relative_path(save_data_frame(self.cd,
                                                                    self.o_path,
                                                                    'correlation_difference')),
            "plot": relative_path(file_path)
        }

        cd = self.cd.reindex(sorted(self.cd.columns), axis=1)
        cd = cd.sort_index()
        cd = cd.abs()
        fig = plt.figure(figsize=(6, 6), dpi=100)
        max_val = cd.to_numpy().max()
        v_max = max_val if max_val > 0.15 else 0.15
        plt.imshow(cd, cmap='Blues', interpolation='none', vmin=0, vmax=v_max)
        im_ratio = cd.shape[0] / cd.shape[1]
        cbar = plt.colorbar(fraction=0.047 * im_ratio)
        plt.xticks(range(cd.shape[1]), cd.columns)
        plt.xticks(rotation=90)
        plt.yticks(range(cd.shape[0]), cd.index)
        plt.title('Pearson Correlation Diff. between Target and Synthetic')
        fig.tight_layout()
        plt.savefig(file_path, bbox_inches='tight')
        plt.close()

        return [file_path]
