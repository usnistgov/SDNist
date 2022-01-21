import numpy as np
import pandas as pd


def discretize(dataset: pd.DataFrame, schema: dict, bins: dict, copy: bool = True):
    """ Discretizes `dataset` using `pandas.CategoricalDtypes`. All values are remapped
    from 0 to `n-1` where `n` is the number of distinct values.

    :param dataset pandas.DataFrame: dataset to discretize
    :param schema dict: dataset schema, as provided by `sdnist.census` for instance.
    :param bins dict: a dict containing (`feature`, `bins) key-value pairs.
        The bins used to compute the k-marginal score are available at
        `sdnist.kmarginal.CensusKMarginalScore.BINS` and
        `sdnist.kmarginal.TaxiKMarginalScore.BINS`.
    :param copy bool: whether the original `dataset` should be copied before discretization.
    :return: the discretized input `pandas.DataFrame`.

    """
    if copy:
        dataset = dataset.copy()

    for column in dataset:
        if column in bins:
            dataset[column] = pd.cut(dataset[column], bins[column], right=False).cat.codes
        elif column in schema:
            desc = schema[column]
            if "values" in desc:
                dataset[column] = dataset[column].astype(pd.CategoricalDtype(desc["values"])).cat.codes
            elif  "min" in desc.keys():
                dataset[column] = (dataset[column] - desc["min"]).astype(int)
            else:
                #feature unmodified, e.g., 'kind == "ID"' columns
                pass


        else:
            # Feature is not modified.
            pass

    return dataset

def undo_discretize(dataset, schema, bins, copy: bool = True, handle_inf: bool = True):
    """ Return an unbinned dataset. """
    if handle_inf:
        # In some cases, the bin interval includes infinity
        # In that case, undoing the discretization is slightly harder
        original_bins = bins
        bins = {}

        for col, bin in original_bins.items():
            bins[col] = bin.copy()
            bins[col][-1] = bin[-2] + 1

    if copy:
        dataset = dataset.copy()

    for column in dataset:
        if column in bins:
            bin = bins[column]
            dataset[column] = bin[dataset[column].values]

        elif column in schema:
            desc = schema[column]
            if "values" in desc:
                dataset[column] = np.array(desc["values"])[dataset[column].values]
            elif "min" in desc:
                dataset[column] += desc["min"]
            else:
                raise ValueError("Unknown column, probably due to invalid schema")
        
        else:
            # Column is not known to bins or schema 
            # -> do not do anything
            pass

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
