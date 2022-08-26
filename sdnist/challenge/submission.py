import argparse
import abc
from pathlib import Path

import pandas as pd

import sdnist
import sdnist.strs as strs
from sdnist.load import load_dataset, TestDatasetName
from sdnist.metrics.kmarginal import CensusKMarginalScore

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


class EmptyModel(Model):
    def train(self, public_dataset: pd.DataFrame, schema: dict, eps: float = 0):
        pass

    def generate(self, n: int = 20000):
        pass


def run(submission: Model,
        challenge: str = "census",
        root: Path = Path("data"),
        results: Path = Path("results"),
        override_results: bool = False,
        public: bool = False,
        test: TestDatasetName = TestDatasetName.NONE,
        download: bool = True,
        html: bool = False):
    """ Runs a full experiment following the protocol of second sprint of the
        NIST 2020 Challenge
    """
    if results is not None:
        results = results / challenge
        if not results.is_dir():
            results.mkdir(parents=True)

    # [optional] train on public data
    if submission.REQUIRES_PRETRAINING:
        public_dataset, schema = load_dataset(challenge, root, public=True, download=download)
        submission.pretrain(public_dataset, schema)

    # train and score on private data with differential privacy
    private, schema = load_dataset(challenge, root, public=public, test=test, download=download)
    # get parameters file
    params = sdnist.load.load_parameters(challenge,
                                         root,
                                         public=public,
                                         test=test,
                                         download=download)
    # get epsilon values from parameters file
    runs = params["runs"]
    if challenge in ["census", "taxi"]:
        EPS = [r["epsilon"] for r in runs]
    else:
        raise ValueError(f"Unknown challenge {challenge}")
    print(schema.keys())
    config = schema[strs.CONFIG]
    temp = schema[strs.SCHEMA]
    schema = temp

    score_per_eps = []

    # use this CensusKMaringalScore instance for just saving collective report
    # of all individual census k-marginal runs for every epsilon value. This is
    # not used for computing score instead it just used for saving report data
    # for the visualization.
    report_kmarg = None
    if challenge == "census" and html:
        report_kmarg = sdnist.metrics.kmarginal.CensusKMarginalScore(private,
                                                                     private,
                                                                     schema,
                                                                     discretize=True,
                                                                     bins=config[strs.BINS],
                                                                     **config[strs.K_MARGINAL])

    for eps in EPS:
        # Attempt to skip already computed scores
        score_location = results / f"eps={eps}.json"
        if results is not None and not override_results:
            if score_location.exists():
                logger.info(f"Skipping scoring for eps={eps}. "
                            f"Score already exist at location: {score_location}")
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
        score = sdnist.score(private_dataset=private,
                             synthetic_dataset=synthetic,
                             schema=schema,
                             config=config,
                             challenge=challenge)
        logger.success(f"eps={eps}\tscore={score.score:.2f}")

        if results is not None:
            score.save(score_location)
        score_per_eps.append(score.score)

        if report_kmarg:
            score_report = score.report()
            for puma_year in score_report["details"]:
                puma_year["epsilon"] = eps
            if report_kmarg.report_data:
                report_kmarg.report_data["details"].extend(score_report["details"])
            else:
                report_kmarg.report_data = score_report

    if len(score_per_eps):
        # compute final aggregate score
        agg_score = sum(score_per_eps) / len(score_per_eps)
        logger.success(f"Final Score: {agg_score:.2f}")
        if report_kmarg and html:
            report_kmarg.report_data["score"] = agg_score
            private_dataset_path = sdnist.load.build_name(challenge, root, public=public, test=test)
            report_kmarg.html(private_dataset_path, browser=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser("Compute final score for the leaderboard comparison \n")
    parser.add_argument("--challenge", choices=["census", "taxi"], default="census",
                        help="Select challenge for which to score the synthetic data file. \n"
                             "Default private data file used by the census challenge: \"NY_PA_10Y_PUMS\".\n"
                             "Default private data file used by the taxi challenge: \"taxi2020\"")
    parser.add_argument("--root", type=Path,
                        help="Root of target dataset", default=Path("data"))
    parser.add_argument("--test-dataset", choices=[_.name for _ in sdnist.load.TestDatasetName],
                        default="NONE",
                        help="Select test target dataset against which to score the synthetic data file."
                             "Test datasets for the census challenge: \n"
                             "[\"GA_NC_SC_10Y_PUMS\", \n"
                             "\"NY_PA_10Y_PUMS\"]. \n"
                             "Test datasets for the taxi challenge: \n"
                             "[\"taxi2016\", \n"
                             "\"taxi2020\"]")
    parser.add_argument("--download", type=bool, default=True,
                        help="Download all datasets in 'root' if the target dataset is not present")
    parser.add_argument("--html", action='store_true',
                        help="Output the result to an html page (only available on the ACS "
                             "dataset). ")
    parser.add_argument("--public", action='store_true',
                        help="Score using the public dataset")

    args = parser.parse_args()

    m = EmptyModel()

    run(submission=m,
        challenge=args.challenge,
        root=args.root,
        public=args.public,
        test=sdnist.load.TestDatasetName[args.test_dataset],
        download=args.download,
        html=args.html)
