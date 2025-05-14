from typing import Tuple

from sdnist.load import \
    TestDatasetName
from sdnist.metrics.pearson_correlation import \
    PearsonCorrelationDifference
from sdnist.report.score.paragraphs import *
from sdnist.report.score.utility.interfaces.kmarginal import KMarginalReport
from sdnist.report.score.utility.interfaces.linear_regression import \
    LinearRegressionReport
from sdnist.report.score.utility.interfaces.inconsistency import \
    InconsistenciesReport
from sdnist.report.score.utility.interfaces.pca import PCAReport
from sdnist.report.score.utility.interfaces.propensity import PropensityMSEReport
from sdnist.report import Dataset
from sdnist.report.report_data import \
    ReportData, ReportUIData, UtilityScorePacket, Attachment, AttachmentType
from sdnist.report.plots import \
    CorrelationDifferencePlot, PearsonCorrelationPlot
from sdnist.report.score.utility.interfaces.univariates import UnivariatesReport

import sdnist.strs as strs
from sdnist.utils import *


def utility_score(dataset: Dataset, ui_data: ReportUIData, report_data: ReportData,
                  log: SimpleLogger) \
        -> Tuple[ReportUIData, ReportData]:
    ds = dataset
    r_ui_d = ui_data  # report ui data
    rd = report_data

    log.msg('Kmarginal', level=3)
    kmr = KMarginalReport(ds, r_ui_d, rd)
    kmr.compute()
    kmr.add_to_ui()
    log.end_msg()

    log.msg('Univariates', level=3)
    ur = UnivariatesReport(ds, r_ui_d, rd)
    ur.compute()
    ur.add_to_ui()
    log.end_msg()

    if dataset.test != TestDatasetName.sbo_target:
        can_compute_correlations = len(ds.corr_features) > 1
        if not can_compute_correlations:
            log.msg(
                "Not enough correlation features to compute correlations",
                level=2,
                timed=False,
                msg_type="warn",
            )
        if can_compute_correlations:
            log.msg('Correlations', level=3)
            cdp_saved_file_paths = []
            pcp_saved_file_paths = []
            corr_features = ds.corr_features
            if len(corr_features) > 1:
                cdp = CorrelationDifferencePlot(ds.t_synthetic_data, ds.t_target_data,
                                                r_ui_d.output_directory,
                                                corr_features)
                cdp_saved_file_paths = cdp.save()

                pcd = PearsonCorrelationDifference(ds.t_target_data,
                                                   ds.t_synthetic_data,
                                                   corr_features)
                pcd.compute()
                pcp = PearsonCorrelationPlot(pcd.pp_corr_diff, r_ui_d.output_directory)
                pcp_saved_file_paths = pcp.save()

                rd.add('Correlations',
                       {"kendall correlation difference": cdp.report_data,
                        "pearson correlation difference": pcp.report_data})

            corr_metric_a = []
            corr_metric_a.append(Attachment(name=None,
                                            _data=corr_para,
                                            _type=AttachmentType.String))

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

            r_ui_d.add(UtilityScorePacket("Correlations",
                                          None,
                                          corr_metric_a))
            log.end_msg()

        log.msg('Linear Regression', level=3)
        lgr = LinearRegressionReport(ds, r_ui_d, rd)
        lgr.add_to_ui()
        log.end_msg()

    log.msg('PropensityMSE', level=3)
    propensity = PropensityMSEReport(ds, r_ui_d, rd)
    propensity.compute()
    propensity.add_to_ui()
    log.end_msg()

    log.msg('PCA', level=3)
    pca_r = PCAReport(ds, r_ui_d, rd)
    pca_r.add_to_ui()
    log.end_msg()

    if dataset.test != TestDatasetName.sbo_target:
        log.msg('Inconsistencies', level=3)
        icr = InconsistenciesReport(ds, r_ui_d, rd)
        icr.add_to_ui()
        log.end_msg()

        log.msg('K-Marginal Breakdown', level=3)
        if kmr:
            kmr.compute_kmarginal_breakdown()
            kmr.add_breakdown_to_ui()
        log.end_msg()

    return r_ui_d, rd

