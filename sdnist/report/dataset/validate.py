from typing import Dict, Optional, List, Any
import pandas as pd

from sdnist.report.report_data import ValidationData
from sdnist.report.dataset.transform import deduce_code_type
from sdnist.report.dataset.data_dict import (
    get_feature_type, dtype_to_python_type, safe_isnan, parse_numeric_value)
from sdnist.utils import SimpleLogger
import sdnist.strs as strs


def console_out(log: SimpleLogger, text: str):
    if log is not None:
        log.msg(text, level=3, timed=False, msg_type='error')


def validate_categorical_feature(
    data: pd.DataFrame,
    data_dict: Dict[str, any],
    feature: str,
    code_type: type,
):
    d = data
    f = feature
    fd: Dict = data_dict[f]
    f_vals: List[str] = list(fd[strs.VALUES].keys())
    f_type = strs.CATEGORICAL
    # c_type = data_dict[f][strs.DTYPE]
    # c_type = dtype_to_python_type(c_type)
    # f_vals = [c_type(v) for v in f_vals]
    null_value_code = fd.get(strs.NULL_VALUE, None)
    if null_value_code == '':
        if '' in f_vals:
            f_vals.remove('')
        f_vals.append('nan')
    elif (null_value_code is not None
          and null_value_code not in f_vals):
        f_vals.append(null_value_code)

    f_uniques = d[f].astype(str).unique().tolist()
    f_uniques = ['nan' if safe_isnan(v) else v
                 for v in f_uniques]
    # If all values are parsed as code_type,
    # then convert them to code_type
    val_types = [type(parse_numeric_value(v)) == code_type
                 for v in f_vals]
    if all(val_types):
        f_vals = [code_type(v) for v in f_vals]
        f_uniques = [code_type(v) if v != 'nan' else v for v in f_uniques]
    vob_values = list(set(f_uniques) - set(f_vals))
    return vob_values


def validate_continuous_feature(data: pd.DataFrame,
                                data_dict: Dict,
                                feature: str):
    d = data
    f = feature
    fd: Dict = data_dict[f]
    num_vals = pd.to_numeric(d[f], errors='coerce')
    mask = num_vals.isna()
    df_non_numeric_or_nan = d[mask]
    f_vals = df_non_numeric_or_nan[f].unique().tolist()
    null_value_code = fd.get(strs.NULL_VALUE, None)

    if null_value_code not in f_vals and null_value_code == '':
        f_vals = [v for v in f_vals if not safe_isnan(v)]
    elif null_value_code is not None:
        f_vals = [v for v in f_vals if v != null_value_code]
    vob_values = list(set(f_vals))
    return vob_values


def validate(data: pd.DataFrame,
             data_dict: Dict,
             features: List[str],
             log: Optional[SimpleLogger] = None):
    """Remove columns with invalid values."""

    validation_log = dict()
    d = data.copy()
    vob_features = []   # features with out-of-bound values
    for f in features:
        f_type = get_feature_type(data_dict, f)
        dc_type = deduce_code_type(f, data_dict)
        if dc_type is int and f not in ['FIPST']:
            with pd.option_context("future.no_silent_downcasting", True):
                d[f] = pd.to_numeric(d[f], errors='coerce').round().astype('Int64').astype(
                    object).fillna(d[f].astype(str))
        if f_type == strs.CATEGORICAL:
            vob_vals = validate_categorical_feature(d, data_dict, f, dc_type)
        else:
            vob_vals = validate_continuous_feature(d, data_dict, f)
        all_vob_vals = vob_vals.copy()
        if len(vob_vals):
            has_nan_vob = 'nan' in vob_vals
            nan_vob_row_counts = len(d[d[f].isna()]) if has_nan_vob else 0
            vob_row_count = len(d[d[f].isin(vob_vals)])
            vob_row_count = vob_row_count + nan_vob_row_counts
            if has_nan_vob:
                d = d[~d[f].isna()]
            if len(vob_vals):
                d = d[~d[f].isin(vob_vals)]
            vob_features.append((f, ValidationData(f, vob_vals, vob_row_count)))
            console_out(log,
                        f'Value out of bound for feature {f}, '
                        f'out of bound values: {all_vob_vals}. '
                        f'Dropped {vob_row_count} rows from evaluation.')
    validation_log = dict(vob_features)

    return d, validation_log
