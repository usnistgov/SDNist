from pathlib import Path

import os

ROOT_DIRECTORY = Path("")
DATA_DIRECTORY = ROOT_DIRECTORY / "data"
CONFIG_DIRECTORY = ROOT_DIRECTORY / "config"
DATALOADER_DIRECTORY = ROOT_DIRECTORY / "dataloader"
PICKLE_DIRECTORY = DATALOADER_DIRECTORY / "pkl"

SUBMISSION_FORMAT = DATA_DIRECTORY / "submission_format.csv"
INPUT = DATA_DIRECTORY / "ground_truth.csv"
PUBLIC_INPUT = DATA_DIRECTORY / "ground_truth.csv"
PARAMS = DATA_DIRECTORY / "parameters.json"
CONFIG_DATA = CONFIG_DIRECTORY / "data.yaml"
OUTPUT = ROOT_DIRECTORY / "submission.csv"

