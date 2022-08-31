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
from sdnist.metrics.pca import PCAMetric, plot_pca

from sdnist.report.score.paragraphs import *
from sdnist.report import Dataset
from sdnist.report.report_data import \
    ReportData, ReportUIData, UtilityScorePacket, Attachment, AttachmentType, \
    DatasetType, DataDescriptionPacket
from sdnist.report.plots import \
    UnivariatePlots, CorrelationDifferencePlot, \
    GridPlot, PropensityDistribution, PearsonCorrelationPlot

import sdnist.strs as strs
from sdnist.utils import *


def best_worst_performing(scores: pd.Series,
                          dataset: Dataset,
                          group_features: List[str],
                          feature_values: Dict[str, Dict]) -> Tuple[List, List]:

    def feat_name_value(feature, feature_val):
        feature_val = str(feature_val)
        default_res = [None, None]

        fv = dataset.mappings
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
            strs.SCORE.capitalize(): int(ss[wf])
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
            strs.SCORE.capitalize(): int(ss[bf])
        })

    return worst_scores, best_scores


def worst_score_breakdown(worst_scores: List,
                          dataset: Dataset,
                          ui_data: ReportUIData,
                          report_data: ReportData,
                          feature: str) -> Tuple[List[Attachment], Dict[str, any]]:
    ds = dataset
    r_ui_d = ui_data
    rd = report_data
    k_marg_break_rd = dict()   # k marginal breakdnow worst performing puma report

    wsh = pd.DataFrame(worst_scores)
    if str(wsh.loc[0, feature]).startswith('['):
        wsh[feature] = wsh[feature].apply(lambda x: list(x)[0])
    wpf = wsh[feature].unique().tolist()[:5]  # worst performing feature values
    t = dataset.d_target_data.copy()
    s = dataset.d_synthetic_data.copy()

    t = t[dataset.target_data[feature].isin(wpf)]
    s = s[dataset.synthetic_data[feature].isin(wpf)]

    out_dir = Path(r_ui_d.output_directory, 'k_marginal_breakdown')
    if not out_dir.exists():
        os.mkdir(out_dir)

    up = UnivariatePlots(s, t,
                         ds, out_dir, ds.challenge)
    u_feature_data = up.save()
    k_marg_break_rd[f'worst_{len(wpf)}_puma_univariate'] = up.report_data()
    k_marg_break_rd[f'worst_{len(wpf)}_puma_k_marginal_scores'] = \
        relative_path(save_data_frame(wsh,
                                      out_dir,
                                      f'worst_{len(wpf)}_puma_k_marginal_scores'))
    u_as = []
    u_as.append(Attachment(name=None,
                           _data=f"h3Univariate Distribution of Worst "
                                 f"Performing Features in {len(wpf)} Worst Performing "
                                  + feature,
                           _type=AttachmentType.String))
    u_as.append(Attachment(name=None,
                           _data=univ_dist_worst_para,
                           _type=AttachmentType.String))

    for k, v in u_feature_data.items():
        u_path = v['path']
        u_rel_path = "/".join(list(u_path.parts)[-2:])
        name = k
        a = Attachment(name=None,
                       _data=f'h4{name}',
                       _type=AttachmentType.String)
        u_as.append(a)
        if "excluded" in v:
            fv = v['excluded']['feature_value']
            tc = v['excluded']['target_counts']
            sc = v['excluded']['synthetic_counts']
            if k.startswith('POVPIP'):
                fv = '501 (Not in poverty: income above 5 x poverty line)'
            elif fv == -1:
                fv = 'N (N/A)'
            a = Attachment(name=None,
                           _data=f"Feature Value: {fv}"
                                 f"<br>Target Data Counts: {tc}"
                                 f"<br>Synthetic Data Counts: {sc}",
                           _type=AttachmentType.String)
            u_as.append(a)

        a = Attachment(name=None,
                       _data=[{strs.IMAGE_NAME: Path(u_rel_path).stem,
                               strs.PATH: u_rel_path}],
                       _type=AttachmentType.ImageLinks)
        u_as.append(a)

    pcd = PearsonCorrelationDifference(t, s,
                                       ds.config[strs.CORRELATION_FEATURES])
    pcd.compute()
    pcp = PearsonCorrelationPlot(pcd.pp_corr_diff, out_dir)
    pcp_saved_file_paths = pcp.save()
    k_marg_break_rd['correlation_difference'] = {
        "pearson_correlation_difference": pcp.report_data
    }

    # rel_up_saved_file_paths = ["/".join(list(p.parts)[-3:])
    #                            for p in up_saved_file_paths]
    rel_pcp_saved_file_paths = ["/".join(list(p.parts)[-3:])
                                for p in pcp_saved_file_paths]
    # attachment for worst feature names
    # a_wf = Attachment(name=f'{len(wpf)} Worst Performing ' + feature,
    #                   _data=", ".join(wpf),
    #                   _type=AttachmentType.String)

    # attachment for records in each data for worst performing feature
    a_para_rt = Attachment(name=f'Record Counts in {len(wpf)} Worst Performing ' + feature,
                           _data=rec_count_worst_para,
                           _type=AttachmentType.String)
    a_rt = Attachment(name=None,
                      _data=[{"Dataset": "Target", "Record Counts": t.shape[0]},
                             {"Dataset": "Synthetic", "Record Counts": s.shape[0]}],
                      _type=AttachmentType.Table)
    # a_up = Attachment(name=f"Univariate Distribution of Worst "
    #                        f"Performing Features in {len(wpf)} Worst Performing "
    #                        + feature,
    #                   _data=[{strs.IMAGE_NAME: Path(p).stem, strs.PATH: p}
    #                          for p in rel_up_saved_file_paths],
    #                   _type=AttachmentType.ImageLinks)

    a_para_pc = Attachment(name=f"Pearson Correlation Coefficient Difference in "
                           f"{len(wpf)} Worst Performing "
                           + feature,
                           _data=pear_corr_worst_para,
                           _type=AttachmentType.String)
    a_pc = Attachment(name=None,
                      _data=[{strs.IMAGE_NAME: Path(p).stem, strs.PATH: p}
                             for p in rel_pcp_saved_file_paths],
                      _type=AttachmentType.ImageLinks)

    return [a_para_rt, a_rt] + u_as + [a_para_pc, a_pc], k_marg_break_rd


def kmarginal_subsamples(dataset: Dataset,
                         k_marginal_cls) \
        -> Dict[float, int]:
    # mapping of sub sample frac to k-marginal score of fraction
    ssample_score = dict()  # subsample scores dictionary
    # find k-marginal of 10%, 20% ... 90% of sub-sample of target data
    for i in range(1, 11):
        # using subsample of target data as synthetic data
        s_sd = dataset.d_target_data.sample(frac=i * 0.1)  # subsample as synthetic data
        rows = dataset.d_target_data.shape[0]
        remain_rows = rows - s_sd.shape[0]
        if remain_rows:
            rr_sd = s_sd.sample(n=remain_rows, replace=True)
            s_sd = pd.concat([s_sd, rr_sd])
        s_kmarg = k_marginal_cls(dataset.d_target_data,
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
                           ui_data: ReportUIData,
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
    k_marg_rd = dict() # k marginal report data
    k_marg_synop_rd = dict()   # k marginal synopsys report data

    ss_para_a = Attachment(name=f"Sampling Error Comparison",
                           _data=sub_sample_para,
                           _type=AttachmentType.String)

    # subsample fraction score attachment
    ssf_a = Attachment(name=None,
                       _data=f"K-Marginal score of the synthetic data closely resembles "
                             f"K-Marginal score of a {int(min_frac * 100)}% sub-sample of "
                             f"the target data.",
                       _type=AttachmentType.String)
    min_idx = 0
    min_score = 10000
    for i, frac in enumerate(sorted_frac):
        diff = abs(subsample_scores[frac] - k_marginal_score)
        if diff < min_score:
            min_score = diff
            min_idx = i

    # sampling error data attachment
    sedf = [{"Sub-Sample Size": f"{int(frac * 100)}%",
             "Sub-Sample K-Marginal Score": subsample_scores[frac],
             "Synthetic Data K-marginal score": k_marginal_score,
             "Absolute Diff. From Synthetic Data K-marginal Score":
                 f"{abs(subsample_scores[frac] - k_marginal_score)}"
             }
            for frac in sorted_frac]

    sedf_df = pd.DataFrame(sedf)
    k_marg_synopsys_path = Path(ui_data.output_directory, 'k_marginal_synopsys')

    if not k_marg_synopsys_path.exists():
        os.mkdir(k_marg_synopsys_path)

    sedf[min_idx]["min_idx"] = True

    sed_a = Attachment(name=None,
                       _data=sedf)

    worst_scores, best_scores = best_worst_performing(group_scores,
                                                      dataset,
                                                      group_features,
                                                      feature_values)
    all_scores = worst_scores
    total_pumas = len(dataset.target_data['PUMA'].unique())
    default_w_b_n = 2 if total_pumas <= 6 else 5


    k_marg_synop_rd['subsample_error_comparison'] = \
        relative_path(save_data_frame(sedf_df, k_marg_synopsys_path, 'subsample_error_comparison'))
    k_marg_synop_rd['k_marginal_score'] = k_marginal_score
    k_marg_synop_rd['score_in_each_puma'] = \
        relative_path(save_data_frame(pd.DataFrame(all_scores),
                                      k_marg_synopsys_path,
                                      'score_in_each_puma'))

    # count of worst or best k-marginal pumas to select
    w_b_n = default_w_b_n if len(worst_scores) > default_w_b_n else len(worst_scores)
    worst_scores, best_scores = worst_scores[0: w_b_n], best_scores[0: w_b_n]

    worst_break_down, k_marg_break_rd = worst_score_breakdown(worst_scores,
                                                              dataset,
                                                              ui_data,
                                                              report_data,
                                                              worst_breakdown_feature)

    # all score attachment
    as_para_a = Attachment(name=f'K-Marginal Score in Each ' + '-'.join(group_features),
                           _data=k_marg_all_puma_para,
                           _type=AttachmentType.String)

    as_a = Attachment(name=None,
                      _data=all_scores)
    k_marg_break_para_a = Attachment(name=None,
                                     _data=k_marg_break_para,
                                     _type=AttachmentType.String)

    # worst score attachment
    ws_para_a = Attachment(name=f"{len(worst_scores)} Worst Performing " + '-'.join(group_features),
                           _data=worst_k_marg_para,
                           _type=AttachmentType.String)
    ws_a = Attachment(name=None,
                      _data=worst_scores)

    # best score attachment
    bs_a = Attachment(name=f"{len(best_scores)} Best Performing " + '-'.join(group_features),
                      _data=best_scores)

    # k marg para attachment
    kmp_a = Attachment(name=None,
                       _data=k_marg_synopsys_para,
                       _type=AttachmentType.String)
    # k marg score attachment
    kms_a = Attachment(name=None,
                       _data=f"Highlight-K-Marginal Score: {k_marginal_score}",
                       _type=AttachmentType.String)
    kmarg_sum_pkt = UtilityScorePacket('K-Marginal Synopsys',
                                       None,
                                       [kmp_a, kms_a, ss_para_a, ssf_a, sed_a, as_para_a, as_a])

    gp_a = grid_plot_attachment(group_features,
                                group_scores,
                                feature_values,
                                ui_data.output_directory)

    metric_attachments = [k_marg_break_para_a, ws_para_a, ws_a]
    if gp_a:
        metric_attachments.append(gp_a)
    metric_attachments.extend(worst_break_down)

    kmarg_det_pkt = UtilityScorePacket('K-Marginal Score Breakdown',
                                       None,
                                       metric_attachments)
    report_data.add('k_marginal', {
        "k_marginal_synopsys": k_marg_synop_rd,
        "k_marginal_breakdown": k_marg_break_rd
    })
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


def utility_score(dataset: Dataset, ui_data: ReportUIData, report_data: ReportData) \
        -> Tuple[ReportUIData, ReportData]:
    ds = dataset
    r_ui_d = ui_data  # report ui data
    rd = report_data

    scorers = []

    features = ds.features
    corr_features = ds.config[strs.CORRELATION_FEATURES]

    # Initiated k-marginal, correlation and propensity scorer
    # selected challenge type: census or taxi
    if ds.challenge == strs.CENSUS:
        up = UnivariatePlots(ds.d_synthetic_data, ds.d_target_data,
                             ds, r_ui_d.output_directory, ds.challenge)
        u_feature_data = up.save()  # univariate features data
        rd.add('Univariate', up.report_data())
        u_as = []  # univariate attachments

        for k, v in u_feature_data.items():
            u_path = v['path']
            u_rel_path = "/".join(list(u_path.parts)[-2:])
            name = k
            a = Attachment(name=None,
                           _data=f'h4{name}',
                           _type=AttachmentType.String)
            u_as.append(a)
            if "excluded" in v:
                fv = v['excluded']['feature_value']
                tc = v['excluded']['target_counts']
                sc = v['excluded']['synthetic_counts']
                if k.startswith('POVPIP'):
                    fv = '501 (Not in poverty: income above 5 x poverty line)'
                elif fv == -1:
                    fv = 'N (N/A)'
                a = Attachment(name=None,
                               _data=f"Feature Value: {fv}"
                                     f"<br>Target Data Counts: {tc}"
                                     f"<br>Synthetic Data Counts: {sc}",
                               _type=AttachmentType.String)
                u_as.append(a)

            a = Attachment(name=None,
                           _data=[{strs.IMAGE_NAME: Path(u_rel_path).stem,
                                  strs.PATH: u_rel_path}],
                           _type=AttachmentType.ImageLinks)
            u_as.append(a)

        cdp_saved_file_paths = []
        pcp_saved_file_paths = []
        if len(corr_features) > 1:
            cdp = CorrelationDifferencePlot(ds.t_synthetic_data, ds.t_target_data, r_ui_d.output_directory,
                                            corr_features)
            cdp_saved_file_paths = cdp.save()

            pcd = PearsonCorrelationDifference(ds.t_target_data, ds.t_synthetic_data,
                                               corr_features)
            pcd.compute()
            pcp = PearsonCorrelationPlot(pcd.pp_corr_diff, r_ui_d.output_directory)
            pcp_saved_file_paths = pcp.save()

            rd.add('Correlations', {"kendall correlation difference": cdp.report_data,
                                    "pearson correlation difference": pcp.report_data})

        scorers = [CensusKMarginalScore(ds.d_target_data,
                                        ds.d_synthetic_data,
                                        ds.schema, **ds.config[strs.K_MARGINAL]),
                   PropensityMSE(ds.t_target_data,
                                 ds.t_synthetic_data,
                                 r_ui_d.output_directory,
                                 features)]
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
                                                                  r_ui_d,
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
                                                                  r_ui_d,
                                                                  subsample_scores,
                                                                  'pickup_community_area')

        elif s.NAME == PropensityMSE.NAME:
            p_dist_plot = PropensityDistribution(s.prob_dist, r_ui_d.output_directory)
            # pps = PropensityPairPlot(s.std_two_way_scores, rd.output_directory)
            #
            prop_rep_data = {**s.report_data, **p_dist_plot.report_data}
            rd.add('propensity mean square error', prop_rep_data)

            p_dist_paths = p_dist_plot.save()
            # pps_paths = pps.save('spmse',
            #                      'Two-Way Standardized Propensity Mean Square Error')
            rel_pd_path = ["/".join(list(p.parts)[-2:])
                            for p in p_dist_paths]
            # rel_pps_path = ["/".join(list(p.parts)[-2:])
            #                 for p in pps_paths]

            # probability distribution attachment
            pd_para_a = Attachment(name=None,
                                   _data=propensity_para,
                                   _type=AttachmentType.String)
            pd_score_a = Attachment(name=None,
                                    _data=f"Highlight-Score: {metric_score}",
                                    _type=AttachmentType.String)
            pd_a = Attachment(name=f'Propensities Distribution',
                              _data=[{strs.IMAGE_NAME: Path(p).stem, strs.PATH: p}
                                     for p in rel_pd_path],
                              _type=AttachmentType.ImageLinks)

            prop_pkt = UtilityScorePacket(metric_name,
                                          None,
                                          [pd_para_a, pd_score_a, pd_a])

    if kmarg_sum_pkt:
        r_ui_d.add(kmarg_sum_pkt)

    # rel_up_saved_file_paths = ["/".join(list(p.parts)[-2:])
    #                            for p in up_saved_file_paths]
    r_ui_d.add(UtilityScorePacket("Univariate Distributions",
                              None,
                              [Attachment(name=None,
                               _data=univ_dist_para,
                               _type=AttachmentType.String),
                               Attachment(name="Three Worst Performing Features",
                                          _data="",
                                          _type=AttachmentType.String)] + u_as))

    corr_metric_a = []
    corr_metric_a.append(Attachment(name=None,
                                    _data=corr_para,
                                    _type=AttachmentType.String))
    if len(cdp_saved_file_paths):
        rel_cdp_saved_file_paths = ["/".join(list(p.parts)[-2:])
                                    for p in cdp_saved_file_paths]
        ktc_p_a = Attachment(name="Kendall Tau Correlation Coefficient Difference",
                               _data=kend_corr_para,
                               _type=AttachmentType.String)
        ktc_a = Attachment(name=None,
                           _data=[{strs.IMAGE_NAME: Path(p).stem, strs.PATH: p}
                                  for p in rel_cdp_saved_file_paths],
                           _type=AttachmentType.ImageLinks)
        corr_metric_a.append(ktc_p_a)
        corr_metric_a.append(ktc_a)

    if len(pcp_saved_file_paths):
        rel_pcp_saved_file_paths = ["/".join(list(p.parts)[-2:])
                                    for p in pcp_saved_file_paths]
        pc_para_a = Attachment(name="Pearson Correlation Coefficient Difference",
                               _data=pear_corr_para,
                               _type=AttachmentType.String)
        pc_a = Attachment(name=None,
                          _data=[{strs.IMAGE_NAME: Path(p).stem, strs.PATH: p}
                                 for p in rel_pcp_saved_file_paths],
                          _type=AttachmentType.ImageLinks)
        corr_metric_a.append(pc_para_a)
        corr_metric_a.append(pc_a)

    r_ui_d.add(UtilityScorePacket("Correlations",
                                  None,
                                  corr_metric_a))

    pca = PCAMetric(dataset.t_target_data, dataset.t_synthetic_data, r_ui_d.output_directory)
    pca.compute_pca()
    pca_saved_file_path = pca.plot()
    rd.add('pca', pca.report_data)
    rel_pca_save_file_path = ["/".join(list(p.parts)[-2:])
                              for p in pca_saved_file_path]
    pca_para_a = Attachment(name=None,
                            _data=pca_para,
                            _type=AttachmentType.String)
    pca_a_tt = Attachment(name="Contribution of Features in Each Principal Component",
                          _data=pca.t_comp_data,
                          _type=AttachmentType.Table)
    # pca_a_st = Attachment(name="Synthetic data: contribution of features in "
    #                            "each principal component")
    pca_a = Attachment(name=None,
                       _data=[{strs.IMAGE_NAME: Path(p).stem, strs.PATH: p}
                              for p in rel_pca_save_file_path],
                       _type=AttachmentType.ImageLinks)

    if prop_pkt:
        r_ui_d.add(prop_pkt)

    r_ui_d.add(UtilityScorePacket("PCA",
                              None,
                              [pca_para_a, pca_a_tt, pca_a]))

    if kmarg_det_pkt:
        r_ui_d.add(kmarg_det_pkt)


    return r_ui_d, rd

