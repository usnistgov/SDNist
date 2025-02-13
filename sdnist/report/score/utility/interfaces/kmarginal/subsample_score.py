from typing import Dict, Optional

import pandas as pd

from sdnist.metrics.kmarginal import KMarginal


def create_subsample(data: pd.DataFrame, frac: float):
    s = data.sample(frac=frac)  # subsample as synthetic data
    return s


def kmarginal_stable_feature_subsamples(target: pd.DataFrame,
                                        stable_feature: Optional[str]) \
        -> pd.DataFrame:
    ss_km_runs: int = 5  # subsample kmarginal runs
    stable_feature_scores = None
    if stable_feature:
        for i in range(ss_km_runs):
            s_sd = create_subsample(target, frac=0.4)
            s_kmarg = KMarginal(target,
                                s_sd,
                                stable_feature)
            s_kmarg.compute_score()
            scores = s_kmarg.scores
            if stable_feature_scores is None:
                stable_feature_scores = scores
            else:
                stable_feature_scores += scores
        stable_feature_scores /= ss_km_runs
    return stable_feature_scores


def kmarginal_subsamples(target: pd.DataFrame,
                         stable_feature: Optional[str] = None) \
        -> Dict[float, int]:
    # mapping of subsample frac to k-marginal score of fraction
    sub_sample_score = dict()   # subsample scores dictionary
    # find k-marginal of 1%, 5%, 10%, 20% ... 90% of sub-sample of target data
    sample_sizes = [1, 5] + [i*10 for i in range(1, 10)]
    for i in sample_sizes:
        # using subsample of target data as synthetic data
        s_sd = create_subsample(target, frac= i * 0.01)
        s_kmarg = KMarginal(target,
                            s_sd,
                            stable_feature)
        s_kmarg.compute_score()
        s_score = int(s_kmarg.score)
        sub_sample_score[i * 0.01] = s_score
    return sub_sample_score