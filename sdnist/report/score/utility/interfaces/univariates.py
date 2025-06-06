from typing import List, Optional
from pathlib import Path

from sdnist.metrics.univariate import UnivariatePlots
from sdnist.report.dataset import Dataset
from sdnist.report.report_data import (
    ReportData, ReportUIData, Attachment, AttachmentType,
    UtilityScorePacket
)
from sdnist.report.score.paragraphs import univ_dist_para, univ_dist_worst_para

import sdnist.strs as strs


class UnivariatesReport:
    def __init__(self,
                 dataset: Dataset,
                 ui_data: ReportUIData,
                 report_data: ReportData,
                 worst_univariates_to_display=24,
                 out_dir: Optional[Path] = None,
                 stable_feature: Optional[str] = None,
                 worst_stable_feature_values: Optional[List[str]] = None):
        self.ds = dataset
        self.ui_data = ui_data
        self.rd = report_data
        self.stable_feature = stable_feature
        self.worst_stable_feature_values = worst_stable_feature_values
        t = self.ds.d_target_data
        s = self.ds.d_synthetic_data

        if self.stable_feature and len(self.worst_stable_feature_values):
            t = t[t[self.stable_feature].isin(self.worst_stable_feature_values)]
            s = s[s[self.stable_feature].isin(self.worst_stable_feature_values)]
        self.out_dir = out_dir
        if self.out_dir is None:
            self.out_dir = self.ui_data.output_directory

        self.up = UnivariatePlots(
            s, t, self.ds, self.out_dir,
            worst_univariates_to_display=worst_univariates_to_display)
        self.features_data = dict()
        self.compute()

    def compute(self, level=2):
        self.features_data = self.up.save(level)  # univariate features data

    def is_worst_kmarginal_output(self) -> bool:
        return (self.stable_feature is not None
                and self.worst_stable_feature_values
                and len(self.worst_stable_feature_values))

    def add_to_ui(self):
        u_as = []  # univariate attachments
        if self.is_worst_kmarginal_output():
            u_as.append(Attachment(name=None,
                                   _data=f"h3Univariate Distribution of Worst "
                                         f"Performing Features with least fidelity "
                                         + self.stable_feature,
                                   _type=AttachmentType.String))
            u_as.append(Attachment(name=None,
                                   _data=univ_dist_worst_para
                                   .replace(strs.STABLE_FEATURE,
                                            self.stable_feature),
                                   _type=AttachmentType.String))
        else:
            self.rd.add('Univariate', self.up.report_data())

        relative_path_level = 2 if not self.is_worst_kmarginal_output() else 3

        for k, v in self.features_data.items():
            u_path = v['path']
            if len(str(u_path)) == 0:
                continue
            u_rel_path = "/".join(list(u_path.parts)[-relative_path_level:])
            name = k
            a = Attachment(name=None,
                           _data=f'h4{name}',
                           _type=AttachmentType.String)
            u_as.append(a)

            if "excluded" in v:
                fv = v['excluded']['feature_value']
                tc = v['excluded']['target_counts']
                sc = v['excluded']['deidentified_counts']
                f_name = name.split(':')[0]

                if k.startswith('POVPIP'):
                    fv = '501 [Not in poverty: income above 5 x poverty line]'
                elif fv == -1:
                    f_detail = '[N/A]'
                    if 'values' in self.ds.data_dict[f_name]:
                        f_detail = self.ds.data_dict[f_name]['values']['N']
                    fv = f'N [{f_detail}]'
                else:
                    f_detail = ''
                    if 'values' in self.ds.data_dict[f_name]:
                        v_data = self.ds.data_dict[f_name]['values']
                        if str(fv) in v_data:
                            f_detail = self.ds.data_dict[f_name]['values'][str(fv)]
                    fv = f'{fv} [{f_detail}]'

                a = Attachment(name=None,
                               _data=f"Feature Values not shown in the chart:"
                                     f"<br>Value: {fv}"
                                     f"<br>Target Data Counts: {tc}"
                                     f"<br>Deidentified Data Counts: {sc}",
                               _type=AttachmentType.String)
                u_as.append(a)

            a = Attachment(name=None,
                           _data=[{strs.IMAGE_NAME: Path(u_rel_path).stem,
                                  strs.PATH: u_rel_path}],
                           _type=AttachmentType.ImageLinks)
            u_as.append(a)

        # if this is intended for kmarginal breakdown section then
        # don't create a separate utility score packet, instead return
        # the univariate metrics attachments as it is.
        if self.is_worst_kmarginal_output():
            return u_as

        self.ui_data.add(
            UtilityScorePacket("Univariate Distributions",
                               None,
                               [Attachment(name=None,
                                           _data=univ_dist_para,
                                           _type=AttachmentType.String)] + u_as))
