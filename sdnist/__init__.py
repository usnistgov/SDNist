import functools

import pandas as pd

import sdnist.load
import sdnist.kmarginal
import sdnist.schema
import sdnist.challenge.submission


census = functools.partial(sdnist.load.load_dataset, challenge="census")
taxi = functools.partial(sdnist.load.load_dataset, challenge="taxi")
run  = sdnist.challenge.submission.run

def score(
        private_dataset: pd.DataFrame, 
        synthetic_dataset: pd.DataFrame, 
        schema: dict,
        challenge: str = "census",
        n_permutations: int = None):
    # TODO : infer challenge from schema
    score_cls = {
        "census": sdnist.kmarginal.CensusKMarginalScore,
        "taxi": sdnist.kmarginal.TaxiKMarginalScore
    }

    score = score_cls[challenge](private_dataset, synthetic_dataset, schema)
    if n_permutations is not None:
        score.N_PERMUTATIONS = n_permutations

    score.compute_score()
    return score
