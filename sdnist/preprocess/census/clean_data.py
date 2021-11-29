from pathlib import Path

import pandas as pd
import numpy as np

from loguru import logger
import typer

from sdnist.schema import COLS


MIN_AGE = 21
MIN_YEAR = 2012

COLS_TO_KEEP = list(COLS.keys())


def main(
    input_file: Path, output_file: Path = None,
):
    logger.info("reading data ...")
    df = pd.read_csv(input_file, dtype={"STATEFIP": str, "PUMA": str, "DEPARTS": int, "ARRIVES": int})
    logger.debug(f"... read in dataframe of shape {df.shape}")

    # narrow down to years we care about
    bad_year_mask = df.YEAR < MIN_YEAR
    logger.info(f"dropping {bad_year_mask.sum():,} rows where YEAR less than {MIN_YEAR}")
    df = df.loc[~bad_year_mask]
    logger.debug(f"... new shape: {df.shape}")

    # narrow down to old enough individuals
    bad_age_mask = df.AGE < MIN_AGE
    logger.info(
        f"dropping {bad_age_mask.sum():,} rows where individuals are younger than {MIN_AGE}"
    )
    df = df.loc[~bad_age_mask]
    logger.debug(f"... new shape: {df.shape}")

    # PUMA is unique within a state, so concatenate the columns
    df["PUMA"] = df.STATEFIP + "-" + df.PUMA

    # zero out when DEPART > ARRIVE
    bad_depart_arrive_mask = df.DEPARTS > df.ARRIVES
    logger.info(f"zeroing {bad_depart_arrive_mask.sum():,} instances where DEPARTS > ARRIVES")
    for col in ("DEPARTS", "ARRIVES"):
        df.loc[bad_depart_arrive_mask, col] = 0

    # drop columns we don't need
    to_keep = set(COLS_TO_KEEP)
    to_drop = set(df.columns) - to_keep
    logger.info(f"dropping {to_drop} columns")
    df = df.loc[:, COLS_TO_KEEP]
    logger.debug(f"... new shape: {df.shape}")

    for col in sorted(df.columns):
        n_col = df[col].nunique()
        values = ""
        if n_col <= 10:
            values = f" ({sorted(df[col].unique())})"
        logger.debug(f"unique values in column {col}: {n_col:,}{values}")

    logger.info("rearranging columns, sorting data, and resetting index")
    first_cols = ["PUMA", "YEAR"]
    other_cols = [col for col in df.columns if col not in first_cols]
    df = df.loc[:, first_cols + other_cols].sort_values(["PUMA", "YEAR"]).reset_index(drop=True)
    df.index.name = "row_id"

    # write out the data
    if output_file is not None:
        logger.info(f"writing {len(df):,} rows out to {output_file}")
        df.to_csv(output_file, index=True)


if __name__ == "__main__":
    typer.run(main)
