import numpy as np
import pandas as pd

import sdnist

from tqdm import tqdm, trange


MIN_HOC_DIFF = 5
MAX_HOC_DIFF = 50


def count_shift_and_pickup_areas(df):
    """
    For each individual (row), count up the number of times each shift is observed
    and each pickup location is observed and concatenate them into a single count
    dataframe representing the "kind" of individual this is by WHEN they work (shift) and
    WHERE they work (pickup_community_area).
    """
    by_shift = pd.pivot_table(
        df.assign(n=1),
        values="n",
        index="taxi_id",
        columns="shift",
        aggfunc="count",
        fill_value=0,
    )

    by_pickup = pd.pivot_table(
        df.assign(n=1),
        values="n",
        index="taxi_id",
        columns="pickup_community_area",
        aggfunc="count",
        fill_value=0,
    )

    return by_shift.join(by_pickup, rsuffix="p")

def count_similar_individuals(counts, individual, threshold):
    abs_err = np.abs(counts - individual)
    return (abs_err < threshold).all(axis=1).sum()


class TaxiHigherOrderConjunction():
    BINS = sdnist.kmarginal.TaxiKMarginalScore.BINS

    N_ITERATIONS = 50

    def __init__(self, 
            private_dataset: pd.DataFrame,
            synthetic_dataset: pd.DataFrame,
            seed: int = None):

        # TODO discritization is probably not needed
        self._private_dataset = sdnist.utils.discretize(private_dataset, self.BINS)
        self._synthetic_dataset = sdnist.utils.discretize(synthetic_dataset, self.BINS)

        self.seed = seed

    def compute_score(self):
        rng = np.random.RandomState(seed=self.seed)

        # Compute pivot table on private dataset
        # = count of shift and pickup areas per taxi_id
        private_pivot = count_shift_and_pickup_areas(self._private_dataset)
        n_taxi_private, n_cols = private_pivot.shape
        assert n_cols == 99 # number of shifts + number of pickup_community_area

        # Compute pivot table on synthetic dataset
        synthetic_pivot = count_shift_and_pickup_areas(self._synthetic_dataset).reindex(columns=private_pivot.columns).fillna(0)
        n_taxi_synthetic, n_cols = synthetic_pivot.shape
        assert n_cols <= 99

        private_pivot = private_pivot.values
        synthetic_pivot = synthetic_pivot.values

        # initialize holders for counting how many individuals are similar in each data set
        n_similar_private = np.zeros(self.N_ITERATIONS, dtype=int)
        n_similar_synthetic = np.zeros(self.N_ITERATIONS, dtype=int)

        for i in trange(self.N_ITERATIONS):
            # choose an individual from the ground truth to represent an archetypal individual
            random_individual = private_pivot[rng.randint(low=0, high=n_taxi_private)]
            # come up with varying "difficulties" for each feature of the count vector to count as similar
            # to the randomly selected individual
            threshold = rng.randint(MIN_HOC_DIFF, MAX_HOC_DIFF + 1, size=n_cols)
            n_similar_private[i] = count_similar_individuals(private_pivot, random_individual, threshold)
            n_similar_synthetic[i] = count_similar_individuals(synthetic_pivot, random_individual, threshold)

        error = np.abs(n_similar_private / n_taxi_private - n_similar_synthetic / n_taxi_synthetic).mean()

        self.score = 1 - error
        return self.score

if __name__ == "__main__":
    df, schema = sdnist.taxi()

    score = HigherOrderConjunction(df, df.sample(frac=.1))
    print(score.compute_score())