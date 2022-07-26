import os
from typing import List, Dict, Tuple, Optional
from pathlib import Path

import pandas as pd

from sdnist.metrics.kmarginal import \
    CensusKMarginalScore, TaxiKMarginalScore, KMarginalScore
from sdnist.metrics.hoc import \
    TaxiHigherOrderConjunction
from sdnist.metrics.graph_edge_map import \
    TaxiGraphEdgeMapScore
from sdnist.metrics.propensity import \
    PropensityMSE
from sdnist.metrics.pearson_correlation import \
    PearsonCorrelationDifference

from sdnist.report import Dataset
from sdnist.report.report_data import \
    ReportData, UtilityScorePacket, Attachment, AttachmentType, \
    DatasetType, DataDescriptionPacket
from sdnist.report.plots import \
    UnivariatePlots, CorrelationDifferencePlot, \
    GridPlot, PropensityDistribution, PearsonCorrelationPlot


import sdnist.strs as strs


def best_worst_performing(scores: pd.Series,
                          dataset: Dataset,
                          group_features: List[str],
                          feature_values: Dict[str, Dict]) -> Tuple[List, List]:
    def feat_name_value(feature, feature_val):
        feature_val = str(feature_val)
        default_res = [None, None]

        fv = dataset.data_dict
        if feature not in fv:
            return default_res

        f_data = fv[feature]
        if feature_val not in f_data:
            return default_res

        f_val_d = f_data[feature_val]
        if type(f_val_d) == str:
            return [f_val_d, None]

        if type(f_val_d) == dict:
            if "name" in f_val_d and "link" in f_val_d:
                return [f_val_d["name"], f_val_d["link"]]

            if "name" in f_val_d:
                return [f_val_d["name"], None]

    ss = scores.sort_values()
    worst_scores = []
    best_scores = []

    for wf in ss.index:  # worst score features
        f_values = {f: (feature_values[f][wf[i]]
                        if type(wf) == tuple else
                        feature_values[f][wf])
                    for i, f in enumerate(group_features)}
        f_values = {f: [f_val] + feat_name_value(f, f_val)
                    for f, f_val in f_values.items()}
        worst_scores.append({
            **f_values,
            strs.SCORE: int(ss[wf])
        })

    ss = scores.sort_values(ascending=False)

    for bf in ss.index:
        f_values = {f: (feature_values[f][bf[i]]
                        if type(bf) == tuple else
                        feature_values[f][bf])
                    for i, f in enumerate(group_features)}
        f_values = {f: [f_val] + feat_name_value(f, f_val)
                    for f, f_val in f_values.items()}
        best_scores.append({
            **f_values,
            strs.SCORE: int(ss[bf])
        })

    return worst_scores, best_scores


def worst_score_breakdown(worst_scores: List,
                          dataset: Dataset,
                          report_data: ReportData,
                          feature: str) -> List[Attachment]:
    ds = dataset
    rd = report_data

    wsh = pd.DataFrame(worst_scores)
    if str(wsh.loc[0, feature]).startswith('['):
        wsh[feature] = wsh[feature].apply(lambda x: list(x)[0])
    wpf = wsh[feature].unique().tolist()[:5]  # worst performing feature values
    t = dataset.target_data.copy()
    s = dataset.synthetic_data.copy()

    t = t[t[feature].isin(wpf)]
    s = s[s[feature].isin(wpf)]

    out_dir = Path(rd.output_directory, 'k_marginal_breakdown')
    if not out_dir.exists():
        os.mkdir(out_dir)

    up = UnivariatePlots(t, s,
                         ds.schema, out_dir, ds.challenge)
    up_saved_file_paths = up.save()

    pcd = PearsonCorrelationDifference(t, s,
                                       ds.config[strs.CORRELATION_FEATURES])
    pcd.compute()
    pcp = PearsonCorrelationPlot(pcd.pp_corr_diff, out_dir)
    pcp_saved_file_paths = pcp.save()

    rel_up_saved_file_paths = ["/".join(list(p.parts)[-3:])
                               for p in up_saved_file_paths]
    rel_pcp_saved_file_paths = ["/".join(list(p.parts)[-3:])
                                for p in pcp_saved_file_paths]
    # attachment for worst feature names
    a_wf = Attachment(name='Five Worst Performing ' + feature,
                      _data=", ".join(wpf),
                      _type=AttachmentType.String)

    # attachment for records in each data for worst performing feature
    a_rt = Attachment(name='Record Counts in Five Worst Performing ' + feature,
                      _data=[{"Dataset": "Target", "Record Counts": t.shape[0]},
                             {"Dataset": "Synthetic", "Record Counts": s.shape[0]}],
                      _type=AttachmentType.Table)
    a_up = Attachment(name="Univariate Distribution of Worst "
                           "Performing Features in Five Worst Performing "
                           + feature,
                      _data=[{strs.IMAGE_NAME: Path(p).stem, strs.PATH: p}
                             for p in rel_up_saved_file_paths],
                      _type=AttachmentType.ImageLinks)

    a_pc = Attachment(name="Pearson Correlation Coefficient Difference in Five Worst Performing "
                           + feature,
                      _data=[{strs.IMAGE_NAME: Path(p).stem, strs.PATH: p}
                             for p in rel_pcp_saved_file_paths],
                      _type=AttachmentType.ImageLinks)

    return [a_wf, a_rt, a_up, a_pc]


def kmarginal_subsamples(dataset: Dataset,
                         k_marginal_cls) \
        -> Dict[float, int]:
    # mapping of sub sample frac to k-marginal score of fraction
    ssample_score = dict()  # subsample scores dictionary
    # find k-marginal of 10%, 20% ... 90% of sub-sample of target data
    for i in range(1, 10):
        # using subsample of target data as synthetic data
        s_sd = dataset.target_data.sample(frac=i * 0.1)  # subsample as synthetic data
        s_kmarg = k_marginal_cls(dataset.target_data,
                                 s_sd,
                                 dataset.schema,
                                 **dataset.config[strs.K_MARGINAL])
        s_kmarg.compute_score()
        s_score = int(s_kmarg.score)
        ssample_score[i * 0.1] = s_score

    return ssample_score


def kmarginal_score_packet(k_marginal_score: int,
                           group_features: List[str],
                           group_scores: pd.Series,
                           feature_values: Dict[str, Dict],
                           dataset: Dataset,
                           report_data: ReportData,
                           subsample_scores: Dict[float, int],
                           worst_breakdown_feature: str) -> Tuple[UtilityScorePacket,
                                                                  UtilityScorePacket]:
    def min_index(data_list: List[float]):
        mi = 0
        m = max(data_list)
        for i, v in enumerate(data_list):
            if v < m:
                mi, m = i, v
        return mi

    sorted_frac = sorted(list(subsample_scores.keys()))
    score_error = [abs(subsample_scores[frac] - k_marginal_score)
                   for frac in sorted_frac]
    min_frac = sorted_frac[min_index(score_error)]

    # subsample fraction score attachment
    ssf_a = Attachment(name=f"Sampling Error Comparison",
                       _data=f"K-Marginal score of synthetic data closely resembles "
                             f"K-Marginal score of {int(min_frac * 100)}% sub-sample of "
                             f"the target data.",
                       _type=AttachmentType.String)

    # sampling error data attachment
    sedf = [{"Sub-Sample Size": f"{int(frac * 100)}%",
             "Sub-Sample K-Marginal Score": subsample_scores[frac],
             "% Difference from Synthetic Data K-marginal Score":
                 f"{abs(subsample_scores[frac] - k_marginal_score)/10}%"}
            for frac in sorted_frac]

    sed_a = Attachment(name=None,
                       _data=sedf,
                       _type=AttachmentType.Table)

    worst_scores, best_scores = best_worst_performing(group_scores,
                                                      dataset,
                                                      group_features,
                                                      feature_values)

    w_b_n = 10 if len(worst_scores) > 10 else len(worst_scores)
    worst_scores, best_scores = worst_scores[0: w_b_n], best_scores[0: w_b_n]

    worst_break_down = worst_score_breakdown(worst_scores,
                                             dataset,
                                             report_data,
                                             worst_breakdown_feature)

    ws_a = Attachment(name=f"{len(worst_scores)} Worst Performing " + '-'.join(group_features),
                      _data=worst_scores)

    bs_a = Attachment(name=f"{len(best_scores)} Best Performing " + '-'.join(group_features),
                      _data=best_scores)

    kmarg_sum_pkt = UtilityScorePacket('K-Marginal Synopsys',
                                       k_marginal_score,
                                       [ssf_a, sed_a, ws_a])

    gp_a = grid_plot_attachment(group_features,
                                group_scores,
                                feature_values,
                                report_data.output_directory)

    metric_attachments = [ws_a, bs_a]
    if gp_a:
        metric_attachments.append(gp_a)
    metric_attachments.extend(worst_break_down)

    kmarg_det_pkt = UtilityScorePacket('K-Marginal Score Breakdown',
                                       None,
                                       metric_attachments)

    return kmarg_sum_pkt, kmarg_det_pkt


def grid_plot_attachment(group_features: List[str],
                         scores: pd.Series,
                         feature_values: Dict[str, Dict],
                         output_directory) -> Optional[Attachment]:
    if len(group_features) <= 1:
        return None

    scores_df = pd.DataFrame(scores, columns=['score']).reset_index()

    scores_df = scores_df.replace(feature_values)
    # fixed values for features except first in group features
    fixed_val = {f: scores_df[f].unique()[0] for f in group_features[1:]}
    gp = GridPlot(scores_df, group_features[0], fixed_val, output_directory)
    gp_paths = gp.save()
    rel_gp_path = ["/".join(list(p.parts)[-2:])
                   for p in gp_paths]
    gp_a = Attachment(name=f'{group_features[0]} '
                           f'wise k-marginal score in '
                           f'{", ".join([f"{k}: {v}" for k, v in fixed_val.items()])}',
                      _data=[{strs.IMAGE_NAME: Path(p).stem, strs.PATH: p}
                             for p in rel_gp_path],
                      _type=AttachmentType.ImageLinks)
    return gp_a


def utility_score(dataset: Dataset, report_data: ReportData) -> ReportData:
    ds = dataset
    rd = report_data

    scorers = []

    features = ds.features
    corr_features = ds.config[strs.CORRELATION_FEATURES]

    # Initiated k-marginal, correlation and propensity scorer
    # selected challenge type: census or taxi
    if ds.challenge == strs.CENSUS:
        up = UnivariatePlots(ds.synthetic_data, ds.target_data,
                             ds.schema, rd.output_directory, ds.challenge)
        up_saved_file_paths = up.save()

        cdp_saved_file_paths = []
        pcp_saved_file_paths = []
        if len(corr_features) > 1:
            cdp = CorrelationDifferencePlot(ds.d_synthetic_data, ds.d_target_data, rd.output_directory,
                                            corr_features)
            cdp_saved_file_paths = cdp.save()

            pcd = PearsonCorrelationDifference(ds.d_target_data, ds.d_synthetic_data,
                                               corr_features)
            pcd.compute()
            pcp = PearsonCorrelationPlot(pcd.pp_corr_diff, rd.output_directory)
            pcp_saved_file_paths = pcp.save()

        scorers = [CensusKMarginalScore(ds.target_data,
                                        ds.synthetic_data,
                                        ds.schema, **ds.config[strs.K_MARGINAL]),
                   PropensityMSE(ds.d_target_data,
                                 ds.d_synthetic_data,
                                 features)]
    elif ds.challenge == strs.TAXI:
        up = UnivariatePlots(ds.synthetic_data, ds.target_data,
                             ds.schema, rd.output_directory, ds.challenge)
        up_saved_file_paths = up.save()

        cdp_saved_file_paths = []
        pcp_saved_file_paths = []
        if len(corr_features) > 1:
            cdp = CorrelationDifferencePlot(ds.d_synthetic_data, ds.d_target_data, rd.output_directory,
                                            corr_features)
            cdp_saved_file_paths = cdp.save()

            pcd = PearsonCorrelationDifference(ds.d_target_data, ds.d_synthetic_data,
                                               corr_features)
            pcd.compute()
            pcp = PearsonCorrelationPlot(pcd.pp_corr_diff, rd.output_directory)
            pcp_saved_file_paths = pcp.save()

        scorers = [TaxiKMarginalScore(ds.target_data, ds.synthetic_data,
                                      ds.schema, **ds.config[strs.K_MARGINAL]),
                   TaxiHigherOrderConjunction(ds.target_data, ds.synthetic_data,
                                              ds.config[strs.K_MARGINAL][strs.BINS]),
                   TaxiGraphEdgeMapScore(ds.target_data, ds.synthetic_data, ds.schema),
                   PropensityMSE(ds.d_target_data,
                                 ds.d_synthetic_data,
                                 features=features)
                   ]
    else:
        raise Exception(f'Unknown challenge type: {ds.challenge}')

    group_features = ds.config[strs.K_MARGINAL][strs.GROUP_FEATURES]
    f_val_dict = {
        f: {i: v for i, v in enumerate(ds.schema[f]['values'])}
        for f in group_features
    }
    kmarg_sum_pkt = None   # K-marginal score summary utility score packet
    kmarg_det_pkt = None   # K-marginal score detail utility score packet
    prop_pkt = None  # propensity score packet

    # compute scores and plots
    for s in scorers:
        s.compute_score()
        metric_name = s.NAME

        metric_score = int(s.score) if s.score > 100 else round(s.score, 5)
        metric_attachments = []

        if s.NAME == CensusKMarginalScore.NAME \
                and ds.challenge == strs.CENSUS:

            subsample_scores = kmarginal_subsamples(ds, CensusKMarginalScore)
            kmarg_sum_pkt, kmarg_det_pkt = kmarginal_score_packet(metric_score,
                                                                  group_features,
                                                                  s.scores,
                                                                  f_val_dict,
                                                                  ds,
                                                                  rd,
                                                                  subsample_scores,
                                                                  'PUMA')

        elif s.NAME == TaxiKMarginalScore.NAME \
                and ds.challenge == strs.TAXI:
            subsample_scores = kmarginal_subsamples(ds, TaxiKMarginalScore)
            kmarg_sum_pkt, kmarg_det_pkt = kmarginal_score_packet(metric_score,
                                                                  group_features,
                                                                  s.scores,
                                                                  f_val_dict,
                                                                  ds,
                                                                  rd,
                                                                  subsample_scores,
                                                                  'pickup_community_area')

        elif s.NAME == PropensityMSE.NAME:
            p_dist_plot = PropensityDistribution(s.prob_dist, rd.output_directory)
            # pps = PropensityPairPlot(s.std_two_way_scores, rd.output_directory)
            #
            p_dist_paths = p_dist_plot.save()
            # pps_paths = pps.save('spmse',
            #                      'Two-Way Standardized Propensity Mean Square Error')
            rel_pd_path = ["/".join(list(p.parts)[-2:])
                            for p in p_dist_paths]
            # rel_pps_path = ["/".join(list(p.parts)[-2:])
            #                 for p in pps_paths]

            # probability distribution attachment
            pd_a = Attachment(name=f'Propensities Distribution',
                              _data=[{strs.IMAGE_NAME: Path(p).stem, strs.PATH: p}
                                     for p in rel_pd_path],
                              _type=AttachmentType.ImageLinks)

            prop_pkt = UtilityScorePacket(metric_name,
                                          metric_score,
                                          [pd_a])

    if kmarg_sum_pkt:
        rd.add(kmarg_sum_pkt)

    rel_up_saved_file_paths = ["/".join(list(p.parts)[-2:])
                               for p in up_saved_file_paths]
    rd.add(UtilityScorePacket("Univariate Distributions",
                              None,
                              [Attachment(name="Three Worst Performing Features",
                                          _data=[{strs.IMAGE_NAME: Path(p).stem, strs.PATH: p}
                                                  for p in rel_up_saved_file_paths],
                                          _type=AttachmentType.ImageLinks)]))

    corr_metric_a = []
    if len(cdp_saved_file_paths):
        rel_cdp_saved_file_paths = ["/".join(list(p.parts)[-2:])
                                    for p in cdp_saved_file_paths]
        ktc_a = Attachment(name="Kendall Tau Correlation Coefficient Difference",
                           _data=[{strs.IMAGE_NAME: Path(p).stem, strs.PATH: p}
                                  for p in rel_cdp_saved_file_paths],
                           _type=AttachmentType.ImageLinks)
        corr_metric_a.append(ktc_a)

    if len(pcp_saved_file_paths):
        rel_pcp_saved_file_paths = ["/".join(list(p.parts)[-2:])
                                    for p in pcp_saved_file_paths]
        pc_a = Attachment(name="Pearson Correlation Coefficient Difference",
                          _data=[{strs.IMAGE_NAME: Path(p).stem, strs.PATH: p}
                                 for p in rel_pcp_saved_file_paths],
                          _type=AttachmentType.ImageLinks)
        corr_metric_a.append(pc_a)

    rd.add(UtilityScorePacket("Correlations",
                              None,
                              corr_metric_a))

    if prop_pkt:
        rd.add(prop_pkt)

    if kmarg_det_pkt:
        rd.add(kmarg_det_pkt)

    return rd
