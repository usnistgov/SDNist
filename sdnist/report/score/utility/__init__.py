import os
from typing import List, Dict, Tuple, Optional
from pathlib import Path

import pandas as pd
from sdnist.metrics.kmarginal import KMarginal
# from sdnist.metrics.kmarg_old import \
#     CensusKMarginalScore, TaxiKMarginalScore, KMarginalScore
from sdnist.metrics.hoc import \
    TaxiHigherOrderConjunction
from sdnist.metrics.graph_edge_map import \
    TaxiGraphEdgeMapScore
from sdnist.metrics.propensity import \
    PropensityMSE
from sdnist.metrics.pearson_correlation import \
    PearsonCorrelationDifference

from sdnist.report.score.paragraphs import *
from sdnist.report.score.utility.linear_regression import \
    LinearRegressionReport
from sdnist.report.score.utility.inconsistency import \
    InconsistenciesReport
from sdnist.report.score.utility.pca import PCAReport
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
                          subsample_group_scores: pd.DataFrame,
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

    ss = pd.concat([scores, subsample_group_scores], axis=1)
    ss = ss.sort_values(by=[0])
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
            "40% Target Subsample Baseline": int(ss.loc[wf, 1]),
            'Deidentified Data ' + strs.SCORE.capitalize(): int(ss.loc[wf, 0])
        })

    ss = ss.sort_values(by=[0], ascending=False)

    for bf in ss.index:
        f_values = {f: (feature_values[f][bf[i]]
                        if type(bf) == tuple else
                        feature_values[f][bf])
                    for i, f in enumerate(group_features)}
        f_values = {f: [f_val] + feat_name_value(f, f_val)
                    for f, f_val in f_values.items()}
        best_scores.append({
            **f_values,
            "40% Target Subsample Baseline": int(ss.loc[bf, 1]),
            strs.SCORE.capitalize(): int(ss.loc[bf, 0])
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
                         ds, out_dir, ds.challenge, worst_univariates_to_display=3)
    u_feature_data = up.save(level=3)
    k_marg_break_rd[f'worst_{len(wpf)}_puma_univariate'] = up.report_data(level=3)
    k_marg_break_rd[f'worst_{len(wpf)}_puma_k_marginal_scores'] = \
        relative_path(save_data_frame(wsh,
                                      out_dir,
                                      f'worst_{len(wpf)}_puma_k_marginal_scores'),
                      level=2)
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
        if len(str(u_path)) == 0:
            continue
        u_rel_path = relative_path(u_path, level=3)
        name = k
        a = Attachment(name=None,
                       _data=f'h4{name}',
                       _type=AttachmentType.String)
        u_as.append(a)
        if "excluded" in v:
            fv = v['excluded']['feature_value']
            tc = v['excluded']['target_counts']
            sc = v['excluded']['deidentified_counts']
            f_name = name.split(':')[0]
            if k.startswith('POVPIP'):
                fv = '501 [Not in poverty: income above 5 x poverty line]'
            elif fv == -1:
                f_detail = '[N/A]'
                if 'values' in ds.data_dict[f_name]:
                    f_detail = ds.data_dict[f_name]['values']['N']
                fv = f'N [{f_detail}]'
            else:
                f_detail = ''
                if 'values' in ds.data_dict[f_name]:
                    v_data = ds.data_dict[f_name]['values']
                    if str(fv) in v_data:
                        f_detail = ds.data_dict[f_name]['values'][str(fv)]
                fv = f'{fv} [{f_detail}]'
            a = Attachment(name=None,
                           _data=f"Feature Values not shown in the chart:"
                                 f"<br>Value: {fv}"
                                 f"<br>Target Data Counts: {tc}"
                                 f"<br>Deidentified Data Counts: {sc}",
                           _type=AttachmentType.String)
            u_as.append(a)

        a = Attachment(name=None,
                       _data=[{strs.IMAGE_NAME: Path(u_rel_path).stem,
                               strs.PATH: u_rel_path}],
                       _type=AttachmentType.ImageLinks)
        u_as.append(a)
    corr_features = ds.config[strs.CORRELATION_FEATURES]
    corr_features = [f for f in ds.data_dict.keys() if f in corr_features]
    pcd = PearsonCorrelationDifference(t, s,
                                       corr_features)
    pcd.compute()
    pcp = PearsonCorrelationPlot(pcd.pp_corr_diff, out_dir)
    pcp_saved_file_paths = pcp.save(path_level=3)
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
                             {"Dataset": "Deidentified", "Record Counts": s.shape[0]}],
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
                         k_marginal_cls,
                         group_features) \
        -> Tuple[Dict[float, int], Optional[pd.DataFrame]]:
    def create_subsample(frac: float):
        s = dataset.d_target_data.sample(frac=frac)  # subsample as synthetic data
        # rows = dataset.d_target_data.shape[0]
        # remain_rows = rows - s.shape[0]
        # if remain_rows:
        #     rr_s = s.sample(n=remain_rows, replace=True)
        #     s = pd.concat([s, rr_s])
        return s

    # mapping of sub sample frac to k-marginal score of fraction
    ssample_score = dict()  # subsample scores dictionary
    # find k-marginal of 1%, 5%, 10%, 20% ... 90% of sub-sample of target data
    sample_sizes = [1, 5] + [i*10 for i in range(1, 10)]
    for i in sample_sizes:
        # using subsample of target data as synthetic data
        s_sd = create_subsample(frac=i * 0.01)
        s_kmarg = k_marginal_cls(dataset.d_target_data,
                                 s_sd,
                                 group_features)
        s_kmarg.compute_score()
        s_score = int(s_kmarg.score)
        ssample_score[i * 0.01] = s_score

    puma_scores = None
    if len(group_features):
        # subsample scores for each PUMA
        for i in range(5):
            s_sd = create_subsample(frac=4 * 0.1)
            s_kmarg = k_marginal_cls(dataset.d_target_data,
                                     s_sd,
                                     group_features)
            s_kmarg.compute_score()
            scores = s_kmarg.scores
            if i == 0:
                puma_scores = scores
            else:
                puma_scores += scores
        puma_scores /= 5

    return ssample_score, puma_scores


def kmarginal_score_packet(k_marginal_score: int,
                           feature_values: Dict[str, Dict],
                           dataset: Dataset,
                           ui_data: ReportUIData,
                           report_data: ReportData,
                           subsample_scores: Dict[float, int],
                           subsample_group_scores: Optional[pd.DataFrame],
                           worst_breakdown_feature: str,
                           group_features: List[str],
                           group_scores: Optional[pd.DataFrame] = None) \
        -> Tuple[UtilityScorePacket, UtilityScorePacket]:

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
                       _data=f"K-Marginal score of the deidentified data closely resembles "
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
             "Deidentified Data K-marginal score": k_marginal_score,
             "Absolute Diff. From Deidentified Data K-marginal Score":
                 f"{round(abs(subsample_scores[frac] - k_marginal_score), 2)}"
             }
            for frac in sorted_frac]

    sedf_df = pd.DataFrame(sedf)
    k_marg_synopsys_path = Path(ui_data.output_directory, 'k_marginal_synopsys')

    if not k_marg_synopsys_path.exists():
        os.mkdir(k_marg_synopsys_path)

    sedf[min_idx]["min_idx"] = True

    sed_a = Attachment(name=None,
                       _data=sedf)

    # add k-marginal subsample and deidentified data scores to json report
    k_marg_synop_rd['subsample_error_comparison'] = \
        relative_path(save_data_frame(sedf_df, k_marg_synopsys_path, 'subsample_error_comparison'))
    k_marg_synop_rd['sub_sampling_equivalent'] = int(min_frac * 100)
    k_marg_synop_rd['k_marginal_score'] = k_marginal_score

    report_data.add('k_marginal', {
        "k_marginal_synopsys": k_marg_synop_rd
    })

    # Create attachments for UI report
    # k marg para attachment
    kmp_a = Attachment(name=None,
                       _data=k_marg_synopsys_para,
                       _type=AttachmentType.String)
    # k marg score attachment
    kms_a = Attachment(name=None,
                       _data=f"Highlight-K-Marginal Score: {k_marginal_score}",
                       _type=AttachmentType.String)
    attachments = [kmp_a, kms_a, ss_para_a, ssf_a, sed_a]

    kmarg_sum_pkt = UtilityScorePacket('K-Marginal Synopsys',
                                       None,
                                       attachments)

    kmarg_det_pkt = None  # k-marginal details breakdown packet
    if group_scores is not None:
        worst_scores, best_scores = best_worst_performing(group_scores,
                                                          subsample_group_scores,
                                                          dataset,
                                                          group_features,
                                                          feature_values)
        all_scores = worst_scores
        # target pumas
        t_pumas = dataset.target_data['PUMA'].unique()
        # synthetic pumas
        s_pumas = dataset.synthetic_data['PUMA'].unique()
        # usable pumas
        usable_pumas = set(t_pumas).intersection(s_pumas)
        default_w_b_n = 2 if len(usable_pumas) <= 6 else 5

        k_marg_synop_rd['score_in_each_puma'] = \
            relative_path(save_data_frame(pd.DataFrame(all_scores),
                                          k_marg_synopsys_path,
                                          'score_in_each_puma'))

        # count of worst or best k-marginal pumas to select
        worst_scores = [ws for ws in worst_scores if ws['PUMA'][0] in usable_pumas]
        best_scores = [bs for bs in best_scores if bs['PUMA'][0] in usable_pumas]
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

        report_data.add('worst_PUMA_breakdown', k_marg_break_rd)
        attachments.extend([as_para_a, as_a])

        metric_attachments = [k_marg_break_para_a, ws_para_a, ws_a]

        gp_a = grid_plot_attachment(group_features,
                                    group_scores,
                                    feature_values,
                                    ui_data.output_directory)
        if gp_a:
            metric_attachments.append(gp_a)
        metric_attachments.extend(worst_break_down)

        kmarg_det_pkt = UtilityScorePacket('Worst Performing PUMAs Breakdown',
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


def utility_score(dataset: Dataset, ui_data: ReportUIData, report_data: ReportData,
                  log: SimpleLogger) \
        -> Tuple[ReportUIData, ReportData]:
    ds = dataset
    r_ui_d = ui_data  # report ui data
    rd = report_data

    features = ds.features
    corr_features = ds.config[strs.CORRELATION_FEATURES]
    corr_features = [f for f in ds.data_dict.keys() if f in corr_features]
    # Initiated k-marginal, correlation and propensity scorer
    # selected challenge type: census or taxi
    if ds.challenge == strs.CENSUS:
        log.msg('Univariates', level=3)
        up = UnivariatePlots(ds.d_synthetic_data, ds.d_target_data,
                             ds, r_ui_d.output_directory, ds.challenge)
        u_feature_data = up.save()  # univariate features data
        rd.add('Univariate', up.report_data())

        u_as = []  # univariate attachments

        for k, v in u_feature_data.items():
            u_path = v['path']
            if len(str(u_path)) == 0:
                continue
            u_rel_path = "/".join(list(u_path.parts)[-2:])
            name = k
            a = Attachment(name=None,
                           _data=f'h4{name}',
                           _type=AttachmentType.String)
            u_as.append(a)

            if "excluded" in v:
                fv = v['excluded']['feature_value']
                tc = v['excluded']['target_counts']
                sc = v['excluded']['deidentified_counts']
                f_name = name.split(':')[0]
                if k.startswith('POVPIP'):
                    fv = '501 [Not in poverty: income above 5 x poverty line]'
                elif fv == -1:
                    f_detail = '[N/A]'
                    if 'values' in ds.data_dict[f_name]:
                        f_detail = ds.data_dict[f_name]['values']['N']
                    fv = f'N [{f_detail}]'
                else:
                    f_detail = ''
                    if 'values' in ds.data_dict[f_name]:
                        v_data = ds.data_dict[f_name]['values']
                        if str(fv) in v_data:
                            f_detail = ds.data_dict[f_name]['values'][str(fv)]
                    fv = f'{fv} [{f_detail}]'

                a = Attachment(name=None,
                               _data=f"Feature Values not shown in the chart:"
                                     f"<br>Value: {fv}"
                                     f"<br>Target Data Counts: {tc}"
                                     f"<br>Deidentified Data Counts: {sc}",
                               _type=AttachmentType.String)
                u_as.append(a)

            a = Attachment(name=None,
                           _data=[{strs.IMAGE_NAME: Path(u_rel_path).stem,
                                  strs.PATH: u_rel_path}],
                           _type=AttachmentType.ImageLinks)
            u_as.append(a)


        log.end_msg()

        log.msg('Correlations', level=3)
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
        log.end_msg()

    else:
        raise Exception(f'Unknown challenge type: {ds.challenge}')

    log.msg('K-Marginal', level=3)
    group_features = ds.config[strs.K_MARGINAL][strs.GROUP_FEATURES]
    f_val_dict = {
        f: {i: v for i, v in enumerate(ds.schema[f]['values'])}
        for f in group_features
    }
    kmarg_sum_pkt = None   # K-marginal score summary utility score packet
    kmarg_det_pkt = None   # K-marginal score detail utility score packet
    prop_pkt = None  # propensity score packet

    # compute scores and plots
    s = KMarginal(ds.d_target_data,
                  ds.d_synthetic_data,
                  group_features)

    s.compute_score()
    metric_name = s.NAME

    metric_score = int(s.score)
    metric_attachments = []

    if s.NAME == KMarginal.NAME \
            and ds.challenge == strs.CENSUS:
        group_scores = s.scores if hasattr(s, 'scores') and len(s.scores) else None
        # s_puma_score: subsample puma scores
        subsample_scores, s_puma_scores = kmarginal_subsamples(ds, KMarginal, group_features)
        kmarg_sum_pkt, kmarg_det_pkt = kmarginal_score_packet(metric_score,
                                                              f_val_dict,
                                                              ds,
                                                              r_ui_d,
                                                              rd,
                                                              subsample_scores,
                                                              s_puma_scores,
                                                              'PUMA',
                                                              group_features,
                                                              group_scores)
    log.end_msg()

    log.msg('PropensityMSE', level=3)
    s = PropensityMSE(ds.t_target_data,
                      ds.t_synthetic_data,
                      r_ui_d.output_directory,
                      features)
    s.compute_score()
    metric_name = s.NAME

    metric_score = int(s.score) if s.score > 100 else round(s.score, 3)

    p_dist_plot = PropensityDistribution(s.prob_dist, r_ui_d.output_directory)
    # pps = PropensityPairPlot(s.std_two_way_scores, rd.output_directory)
    #

    p_dist_paths = p_dist_plot.save()
    prop_rep_data = {**s.report_data, **p_dist_plot.report_data}
    rd.add('propensity mean square error', prop_rep_data)
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

    log.end_msg()

    # rel_up_saved_file_paths = ["/".join(list(p.parts)[-2:])
    #                            for p in up_saved_file_paths]


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


    # Add metrics reports to UI
    if kmarg_sum_pkt:
        r_ui_d.add(kmarg_sum_pkt)

    r_ui_d.add(UtilityScorePacket("Univariate Distributions",
                                  None,
                                  [Attachment(name=None,
                                              _data=univ_dist_para,
                                              _type=AttachmentType.String)] + u_as))

    r_ui_d.add(UtilityScorePacket("Correlations",
                                  None,
                                  corr_metric_a))
    log.msg('Linear Regression', level=3)
    lgr = LinearRegressionReport(ds, r_ui_d, rd)
    lgr.add_to_ui()
    log.end_msg()

    if prop_pkt:
        r_ui_d.add(prop_pkt)

    log.msg('PCA', level=3)
    pca_r = PCAReport(ds, r_ui_d, rd)
    pca_r.add_to_ui()
    log.end_msg()

    log.msg('Inconsistencies', level=3)
    icr = InconsistenciesReport(ds, r_ui_d, rd)
    icr.add_to_ui()
    log.end_msg()

    if kmarg_det_pkt:
        r_ui_d.add(kmarg_det_pkt)

    return r_ui_d, rd

