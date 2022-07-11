from typing import List, Dict, Tuple
from pathlib import Path

import pandas as pd

from sdnist.metrics.kmarginal import \
    CensusKMarginalScore, TaxiKMarginalScore
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
                          group_features: List[str],
                          feature_values: Dict[str, Dict]) -> Tuple[List, List]:
    ss = scores.sort_values()
    total_ss = len(ss)
    total_scores = 10 if total_ss > 10 else total_ss

    worst_scores = []
    best_scores = []

    for wf in ss[0: 10].index:  # worst score features
        f_values = {f: (feature_values[f][wf[i]]
                        if type(wf) == tuple else feature_values[f][wf])
                    for i, f in enumerate(group_features)}
        worst_scores.append({
            **f_values,
            "SCORE": int(ss[wf])
        })

    for bf in ss[total_ss - total_scores: total_ss].index:
        f_values = {f: (feature_values[f][bf[i]]
                        if type(bf) == tuple else feature_values[f][bf])
                    for i, f in enumerate(group_features)}
        best_scores.append({
            **f_values,
            "SCORE": int(ss[bf])
        })

    return worst_scores, best_scores


def utility_score(dataset: Dataset, report_data: ReportData) -> ReportData:
    ds = dataset
    rd = report_data

    scorers = []
    features = ds.config[strs.CORRELATION_FEATURES]
    if ds.challenge == strs.CENSUS:
        up = UnivariatePlots(ds.synthetic_data, ds.target_data,
                             ds.schema, rd.output_directory, ds.challenge)
        up_saved_file_paths = up.save()

        cdp = CorrelationDifferencePlot(ds.synthetic_data, ds.target_data, rd.output_directory,
                                        features)
        cdp_saved_file_paths = cdp.save()

        pcd = PearsonCorrelationDifference(ds.target_data, ds.synthetic_data,
                                           features)
        pcd.compute()
        pcp = PearsonCorrelationPlot(pcd.pp_corr_diff, rd.output_directory)
        pcp_saved_file_paths = pcp.save()

        scorers = [CensusKMarginalScore(ds.target_data,
                                        ds.synthetic_data,
                                        ds.schema, **ds.config[strs.K_MARGINAL]),
                   PropensityMSE(ds.target_data,
                                 ds.synthetic_data,
                                 features)]
    elif ds.challenge == strs.TAXI:
        up = UnivariatePlots(ds.synthetic_data, ds.target_data,
                             ds.schema, rd.output_directory, ds.challenge)
        up_saved_file_paths = up.save()

        cdp = CorrelationDifferencePlot(ds.synthetic_data, ds.target_data, rd.output_directory,
                                        features)
        cdp_saved_file_paths = cdp.save()

        pcd = PearsonCorrelationDifference(ds.target_data, ds.synthetic_data,
                                           features)
        pcd.compute()
        pcp = PearsonCorrelationPlot(pcd.pp_corr_diff, rd.output_directory)
        pcp_saved_file_paths = pcp.save()

        scorers = [TaxiKMarginalScore(ds.target_data, ds.synthetic_data,
                                      ds.schema, **ds.config[strs.K_MARGINAL]),
                   TaxiHigherOrderConjunction(ds.target_data, ds.synthetic_data,
                                              ds.config[strs.K_MARGINAL][strs.BINS]),
                   TaxiGraphEdgeMapScore(ds.target_data, ds.synthetic_data, ds.schema),
                   PropensityMSE(ds.target_data,
                                 ds.synthetic_data,
                                 features=features)
                   ]
    else:
        raise Exception(f'Unknown challenge type: {ds.challenge}')

    group_features = ds.config[strs.K_MARGINAL][strs.GROUP_FEATURES]
    f_val_dict = {
        f: {i: v for i, v in enumerate(ds.schema[f]['values'])}
        for f in group_features
    }

    for s in scorers:
        s.compute_score()
        metric_name = s.NAME

        metric_score = int(s.score) if s.score > 100 else round(s.score, 5)
        metric_attachments = []

        if s.NAME == CensusKMarginalScore.NAME \
                and ds.challenge == strs.CENSUS:
            # N worst and best performing puma-years

            worst_scores, best_scores = best_worst_performing(s.scores,
                                                              group_features,
                                                              f_val_dict)
            metric_attachments.append(
                Attachment(name=f"{len(worst_scores)} Worst Performing " + '-'.join(group_features),
                           _data=worst_scores)
            )
            metric_attachments.append(
                Attachment(name=f"{len(best_scores)} Best Performing " + '-'.join(group_features),
                           _data=best_scores)
            )

            if len(group_features) > 1:
                scores_df = pd.DataFrame(s.scores, columns=['score']).reset_index()

                scores_df = scores_df.replace(f_val_dict)
                # fixed values for features except first in group features
                fixed_val = {f: scores_df[f].unique()[0] for f in group_features[1:]}
                gp = GridPlot(scores_df, group_features[0], fixed_val, rd.output_directory)
                gp_paths = gp.save()
                rel_gp_path = ["/".join(list(p.parts)[-2:])
                               for p in gp_paths]
                metric_attachments.append(
                    Attachment(name=f'{group_features[0]} '
                                    f'wise k-marginal score in '
                                    f'{", ".join([f"{k}: {v}" for k, v in fixed_val.items()])}',
                               _data=[{strs.IMAGE_NAME: Path(p).stem, strs.PATH: p}
                                      for p in rel_gp_path],
                               _type=AttachmentType.ImageLinks)
                )
            rd.add(UtilityScorePacket(metric_name,
                                      metric_score,
                                      metric_attachments))
        elif s.NAME == TaxiKMarginalScore.NAME \
                and ds.challenge == strs.TAXI:
            # N worst and best performing pickup_community_area and shift
            worst_scores, best_scores = best_worst_performing(s.scores,
                                                              group_features,
                                                              f_val_dict)
            metric_attachments.append(
                Attachment(name=f"{len(worst_scores)} Worst Performing " + '-'.join(group_features),
                           _data=worst_scores)
            )
            metric_attachments.append(
                Attachment(name=f"{len(best_scores)} Best Performing " + '-'.join(group_features),
                           _data=best_scores)
            )
            rd.add(UtilityScorePacket(metric_name,
                                      metric_score,
                                      metric_attachments))
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
            metric_attachments.append(
                Attachment(name=f'Propensities Distribution',
                           _data=[{strs.IMAGE_NAME: Path(p).stem, strs.PATH: p}
                                  for p in rel_pd_path],
                           _type=AttachmentType.ImageLinks)
            )
            # metric_attachments.append(
            #     Attachment(name=f'Two way standardized propensity mean square error',
            #                _data=[{IMAGE_NAME: Path(p).stem, PATH: p}
            #                       for p in rel_pps_path],
            #                _type=AttachmentType.ImageLinks)
            # )
            rd.add(UtilityScorePacket(metric_name,
                                      metric_score,
                                      metric_attachments))

    rel_up_saved_file_paths = ["/".join(list(p.parts)[-2:])
                               for p in up_saved_file_paths]
    rel_cdp_saved_file_paths = ["/".join(list(p.parts)[-2:])
                                for p in cdp_saved_file_paths]
    rel_pcp_saved_file_paths = ["/".join(list(p.parts)[-2:])
                                for p in pcp_saved_file_paths]

    rd.add(UtilityScorePacket("Univariate Distributions",
                              None,
                              [Attachment(name="Three Worst Performing Features",
                                          _data=[{strs.IMAGE_NAME: Path(p).stem, strs.PATH: p}
                                                  for p in rel_up_saved_file_paths],
                                          _type=AttachmentType.ImageLinks)]))

    rd.add(UtilityScorePacket("Kendall Tau Correlation Coefficient Difference",
                              None,
                              [Attachment(name=None,
                                          _data=[{strs.IMAGE_NAME: Path(p).stem, strs.PATH: p}
                                                 for p in rel_cdp_saved_file_paths],
                                          _type=AttachmentType.ImageLinks)]))
    rd.add(UtilityScorePacket("Pearson Correlation Coefficient Difference",
                              None,
                              [Attachment(name=None,
                                          _data=[{strs.IMAGE_NAME: Path(p).stem, strs.PATH: p}
                                                 for p in rel_pcp_saved_file_paths],
                                          _type=AttachmentType.ImageLinks)]))

    return rd
