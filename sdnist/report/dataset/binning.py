from typing import Dict, List
import pandas as pd
import numpy as np
import math


def percentile_rank_target(data: pd.DataFrame, features: List[str]):
    data = data.copy()
    for c in features:
        if c not in data.columns:
            continue

        if c == 'POVPIP':
            nna_mask = data[~data[c].isin(['N', '501'])].index
        else:
            nna_mask = data[~data[c].isin(['N'])].index  # not na mask
        d_temp = pd.DataFrame(pd.to_numeric(data.loc[nna_mask, c]).astype(int), columns=[c])
        data.loc[nna_mask, c] = d_temp[c]\
            .rank(pct=True).apply(lambda x: int(20 * x) if x < 1 else 19)
        if c == 'POVPIP':
            data[c] = data[c].apply(lambda x: int(x) if x == '501' else x)
    return data


def percentile_rank_synthetic(synthetic: pd.DataFrame,
                              target_orig: pd.DataFrame,
                              target_binned: pd.DataFrame,
                              features: List[str]):
    s, to, tb = synthetic.copy(), target_orig, target_binned

    for f in features:
        if f not in to.columns.tolist():
            continue
        nna_mask = s[~s[f].isin(['N'])].index  # not na mask
        st = pd.DataFrame(pd.to_numeric(s.loc[nna_mask, f]).astype(int), columns=[f])
        final_st = st.copy()
        max_b = 0
        last_bin = sorted(target_binned[f].unique().tolist())[-1]
        for b, g in target_binned.sort_values(by=[f]).groupby(by=f):
            if b == -1:
                continue
            t_bp = pd.DataFrame(pd.to_numeric(to.loc[g.index, f]).astype(int), columns=[f])
            if b == 0:
                max_b = max(t_bp[f])
                final_st.loc[(st[f] <= max_b), f] = b
            elif b != last_bin:
                min_b = max_b
                max_b = max(t_bp[f])
                final_st.loc[(st[f] > min_b) & (st[f] <= max_b), f] = b
            else:
                min_b = max_b
                final_st.loc[(st[f] > min_b), f] = b
        s.loc[nna_mask, f] = final_st
    return s


def add_bin_for_NA(data, reference_data, features):
    d = data
    rd = reference_data

    for c in features:
        if c not in data.columns:
            continue
        na_mask = rd[rd[c].isin(['N'])].index
        if len(na_mask):
            d.loc[na_mask, c] = -1
    return d


def bin_density(data: pd.DataFrame, data_dict: Dict, update: bool = True) -> pd.DataFrame:
    """
    data: Data containing density feature
    data_dict: Dictionary containing values range for density feature
    update: if True, update the input data's density feature and return
            else, create two new columns: binned_density and bin_range
            and return the data
    """
    def get_bin_range_log(x):
        for i, v in enumerate(bins):
            if i == x:
                return f'({round(v, 2)}, {round(bins[i + 1], 2)}]'
    d = data
    dd = data_dict
    base = 10
    # we remove first 8 bins from this bins list, and prepend
    # two bins. So effective bins are 12. This is done to bottom
    # code density category for the PUMAs with small density.
    n_bins = 20  # number of bins
    # max of range
    n_max = dd['DENSITY']['values']['max'] + 500

    bins = np.logspace(start=math.log(10, base), stop=math.log(n_max, base), num=n_bins+1)
    # remove first 8 bins and prepend two new bins
    bins = [0, 150] + list(bins[8:])
    # print('Bins', bins)
    # print('Densities', d['DENSITY'].unique().tolist())
    n_bins = len(bins)  # update number of bins to effective bins
    labels = [i for i in range(n_bins-1)]

    # top code values to n_max and bottom code values to 0 in the data
    d.loc[d['DENSITY'] < 0, 'DENSITY'] = float(0)
    d.loc[d['DENSITY'] > n_max, 'DENSITY'] = float(n_max) - 100

    if update:
        d['DENSITY'] = pd.cut(d['DENSITY'], bins=bins, labels=labels)
        return d
    else:
        d['binned_density'] = pd.cut(d['DENSITY'], bins=bins, labels=labels)

        d['bin_range'] = d['binned_density'].apply(lambda x: get_bin_range_log(x))
        return d


def get_density_bins_description(data: pd.DataFrame,
                                 data_dict: Dict,
                                 mappings: Dict) -> Dict:
    bin_desc = dict()
    # If puma is not available in the features, return empty description dictionary
    if 'PUMA' not in data:
        return bin_desc

    d = bin_density(data.copy(), data_dict, update=False)

    for dbin, g in d.groupby(by='binned_density'):
        if g.shape[0] == 0:
            continue

        density_range = g['bin_range'].unique()[0]
        bin_data = []
        for puma, pg in g.groupby(by='PUMA'):
            density = pg['DENSITY'].unique()[0]
            bin_data.append([puma, density, mappings["PUMA"][puma]["name"]])
        bin_df = pd.DataFrame(bin_data, columns=['PUMA', 'DENSITY', 'PUMA NAME'])
        bin_desc[dbin] = (density_range, bin_df)
    del d
    # print(bin_desc)
    return bin_desc