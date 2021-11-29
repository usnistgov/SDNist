from pathlib import Path

from loguru import logger
import pandas as pd
import typer

from sdnist.schema import COLS


def main(input_file: Path, output_file: Path, min_rows_per_individual: int = 4):
    logger.info("reading in data ...")
    cols = [c for c in COLS] + ["sim_individual_id"]
    df = pd.read_csv(input_file, usecols=cols)
    n_rows = len(df)
    n_individuals = df.sim_individual_id.nunique()
    logger.debug(
        f"read {n_rows:,} rows with {n_individuals:,} unique values for sim_individual_id"
    )

    logger.debug("counting up individuals ...")
    counts = df.sim_individual_id.value_counts()
    logger.debug(
        f"counts of number of appearances per individual:\n{counts.value_counts().sort_index()}"
    )
    filtered_counts = counts[counts >= min_rows_per_individual]

    logger.info(f"filtering down to individuals with >= {min_rows_per_individual} appearances ...")
    individuals_to_keep = filtered_counts.index.unique()
    keep_mask = df.sim_individual_id.isin(individuals_to_keep)
    n_individuals_dropped = n_individuals - len(individuals_to_keep)
    n_rows_dropped = n_rows - keep_mask.sum()
    logger.warning(
        f"dropping {n_individuals_dropped:,} individuals, accounting for {n_rows_dropped:,} rows"
    )

    logger.debug(f"years per PUMA before:\n{df.groupby('YEAR').PUMA.nunique()}\n")
    logger.debug(f"years per PUMA after:\n{df.loc[keep_mask].groupby('YEAR').PUMA.nunique()}")
    logger.success(f"writing {keep_mask.sum():,} rows to {output_file} ...")
    final = df.loc[keep_mask]

    if output_file.suffix == ".csv":
        final.to_csv(output_file, index=False)
    elif output_file.suffix == ".parquet":
        final.to_parquet(output_file, index=False)
    else:
        raise ValueError("Unrecognized extension")


if __name__ == "__main__":
    typer.run(main)
