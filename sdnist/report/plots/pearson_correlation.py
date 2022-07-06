import os
from typing import List
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt


class PearsonCorrelationPlot:
    def __init__(self,
                 correlation_differences: pd.DataFrame,
                 output_directory: Path):
        self.cd = correlation_differences
        self.o_dir = output_directory
        self.plot_path = Path(self.o_dir, 'pearson_correlation')
        self._setup()

    def _setup(self):
        if not self.o_dir.exists():
            raise Exception(f'Path {self.o_dir} does not exist. Cannot save plots')
        if not self.plot_path.exists():
            os.mkdir(self.plot_path)

    def save(self) -> List[Path]:
        file_path = Path(self.plot_path, 'pearson_corr_diff.jpg')
        print(file_path)
        cd = self.cd[reversed(self.cd.columns)]
        plt.imshow(cd, cmap='RdBu')
        plt.colorbar()

        plt.xticks(range(cd.shape[1]), cd.columns)
        plt.yticks(range(cd.shape[0]), cd.index)

        plt.title('Pearson Correlation Difference between Target and Synthetic Data')
        plt.savefig(file_path)
        plt.close()

        return [file_path]
