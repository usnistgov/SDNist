import json
from pathlib import Path

from loguru import logger
import numpy as np
import pandas as pd
import typer

from sdnist.schema import COLS, check_compliance


def main(ground_truth_csv: Path):
    data_folder = ground_truth_csv.parent
    logger.info(f"reading in data from {ground_truth_csv} ...")
    data = pd.read_csv(ground_truth_csv, dtype=COLS)
    n_rows = len(data)
    n_individuals = data.sim_individual_id.nunique()
    logger.debug(f"read {n_rows:} rows with {n_individuals:} unique values for sim_individual_id")

    parameters = {
        "schema": {},
    }

    valid_values = {
        "GQ": {"values": [0, 1, 2, 3, 4, 5, 6]},
        "SEX": {"values": [1, 2]},
        "AGE": {"min": 0, "max": 135},
        "MARST": {"values": [1, 2, 3, 4, 5, 6]},
        "RACE": {"values": [1, 2, 3, 4, 5, 6, 7, 8, 9]},
        "HISPAN": {"values": [0, 1, 2, 3, 4, 9]},
        "CITIZEN": {"values": [0, 1, 2, 3, 4, 5, 6]},
        "SPEAKENG": {"values": [0, 1, 2, 3, 4, 5, 6, 7, 8]},
        "HCOVANY": {"values": [1, 2]},
        "HCOVPRIV": {"values": [1, 2]},
        "HINSEMP": {"values": [1, 2]},
        "HINSCAID": {"values": [1, 2]},
        "HINSCARE": {"values": [1, 2]},
        "EDUC": {"values": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]},
        "EMPSTAT": {"values": [0, 1, 2, 3]},
        "LABFORCE": {"values": [0, 1, 2]},
        "WRKLSTWK": {"values": [0, 1, 2, 3]},
        "ABSENT": {"values": [0, 1, 2, 3, 4]},
        "LOOKING": {"values": [0, 1, 2, 3]},
        "AVAILBLE": {"values": [0, 1, 2, 3, 4, 5]},
        "WRKRECAL": {"values": [0, 1, 2, 3]},
        "WORKEDYR": {"values": [0, 1, 2, 3]},

        # Not in IPUMS search; assume the "d" is for detailed
        # selected 'detailed' button on this page for codes:
        #   https://usa.ipums.org/usa-action/variables/EMPSTAT#codes_section
        "EMPSTATD": {"values": [0, 10, 11, 12, 13, 14, 15, 20, 21, 22, 30, 31, 32, 33, 34]},
        # 000 - 501; (percent of poverty line) should be uint32
        "POVERTY": {"min": 0, "max": 501},
        # 0000 - 2359; (4 digit time code) should be uint32
        "DEPARTS": {"min": 0, "max": 2359},
        # 0000 - 2359; (4 digit time code) should be uint32
        "ARRIVES": {"min": 0, "max": 2359},
    }

    logger.info("initializing schema")
    for col, dtype in COLS.items():
        logger.debug(f"... setting up {col}")
        col_schema = valid_values.get(col, {})
        col_schema["dtype"] = dtype
        parameters["schema"][col] = col_schema

    # empirical columns
    parameters["schema"]["PUMA"]["values"] = list(sorted(data.PUMA.unique()))
    parameters["schema"]["YEAR"]["values"] = list(sorted(int(y) for y in data.YEAR.unique()))

    logger.info("validating new parameters")
    check_compliance(data, parameters["schema"])

    parameters_path = ground_truth_csv.with_suffix(".json")
    logger.success(f"writing out paramaters to {parameters_path}")
    with parameters_path.open("w") as fp:
        json.dump(parameters, fp, indent=2, sort_keys=False)


if __name__ == "__main__":
    typer.run(main)
