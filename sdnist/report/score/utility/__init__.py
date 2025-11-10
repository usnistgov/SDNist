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
from sdnist.report.score.utility.interfaces.correlations import CorrelationsReport
from sdnist.report.score.utility.interfaces.predictive_utility import PredictiveUtilityReport
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
    metrics = ds.config.get('metrics', [])
    r_ui_d = ui_data  # report ui data
    rd = report_data

    kmr = None
    if 'Kmarginal' in metrics:
        log.msg('Kmarginal', level=3)
        kmr = KMarginalReport(ds, r_ui_d, rd)
        kmr.compute()
        kmr.add_to_ui()
        log.end_msg()

    if 'Univariates' in metrics:
        log.msg('Univariates', level=3)
        ur = UnivariatesReport(ds, r_ui_d, rd)
        ur.compute()
        ur.add_to_ui()
        log.end_msg()

    if 'Correlations' in metrics:
        log.msg('Correlations', level=3)
        corr_report = CorrelationsReport(ds, r_ui_d, rd)
        corr_report.compute()
        corr_report.add_to_ui()
        log.end_msg()

    if 'PredictiveUtility' in metrics:
        log.msg('Predictive Utility', level=3)
        pur = PredictiveUtilityReport(ds, r_ui_d, rd)
        pur.compute()
        pur.add_to_ui()
        log.end_msg()

    if 'Linear Regression' in metrics:
        log.msg('Linear Regression', level=3)
        lgr = LinearRegressionReport(ds, r_ui_d, rd)
        lgr.add_to_ui()
        log.end_msg()

    if 'PropensityMSE' in metrics:
        log.msg('PropensityMSE', level=3)
        propensity = PropensityMSEReport(ds, r_ui_d, rd)
        propensity.compute()
        propensity.add_to_ui()
        log.end_msg()

    if 'PCA' in metrics:
        log.msg('PCA', level=3)
        pca_r = PCAReport(ds, r_ui_d, rd)
        pca_r.add_to_ui()
        log.end_msg()

    if 'Inconsistencies' in metrics:
        log.msg('Inconsistencies', level=3)
        icr = InconsistenciesReport(ds, r_ui_d, rd)
        icr.add_to_ui()
        log.end_msg()

    if 'Kmarginal Breakdown' in metrics and kmr:
        log.msg('K-Marginal Breakdown', level=3)
        if kmr:
            kmr.compute_kmarginal_breakdown()
            kmr.add_breakdown_to_ui()
        log.end_msg()

    return r_ui_d, rd

