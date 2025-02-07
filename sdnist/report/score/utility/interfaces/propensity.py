from pathlib import Path

from sdnist.report.dataset import Dataset
from sdnist.report.report_data import \
    ReportData, ReportUIData, UtilityScorePacket, Attachment, AttachmentType
from sdnist.report.plots.propensity import PropensityDistribution
from sdnist.metrics.propensity import \
    PropensityMSE
from sdnist.report.score.paragraphs import propensity_para
import sdnist.strs as strs


class PropensityMSEReport:
    def __init__(self,
                 dataset: Dataset,
                 ui_data: ReportUIData,
                 report_data: ReportData):
        self.ds = dataset
        self.r_ui_d = ui_data
        self.rd = report_data

        self.p = PropensityMSE(
            self.ds.t_target_data,
            self.ds.t_synthetic_data,
            self.r_ui_d.output_directory,
            self.ds.features)
        self.pp = None

        self.propensity_score = 0

    def compute(self):
        # get propensity score
        self.p.compute_score()
        s = self.p.score
        self.propensity_score = int(s) if s > 100 else round(s, 3)

        # get and plot propensity distribution
        self.pp = PropensityDistribution(self.p.prob_dist,
                                         self.r_ui_d.output_directory)

    def add_to_ui(self):
        plot_paths = self.pp.save()
        prop_rep_data = {**self.p.report_data,
                         **self.pp.report_data}
        self.rd.add('propensity mean square error', prop_rep_data)

        rel_pd_path = ["/".join(list(p.parts)[-2:])
                       for p in plot_paths]

        # propensity MSE attachment
        pd_para_a = Attachment(name=None,
                               _data=propensity_para,
                               _type=AttachmentType.String)
        pd_score_a = Attachment(name=None,
                                _data=f"Highlight-Score: {self.propensity_score}",
                                _type=AttachmentType.String)
        pd_a = Attachment(name=f'Propensities Distribution',
                          _data=[{strs.IMAGE_NAME: Path(p).stem, strs.PATH: p}
                                 for p in rel_pd_path],
                          _type=AttachmentType.ImageLinks)

        prop_pkt = UtilityScorePacket(self.p.NAME,
                                      None,
                                      [pd_para_a, pd_score_a, pd_a])
        self.r_ui_d.add(prop_pkt)
