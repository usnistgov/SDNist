
import pandas as pd

from sdnist.load import \
    TestDatasetName, load_dataset, build_name
from sdnist.metrics.kmarginal import \
    CensusKMarginalScore, TaxiKMarginalScore
from sdnist.metrics.hoc import \
    TaxiHigherOrderConjunction
from sdnist.metrics.graph_edge_map import \
    TaxiGraphEdgeMapScore

from sdnist.report import Path
from sdnist.report.report_data import \
    ReportData, ScorePacket, Attachment, AttachmentType, \
    DatasetType, DataDescriptionPacket
from sdnist.report.plots import UnivariatePlots
from sdnist.report.plots import CorrelationDifferencePlot

from sdnist.report.strs import *


def score(challenge: str,
          synthetic_filepath: Path,
          output_directory: Path,
          public: bool = True,
          test: TestDatasetName = TestDatasetName.NONE,
          data_root: Path = 'data') -> ReportData:

    rep_data = ReportData()
    # load target dataset that is used to score synthetic dataset
    target_dataset, schema = load_dataset(
        challenge=challenge,
        root=data_root,
        download=True,
        public=public,
        test=test
    )
    target_dataset_path = build_name(challenge=challenge,
                                     root=data_root,
                                     public=public,
                                     test=test)

    rep_data.add_data_description(DatasetType.Target,
                                  DataDescriptionPacket(target_dataset_path.stem,
                                                        target_dataset.shape[0],
                                                        target_dataset.shape[1]))
    # load synthetic dataset
    dtypes = {feature: desc["dtype"] for feature, desc in schema.items()}
    synthetic_dataset = pd.read_csv(synthetic_filepath, dtype=dtypes)
    rep_data.add_data_description(DatasetType.Synthetic,
                                  DataDescriptionPacket(synthetic_filepath.stem,
                                                        synthetic_dataset.shape[0],
                                                        synthetic_dataset.shape[1]))

    scorers = []
    if challenge == CENSUS:

        up = UnivariatePlots(synthetic_dataset, target_dataset, schema, output_directory, challenge)
        up_saved_file_paths = up.save()

        cdp = CorrelationDifferencePlot(synthetic_dataset, target_dataset, output_directory,
                                        ['SEX', 'INCTOT', 'RACE', 'CITIZEN', 'EDUC'])
        cdp_saved_file_paths = cdp.save()

        scorers = [CensusKMarginalScore(target_dataset,
                                        synthetic_dataset,
                                        schema)]
    elif challenge == TAXI:
        up = UnivariatePlots(synthetic_dataset, target_dataset, schema, output_directory, challenge)
        up_saved_file_paths = up.save()

        cdp = CorrelationDifferencePlot(synthetic_dataset, target_dataset, output_directory,
                                        ['fare', 'trip_miles', 'trip_seconds', 'trip_hour_of_day'])
        cdp_saved_file_paths = cdp.save()

        scorers = [TaxiKMarginalScore(target_dataset, synthetic_dataset, schema),
                   TaxiHigherOrderConjunction(target_dataset, synthetic_dataset),
                   TaxiGraphEdgeMapScore(target_dataset, synthetic_dataset, schema)]
    else:
        raise Exception(f'Unknown challenge type: {challenge}')

    for s in scorers:
        s.compute_score()
        metric_name = s.NAME
        metric_score = int(s.score)
        metric_attachments = []

        if s.NAME == CensusKMarginalScore.NAME \
                and challenge == CENSUS:
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
        elif s.NAME == TaxiKMarginalScore.NAME \
                and challenge == TAXI:
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

        rep_data.add(ScorePacket(metric_name,
                                 metric_score,
                                 metric_attachments))
    rel_up_saved_file_paths = ["/".join(list(p.parts)[-2:])
                               for p in up_saved_file_paths]
    rel_cdp_saved_file_paths = ["/".join(list(p.parts)[-2:])
                                for p in cdp_saved_file_paths]

    rep_data.add(ScorePacket("Univariate Distributions",
                             None,
                             [Attachment(name="Three Worst Performing Features",
                                         _data=[{IMAGE_NAME: Path(p).stem, PATH: p}
                                                for p in rel_up_saved_file_paths],
                                         _type=AttachmentType.ImageLinks)]))

    rep_data.add(ScorePacket("Correlation Coefficient Difference",
                             None,
                             [Attachment(name=None,
                                         _data=[{IMAGE_NAME: Path(p).stem, PATH: p}
                                                for p in rel_cdp_saved_file_paths],
                                         _type=AttachmentType.ImageLinks)]))

    return rep_data
