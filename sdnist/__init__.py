from typing import List
import functools

import pandas as pd

import sdnist.load
import sdnist.metrics.kmarginal
import sdnist.schema
import sdnist.challenge.submission
import sdnist.utils
import sdnist.strs as strs

from sdnist.metrics.hoc import TaxiHigherOrderConjunction
from sdnist.metrics.graph_edge_map import TaxiGraphEdgeMapScore

census = functools.partial(sdnist.load.load_dataset, challenge="census")
taxi = functools.partial(sdnist.load.load_dataset, challenge="taxi")
run = sdnist.challenge.submission.run


def log(message: str, verbose: bool = False):
    if verbose:
        print(message)


def score(private_dataset: pd.DataFrame,
          synthetic_dataset: pd.DataFrame,
          schema: dict,
          config: dict,
          challenge: str = "census",
          n_permutations: int = None,
          verbose: bool = False):
    """Computes the k-marginal score between `private_dataset` and `synthetic_dataset`.

    :param private_dataset: pd.DataFrame: original dataset, as provided by `sdnist.census` for instance.
    :param synthetic_dataset: pd.DataFrame: synthetic dataset, computed using your own method.
    :param schema: dict: dataset schema, as provided by `sdnist.census` for instance.
    :param config: dict: configurations for k-marginal scorer class
    :param challenge: str: challenge rules to define the scoring method. Must be `census` or `taxi`.
    :param n_permutations: int: number of k-marginal permutations to use. By default, the number of
        permutations used corresponds to the default value of the chosen challenge.
    :param verbose: bool: print scoring steps and outputs

    :return: score object containing several score-related metrics.
    """
    # TODO : infer challenge from schema
    score_cls = {
        "census": sdnist.metrics.kmarginal.CensusKMarginalScore,
        "taxi": sdnist.metrics.kmarginal.TaxiKMarginalScore
    }

    log(f'Computing K-marginal for the challenge: {challenge}', verbose)
    k_marg_score = score_cls[challenge](private_dataset, synthetic_dataset,
                                        schema, loading_bar=True,
                                        discretize=True,
                                        bins=config[strs.BINS],
                                        **config[strs.K_MARGINAL])
    if n_permutations is not None:
        score.N_PERMUTATIONS = n_permutations

    k_marg_score.compute_score()

    hoc_score = None
    gme_score = None
    if challenge == 'taxi':
        # compute higher order conjunction scores
        log(f'Computing Higher Order Conjunction scores for the challenge: {challenge}', verbose)
        hoc_score = TaxiHigherOrderConjunction(private_dataset, synthetic_dataset,
                                               **config[strs.K_MARGINAL])
        hoc_score.compute_score()

        # compute graph edge map scores
        log(f'Computing Graph Edge Map scores for the challenge: {challenge}', verbose)
        gme_score = TaxiGraphEdgeMapScore(private_dataset, synthetic_dataset, schema)
        gme_score.compute_score()

    log('Final Scores: ', verbose)
    log(f'K-marginal Scores: {k_marg_score.score}', verbose)

    net_score = 0
    if challenge == 'taxi':
        net_score = (k_marg_score.score + hoc_score.score + gme_score.score) / 3

        log(f'Higher Order Conjunction Scores: {hoc_score.score}', verbose)
        log(f'Graph Edge Map Scores: {gme_score.score}', verbose)
        log(f'Net Score: {net_score}', verbose)
    elif challenge == "census":
        net_score = k_marg_score.score
        log(f'Net Score: {net_score}', verbose)

    # TODO: saving net compute score that is aggregate of k-marginal ,hoc and graph edge map
    # TODO: to the k-marginal score object, and this is a hack, ideally there should be
    # TODO: a higher level score object that saves all the scores separately and can
    # TODO: provide functions for saving report from each scoring metric separately or
    # TODO: combined. And, can also provide function for k-marginal html visualization
    k_marg_score.score = net_score

    return k_marg_score
