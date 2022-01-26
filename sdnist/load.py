import json
from pathlib import Path
from typing import Tuple
import urllib.request

import pandas as pd


def check_exists(name: Path, download: bool):
    if not name.exists():
        print(f"{name} does not exist." )
        if download:
            print(f"Downloading https://data.nist.gov/od/ds/mds2-2515/{name.name} ...")
            try:
                urllib.request.urlretrieve(
                    # f"https://storage.googleapis.com/sdnist-sarus/{name.name}",  #moved resources to NIST servers
                    f"https://data.nist.gov/od/ds/mds2-2515/{name.name}",
                    name.as_posix()
                )
            except:
                raise RuntimeError(f"Unable to download {name}. \n You can attempt to download manually from https://data.nist.gov/od/id/mds2-2515 and install to {name}")
        else:
            raise ValueError(f"{name} does not exist.")

def build_name(challenge: str, root: Path = Path("data"), public: bool = False, test: bool = False):
    root = root.expanduser()
    if challenge == "census":
        directory = root / "census" / "final"

        if public:
            fname = "IL_OH_10Y_PUMS"
        elif test:
            fname = "GA_NC_SC_10Y_PUMS"
        else:
            fname = "NY_PA_10Y_PUMS"

    elif challenge == "taxi":
        directory = root / "taxi"

        if public:
            fname = "taxi"
        elif test:
            fname = "taxi2016"
        else:
            fname = "taxi2020"

    else:
        raise ValueError("Unrecognized challenge {challenge}")

    return directory / fname

def load_dataset(
        challenge: str,
        root: Path = Path("data"),
        public: bool = True,
        test: bool = False,
        download: bool = True,
        format_: str = "parquet"
    ) -> Tuple[pd.DataFrame, dict]:
    """ Load one of the original SDNist datasets.

    :param challenge str: base challenge. Must be `census` or `taxi`.
    :param root Path: directory of the dataset.
    :param public bool: whether to use the public dataset or the private dataset
        (see below).
    :param test bool: retrieve the additinal private dataset (see below).
    :param download bool: download files if not present in the `root` directory.
    :param format_ str: prefered format when retrieving the files. Must be `parquet` or `csv`.
        Note that only `parquet` files are actually available for download.
    :return: A tuple containing the requested dataset as a `pandas.DataFrame`, along with
        its corresponding schema, i.e a `dict` description of each feature of the dataset.

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
        Your synthesizer should not be finetuned for the best score on this dataset.
    - using any information available in the 'public' dataset is allowed.
    - manually inspecting any of the two 'private' dataset is not allowed within the challenge,
    even though there is nothing preventing you from doing so.
    """

    if isinstance(root, str):
        root = Path(root)

    if public and test:
        raise ValueError("A public test dataset does not make sense.")

    name = build_name(challenge, root, public, test)
    name.parent.mkdir(exist_ok=True, parents=True)

    # Load schema
    schema_name = name.with_suffix(".json")
    check_exists(schema_name, download)
    with schema_name.open("r") as handler:
        schema = json.load(handler)["schema"]

    # TODO: remove .csv option

    # Load dataset
    if format_ == "parquet":
        dataset_name = name.with_suffix(".parquet")
        check_exists(dataset_name, download)
        dataset = pd.read_parquet(dataset_name)

    elif format_ == "csv":
        dataset_name = name.with_suffix(".csv")
        check_exists(dataset_name, download)

        columns = {name: schema[name]["dtype"] for name in schema}
        dataset = pd.read_csv(dataset_name, dtype=columns)

    else:
        raise ValueError(f"Unknown format {format_}")

    return dataset, schema


if __name__ == "__main__":
    d = load_dataset("taxi")
