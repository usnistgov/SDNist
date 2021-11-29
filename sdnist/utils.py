import numpy as np
import pandas as pd


def discretize(dataset, schema, bins, copy: bool = True):
    """ Digitize the float columns. """
    if copy:
        dataset = dataset.copy()

    for column, desc in schema.items():
        if column in bins:
            dataset[column] = pd.cut(dataset[column], bins[column], right=False).cat.codes
        elif "values" in desc:
            dataset[column] = dataset[column].astype(pd.CategoricalDtype(desc["values"])).cat.codes
        else:
            dataset[column] = (dataset[column] - desc["min"]).astype(int)

    return dataset

def undo_discretize(dataset, schema, bins, copy: bool = True, handle_inf: bool = True):
    """ Return an unbinned dataset. """
    if handle_inf:
        original_bins = bins
        bins = {}

        for col, bin in original_bins.items():
            bins[col] = bin.copy()
            bins[col][-1] = bin[-2] + 1

    if copy:
        dataset = dataset.copy()

    for column, desc in schema.items():
        if column in bins:
            bin = bins[column]
            dataset[column] = bin[dataset[column].values]
        elif "values" in desc:
            dataset[column] = np.array(desc["values"])[dataset[column].values]
        else:
            dataset[column] += desc["min"]

    return dataset

def unstack(dataset, user_id: str = "sim_individual_id", time: str = "YEAR", flat: bool = False):
    df = dataset.set_index([user_id, time]).unstack(time, fill_value=-1)

    if flat:
        df.columns = df.columns.to_flat_index()

    return df

def stack(dataset, user_id: str = "sim_individual_id", time: str = "YEAR"):
    if not isinstance(dataset.columns, pd.MultiIndex):
        dataset.columns = pd.MultiIndex.from_tuples(dataset.columns)

    df = dataset.stack().reset_index()

    # Rename year and user_id
    col_names = list(df)
    df.rename(columns={
        col_names[0]: user_id,
        col_names[1]: time
    }, inplace=True)
    
    # Remove empty rows
    keep = (df != -1).all(axis="columns")
    return df[keep]