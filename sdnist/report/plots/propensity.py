import matplotlib.pyplot as plt

from sdnist.utils import *


class PropensityDistribution:

    def __init__(self,
                 propensity_dist: pd.DataFrame,
                 output_directory: Path):
        self.p_dist = propensity_dist
        self.o_dir = output_directory
        self.o_path = Path(self.o_dir, 'propensity')
        self.report_data = dict()

        self._setup()

    def _setup(self):
        if not self.o_dir.exists():
            raise Exception(f'Path {self.o_dir} does not exist. Cannot save plots')
        if not self.o_path.exists():
            os.mkdir(self.o_path)

    def save(self,
             filename: str = 'dist',
             title: str = 'Distribution of data samples over 100 propensity bins') \
            -> List[Path]:
        file_path = Path(self.o_path, f'{filename}.jpg')
        ax = self.p_dist.plot(title=title,
                              xlabel="100 Propensity Bins",
                              ylabel='Record Counts',
                              color=['mediumblue', 'limegreen'],
                              alpha=0.8,
                              lw=2,
                              figsize=(12, 6))

        ax.set_title(title, fontsize=12)
        ax.set_xlabel("100 Propensity Bins", fontsize=10)
        ax.set_ylabel("Record Counts", fontsize=10)

        ax.tick_params(axis='x', labelsize=10)
        ax.tick_params(axis='y', labelsize=10)
        ax.legend(prop={'size': 10})

        fig = ax.get_figure()
        fig.savefig(file_path)
        plt.close(fig)
        self.report_data['plot'] = relative_path(file_path)
        return [file_path]


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
        # for i, row in sd.iterrows():
        #     print(row.values.tolist())
        fig = plt.figure(figsize=(6, 6), dpi=100)
        plt.imshow(sd, cmap='RdBu')

        plt.xticks(range(sd.shape[1]), sd.columns)
        plt.yticks(range(sd.shape[0]), sd.index)
        file_path = Path(self.plot_path, f'{filename}.jpg')
        plt.title(title)
        fig.tight_layout()
        plt.savefig(file_path, bbox_inches='tight')
        plt.close()
        return [file_path]
