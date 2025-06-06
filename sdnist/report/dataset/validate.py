from typing import Dict, Optional, List, Any
import pandas as pd

from sdnist.report.report_data import ValidationData
from sdnist.report.dataset.transform import deduce_code_type
from sdnist.report.dataset.data_dict import (
    get_feature_type, dtype_to_python_type, safe_isnan)
from sdnist.utils import SimpleLogger
import sdnist.strs as strs


def console_out(log: SimpleLogger, text: str):
    if log is not None:
        log.msg(text, level=3, timed=False, msg_type='error')


def validate_categorical_feature(
    data: pd.DataFrame,
    data_dict: Dict[str, any],
    feature: str
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
    "Remove columns with invalid values."
    validation_log = dict()
    d = data.copy()
    vob_features = []   # features with out of bound values
    for f in features:
        f_type = get_feature_type(data_dict, f)
        dc_type = deduce_code_type(f, data_dict)
        if dc_type is int and f not in ['FIPST']:
            with pd.option_context("future.no_silent_downcasting", True):
                d[f] = pd.to_numeric(d[f], errors='coerce').round().astype('Int64').astype(
                    object).fillna(d[f].astype(str))
        if f_type == strs.CATEGORICAL:
            vob_vals = validate_categorical_feature(d, data_dict, f)
        else:
            vob_vals = validate_continuous_feature(d, data_dict, f)
        if len(vob_vals):
            has_nan_vob = 'nan' in vob_vals
            nan_vob_row_counts = len(d[d[f].isna()]) if has_nan_vob else 0
            vob_row_count = len(d[d[f].isin(vob_vals)])
            vob_row_count = vob_row_count + nan_vob_row_counts
            if any([v for v in vob_vals if safe_isnan(v)]):
                d = d[~d[f].isna()]
            vob_features.append((f, ValidationData(f, vob_vals, vob_row_count)))
            console_out(log,
                        f'Value out of bound for feature {f}, '
                        f'out of bound values: {vob_vals}. '
                        f'Dropped {f} from evaluation.')
    validation_log = dict(vob_features)

    return d, validation_log


# def validate_old(synth_data: pd.DataFrame,
#              data_dict: Dict,
#              features: List[str],
#              log: Optional[SimpleLogger] = None):
#     """
#     Removes all columns with the out of bound values.
#     """
#     def console_out(text: str):
#         if log is not None:
#             log.msg(text, level=3, timed=False, msg_type='error')
#
#     validation_log = dict()
#     sd = synth_data.copy()
#     vob_features = []  # value out of bound
#     nan_df = sd[sd.isna().any(axis=1)]
#     nan_features = []
#     if len(nan_df):
#         nan_features = sd.columns[sd.isna().any()].tolist()
#         validation_log['nans'] = {
#             "nan_records": len(nan_df),
#             "nan_features": nan_features
#         }
#         # sd = sd.dropna()
#         # console_out(f'Found {len(nan_df)} records with NaN values. '
#         #             f'Removed records with NaN values.')
#
#     for f in features:
#         # check feature has out of bound value
#         f_data = data_dict[f]
#         has_nan = f in nan_features
#         has_N = 'N' in f_data['values'] if f != 'INDP' else True
#         f_vals = f_data['values'] if "values" in f_data else []
#
#         if 'min' in f_vals:
#             fd = sd[[f]].copy()
#             mask = fd[fd[f] != 'N'].index if has_N else fd.index
#             fd.loc[mask, f] = pd.to_numeric(fd.loc[mask, f], errors="coerce")
#             nans = fd[fd.isna().any(axis=1)]
#             if len(nans):
#                 vob_vals = list(set([str(v)
#                                      for v in synth_data.loc[nans.index, f].values.tolist()]))
#                 vob_features.append((f, vob_vals))
#                 console_out(f'Value out of bound for feature {f}, '
#                       f'out of bound values: {vob_vals}. '
#                             f'Dropping feature from evaluation.')
#
#             mask = sd[sd[f] != 'N'].index if has_N else sd.index
#
#             if f in ['PINCP'] and not len(nans):
#                 sd.loc[mask, f] = pd.to_numeric(sd.loc[mask, f])
#                 sd.loc[mask, f] = sd.loc[mask, f].astype(float)
#             elif not len(nans):
#                 sd.loc[mask, f] = pd.to_numeric(sd.loc[mask, f])
#                 sd.loc[mask, f] = sd.loc[mask, f].astype(int)
#         elif f == 'PUMA':
#             # values intersection
#             f_unique = sd['PUMA'].unique().tolist()
#             v_intersect = set(f_unique).intersection(set(f_vals))
#             if len(v_intersect) < len(f_unique):
#                 vob_vals = list(set([str(v) for v in
#                                      list(set(f_unique).difference(v_intersect))]))
#                 vob_features.append((f, vob_vals))
#                 console_out(f'Value out of bound for feature {f}, '
#                             f'out of bound values: {vob_vals}. Dropping feature from evaluation.')
#         else:
#             fd = sd[[f]].copy()
#             mask = fd[fd[f] != 'N'].index if has_N else fd.index
#             fd.loc[mask, f] = pd.to_numeric(fd.loc[mask, f], errors="coerce")
#             nans = fd[fd.isna().any(axis=1)]
#             vob_vals = []
#             if len(nans):
#                 vob_vals.extend(list(set([str(v)
#                                           for v in synth_data.loc[nans.index, f].values.tolist()])))
#                 fd = fd.dropna()
#
#             mask = fd[fd[f] != 'N'].index if has_N else fd.index
#             fd.loc[mask, f] = fd.loc[mask, f].astype(int)
#
#             if f != 'INDP':
#                 real_vals = list(f_vals.keys())
#                 if 'N' in real_vals:
#                     real_vals.remove('N')
#                 f_unique = set(fd.loc[mask, f].unique().tolist())
#                 real_vals = [int(v) for v in real_vals]
#                 v_intersect = set(f_unique).intersection(set(real_vals))
#                 if len(v_intersect) < len(f_unique):
#                     vob_vals.extend(set([str(v)
#                                          for v in list(set(f_unique).difference(v_intersect))]))
#
#             if len(vob_vals):
#                 vob_features.append((f, vob_vals))
#                 console_out(f'Value out of bound for feature {f}, '
#                       f'out of bound values: {vob_vals}. Dropping feature from evaluation.')
#             else:
#                 mask = sd[sd[f] != 'N'].index if has_N else sd.index
#                 sd.loc[mask, f] = pd.to_numeric(sd.loc[mask, f])
#                 sd.loc[mask, f] = sd.loc[mask, f].astype(int)
#         if has_N:
#             sd[f] = sd[f].astype(object)
#
#         if len(vob_features):
#             last_vob_f, vob_vals = vob_features[-1]
#             if last_vob_f == f:
#                 sd = sd.loc[:, sd.columns != f]
#                 if has_nan:
#                     vob_features[-1] = (last_vob_f, ['nan'] + list(set(vob_vals)))
#
#     validation_log['values_out_of_bound'] = dict(vob_features)
#     return sd, validation_log