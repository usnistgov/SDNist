from pathlib import Path

import numpy as np
import pandas as pd

from loguru import logger
import typer
from tqdm import tqdm
tqdm.pandas()

from sdnist.schema import COLS


FIXED_TRAITS = ["SEX", "RACE", "HISPAN"]
MARRIAGE_TRANSITIONS = {
    1: (1, 2, 3, 4, 5),
    2: (1, 2,),
    3: (3, 4,),
    4: (4,),
    5: (5,),
    6: (1, 2, 6),
}

CITIZEN_TRANSITIONS = {
    0: (0,),
    1: (1,),
    2: (2,),
    3: (2, 3, 4),
    4: (2, 4),
    5: (2, 3, 4, 5,),
}

def filter_candidates(df: pd.DataFrame, row, delta: int):
    # only people who have not already been assigned
    mask = df.sim_individual_id < 0
    # education monotonically increasing
    mask &= df.EDUC >= int(row.EDUC)
    # education doesn't skip too many levels
    mask &= df.EDUC <= int(row.EDUC) + delta + 1
    # marriage status transition makes sense
    mask &= df.MARST.isin(MARRIAGE_TRANSITIONS.get(int(row.MARST), (1, 2, 3, 4, 5, 6)))
    # speaks english makes sense
    mask &= df.SPEAKENG >= row.SPEAKENG
    # citizenship status makes sense
    mask &= df.CITIZEN.isin(
        CITIZEN_TRANSITIONS.get(int(row.CITIZEN), (1, 2, 3, 4, 5, 6))
    )
    return df.loc[mask]  # candidates

def sorted_groupby(df, fields):
    changes = [0] + list(np.abs(np.diff(df[fields].to_numpy(), axis=0)).sum(axis=1).nonzero()[0] + 1) + [len(df)]
    groups = {}
    
    for i, j in zip(changes[:-1], changes[1:]):
        groups[tuple(df[fields].iloc[i])] = df.iloc[i:j]
        assert (df.iloc[i:j][fields].nunique() == 1).all()

    return groups


def simulate_individuals_groupby(subdf, max_year=2018):
    """
    Take a DataFrame grouped by the non-negotiable features and then loop through it.
    For each row, start at that row's year and iterate through the remaining years in
    the data to narrow down all the other rows which haven't already been assigned
    and see if they would work as subsequent data for the same individual.
    """
    # initialize the mapping
    subdf["sim_individual_id"] = -1

    # for each row in the grouped dataframe
    subdf.sort_values(["YEAR", "AGE", "PUMA"], inplace=True)
    year_age_subdf = sorted_groupby(subdf, ["YEAR", "AGE"])

    pbar = tqdm(total=len(subdf), leave=False)
    for row_id in subdf.index.values:
        if subdf.loc[row_id, "sim_individual_id"] > -1:
            # if already assigned then skip the row - we did it already
            continue

        # initialize the state variables
        individual = row_id
        subdf.loc[row_id, "sim_individual_id"] = row_id
        pbar.update(1)
        row = subdf.loc[row_id]

        # for all the years left, see if there are more rows that could be this person
        for year in range(int(row.YEAR) + 1, max_year + 1):
            # filter down to appropriate rows
            delta = year - row.YEAR
            age = int(row.AGE) + delta

            if (year, age) not in year_age_subdf:
                continue

            df = year_age_subdf[(year, age)]
            candidates = filter_candidates(df, row, delta)

            # Attempt to find the candidates in the same PUMA first
            puma_mask = candidates.PUMA == row.PUMA
            if puma_mask.any():
                candidates = candidates.loc[puma_mask]

            # ... now choose the row with the most similar income
            if len(candidates) > 0:
                new_row_id = (candidates.INCTOT - row.INCTOT).abs().idxmin()
                # tag this as belonging to the same individual
                subdf.loc[new_row_id, "sim_individual_id"] = individual
                pbar.update(1)
                # add to our mapping
                row_id, row = new_row_id, subdf.loc[new_row_id]

    return subdf


def main(input_file: Path, output_file: Path, frac: float = None):
    logger.info("Reading in data ...")
    df = pd.read_csv(input_file, index_col=0)

    if frac is not None:
        logger.info(f"... taking a subsample of {frac:%} of rows")
        # df = df.sample(frac=frac)
        df = df.iloc[:int(len(df) * frac)]

    logger.info("running simulation ...")
    final_df = df.groupby(FIXED_TRAITS).progress_apply(simulate_individuals_groupby)

    logger.success(f"writing output to {output_file} ...")
    final_df.to_csv(output_file, index=False)


if __name__ == "__main__":
    typer.run(main)

    
