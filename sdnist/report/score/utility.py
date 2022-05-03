from pathlib import Path

import pandas as pd

from sdnist.metrics.kmarginal import \
    CensusKMarginalScore, TaxiKMarginalScore
from sdnist.metrics.hoc import \
    TaxiHigherOrderConjunction
from sdnist.metrics.graph_edge_map import \
    TaxiGraphEdgeMapScore

from sdnist.report import Dataset
from sdnist.report.report_data import \
    ReportData, UtilityScorePacket, Attachment, AttachmentType, \
    DatasetType, DataDescriptionPacket
from sdnist.report.plots import \
    UnivariatePlots, CorrelationDifferencePlot, \
    GridPlot


from sdnist.report.strs import *


def utility_score(dataset: Dataset, report_data: ReportData) -> ReportData:
    ds = dataset
    rd = report_data

    scorers = []
    if ds.challenge == CENSUS:
        up = UnivariatePlots(ds.synthetic_data, ds.target_data,
                             ds.schema, rd.output_directory, ds.challenge)
        up_saved_file_paths = up.save()

        cdp = CorrelationDifferencePlot(ds.synthetic_data, ds.target_data, rd.output_directory,
                                        ['SEX', 'INCTOT', 'RACE', 'CITIZEN', 'EDUC'])
        cdp_saved_file_paths = cdp.save()

        scorers = [CensusKMarginalScore(ds.target_data,
                                        ds.synthetic_data,
                                        ds.schema)]
    elif ds.challenge == TAXI:
        up = UnivariatePlots(ds.synthetic_data, ds.target_data,
                             ds.schema, rd.output_directory, ds.challenge)
        up_saved_file_paths = up.save()

        cdp = CorrelationDifferencePlot(ds.synthetic_data, ds.target_data, rd.output_directory,
                                        ['fare', 'trip_miles', 'trip_seconds', 'trip_hour_of_day'])
        cdp_saved_file_paths = cdp.save()

        scorers = [TaxiKMarginalScore(ds.target_data, ds.synthetic_data, ds.schema),
                   TaxiHigherOrderConjunction(ds.target_data, ds.synthetic_data),
                   TaxiGraphEdgeMapScore(ds.target_data, ds.synthetic_data, ds.schema)]
    else:
        raise Exception(f'Unknown challenge type: {ds.challenge}')

    for s in scorers:
        s.compute_score()
        metric_name = s.NAME
        metric_score = int(s.score)
        metric_attachments = []

        if s.NAME == CensusKMarginalScore.NAME \
                and ds.challenge == CENSUS:
            # 10 worst performing puma-years
            ss = s.scores.sort_values()
            worst_puma_years = []
            for (puma, year) in ss[0: 10].index:
                worst_puma_years.append({
                    "PUMA": puma,
                    "YEAR": year,
                    "SCORE": int(ss[(puma, year)])
                })
            metric_attachments.append(
                Attachment(name="10 Worst Performing PUMA - YEAR",
                           _data=worst_puma_years)
            )

            scores_df = pd.DataFrame(s.scores, columns=['score']).reset_index()
            puma_val_dict = {i: v for i, v in enumerate(ds.schema['PUMA']['values'])}
            year_val_dict = {i: v for i, v in enumerate(ds.schema['YEAR']['values'])}

            scores_df = scores_df.replace({"PUMA": puma_val_dict, "YEAR": year_val_dict})
            puma_year = 2015
            gp = GridPlot(scores_df, 'PUMA', {'YEAR': puma_year}, rd.output_directory)
            gp_paths = gp.save()
            rel_gp_path = ["/".join(list(p.parts)[-2:])
                            for p in gp_paths]
            metric_attachments.append(
                Attachment(name=f'PUMA wise k-marginal score in YEAR {puma_year}',
                           _data=[{IMAGE_NAME: Path(p).stem, PATH: p}
                                  for p in rel_gp_path],
                           _type=AttachmentType.ImageLinks)
            )
        elif s.NAME == TaxiKMarginalScore.NAME \
                and ds.challenge == TAXI:
            # 10 worst performing pickup_community_area and shift
            ss = s.scores.sort_values()
            worst_pickup_shifts = []
            for (pickup, shift) in ss[0: 10].index:
                worst_pickup_shifts.append({
                    "PICKUP_COMMUNITY_AREA": pickup,
                    "SHIFT": shift,
                    "SCORE": int(ss[(pickup, shift)])
                })
            metric_attachments.append(
                Attachment(name="10 Worst Performing PICKUP_COMMUNITY_AREA - SHIFT",
                           _data=worst_pickup_shifts)
            )

        rd.add(UtilityScorePacket(metric_name,
                                  metric_score,
                                  metric_attachments))
    rel_up_saved_file_paths = ["/".join(list(p.parts)[-2:])
                               for p in up_saved_file_paths]
    rel_cdp_saved_file_paths = ["/".join(list(p.parts)[-2:])
                                for p in cdp_saved_file_paths]

    rd.add(UtilityScorePacket("Univariate Distributions",
                              None,
                              [Attachment(name="Three Worst Performing Features",
                                          _data=[{IMAGE_NAME: Path(p).stem, PATH: p}
                                                  for p in rel_up_saved_file_paths],
                                          _type=AttachmentType.ImageLinks)]))

    rd.add(UtilityScorePacket("Correlation Coefficient Difference",
                              None,
                              [Attachment(name=None,
                                          _data=[{IMAGE_NAME: Path(p).stem, PATH: p}
                                                 for p in rel_cdp_saved_file_paths],
                                          _type=AttachmentType.ImageLinks)]))

    return rd
