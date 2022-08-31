from typing import List, Dict, Optional

import json

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from tqdm import tqdm
from pathlib import Path

import sdnist.utils


def compute_marginal(df, columns):
    return df.groupby(columns).size() / len(df)


def compute_marginal_grouped(df, columns, groups):
    counts = df.groupby(groups + columns).size()
    # https://stackoverflow.com/questions/47876663/pandas-divide-two-multi-index-series
    return counts / counts.groupby(groups).transform("sum")


class KMarginalScore:
    NAME = 'K-Marginal'

    RANK: int = 2  # Actual rank is RANK + len(ALWAYS_GROUPBY)
    N_PERMUTATIONS: int = 100

    def __init__(self,
                 private_dataset: pd.DataFrame,
                 synthetic_dataset: pd.DataFrame,
                 schema: dict,
                 seed: int = None,
                 bins: Optional[Dict] = None,
                 discretize: bool = False,
                 group_features: Optional[List[str]] = None,
                 ignore_features: Optional[List[str]] = None,
                 bias_penalty_cutoff: Optional[int] = None,
                 loading_bar: bool = False):
        self.BINS = bins
        self.ALWAYS_GROUPBY = group_features or []
        self.drop_columns = ignore_features or []
        self.COLUMNS = list(set(private_dataset.columns.tolist())
                            .difference(set(self.ALWAYS_GROUPBY + self.drop_columns)))

        if set(self.COLUMNS) - set(private_dataset.columns):
            raise ValueError("The columns of the private dataset does not match the columns of the score")

        if set(self.COLUMNS) - set(synthetic_dataset.columns):
            raise ValueError("The columns of the synthetic dataset does not match the columns of the score")

        self.BIAS_PENALTY_CUTOFF = bias_penalty_cutoff
        if discretize:
            self._private_dataset = sdnist.utils.discretize(private_dataset, schema, self.BINS)
            self._synthetic_dataset = sdnist.utils.discretize(synthetic_dataset, schema, self.BINS)
        else:
            self._private_dataset = private_dataset
            self._synthetic_dataset = synthetic_dataset
        self.schema = schema
        self.loading_bar = loading_bar
        if len(synthetic_dataset) / len(private_dataset) < .5 and self.BIAS_PENALTY_CUTOFF:
            print("Score is computed on two dataset of largely different sizes with a bias penalty.")

        self.seed = seed if seed is not None else 12345

        # Cache
        self._p0_cache = {}  # cache for private dataset marginal

    def __str__(self):
        if self.score is not None:
            return f"{type(self).__name__}({int(self.score)})"
        return f"{type(self).__name__}(None)"

    __repr__ = __str__

    def columns(self):
        assert self.COLUMNS is not None
        random_state = np.random.RandomState(seed=self.seed)

        cols = list(set(self.COLUMNS) - set(self.drop_columns))

        for _ in range(self.N_PERMUTATIONS):
            yield list(random_state.choice(cols, size=self.RANK))

    def compute_score(self):
        if self.ALWAYS_GROUPBY:
            return self._compute_score_grouped()
        else:
            return self._compute_score()

    def _compute_score_grouped(self):
        total_tv = None

        column_scores = {}
        column_score_counts = {}

        # Compute KMarginal per group in ALWAYS_GROUPBY
        if self.loading_bar:
            c_list = tqdm(self.columns(), total=self.N_PERMUTATIONS)
        else:
            c_list = self.columns()

        for columns in c_list:
            idx = tuple(columns)
            if idx not in self._p0_cache:
                self._p0_cache[idx] = compute_marginal_grouped(self._private_dataset, columns,
                                                               self.ALWAYS_GROUPBY)

            p0 = self._p0_cache[idx]
            p1 = compute_marginal_grouped(self._synthetic_dataset, columns, self.ALWAYS_GROUPBY)
            tv = p0.subtract(p1, fill_value=0).abs().groupby(self.ALWAYS_GROUPBY).sum()

            if total_tv is None:
                total_tv = tv
            else:
                total_tv = total_tv.add(tv)

            for col in columns:
                if col not in column_scores:
                    column_scores[col] = tv
                    column_score_counts[col] = 1
                else:
                    column_scores[col] = column_scores[col] + tv
                    column_score_counts[col] += 1

        mean_tv = total_tv / self.N_PERMUTATIONS

        # Compute mean column score
        for col in column_scores:
            column_scores[col] = (2 - column_scores[col] / column_score_counts[col]) * 500
        self.column_scores = column_scores

        # Compute bias penalty
        if self.BIAS_PENALTY_CUTOFF is not None:
            c0 = self._private_dataset.groupby(self.ALWAYS_GROUPBY).size()
            c1 = self._synthetic_dataset.groupby(self.ALWAYS_GROUPBY).size()
            self.bias_mask = c0.subtract(c1, fill_value=0).abs() > self.BIAS_PENALTY_CUTOFF
            mean_tv[self.bias_mask] = 2

        # Remap to 0-1000 (worst to best)
        self.scores = (2 - mean_tv) * 500
        self.score = self.scores.mean()

        return self.score

    def _compute_score(self):
        total_tv = 0

        # Compute KMarginal per group in ALWAYS_GROUPBY
        for columns in tqdm(self.columns(), total=self.N_PERMUTATIONS):
            p0 = compute_marginal(self._private_dataset, columns)
            p1 = compute_marginal(self._synthetic_dataset, columns)
            tv = p0.subtract(p1, fill_value=0).abs().sum()

            total_tv += tv

        mean_tv = total_tv / self.N_PERMUTATIONS

        # Remap to 0-1000 (worst to best)
        self.score = (2 - mean_tv) * 500

        return self.score


class CensusKMarginalScore(KMarginalScore):
    # JINJA_TEMPLATE_URL = "https://drivendata-competition-deid2-public.s3.amazonaws.com/visualization/report2.jinja2"
    # TODO change to local report in kmarginal directory
    # JINJA_TEMPLATE_URL = "https://data.nist.gov/od/ds/mds2-2515/report2.jinja2"

    # JINJA_TEMPLATE_URL = "report2.jinja2"
    report_data = None

    def report(self, column: str = None):
        """ Return a serializable report.  """
        if self.score is None:
            raise RuntimeError("Score has not been computed yet.")

        report = {
            "score": self.score,
            "details": []
        }

        if column is None:
            score = self.scores
        else:
            if column in self.column_scores:
                score = self.column_scores[column]
            else:
                raise ValueError(f"Column {column} does not appear in any score.")

        for (puma, year) in self.scores.index:
            puma_name = self.schema["PUMA"]["values"][puma]
            year_name = self.schema["YEAR"]["values"][year]
            report["details"].append({
                "PUMA": puma_name,
                "YEAR": year_name,
                "score": score[(puma, year)],
                "bias_penalty": bool(self.bias_mask.get((puma, year), False))
                                if self.BIAS_PENALTY_CUTOFF is not None else False,
            })

        return report

    def save(self, path: str = "report.json", column: str = None):
        """ Store the results per puma-year as json. """
        with open(path, "w") as f_handler:
            json.dump(self.report(), f_handler, indent=2)

    # Visualizations
    def html(self, target_dataset_path: Path, browser=True, column=None):
        """ Renders the score to a beautiful html page. """
        # TODO : this only works on the public dataset (IL-OH)

        import webbrowser
        import tempfile
        import jinja2
        cwdir = Path.cwd()
        this_dir = Path(__file__).parent
        report_path = Path(this_dir, '../visualizer_resources', 'report2.jinja2')

        with open(report_path) as file_:  # local reference
            template = jinja2.Template(file_.read())

        # r = requests.get(self.JINJA_TEMPLATE_URL)  # moving to local reference
        # template_text = r.content.decode("utf-8")

        env = jinja2.Environment()
        # template = env.from_string(template_text)

        if self.report_data is None:
            report = self.report(column)
        else:
            report = self.report_data

        # The jinja template expects an epsilon=10 parameter per puma/year
        for pumayear in report["details"]:
            if "epsilon" not in pumayear:
                pumayear["epsilon"] = 10
        report = json.dumps(report)

        if browser:
            # geojson path
            gj_p = Path(cwdir, target_dataset_path.parent.parent, 'geojson', f'{target_dataset_path.stem}.geojson')
            parameters_p = Path(cwdir, f'{target_dataset_path}.json')
            # geojson data
            params = json.load(parameters_p.open('r'))
            gj_d = json.load(gj_p.open('r'))
            gj_d = {'data': gj_d}
            tmp = tempfile.NamedTemporaryFile("w+", suffix=".html", delete=False)
            tmp.write(template.render(report=report, parameters=params, geojson=gj_d))
            webbrowser.open(f"file://{tmp.name}", new=True)

    def violin(self, idx: int = 0, name : str = None):
        plt.violinplot([self.scores], [idx], showmeans=True)
        # ...

    def boxplot(self, idx: int = 0, name: str = None):
        plt.text(self.score, idx+.3, s=f"{self.score:.0f}", horizontalalignment="center", verticalalignment="bottom", c="g")
        plt.boxplot([self.scores], positions=[idx], showmeans=True, vert=False, widths=[.6])

        if idx == 0:
            plt.xlim(0, 1000)
            plt.grid()

        # Update ticks
        ticks = list(plt.yticks())[1][:-1]
        plt.yticks(list(range(idx+1)), ticks+[name])

    def boxplot_columns(self, columns = None):
        if columns is not None:
            scores = {self.column_scores[col] for col in columns if columns is not None}
        else:
            scores = self.column_scores

        x_pos = list(range(len(scores)))
        plt.boxplot(scores.values(), positions=x_pos, showmeans=True)
        plt.xticks(x_pos, scores.keys(), rotation=45)
        plt.grid()
        plt.tight_layout()
        plt.axhline(1000, c="k")


class TaxiKMarginalScore(KMarginalScore):
    def report(self, column: str = None):
        # TODO
        return ""

    def save(self, path: str = "report.json", column: str = None):
        """ Store the results per puma-year as json. """
        with open(path, "w") as f_handler:
            json.dump(self.report(), f_handler, indent=2)


class CensusLongitudinalKMarginalScore(CensusKMarginalScore):
    # ALWAYS_GROUPBY = None
    #
    # COLUMNS = CensusKMarginalScore.COLUMNS + ["PUMA", "YEAR"]
    # COLUMNS.remove("YEAR")

    N_PERMUTATIONS = 300
    RANK = 3

    def __init__(self,
            private_dataset: pd.DataFrame,
            synthetic_dataset: pd.DataFrame,
            schema: dict,
            seed: int = None):

        self._private_dataset = sdnist.utils.unstack(sdnist.utils.discretize(private_dataset, schema, self.BINS), flat=True)
        self._synthetic_dataset = sdnist.utils.unstack(sdnist.utils.discretize(synthetic_dataset, schema, self.BINS), flat=True)
        self.schema = schema

        self.seed = seed if seed is not None else 12345

    def columns(self):
        random_state = np.random.RandomState(seed=self.seed)
        years = list(range(len(self.schema["YEAR"]["values"])))

        for _ in range(self.N_PERMUTATIONS):
            years = random_state.choice(years, size=self.RANK, replace=True)
            features = random_state.choice(self.COLUMNS, size=self.RANK, replace=True)
            yield list(zip(features, years))
