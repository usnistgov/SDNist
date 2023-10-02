from typing import Tuple, List
import pandas as pd

import sdnist.gui.strs as strs
from sdnist.gui.constants import *

feature_set_dict = {
    strs.ALL_FEATURES: all_features,
    strs.SIMPLE_FEATURES: simple_features,
    strs.DEMOGRAPHIC_FOCUSED: demographic_focused,
    strs.DETAILED_INDUSTRY_FOCUSED: detailed_industry_focused,
    strs.FAMILY_FOCUSED: family_focused,
    strs.INDUSTRY_FOCUSED: industry_focused,
    strs.SMALL_CATEGORICAL: small_categorical,
    strs.TINY_CATEGORICAL: tiny_categorical
}


def feature_set(deid_data: pd.DataFrame) -> Tuple[str, List[str]]:
    # check for unnamed columns
    dd = deid_data
    dd = dd.loc[:, ~dd.columns.str.startswith('Unnamed')]

    d_cols = set(dd.columns.tolist())

    for fs_name, fs in feature_set_dict.items():
        if d_cols == set(fs):
            return fs_name, sorted(fs)

    t_cols = len(d_cols)
    return f'custom-features-{t_cols}', sorted(list(d_cols))
