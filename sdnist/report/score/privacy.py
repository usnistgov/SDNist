from pathlib import Path

import matplotlib.pyplot as plt

from sdnist.report import Dataset, ReportData
from sdnist.report.plots import ApparentMatchDistributionPlot
from sdnist.report.report_data import \
    PrivacyScorePacket, Attachment, AttachmentType

from sdnist.report.strs import *


def privacy_score(dataset: Dataset, report_data: ReportData) -> ReportData:
    ds = dataset
    rd = report_data

    if ds.challenge == CENSUS:
        amd_plot = ApparentMatchDistributionPlot(ds.synthetic_data,
                                                 ds.target_data,
                                                 rd.output_directory,
                                                 ['SEX', 'RACE', 'EDUC', 'INCTOT'],
                                                 ['PUMA', 'YEAR'])
        amd_plot_paths = amd_plot.save()

    elif ds.challenge == TAXI:
        amd_plot = ApparentMatchDistributionPlot(ds.synthetic_data,
                                                 ds.target_data,
                                                 rd.output_directory,
                                                 ['company_id', 'trip_miles', 'payment_type'],
                                                 ['pickup_community_area', 'shift'])
        amd_plot_paths = amd_plot.save()
    else:
        raise Exception(f'Unknown challenge type: {ds.challenge}')

    rel_cdp_saved_file_paths = ["/".join(list(p.parts)[-2:])
                                for p in amd_plot_paths]

    rd.add(PrivacyScorePacket("Apparent Match Distribution",
                              None,
                              [Attachment(name=None,
                                          _data=[{IMAGE_NAME: Path(p).stem, PATH: p}
                                                 for p in rel_cdp_saved_file_paths],
                                          _type=AttachmentType.ImageLinks)]))
    return rd
