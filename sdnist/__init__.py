from typing import List
import functools

import pandas as pd

import sdnist.load
import sdnist.kmarginal
import sdnist.schema
import sdnist.challenge.submission
import sdnist.utils

from sdnist.hoc import TaxiHigherOrderConjunction

census = functools.partial(sdnist.load.load_dataset, challenge="census")
taxi = functools.partial(sdnist.load.load_dataset, challenge="taxi")
run = sdnist.challenge.submission.run


def score(
        private_dataset: pd.DataFrame,
        synthetic_dataset: pd.DataFrame,
        schema: dict,
        challenge: str = "census",
        drop_columns: List[str] = None,
        n_permutations: int = None):
    """Computes the k-marginal score between `private_dataset` and `synthetic_dataset`.

    :param private_dataset pd.DataFrame: original dataset, as provided by `sdnist.census` for instance.
    :param synthetic_data pd.DataFrame: synthetic dataset, computed using your own method.
    :param schema dict: dataset schema, as provided by `sdnist.census` for instance.
    :param challenge str: challenge rules to define the scoring method. Must be `census` or `taxi`.
    :param n_permutations int: number of k-marginal permutations to use. By default, the number of 
        permutations used corresponds to the default value of the chosen challenge.

    :return: score object containing several score-related metrics.
    """
    # TODO : infer challenge from schema
    score_cls = {
        "census": sdnist.kmarginal.CensusKMarginalScore,
        "taxi": sdnist.kmarginal.TaxiKMarginalScore
    }

    print(f'Computing K-marginal for the challenge: {challenge}')
    score = score_cls[challenge](private_dataset, synthetic_dataset, schema, drop_columns)
    if n_permutations is not None:
        score.N_PERMUTATIONS = n_permutations

    km_score = score.compute_score()

    hoc_score = None
    if challenge == 'taxi':
        # compute higher order conjunction scores
        print(f'Computing Higher Order Conjunction scores for the challenge: {challenge}')
        hoc_score = TaxiHigherOrderConjunction(private_dataset, synthetic_dataset)
        hoc_score.compute_score()

    print('Final Scores: ')
    print(f'K-marginal Scores: {km_score}')

    if challenge == 'taxi':
        print(f'Higher Order Conjunction Scores: {hoc_score.score}')
    return score
