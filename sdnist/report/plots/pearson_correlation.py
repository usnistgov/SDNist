from typing import Dict
import matplotlib.pyplot as plt

from sdnist.utils import *
from sdnist.strs import *


class PearsonCorrelationPlot:
    def __init__(self,
                 cfg: Dict[str, any],
                 correlation_differences: pd.DataFrame,
                 output_directory: Path):
        self.cfg = cfg
        self.cd = correlation_differences
        self.o_dir = output_directory
        self.o_path = Path(self.o_dir,
                           'pearson_correlation')

        self.report_data = dict()
        self._setup()

    def _setup(self):
        if not self.o_dir.exists():
            raise Exception(f'Path {self.o_dir} does not exist. Cannot save plots')
        if not self.o_path.exists():
            os.mkdir(self.o_path)

    def save(self, path_level=2) -> List[Path]:
        file_path = Path(self.o_path, 'pearson_corr_diff.jpg')

        self.report_data = {
            "correlation_difference": relative_path(save_data_frame(self.cd,
                                                                    self.o_path,
                                                                    'correlation_difference'),
                                                     level=path_level)
        }

        file_paths = []
        if not self.cfg[ONLY_NUMERICAL_METRIC_RESULTS]:
            cd = self.cd
            cd = cd.abs()
            fig = plt.figure(figsize=(6, 6), dpi=100)
            v_max = 0.15
            plt.imshow(cd, cmap='Blues', interpolation='none', vmin=0, vmax=v_max)
            im_ratio = cd.shape[0] / cd.shape[1]
            plt.colorbar(fraction=0.04 * im_ratio)
            plt.xticks(range(cd.shape[1]), cd.columns)
            plt.xticks(rotation=90)
            plt.yticks(range(cd.shape[0]), cd.index)
            plt.title('Pearson Correlation Diff. Between Target and Deid. Data')
            fig.tight_layout()
            plt.savefig(file_path, bbox_inches='tight')
            plt.close()
            self.report_data[PLOT] = relative_path(file_path, level=path_level)
            file_paths = [file_path]
        return file_paths
