from typing import Dict, Tuple, Union
import pandas as pd
import numpy as np

from sdnist.report.dataset.data_dict import (
    is_numeric, parse_numeric_value, deduce_code_type)
import sdnist.strs as strs


def create_null_value_map(null_code: any,
                          code_for_nan: int) -> Dict[any, Union[int, float]]:
    """
    convert a null code to an integer value if its not already
    an integer of float.
    :param null_code:
    :param code_for_nan:
    :return:
    """
    null_mapping = dict()
    if null_code is not None:
        if null_code == '':
            null_mapping['nan'] = code_for_nan
        elif not str(null_code).isnumeric():
            null_mapping[null_code] = code_for_nan
        else:
            null_mapping[null_code] = null_code
    return null_mapping


def get_str_codes(feature: str, data_dict: Dict[str, Dict]) -> \
        Dict[str, int]:
    """
    Get integer codes for string values of a feature.
    """
    fd = data_dict[feature]
    values = fd.get(strs.VALUES, [])
    null_value_code = fd.get(strs.NULL_VALUE, None)
    max_val = 0
    if strs.MAX in values:
        max_val = parse_numeric_value(values[strs.MAX])
    num_vals = [parse_numeric_value(v) for v in values if str(v).isnumeric()]
    str_vals = [str(v) for v in values if not str(v).isnumeric() and
                v not in [strs.MIN, strs.MAX, strs.STEP_SIZE, null_value_code]]
    if num_vals:
        max_val = max(max_val, max(num_vals))
    max_val = int(max_val + 1)
    str_codes = {sv: i for i, sv in enumerate(str_vals, start=max_val)}
    return str_codes


def get_null_codes(feature: str, data_dict: Dict[str, Dict]) \
        -> Dict[any, Union[int, float]]:
    """
    Get mapping of null codes (logical skip code and missing value code).
    mapping contains actual null code value as key and its integer code
    as value. If one of the null codes is empty string, it is mapped to 'nan'.
    """
    fd = data_dict[feature]
    values = fd.get(strs.VALUES, [])
    null_value_code = fd.get(strs.NULL_VALUE, None)
    min_val = 0
    if strs.MIN in values:
        min_val = parse_numeric_value(values[strs.MIN])

    num_vals = [parse_numeric_value(v) for v in values if str(v).isnumeric()]
    if num_vals:
        min_val = min(min_val, min(num_vals))
    if is_numeric(null_value_code):
        min_val = min(min_val, int(null_value_code))
    min_val -= 1
    null_codes = dict()

    if null_value_code is not None and not is_numeric(null_value_code):
        null_codes |= create_null_value_map(null_value_code, min_val)
        min_val -= 1

    return null_codes

def feature_space_size(target_df: pd.DataFrame):
    size = 1

    for col in target_df.columns:
        size = size * len(target_df[col].unique())

    return size


def transform(t: pd.DataFrame, d: pd.DataFrame, ddict: Dict) \
        -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, Dict]]:
    tt = t.copy()  # transformed target data
    dt = d.copy()  # transformed deid data
    # replace np.nan with string nan
    with pd.option_context("future.no_silent_downcasting", True):
        tt = tt.fillna('nan')
        dt = dt.fillna('nan')
    mappings = dict()  # mappings for transformed values
    for f in t.columns.tolist():  # for each feature transform
        fd = ddict[f]  # feature dictionary
        # deduce if feature values are int or float
        c_type = deduce_code_type(f, ddict)
        if c_type is str:
            c_type = int
        # find null/nan codes and get the null codes mappings
        null_codes = get_null_codes(f, ddict)
        # find string codes and get the string codes mappings
        str_codes = get_str_codes(f, ddict)
        # mapping for all the values that are to be transformed
        value_to_code = null_codes | str_codes

        # if no nan or missing values to transform, then
        # check if both features has the same dtype, fix dtypes
        # and continue to the next feature
        if not value_to_code:
            t_dtype = tt[f].dtype
            d_dtype = dt[f].dtype
            if t_dtype != d_dtype:
                dt[f] = dt[f].astype(c_type)
            continue

        # get values
        tt_array = tt[f].values
        dt_array = dt[f].values

        # Map the keys in the value_to_code dict to its values
        mapper = np.vectorize(
            lambda x: value_to_code.get(x, x)
        )

        # Update the dataframe with transformed values
        tt[f] = pd.to_numeric(mapper(tt_array)).astype(c_type)
        dt[f] = pd.to_numeric(mapper(dt_array)).astype(c_type)
        mappings[f] = value_to_code
    return tt, dt, mappings


def transform_old(data: pd.DataFrame, schema: Dict):
    # replace categories with codes
    # replace N: NA with -1 for categoricals
    # replace N: NA with mean for numericals
    data = data.copy()
    for c in data.columns.tolist():
        desc = schema[c]
        with pd.option_context("future.no_silent_downcasting", True):
            if "values" in desc and not 'min' in desc["values"]:
                if "has_null" in desc:
                    null_val = desc["null_value"]
                    data[c] = data[c].replace(null_val, -1)
            elif "min" in desc["values"]:
                if "has_null" in desc:
                    null_val = desc["null_value"]
                    nna_mask = data[~data[c].isin(['N'])].index  # not na mask
                    if c == 'PINCP':
                        data[c] = data[c].replace(null_val, 9999999)
                        data[c] = pd.to_numeric(data[c]).astype(float)
                    elif c == 'POVPIP':
                        data[c] = data[c].replace(null_val, 999)
                        data[c] = pd.to_numeric(data[c]).astype(int)
                    else:
                        data[c] = data[c].replace(null_val, -1)
                        data[c] = pd.to_numeric(data[c]).astype(int)
            if c == 'PUMA':
                data[c] = data[c].astype(pd.CategoricalDtype(desc["values"])).cat.codes
                if "N" in desc['values']:
                    data[c] = data[c].replace(0, -1)
            else:
                data[c] = pd.to_numeric(data[c]).astype(int)

    return data