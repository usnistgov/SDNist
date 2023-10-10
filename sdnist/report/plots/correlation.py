from typing import List, Dict

import matplotlib.pyplot as plt

from sdnist.utils import *
from sdnist.strs import *

plt.style.use('seaborn-deep')


class CorrelationDifferencePlot:
    def __init__(self,
                 cfg: Dict[str, any],
                 synthetic: pd.DataFrame,
                 target: pd.DataFrame,
                 output_directory: Path,
                 features: List[str]):
        """
        Computes and plots features correlation difference between
        synthetic and target data

        Parameters
        ----------
            cfg: Dict[str, any]
                Program configuration
            synthetic : pd.Dataframe
                synthetic dataset
            target : pd.Dataframe
                target dataset
            output_directory: pd.Dataframe
                path of the directory to which plots will will be saved
            features: List[str]
                List of names of features for which to compute correlation
        """
        self.cfg: Dict[str, any] = cfg
        self.syn = synthetic
        self.tar = target
        self.o_dir = output_directory
        self.o_path = Path(self.o_dir, 'correlation_difference')
        self.features = features
        self.report_data = dict()

        self._setup()

    def _setup(self):
        if not self.o_dir.exists():
            raise Exception(f'Path {self.o_dir} does not exist. Cannot save plots')

        os.mkdir(self.o_path)

    def save(self) -> List[Path]:
        corr_df = correlation_difference(self.syn, self.tar, self.features)

        self.report_data = {"correlation_difference":
                            relative_path(save_data_frame(corr_df,
                                                          self.o_path,
                                                          'correlation_difference'))}
        plot_paths = []
        if not self.cfg[ONLY_NUMERICAL_METRIC_RESULTS]:
            plot_paths = save_correlation_difference_plot(corr_df, self.o_path)
            self.report_data[PLOT] = relative_path(plot_paths[0])
        return plot_paths


def correlations(data: pd.DataFrame, features: List[str]):
    corr_list = []

    for f_a in features:
        f_a_corr = []
        for f_b in features:
            c_val = data[f_a].corr(data[f_b], method='kendall')
            f_a_corr.append(c_val)
        corr_list.append(f_a_corr)

    return pd.DataFrame(corr_list, columns=features, index=features)


def correlation_difference(synthetic: pd.DataFrame,
                           target: pd.DataFrame,
                           features: List[str]) -> pd.DataFrame:

    syn_corr = correlations(synthetic, features)
    tar_corr = correlations(target, features)

    diff = syn_corr - tar_corr

    return diff


def save_correlation_difference_plot(correlation_data: pd.DataFrame,
                                     output_directory: Path) -> List[Path]:
    cd = correlation_data
    cd = cd.abs()
    fig = plt.figure(figsize=(6, 6), dpi=100)
    v_max = 0.15
    plt.imshow(cd, cmap='Blues', interpolation='none', vmin=0, vmax=v_max)
    im_ratio = cd.shape[0] / cd.shape[1]

    plt.colorbar(fraction=0.04 * im_ratio)
    plt.xticks(range(cd.shape[1]), cd.columns)
    plt.xticks(rotation=90)
    plt.yticks(range(cd.shape[0]), cd.index)
    file_path = Path(output_directory, 'corr_diff.jpg')
    plt.title('Correlation Diff. Between Target and Deid. Data')
    fig.tight_layout()
    plt.savefig(file_path, bbox_inches='tight')
    plt.close()

    return [file_path]


