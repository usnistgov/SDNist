from typing import Dict

from sdnist.metrics.regression import LinearRegressionMetric
from sdnist.report import Dataset
from sdnist.report.report_data import (
    ReportData, ReportUIData, UtilityScorePacket, Attachment, AttachmentType)
from sdnist.report.score.paragraphs import (
    corr_para, pear_corr_para, kend_corr_para)
from sdnist.report.plots import (
    CorrelationDifferencePlot, PearsonCorrelationPlot)
from sdnist.metrics.pearson_correlation import \
    PearsonCorrelationDifference

import sdnist.strs as strs
from sdnist.utils import *

class CorrelationsReport:
    def __init__(self, dataset: Dataset,
                 ui_data: ReportUIData, report_data: ReportData):
        self.ds = dataset
        self.r_ui_d = ui_data
        self.rd = report_data
        self.corr_features = self.ds.corr_features
        self.can_compute = len(self.corr_features) > 1

        self.cdp_saved_file_paths = []
        self.pcp_saved_file_paths = []

    def compute(self):
        if not self.can_compute:
           return

        cdp = CorrelationDifferencePlot(self.ds.t_synthetic_data,
                                        self.ds.t_target_data,
                                        self.r_ui_d.output_directory,
                                        self.corr_features)
        self.cdp_saved_file_paths = cdp.save()

        pcd = PearsonCorrelationDifference(self.ds.t_target_data,
                                           self.ds.t_synthetic_data,
                                           self.corr_features)
        pcd.compute()
        pcp = PearsonCorrelationPlot(pcd.pp_corr_diff,
                                     self.r_ui_d.output_directory)
        self.pcp_saved_file_paths = pcp.save()

        self.rd.add('Correlations',
               {"kendall correlation difference": cdp.report_data,
                "pearson correlation difference": pcp.report_data})

    def add_to_ui(self):
        if not self.can_compute:
            return

        corr_metric_a = []
        corr_metric_a.append(Attachment(name=None,
                                        _data=corr_para,
                                        _type=AttachmentType.String))

        if len(self.pcp_saved_file_paths):
            rel_pcp_saved_file_paths = ["/".join(list(p.parts)[-2:])
                                        for p in self.pcp_saved_file_paths]
            pc_para_a = Attachment(
                name="Pearson Correlation Coefficient Difference",
                _data=pear_corr_para,
                _type=AttachmentType.String)
            pc_a = Attachment(name=None,
                              _data=[
                                  {strs.IMAGE_NAME: Path(p).stem, strs.PATH: p}
                                  for p in rel_pcp_saved_file_paths],
                              _type=AttachmentType.ImageLinks)
            corr_metric_a.append(pc_para_a)
            corr_metric_a.append(pc_a)

        if len(self.cdp_saved_file_paths):
            rel_cdp_saved_file_paths = ["/".join(list(p.parts)[-2:])
                                        for p in self.cdp_saved_file_paths]
            ktc_p_a = Attachment(
                name="Kendall Tau Correlation Coefficient Difference",
                _data=kend_corr_para,
                _type=AttachmentType.String)
            ktc_a = Attachment(name=None,
                               _data=[
                                   {strs.IMAGE_NAME: Path(p).stem, strs.PATH: p}
                                   for p in rel_cdp_saved_file_paths],
                               _type=AttachmentType.ImageLinks)
            corr_metric_a.append(ktc_p_a)
            corr_metric_a.append(ktc_a)

        self.r_ui_d.add(UtilityScorePacket("Correlations",
                                      None,
                                      corr_metric_a))