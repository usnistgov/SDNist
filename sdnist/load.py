import json
import os
import shutil
from enum import Enum
from pathlib import Path
from typing import Tuple
import urllib.request
import sys
import time
import zipfile
from tqdm import tqdm
from distutils.dir_util import copy_tree

import pandas as pd


class TestDatasetName(Enum):
    NONE = 1
    GA_NC_SC_10Y_PUMS = 2
    NY_PA_10Y_PUMS = 3
    taxi2016 = 4
    taxi2020 = 5


def reporthook(count, block_size, total_size):
    global start_time
    if count == 0:
        start_time = time.time() - 1
        return
    duration = time.time() - start_time
    progress_size = int(count * block_size)
    speed = int(progress_size / (1024 * duration))
    progress = int(count * block_size * 100 / total_size)
    percent = min(progress, 100)  # keeps from exceeding 100% for small data
    sys.stdout.flush()
    sys.stdout.write("\r...%d%%, %d KB, %d KB/s, %d seconds elapsed" %
                     (percent, progress_size / 1024, speed, duration))


def check_exists(root: Path, name: Path, download: bool):
    root = root.expanduser()
    if not name.exists():
        print(f"{name} does not exist.")
        zip_path = Path(root.parent, 'data.zip')
        if not zip_path.exists() and download:
            print(f"Downloading all SDNist datasets from: \n"
                  f"https://github.com/usnistgov/SDNist/releases/download/v1.2.0/SDNist-data-1.2.0.zip ...")
            try:
                urllib.request.urlretrieve(
                    f"https://github.com/usnistgov/SDNist/releases/download/v1.2.0/SDNist-data-1.2.0.zip",
                    zip_path.as_posix(),
                    reporthook
                )
                print('\n Success! Downloaded all datasets zipfile to'.format(zip_path))
            except:
                shutil.rmtree(zip_path)
                raise RuntimeError(f"Unable to download {name}. Try: \n   "
                                   f"- re-running the command, \n   "
                                   f"- downloading manually from https://github.com/usnistgov/SDNist/releases/download/v1.2.0/SDNist-data-1.2.0.zip "
                                   f"and unpack the zip, and copy 'data' directory in the root/working-directory, \n   "
                                   f"- or download the data as part of a release: https://github.com/usnistgov/SDNist/releases")

        if zip_path.exists():
            # extract zipfile
            extract_path = Path(root.parent, 'sdnist_data')
            with zipfile.ZipFile(zip_path, 'r') as f:
                for member in tqdm(f.infolist(), desc='Extracting '):
                    try:
                        f.extract(member, extract_path)
                    except zipfile.error as e:
                        raise e
            # delete zipfile
            os.remove(zip_path)
            copy_from_path = str(Path(extract_path, 'SDNist-data-1.2.0', 'data'))
            copy_to_path = str(Path(root))
            copy_tree(copy_from_path, copy_to_path)
            shutil.rmtree(extract_path)
        else:
            raise ValueError(f"{name} does not exist.")


def build_name(challenge: str,
               root: Path = Path("data"),
               public: bool = False,
               test: TestDatasetName = TestDatasetName.NONE):
    root = root.expanduser()

    if challenge == "census":
        directory = root / "census" / "final"

        if public:
            fname = "IL_OH_10Y_PUMS"
        elif test != TestDatasetName.NONE:
            if test in [TestDatasetName.taxi2020, TestDatasetName.taxi2016]:
                raise ValueError(f'Invalid challenge and test-dataset combination:'
                                 f'challenge: {challenge} | test-dataset: {test.name}. '
                                 f'Available test datasets for the census challenge: '
                                 f'{TestDatasetName.GA_NC_SC_10Y_PUMS.name}',
                                 f'{TestDatasetName.NY_PA_10Y_PUMS.name}')
            fname = test.name
        else:
            fname = TestDatasetName.NY_PA_10Y_PUMS.name

    elif challenge == "taxi":
        directory = root / "taxi"

        if public:
            fname = "taxi"
        elif test != TestDatasetName.NONE:
            if test in [TestDatasetName.GA_NC_SC_10Y_PUMS, TestDatasetName.NY_PA_10Y_PUMS]:
                raise ValueError(f'Invalid challenge and test-dataset combination: '
                                 f'challenge: {challenge} | test-dataset: {test.name}. '
                                 f'Available test datasets for the taxi challenge: '
                                 f'{TestDatasetName.taxi2016.name}',
                                 f'{TestDatasetName.taxi2020.name}')
            fname = test.name
        else:
            fname = TestDatasetName.taxi2020.name

    else:
        raise ValueError(f"Unrecognized challenge {challenge}")

    return directory / fname


def load_dataset(challenge: str,
                 root: Path = Path("data"),
                 public: bool = True,
                 test: TestDatasetName = TestDatasetName.NONE,
                 download: bool = True,
                 format_: str = "parquet") -> Tuple[pd.DataFrame, dict]:
    """ Load one of the original SDNist datasets.

    :param challenge: str: base challenge. Must be `census` or `taxi`.
    :param root: Path: directory of the dataset.
    :param public: bool: whether to use the public dataset or the private dataset
        (see below).
    :param test: TestDatasetName: if not None, retrieve the given private dataset (see below).
    :param download: bool: download files if not present in the `root` directory.
    :param format_: str: preferred format when retrieving the files. Must be `parquet` or `csv`.
        Note that only `parquet` files are actually available for download.
    :return: A tuple containing the requested dataset as a `pandas.DataFrame`, along with
        its corresponding schema, i.e a `dict` description of each feature of the dataset

    Regarding the public/private/test datasets:
    - during the challenge, the participants were given access to the "public"
    dataset (`public=True`, `test=False) to make experiments and inspect data.
    - their synthesizers were evaluated against two new datasets which they
    were not allowed to see before:
        1) The (`public=False`, `test=False`) corresponds to a dataset to privatize.
        The results were published on the public leaderboard. The participants
        were allowed to make several submission. In traditional machine learning scenarios,
        this would somewhat correspond to a 'validation' dataset.
        2) The (`public=False`, `test=True`) corresponds to another dataset to privatize.
        This time, the results were kepts secret until the end of the challenge.
        In traditional machine learning scenarios, this would correspond to a 'test' dataset.
        Your synthesizer should not be fine-tuned for the best score on this dataset.
    - using any information available in the 'public' dataset is allowed.
    - manually inspecting any of the two 'private' dataset is not allowed within the challenge,
        even though there is nothing preventing you from doing so.
    """

    if isinstance(root, str):
        root = Path(root)

    if public and test != TestDatasetName.NONE:
        raise ValueError("A public test dataset does not make sense.")

    name = build_name(challenge, root, public, test)
    name.parent.mkdir(exist_ok=True, parents=True)

    # Load schema
    schema_name = name.with_suffix(".json")
    check_exists(root, schema_name, download)
    with schema_name.open("r") as handler:
        schema = json.load(handler)["schema"]

    # TODO: remove .csv option

    # Load dataset
    if format_ == "parquet":
        dataset_name = name.with_suffix(".parquet")
        check_exists(root, dataset_name, download)
        dataset = pd.read_parquet(dataset_name)

    elif format_ == "csv":
        dataset_name = name.with_suffix(".csv")
        check_exists(root, dataset_name, download)

        columns = {name: schema[name]["dtype"] for name in schema}
        dataset = pd.read_csv(dataset_name, dtype=columns)

    else:
        raise ValueError(f"Unknown format {format_}")

    return dataset, schema


if __name__ == "__main__":
    d = load_dataset("taxi")
