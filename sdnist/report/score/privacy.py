from typing import Tuple
from pathlib import Path

from sdnist.report import Dataset, ReportData, ReportUIData
from sdnist.report.plots import ApparentMatchDistributionPlot
from sdnist.report.report_data import \
    PrivacyScorePacket, Attachment, AttachmentType
from sdnist.report.score.paragraphs import *
from sdnist.strs import *


def privacy_score(dataset: Dataset, ui_data: ReportUIData, report_data) \
        -> Tuple[ReportUIData, ReportData]:
    ds = dataset
    r_ui_d = ui_data
    rd = report_data

    quasi_idf = []  # list of quasi-identifier features
    excluded = []  # list of excluded features from apparent match computation
    if ds.challenge == CENSUS:
        quasi_idf = ['SEX', 'RAC1P', 'EDU', 'INDP_CAT', 'MST']
        quasi_idf = list(set(ds.features).intersection(set(quasi_idf)))
        excluded = ['PUMA', 'RACE']
        amd_plot = ApparentMatchDistributionPlot(ds.synthetic_data,
                                                 ds.target_data,
                                                 r_ui_d.output_directory,
                                                 quasi_idf,
                                                 excluded)
        amd_plot_paths = amd_plot.save()
        rd.add('apparent_match_distribution', amd_plot.report_data)

    elif ds.challenge == TAXI:
        quasi_idf = ['company_id', 'trip_miles', 'payment_type']
        quasi_idf = list(set(ds.features).intersection(set(quasi_idf)))
        excluded = ['pickup_community_area', 'shift']
        amd_plot = ApparentMatchDistributionPlot(ds.synthetic_data,
                                                 ds.target_data,
                                                 r_ui_d.output_directory,
                                                 quasi_idf,
                                                 excluded)
        amd_plot_paths = amd_plot.save()
    else:
        raise Exception(f'Unknown challenge type: {ds.challenge}')

    rel_cdp_saved_file_paths = ["/".join(list(p.parts)[-2:])
                                for p in amd_plot_paths]

    amd_para_a = Attachment(name=None,
                            _data=app_match_para,
                            _type=AttachmentType.String)
    # Quasi-identifier list as attachment
    quasi_para_a = Attachment(name='Quasi-Identifiers',
                              _data=quasi_idf_para,
                              _type=AttachmentType.String)
    quasi_list_atch = Attachment(name=None,
                                 _data=', '.join(quasi_idf),
                                 _type=AttachmentType.String)
    # Total rows matched on quasi-identifiers as attachment
    rec_matched = amd_plot.quasi_matched_df.shape[0]
    rec_percent = round(rec_matched/ds.synthetic_data.shape[0], 3)

    rec_mat_para_a = Attachment(name='Records Matched on Quasi-Identifiers',
                                _data=rec_matched_para,
                                _type=AttachmentType.String)
    total_quasi_matched = Attachment(name=None,
                                     _data=f"{rec_matched}, {rec_percent}% of "
                                           f"the synthetic records",
                                     _type=AttachmentType.String)
    # Apparent match distribution plot as attachment
    adp_para_a = Attachment(name='Percentage Similarity of the Matched Records',
                            _data=percn_matched_para,
                            _type=AttachmentType.String)
    adp = Attachment(name=None,
                     _data=[{IMAGE_NAME: Path(p).stem, PATH: p}
                            for p in rel_cdp_saved_file_paths],
                     _type=AttachmentType.ImageLinks)
    r_ui_d.add(PrivacyScorePacket("Apparent Match Distribution",
                              None,
                              [quasi_para_a,
                               quasi_list_atch,
                               rec_mat_para_a,
                               total_quasi_matched,
                               adp_para_a,
                               adp]))
    return r_ui_d, rd
