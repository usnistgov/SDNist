from pathlib import Path

from sdnist.report import Dataset, ReportData
from sdnist.report.plots import ApparentMatchDistributionPlot
from sdnist.report.report_data import \
    PrivacyScorePacket, Attachment, AttachmentType

from strs import *


def privacy_score(dataset: Dataset, report_data: ReportData) -> ReportData:
    ds = dataset
    rd = report_data

    quasi_idf = []  # list of quasi-identifier features
    excluded = []  # list of excluded features from apparent match computation
    if ds.challenge == CENSUS:
        quasi_idf = ['SEX', 'RACE', 'EDUC', 'INCTOT']
        excluded = ['PUMA', 'YEAR']
        amd_plot = ApparentMatchDistributionPlot(ds.synthetic_data,
                                                 ds.target_data,
                                                 rd.output_directory,
                                                 quasi_idf,
                                                 excluded)
        amd_plot_paths = amd_plot.save()

    elif ds.challenge == TAXI:
        quasi_idf = ['company_id', 'trip_miles', 'payment_type']
        excluded = ['pickup_community_area', 'shift']
        amd_plot = ApparentMatchDistributionPlot(ds.synthetic_data,
                                                 ds.target_data,
                                                 rd.output_directory,
                                                 quasi_idf,
                                                 excluded)
        amd_plot_paths = amd_plot.save()
    else:
        raise Exception(f'Unknown challenge type: {ds.challenge}')

    rel_cdp_saved_file_paths = ["/".join(list(p.parts)[-2:])
                                for p in amd_plot_paths]

    # Quasi-identifier list as attachment
    quasi_list_atch = Attachment(name='Quasi-Identifiers',
                                 _data=', '.join(quasi_idf),
                                 _type=AttachmentType.String)
    # Total rows matched on quasi-identifiers as attachment
    print(amd_plot.quasi_matched_df.shape[0])
    total_quasi_matched = Attachment(name='Records matched on quasi-identifiers',
                                     _data=str(amd_plot.quasi_matched_df.shape[0]),
                                     _type=AttachmentType.String)
    # Apparent match distribution plot as attachment
    adp = Attachment(name=None,
                     _data=[{IMAGE_NAME: Path(p).stem, PATH: p}
                            for p in rel_cdp_saved_file_paths],
                     _type=AttachmentType.ImageLinks)
    rd.add(PrivacyScorePacket("Apparent Match Distribution",
                              None,
                              [quasi_list_atch,
                               total_quasi_matched,
                               adp]))
    return rd
