from typing import List, Dict

import matplotlib.pyplot as plt

from sdnist.metrics.apparent_match_dist import cellchange
from sdnist.utils import *
from sdnist.strs import *


def plot_apparent_match_dist(match_percentages: pd.Series,
                             output_directory: Path) -> Path:
    fig = plt.figure(figsize=(6, 6), dpi=100)

    if len(match_percentages):
        df = pd.DataFrame(match_percentages, columns=['perc'])
    else:
        df = pd.DataFrame([200], columns=['perc'])
    df.hist(width=1.5, align='mid')
    plt.xlim(0, 100)
    ax = plt.gca()
    ax.grid(False)
    ax.locator_params(axis='y', integer=True)
    plt.xlabel('Match Percentage', fontsize=14)
    plt.ylabel('Record Counts', fontsize=14)
    plt.title(
        'Percentage of Matched Records')
    out_file = Path(output_directory, f'apparent_match_distribution.jpg')
    x1, x2, y1, y2 = plt.axis()
    plt.axis((x1 - 2, x2 + 2, y1, y2 + 0.05))
    fig.tight_layout()
    plt.savefig(out_file, bbox_inches='tight')
    plt.close()
    return out_file


class ApparentMatchDistributionPlot:
    def __init__(self,
                 cfg: Dict[str, any],
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
            cfg: Dict[str, any]
                Program configuration
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
        self.cfg = cfg
        self.syn = synthetic
        self.tar = target
        self.o_dir = output_directory
        self.o_path = Path(self.o_dir, 'apparent_match_distribution')
        self.quasi_features = quasi_features
        self.exclude_features = exclude_features
        self.quasi_matched_df = pd.DataFrame()
        self.report_data = dict()
        self._setup()

    def _setup(self):
        if not self.o_dir.exists():
            raise Exception(f'Path {self.o_dir} does not exist. Cannot save plots')

        os.mkdir(self.o_path)

    def save(self) -> List[Path]:
        percents, u1, u2, mu = cellchange(self.syn, self.tar,
                                          self.quasi_features,
                                          self.exclude_features)
        self.quasi_matched_df = mu
        mu['percent_match'] = percents
        self.report_data['unique_matched_percents'] = \
            relative_path(save_data_frame(mu, self.o_path, 'unique_matched_percents'))

        plot_paths = []
        if not self.cfg[ONLY_NUMERICAL_METRIC_RESULTS]:
            save_file_path = plot_apparent_match_dist(percents,
                                                      self.o_path)
            self.report_data[PLOT] = relative_path(save_file_path)
            plot_paths.append(save_file_path)

        return plot_paths
