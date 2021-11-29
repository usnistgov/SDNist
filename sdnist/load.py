import json
from pathlib import Path
from typing import Tuple
import urllib.request

import pandas as pd


def check_exists(name: Path, download: bool):
    if not name.exists():
        print(f"{name} does not exist." )
        if download:
            print(f"Downloading {name.name}...")
            urllib.request.urlretrieve(f"https://storage.googleapis.com/sdnist-sarus/{name.name}", name.as_posix())
        else:
            raise ValueError(f"{name} does not exist.")

def build_name(challenge: str, root: Path = Path("data"), public: bool = False, test: bool = False):
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
    """ Load one of the SDNIST datasets. """

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