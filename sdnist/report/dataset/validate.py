from typing import Dict, Optional, List
import pandas as pd

from sdnist.utils import SimpleLogger

def validate(synth_data: pd.DataFrame,
             schema: Dict,
             features: List[str],
             log: Optional[SimpleLogger] = None):
    def console_out(text: str):
        if log is not None:
            log.msg(text, level=3, timed=False, msg_type='error')

    validation_log = dict()
    sd = synth_data.copy()
    vob_features = []  # value out of bound
    nan_df = sd[sd.isna().any(axis=1)]

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

        if 'min' in f_data:
            mask = sd[sd[f] != 'N'].index if 'has_null' in f_data else sd.index
            sd.loc[mask, f] = pd.to_numeric(sd.loc[mask, f], errors="coerce")
            nans = sd[sd.isna().any(axis=1)]
            if len(nans):
                vob_vals = list(set(synth_data.loc[nans.index, f].values.tolist()))
                vob_features.append((f, vob_vals))
                console_out(f'Value out of bound for feature {f}, '
                      f'out of bound values: {vob_vals}. '
                            f'Removed records with out of bound values.')
                sd = sd.dropna()
            mask = sd[sd[f] != 'N'].index if 'has_null' in f_data else sd.index
            if f in ['PINCP']:
                sd.loc[mask, f] = sd.loc[mask, f].astype(float)
            else:
                sd.loc[mask, f] = sd.loc[mask, f].astype(int)
        elif f == 'PUMA':
            # values intersection
            f_unique = sd['PUMA'].unique().tolist()
            v_intersect = set(f_unique).intersection(set(f_data['values']))
            if len(v_intersect) < len(f_unique):
                vob_vals = list(set(f_unique).difference(v_intersect))
                vob_features.append((f, vob_vals))
                console_out(f'Value out of bound for feature {f}, '
                            f'out of bound values: {vob_vals}. Removed records with out of bound values.')
                sd = sd[~sd[f].isin(vob_vals)]
        else:
            mask = sd[sd[f] != 'N'].index if 'has_null' in f_data else sd.index
            sd.loc[mask, f] = pd.to_numeric(sd.loc[mask, f], errors="coerce")
            nans = sd[sd.isna().any(axis=1)]
            vob_vals = []
            if len(nans):
                vob_vals.extend(list(set(synth_data.loc[nans.index, f].values.tolist())))
                sd = sd.dropna()

            mask = sd[sd[f] != 'N'].index if 'has_null' in f_data else sd.index
            sd.loc[mask, f] = sd.loc[mask, f].astype(int)
            real_vals = f_data['values']
            if 'has_null' in f_data:
                real_vals.remove('N')
            if f != 'INDP':
                f_unique = set(sd.loc[mask, f].unique().tolist())
                real_vals = [int(v) for v in real_vals]
                v_intersect = set(f_unique).intersection(set(real_vals))
                if len(v_intersect) < len(f_unique):
                    vob_vals.extend(list(set(f_unique).difference(v_intersect)))

            if len(vob_vals):
                vob_features.append((f, vob_vals))
                console_out(f'Value out of bound for feature {f}, '
                      f'out of bound values: {vob_vals}. Removed records with out of bound values.')

    validation_log['values_out_of_bound'] = dict(vob_features)
    # print(validation_log)
    return sd