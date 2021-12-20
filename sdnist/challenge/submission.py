import os
import abc
from pathlib import Path

from loguru import logger

import pandas as pd

import sdnist
from sdnist.load import load_dataset
from sdnist.kmarginal import CensusKMarginalScore

from loguru import logger


class Model(abc.ABC):
    """ Base class for running experiments in the same setting as the challenge. """
    REQUIRES_PRETRAINING = False

    def pretrain(self, public_dataset: pd.DataFrame, schema: dict):
        pass

    @abc.abstractmethod
    def train(self, private_dataset: pd.DataFrame, schema: dict, eps: float = 0):
        pass

    @abc.abstractmethod
    def generate(self, n: int = 20000):
        pass


def run(submission: Model,
        challenge: str = "census",
        root: Path = Path("data"),
        results: Path = Path("results"),
        override_results: bool = False,
        test: bool = False,
        download: bool = True):
    """ Runs a full experiment following the protocol of second sprint of the
        NIST 2020 Challenge
    """
    if challenge == "census":
        EPS = [0.1, 1, 10]
    elif challenge == "taxi":
        EPS = [1, 10]
    else:
        raise ValueError(f"Unknown challenge {challenge}")

    if results is not None:
        results = results / challenge
        if not results.is_dir():
            results.mkdir(parents=True)

    # [optional] train on public data
    if submission.REQUIRES_PRETRAINING:
        public, schema = load_dataset(challenge, root, public=True, download=download)
        submission.pretrain(public, schema)

    # train and score on private data with differential privacy
    private, schema = load_dataset(challenge, root, public=False, test=test, download=download)

    for eps in EPS:
        # Attempt to skip already computed scores
        score_location = results / f"eps={eps}.json"
        if results is not None and not override_results:
            if score_location.exists():
                logger.info(f"Skipping scoring for eps={eps}.")
                continue

        # Attempt to retrieve a previously generated synthetic dataset
        synthetic_location = results / f"eps={eps}.csv"

        if results is not None and not override_results and synthetic_location.exists():
            logger.info(f"Resuming scoring from {synthetic_location}.")
            dtype = {name: schema[name]["dtype"] for name in schema}
            synthetic = pd.read_csv(synthetic_location, dtype=dtype)

        # Generate synthetic data
        else:
            logger.info(f"Generating synthetic data for eps={eps}.")
            submission.train(private, schema, eps)
            synthetic = submission.generate(n=len(private), eps=eps)

            if results is not None:
                synthetic.to_csv(synthetic_location)
                logger.info(f"(saved to {synthetic_location})")

        # Compute score
        logger.info(f"Computing scores for eps={eps}.")

        # TODO score object can be reused for marginal speed gains.
        score = sdnist.score(private, synthetic, schema, challenge)
        logger.success(f"eps={eps}\tscore={score.score:.2f}")

        if results is not None:
            score.save(score_location)
