from typing import List
import os
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt


class PropensityPairPlot:
    def __init__(self,
                 propensity_scores: pd.DataFrame,
                 output_directory: Path):
        self.scores = propensity_scores
        self.o_dir = output_directory
        self.plot_path = Path(self.o_dir, 'pMSE')
        self._setup()

    def _setup(self):
        if not self.o_dir.exists():
            raise Exception(f'Path {self.o_dir} does not exist. Cannot save plots')
        if not self.plot_path.exists():
            os.mkdir(self.plot_path)

    def save(self,
             filename: str = 'pmse',
             title: str = 'Two Way Propensity Mean Error') -> List[Path]:
        s = self.scores
        sd = s[reversed(s.columns)]
        for i, row in sd.iterrows():
            print(row.values.tolist())
        plt.imshow(sd, cmap='RdBu')
        plt.colorbar()

        plt.xticks(range(sd.shape[1]), sd.columns)
        plt.yticks(range(sd.shape[0]), sd.index)
        file_path = Path(self.plot_path, f'{filename}.jpg')
        plt.title(title)
        plt.savefig(file_path)
        plt.close()

        return [file_path]
