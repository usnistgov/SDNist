from typing import Dict, Tuple, Any

from sdnist.report.dataset import Dataset

import sdnist.strs as strs
from sdnist.utils import *


def stable_feature_mappings(data_dict: Dict[str, Any],
                            mappings: Dict[str, Any],
                            feature: str,
                            feature_val: str) -> Tuple[str, str]:
    feature_val = str(feature_val)
    default_res = ('', '')

    def get_mapping(source: Dict[str, Any]) -> Tuple[str, str]:
        if feature not in source or feature_val not in source[feature]:
            return default_res

        f_val_data = source[feature][feature_val]

        if isinstance(f_val_data, str):
            return f_val_data, ''
        if isinstance(f_val_data, dict):
            return f_val_data.get("name", ''), f_val_data.get("link", '')

        return default_res

    result = get_mapping(mappings)
    if result == default_res:
        result = get_mapping(data_dict)
    return result


def best_worst_performing(scores: pd.Series,
                          subsample_stable_feature_scores: pd.DataFrame,
                          dataset: Dataset,
                          stable_feature: str,
                          stable_feature_values: Dict[str, Dict]) -> Tuple[List, List]:

    ss = pd.concat([scores, subsample_stable_feature_scores], axis=1)
    ss = ss.sort_values(by=[0])
    worst_scores = []
    best_scores = []
    sf_bin_map = dataset.bin_mappings[stable_feature]

    for wf in ss.index:  # feature values with worst k-marginal scores
        f_values = {f: (stable_feature_values[f][wf[i]]
                        if isinstance(wf, tuple) else wf)
                        for i, f in enumerate([stable_feature])}
        str_values = {f: sf_bin_map[f_val] for f, f_val in f_values.items()}
        f_values = {f: [f_val] + list(stable_feature_mappings(dataset.data_dict,
                                                              dataset.mappings,
                                                              f, f_val))
                    for f, f_val in str_values.items()}
        worst_scores.append({
            **f_values,
            "40% Target Subsample Baseline": int(ss.loc[wf, 1]),
            'Deidentified Data ' + strs.SCORE.capitalize(): int(ss.loc[wf, 0])
        })
    ss = ss.sort_values(by=[0], ascending=False)
    for bf in ss.index:  # feature values with best k-marginal scores
        f_values = {f: (stable_feature_values[f][bf[i]]
                        if isinstance(bf, tuple) else
                        bf)
                    for i, f in enumerate([stable_feature])}
        str_values = {f: sf_bin_map[f_val] for f, f_val in f_values.items()}
        f_values = {f: [f_val] + list(stable_feature_mappings(dataset.data_dict,
                                                              dataset.mappings,
                                                              f, f_val))
                    for f, f_val in str_values.items()}
        best_scores.append({
            **f_values,
            "40% Target Subsample Baseline": int(ss.loc[bf, 1]),
            strs.SCORE.capitalize(): int(ss.loc[bf, 0])
        })

    return worst_scores, best_scores
