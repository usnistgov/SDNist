from typing import Tuple
from pathlib import Path

from sdnist.report import Dataset, ReportData, ReportUIData
from sdnist.report.plots import ApparentMatchDistributionPlot
from sdnist.metrics.unique_exact_matches import unique_exact_matches
from sdnist.report.report_data import \
    PrivacyScorePacket, Attachment, AttachmentType
from sdnist.report.score.paragraphs import *
from sdnist.strs import *
from sdnist.utils import *


def privacy_score(dataset: Dataset, ui_data: ReportUIData, report_data, log: SimpleLogger) \
        -> Tuple[ReportUIData, ReportData]:
    ds = dataset
    r_ui_d = ui_data
    rd = report_data

    log.msg('Unique Exact Matches', level=3)
    t_rec_matched, perc_t_rec_matched, \
        unique_target_records, perc_unique_target_records = \
        unique_exact_matches(ds.c_target_data, ds.c_synthetic_data)
    perc_t_rec_matched = perc_t_rec_matched
    uem_para1_a = Attachment(name=None,
                            _data=unique_exact_match_para_1,
                            _type=AttachmentType.String)
    uem_para2_a = Attachment(name=None,
                            _data=unique_exact_match_para_2,
                            _type=AttachmentType.String)
    uem_para3_a = Attachment(name=None,
                            _data=unique_exact_match_para_3,
                            _type=AttachmentType.String)
    uem_para4_a = Attachment(name=None,
                            _data=unique_exact_match_para_4,
                            _type=AttachmentType.String)

    feat_space_str = "{:0.3e}".format(ds.feature_space)
    target_matched_a = Attachment(name="Target Data Properties",
                                     _data=f"Feature space size (possible combinations): "
                                           f"-Highlight-{feat_space_str}-Highlight-<br>"
                                           f"Number of unique records in Target Data: "
                                           f"-Highlight-{unique_target_records} "
                                           f"({perc_unique_target_records}%-Highlight-)",
                                     _type=AttachmentType.String)
    deid_matched_a = Attachment(name="Deidentified Data Properties",
                                     _data=f"Number of unique Target Data records exactly "
                                           f"matched in Deid. Data: "
                                           f"-Highlight-{t_rec_matched} "
                                           f"({perc_t_rec_matched}%)-Highlight-",
                                     _type=AttachmentType.String)
    r_ui_d.add(PrivacyScorePacket("Unique Exact Matches",
                              None,
                              [uem_para1_a, uem_para2_a, uem_para3_a, uem_para4_a,
                               target_matched_a,
                               deid_matched_a]))
    rd.add('unique_exact_matches', {
        "records matched in target data": t_rec_matched,
        "percent records matched in target data": perc_t_rec_matched,
        "unique target records": unique_target_records,
        "percent unique target records": perc_unique_target_records,
    })

    log.end_msg()

    log.msg('Apparent Match Distribution', level=3)
    quasi_idf = []  # list of quasi-identifier features
    excluded = []  # list of excluded features from apparent match computation
    if ds.challenge == CENSUS:
        quasi_idf = ['SEX', 'MSP', 'RAC1P', 'OWN_RENT', 'EDU', 'PUMA', 'INDP_CAT', 'HISP']
        quasi_idf = list(set(ds.features).intersection(set(quasi_idf)))
        excluded = []
        amd_plot = ApparentMatchDistributionPlot(ds.c_synthetic_data,
                                                 ds.c_target_data,
                                                 r_ui_d.output_directory,
                                                 quasi_idf,
                                                 excluded)
        amd_plot_paths = amd_plot.save()
        rd.add('apparent_match_distribution', amd_plot.report_data)
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
    rec_percent = round(rec_matched/ds.c_target_data.shape[0] * 100, 2)

    rec_mat_para_a = Attachment(name='Records Matched on Quasi-Identifiers',
                                _data=rec_matched_para,
                                _type=AttachmentType.String)
    total_quasi_matched = Attachment(name=None,
                                     _data=f"Number of Target Data records exactly matched "
                                           f"in Deid. Data on Quasi-Identifiers: "
                                           f"-Highlight-{rec_matched} ({rec_percent}%)-Highlight-",
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
                              [amd_para_a,
                               quasi_para_a,
                               quasi_list_atch,
                               rec_mat_para_a,
                               total_quasi_matched,
                               adp_para_a,
                               adp]))
    log.end_msg()


    return r_ui_d, rd
