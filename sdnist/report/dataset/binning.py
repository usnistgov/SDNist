from typing import Dict, List, Tuple
import pandas as pd
import numpy as np
import math

import sdnist.strs as strs
from sdnist.report.dataset.data_dict import get_feature_type
from sdnist.report.dataset.transform import (
    parse_numeric_value, get_null_codes)


def bin_continuous_feature(t_f: pd.DataFrame,
                           d_f: pd.DataFrame,
                           data_dict: Dict,
                           n_bins) \
        -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, dict]]:
    t_f = t_f.copy()
    d_f = d_f.copy()
    bin_mappings = dict()
    f = t_f.columns.tolist()[0]
    f_values = list(data_dict[f][strs.VALUES])

    f_min = parse_numeric_value(data_dict[f][strs.VALUES][strs.MIN])
    f_max = parse_numeric_value(data_dict[f][strs.VALUES][strs.MAX])
    if f_max - f_min <= n_bins:
        return t_f, d_f, bin_mappings

    null_codes = get_null_codes(f, data_dict)

    # find values to leave out of binning
    no_bin_vals = list(null_codes.values())
    # target and deid unique vals
    tuv = t_f[~t_f[f].isin(no_bin_vals)][f].unique().tolist()
    duv = d_f[~d_f[f].isin(no_bin_vals)][f].unique().tolist()
    t_max_val = max(tuv)
    t_min_val = min(tuv)
    d_max_val = max(duv) if len(duv) else t_max_val  # deid data max value
    d_min_val = min(duv) if len(duv) else t_min_val  # deid data min value


    # total bins to create after leaving off other values
    n_bins = n_bins - len(no_bin_vals)
    extra_bin_edges = [t_max_val]

    # if deid data has the absolute max, then create another top bin
    # with deid max value
    if d_max_val > t_max_val:
        n_bins = n_bins - 1
        extra_bin_edges.append(d_max_val)

    if d_min_val < t_min_val:
        extra_bin_edges = [d_min_val] + extra_bin_edges
        n_bins = n_bins - 1

    # create bin percentiles
    bins = [i * (100 / n_bins) for i in range(n_bins)]

    tv = t_f[~t_f[f].isin(no_bin_vals)][f].values.tolist()
    bin_edges = list(np.unique(np.percentile(tv, bins, method='higher'))) + extra_bin_edges

    if bin_edges[-1] == bin_edges[-2]:
        bin_edges = bin_edges[:-1]
    bin_edges = sorted(bin_edges)
    # update lowest bin to be the minimum values of target or deid data
    # min_val = d_min_val if d_min_val < t_min_val else t_min_val
    # bin_edges[0] = min_val
    mapping = {i: int(bin_edges[i]) for i, bv in enumerate(bin_edges)}
    # create reverse string and null codes mapping
    rev_null_codes = {v: k for k, v in null_codes.items()}

    for nv in null_codes:
        if nv in rev_null_codes:
            mapping[nv] = rev_null_codes[nv]
        else:
            mapping[nv] = nv

    dtype = t_f[f].dtype
    tna = t_f[t_f[f].isin(no_bin_vals)]
    dna = d_f[d_f[f].isin(no_bin_vals)]
    tnna = t_f[~t_f[f].isin(no_bin_vals)]
    dnna = d_f[~d_f[f].isin(no_bin_vals)]
    tnna.loc[:, f] = (pd.cut(tnna[f], bins=bin_edges, labels=False,
                            include_lowest=True, duplicates='drop')
                      .astype(dtype))
    dnna.loc[:, f] = (pd.cut(dnna[f], bins=bin_edges, labels=False,
                            include_lowest=True, duplicates='drop')
                      .astype(dtype))
    tb = pd.concat([tnna, tna])
    db = pd.concat([dnna, dna])
    tb = tb.reindex(t_f.index)
    db = db.reindex(d_f.index)
    t_f[f], d_f[f] = tb[f], db[f]
    bin_mappings[f] = mapping

    return t_f, d_f, bin_mappings


def bin_data(t: pd.DataFrame,
             d: pd.DataFrame,
             ddict: Dict,
             n_bins: int = 20) \
        -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, Dict]]:
    """
    Bin numerical features and categorical features with range.
    Features is list of lists. Each sub list contains features
    that are to binned at same time using min and max values
    from all features in a group.
    :param t: target
    :param d: deid data
    :param ddict: data dictionary
    :param features: feature groups to bin
    :param n_bins: number of bins to create
    :param binning_method: method used to bin values: equal frequency
        or equal width
    :return: binned target, binned deid data, bin to orig edge value mappings
    """
    tb = t.copy()
    db = d.copy()
    no_binning = ['DENSITY']
    bin_mappings = dict()
    continuous_features = [f for f in tb.columns
                          if get_feature_type(ddict, f) == strs.CONTINUOUS]
    for f in continuous_features:
        if f in no_binning:
            continue
        tb_n, db_n, mappings = bin_continuous_feature(tb[[f]],
                                                      db[[f]],
                                                      ddict, n_bins)
        tb[f], db[f] = tb_n[f], db_n[f]
        bin_mappings.update(mappings)

    for f in tb.columns:
        if f not in bin_mappings and f not in no_binning:
            unique_vals = sorted(set(tb[f].unique().tolist())
                                 .union(set(db[f].unique().tolist())))
            bin_mappings[f] = {v: v for v in unique_vals}
    return tb, db, bin_mappings


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
        s.loc[nna_mask, f] = final_st[f]
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
                return round(v, 2), round(bins[i + 1], 2)
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
        d['DENSITY'] = pd.cut(d['DENSITY'], bins=bins, labels=labels).astype(int)
        return d
    else:
        d['binned_density'] = pd.cut(d['DENSITY'], bins=bins, labels=labels).astype(int)

        d['bin_range'] = d['binned_density'].apply(lambda x: get_bin_range_log(x))
        return d


def get_density_bins_description(data: pd.DataFrame,
                                 data_dict: Dict,
                                 mappings: Dict) -> Tuple[Dict, Dict]:
    bin_desc = dict()
    # If puma is not available in the features, return empty description dictionary
    if 'PUMA' not in data:
        return bin_desc

    d = bin_density(data.copy(), data_dict, update=False)
    bin_mappings = {}
    for dbin, g in d.groupby(by='binned_density'):
        if g.shape[0] == 0:
            continue
        density_range = g['bin_range'].unique()[0]
        bin_data = []
        for puma, pg in g.groupby(by='PUMA'):
            density = pg['DENSITY'].unique()[0]
            bin_data.append([puma, density, mappings["PUMA"][puma]["name"]])
        bin_df = pd.DataFrame(bin_data, columns=['PUMA', 'DENSITY', 'PUMA NAME'])
        bin_desc[dbin] = (str(density_range), bin_df)
        bin_mappings[dbin] = density_range[0]
    del d
    # print(bin_desc)
    return bin_desc, bin_mappings