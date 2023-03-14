from typing import Dict, Optional, List
import pandas as pd

from sdnist.utils import SimpleLogger

def validate(synth_data: pd.DataFrame,
             schema: Dict,
             features: List[str],
             log: Optional[SimpleLogger] = None):
    """
    Removes all columns with the out of bound values.
    """
    def console_out(text: str):
        if log is not None:
            log.msg(text, level=3, timed=False, msg_type='error')

    validation_log = dict()
    sd = synth_data.copy()
    vob_features = []  # value out of bound
    nan_df = sd[sd.isna().any(axis=1)]
    nan_features = []
    if len(nan_df):
        nan_features = sd.columns[sd.isna().any()].tolist()
        validation_log['nans'] = {
            "nan_records": len(nan_df),
            "nan_features": nan_features
        }
        sd = sd.dropna()
        console_out(f'Found {len(nan_df)} records with NaN values. '
                    f'Removed records with NaN values.')

    for f in features:
        # check feature has out of bound value
        f_data = schema[f]
        has_nan = f in nan_features

        if 'min' in f_data:
            fd = sd[[f]].copy()
            mask = fd[fd[f] != 'N'].index if 'has_null' in f_data else fd.index
            fd.loc[mask, f] = pd.to_numeric(fd.loc[mask, f], errors="coerce")
            nans = fd[fd.isna().any(axis=1)]
            if len(nans):
                vob_vals = list(set(synth_data.loc[nans.index, f].values.tolist()))
                vob_features.append((f, vob_vals))
                console_out(f'Value out of bound for feature {f}, '
                      f'out of bound values: {vob_vals}. '
                            f'Dropping feature from evaluation.')
            mask = sd[sd[f] != 'N'].index if 'has_null' in f_data else sd.index
            if f in ['PINCP'] and not len(nans):
                sd.loc[mask, f] = sd.loc[mask, f].astype(float)
            elif not len(nans):
                sd.loc[mask, f] = sd.loc[mask, f].astype(int)
        elif f == 'PUMA':
            # values intersection
            f_unique = sd['PUMA'].unique().tolist()
            v_intersect = set(f_unique).intersection(set(f_data['values']))
            if len(v_intersect) < len(f_unique):
                vob_vals = list(set(f_unique).difference(v_intersect))
                vob_features.append((f, vob_vals))
                console_out(f'Value out of bound for feature {f}, '
                            f'out of bound values: {vob_vals}. Dropping feature from evaluation.')
        else:
            fd = sd[[f]].copy()
            mask = fd[fd[f] != 'N'].index if 'has_null' in f_data else fd.index
            fd.loc[mask, f] = pd.to_numeric(fd.loc[mask, f], errors="coerce")
            nans = fd[fd.isna().any(axis=1)]
            vob_vals = []
            if len(nans):
                vob_vals.extend(list(set(synth_data.loc[nans.index, f].values.tolist())))
                fd = fd.dropna()

            mask = fd[fd[f] != 'N'].index if 'has_null' in f_data else fd.index
            fd.loc[mask, f] = fd.loc[mask, f].astype(int)
            real_vals = f_data['values']
            if 'has_null' in f_data:
                real_vals.remove('N')
            if f != 'INDP':
                f_unique = set(fd.loc[mask, f].unique().tolist())
                real_vals = [int(v) for v in real_vals]
                v_intersect = set(f_unique).intersection(set(real_vals))
                if len(v_intersect) < len(f_unique):
                    vob_vals.extend(list(set(f_unique).difference(v_intersect)))

            if len(vob_vals):
                vob_features.append((f, vob_vals))
                console_out(f'Value out of bound for feature {f}, '
                      f'out of bound values: {vob_vals}. Dropping feature from evaluation.')
            else:
                mask = sd[sd[f] != 'N'].index if 'has_null' in f_data else sd.index
                sd.loc[mask, f] = sd.loc[mask, f].astype(int)

        if len(vob_features):
            last_vob_f, vob_vals = vob_features[-1]

            if last_vob_f == f:
                sd = sd.loc[:, sd.columns != f]
                if has_nan:
                    vob_features = (last_vob_f, ['nan'] + vob_vals)

    validation_log['values_out_of_bound'] = dict(vob_features)
    return sd, validation_log