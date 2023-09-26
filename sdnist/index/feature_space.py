from typing import Dict
import pandas as pd


def feature_space_size(target_df: pd.DataFrame, data_dict: Dict):
    size = 1

    for col in target_df.columns:
        if col in ['PINCP', 'POVPIP', 'WGTP', 'PWGTP', 'AGEP']:
            size = size * 100
        elif col in ['SEX', 'MSP', 'HISP', 'RAC1P', 'HOUSING_TYPE', 'OWN_RENT',
                     'INDP_CAT', 'EDU', 'PINCP_DECILE', 'DVET', 'DREM', 'DPHY', 'DEYE',
                     'DEAR']:
            size = size * len(data_dict[col]['values'])
        elif col in ['PUMA', 'DENSITY']:
            size = size * len(target_df['PUMA'].unique())
        elif col in ['NOC', 'NPF', 'INDP']:
            size = size * len(target_df[col].unique())
    return size
