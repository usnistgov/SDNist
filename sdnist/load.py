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
import numpy as np

import sdnist.strs as strs


class TestDatasetName(Enum):
    NONE = 1
    GA_NC_SC_10Y_PUMS = 2
    NY_PA_10Y_PUMS = 3
    IL_OH_10Y_PUMS = 4
    taxi2016 = 5
    taxi2020 = 6
    ma2019 = 7
    tx2019 = 8
    national2019 = 9


data_challenge_map = {
    TestDatasetName.NONE: None,
    TestDatasetName.GA_NC_SC_10Y_PUMS: strs.CENSUS,
    TestDatasetName.NY_PA_10Y_PUMS: strs.CENSUS,
    TestDatasetName.IL_OH_10Y_PUMS: strs.CENSUS,
    TestDatasetName.ma2019: strs.CENSUS,
    TestDatasetName.tx2019: strs.CENSUS,
    TestDatasetName.national2019: strs.CENSUS,
    TestDatasetName.taxi2016: strs.TAXI,
    TestDatasetName.taxi2020: strs.TAXI
}


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


def error_opening_zip(zip_path):
    try:
        z = zipfile.ZipFile(zip_path)
    except zipfile.BadZipfile:
        return True

    if z.testzip() is not None:
        return True
    return False


def check_exists(root: Path, name: Path, download: bool, data_name: str = strs.DATA):
    root = root.expanduser()
    if not name.exists():
        print(f"{name} does not exist.")
        zip_path = Path(root.parent, 'data.zip')
        version = "1.4.0-b.1"

        version_v = f"v{version}"
        sdnist_version = f"SDNist-{data_name}-{version}"
        download_link = f"https://github.com/usnistgov/SDNist/releases/download/{version_v}/{sdnist_version}.zip"
        if zip_path.exists() and error_opening_zip(zip_path):
            os.remove(zip_path)

        if not zip_path.exists() and download:
            print(f"Downloading all SDNist datasets from: \n"
                  f"{download_link} ...")
            try:
                urllib.request.urlretrieve(
                    download_link,
                    zip_path.as_posix(),
                    reporthook
                )
                print('\n Success! Downloaded all datasets zipfile to'.format(zip_path))
            except:
                shutil.rmtree(zip_path)
                raise RuntimeError(f"Unable to download {name}. Try: \n   "
                                   f"- re-running the command, \n   "
                                   f"- downloading manually from {download_link} "
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
            copy_from_path = str(Path(extract_path, sdnist_version, 'data'))
            copy_to_path = str(Path(root))
            copy_tree(copy_from_path, copy_to_path)
            shutil.rmtree(extract_path)
        else:
            raise ValueError(f"{name} does not exist.")


def build_name(challenge: str,
               root: Path = Path("data"),
               public: bool = False,
               test: TestDatasetName = TestDatasetName.NONE,
               data_name: str = strs.DATA):
    root = root.expanduser()
    directory = root

    if data_name == "toy-data":
        directory = root
    elif challenge == strs.CENSUS:
        directory = root / "census" / "dataset"
    elif challenge == strs.TAXI:
        directory = root / "taxi" / "dataset"

    if challenge == "census":
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


def load_parameters(challenge: str,
                    root: Path = Path("data"),
                    public: bool = True,
                    test: TestDatasetName = TestDatasetName.NONE,
                    download: bool = True,
                    data_name: str = strs.DATA) -> dict:
    dataset_path = build_name(challenge=challenge, root=root,
                              public=public, test=test, data_name=data_name)
    dataset_parameters = dataset_path.with_suffix('.json')
    check_exists(root, dataset_parameters, download, data_name=data_name)

    with dataset_parameters.open("r") as handler:
        params = json.load(handler)
    return params


def load_config(challenge: str,
                root: Path = Path("data"),
                public: bool = True,
                test: TestDatasetName = TestDatasetName.NONE,
                download: bool = True) -> dict:
    dataset_path = build_name(challenge=challenge, root=root, public=public, test=test)
    dataset_config_path = dataset_path.with_suffix('.config.json')
    check_exists(root, dataset_config_path, download)

    with dataset_config_path.open("r") as handler:
        config = json.load(handler)

    if strs.K_MARGINAL in config:
        km_cnf = config[strs.K_MARGINAL]
        if strs.BINS in km_cnf and len(km_cnf[strs.BINS]):
            b_cnf = km_cnf[strs.BINS]
            for f, b in b_cnf.items():
                b_cnf[f] = eval(b)
    return config


def load_dataset(challenge: str,
                 root: Path = Path("data"),
                 public: bool = True,
                 test: TestDatasetName = TestDatasetName.NONE,
                 download: bool = True,
                 format_: str = "parquet",
                 data_name: str = 'data') -> Tuple[pd.DataFrame, dict]:
    """ Load one of the original SDNist datasets.

    :param challenge: str: base challenge. Must be `census` or `taxi`.
    :param root: Path: directory of the dataset.
    :param public: bool: whether to use the public dataset or the private dataset
        (see below).
    :param test: TestDatasetName: if not None, retrieve the given private dataset (see below).
    :param download: bool: download files if not present in the `root` directory.
    :param format_: str: preferred format when retrieving the files. Must be `parquet` or `csv`.
        Note that only `parquet` files are actually available for download.
    :param data_name: str: name of the dataset bundle from where to load data file
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

    name = build_name(challenge, root, public, test, data_name)
    name.parent.mkdir(exist_ok=True, parents=True)

    # Load schema
    params = load_parameters(challenge, root, public, test, download, data_name)
    config = dict()

    # TODO: remove .csv option

    # Load dataset
    if format_ == "parquet":
        dataset_name = name.with_suffix(".parquet")
        check_exists(root, dataset_name, download, data_name)
        dataset = pd.read_parquet(dataset_name)

    elif format_ == "csv":
        dataset_name = name.with_suffix(".csv")
        check_exists(root, dataset_name, download, data_name)

        columns = {name : params[strs.SCHEMA][name]["dtype"]
                   for name in params[strs.SCHEMA]}
        dataset = pd.read_csv(dataset_name, dtype=columns)

    else:
        raise ValueError(f"Unknown format {format_}")

    if data_name != 'toy-data':
        config = load_config(challenge, root, public, test, download)
    params[strs.CONFIG] = config
    return dataset, params


if __name__ == "__main__":
    d = load_dataset("taxi")
