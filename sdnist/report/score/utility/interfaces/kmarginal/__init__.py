from typing import Dict, List, Optional
import pandas as pd
from pathlib import Path

from sdnist.report.report_data import \
    ReportData, ReportUIData, Attachment, AttachmentType, UtilityScorePacket
from sdnist.report.dataset import Dataset, get_stable_features
from sdnist.metrics.kmarginal import KMarginal
from sdnist.report.score.utility.interfaces.kmarginal.subsample_score import (
    kmarginal_subsamples, kmarginal_stable_feature_subsamples)
from sdnist.report.score.utility.interfaces.kmarginal.stable_feature_scores import (
    best_worst_performing
)
from sdnist.report.score.utility.interfaces.kmarginal.detailed_breakdown import (
    worst_kmarginal_score_breakdown
)

from sdnist.report.score.paragraphs import (
    worst_k_marg_para, k_marg_synopsys_para, k_marg_break_para,
    sub_sample_para, k_marg_all_geo_para, k_marg_sector_para
)
import sdnist.strs as strs
from sdnist.utils import create_path, save_data_frame, relative_path



class KMarginalReport:
    def __init__(self,
                 dataset: Dataset,
                 ui_data: ReportUIData,
                 report_data: ReportData):
        self.ds = dataset
        self.r_ui_d = ui_data
        self.rd = report_data

        self.stable_features: Optional[List[str]] = \
                get_stable_features(self.ds.config, self.ds.c_target_data.columns.tolist())
        self.stable_feature_values: Optional[Dict] = self.get_stable_feature_values(0)

        self.kmarginal_score = 0
        self.kmarginal_stable_feature_scores = None

        self.stable_feature_worst_scores: List[Dict] = []
        self.stable_feature_best_score: List[Dict] = []

        self.other_stable_feature_worst_scores: List = []
        self.other_stable_feature_best_scores: List = []

        self.subsample_scores: Dict[float, int] = dict()
        self.subsample_stable_feature_score: pd.DataFrame = pd.DataFrame()

        # list of report attachments created by other metrics (univariate, correlations, etc)
        # for the detail breakdown of worst performing stable feature values.
        self.worst_kmarginal_attachments: List[Attachment] = []

        # number of worst stable feature values to show on the report
        self.default_worst_stable_feature_values = 2

        self.main_table_name = 'all_groups'
        self.stable_feature_table_name = 'stable_feature'

    def compute(self):
        sf = None
        if self.stable_features is not None:
            if len(self.stable_features) == 0:
                sf = None
            else:
                sf = self.stable_features[0]

        k_marginal = KMarginal(self.ds.d_target_data,
                               self.ds.d_synthetic_data,
                               sf)
        k_marginal.compute_score()
        self.kmarginal_score = int(k_marginal.score)

        self.subsample_scores, self.subsample_stable_feature_score = \
            self.compute_subsample_kmarginal_scores(sf)
        if self.stable_features:
            self.kmarginal_stable_feature_scores = k_marginal.scores
            self.stable_feature_worst_scores, self.stable_feature_best_score = (
                best_worst_performing(
                    self.kmarginal_stable_feature_scores,
                    self.subsample_stable_feature_score,
                    self.ds,
                    self.stable_features[0],
                    self.stable_feature_values)
            )
        if self.stable_features and len(self.stable_features) > 1:
            self.compute_other_stable_features_scores()
        return k_marginal

    def compute_subsample_kmarginal_scores(self, stable_feature: Optional[str]):

        subsample_scores = kmarginal_subsamples(self.ds.d_target_data, stable_feature)
        subsample_stable_feature_score = kmarginal_stable_feature_subsamples(
            self.ds.d_target_data, stable_feature)
        return subsample_scores, subsample_stable_feature_score

    def get_stable_feature_values(self, index: int):
        if self.stable_features and self.stable_features[index] in self.ds.data_dict:
            return {
                self.stable_features[index]:
                    {
                        i: v
                        for i, v in enumerate(self.ds.data_dict[self.stable_features[index]]['values'])
                    }
            }
        else:
            return None

    def compute_other_stable_features_scores(self):
        for i, sf in enumerate(self.stable_features[1:]):
            stable_feature_values = self.get_stable_feature_values(i + 1)
            k_marginal = KMarginal(self.ds.d_target_data,
                                   self.ds.d_synthetic_data,
                                   sf)
            k_marginal.compute_score()
            stable_feature_scores = k_marginal.scores
            _, subsample_stable_feature_score = \
                self.compute_subsample_kmarginal_scores(sf)
            o_worst, o_best = (
                best_worst_performing(
                    k_marginal.scores,
                    subsample_stable_feature_score,
                    self.ds,
                    sf,
                    stable_feature_values)
            )
            self.other_stable_feature_worst_scores.append(o_worst)
            self.other_stable_feature_best_scores.append(o_best)

    def compute_kmarginal_breakdown(self):
        if self.kmarginal_stable_feature_scores is None:
            return

        # target pumas
        t_group_values = self.ds.d_target_data[self.stable_features[0]].unique()
        # synthetic pumas
        s_group_values = self.ds.d_synthetic_data[self.stable_features[0]].unique()
        # usable pumas
        usable_group_values = set(t_group_values).intersection(s_group_values)
        usable_group_values = [ self.ds.bin_mappings[self.stable_features[0]].get(v, v)
                                for v in usable_group_values]
        # default worst best
        default_w_b_n = self.default_worst_stable_feature_values \
            if len(usable_group_values) <= 6 else 5

        # count of worst or best k-marginal pumas to select
        worst_scores = [ws for ws in self.stable_feature_worst_scores
                        if ws[self.stable_features[0]][0] in usable_group_values]
        best_scores = [bs for bs in self.stable_feature_best_score
                       if bs[self.stable_features[0]][0] in usable_group_values]

        w_b_n = default_w_b_n if len(worst_scores) > default_w_b_n else len(worst_scores)
        worst_scores, best_scores = worst_scores[0: w_b_n], best_scores[0: w_b_n]

        sub_metric_attachments, k_marg_break_rd = (
            worst_kmarginal_score_breakdown(worst_scores,
                                            self.ds,
                                            self.r_ui_d,
                                            self.rd,
                                            self.stable_features[0])
        )

        k_marg_break_para_a = Attachment(name=None,
                                         _data=k_marg_break_para.replace(strs.STABLE_FEATURE,
                                                                         self.stable_features[0]),
                                         _type=AttachmentType.String)

        # worst score attachment
        ws_para_a = Attachment(name=f"{len(worst_scores)} " + '- '
                                    + self.stable_features[0] + ' with least fidelity',
                               _data=worst_k_marg_para.replace(strs.STABLE_FEATURE, self.stable_features[0]),
                               _type=AttachmentType.String)
        ws_a = Attachment(name=None,
                          _data=worst_scores)

        self.worst_kmarginal_attachments = [k_marg_break_para_a, ws_para_a, ws_a]

        self.worst_kmarginal_attachments.extend(sub_metric_attachments)

        self.rd.add('worst_kmarginal_breakdown', k_marg_break_rd)

    def add_to_ui(self):
        # calculate kmarginal sampling error comparison
        # get subsample fractions used for computing kmarginal scores of
        # target subsamples
        sorted_frac = sorted(list(self.subsample_scores.keys()))
        # compute difference (error) between target subsamples and deid data
        # kmarginal scores
        score_error = [abs(self.subsample_scores[frac] - self.kmarginal_score)
                       for frac in sorted_frac]
        min_score_diff = min(score_error)
        min_err_idx = score_error.index(min_score_diff)
        min_frac = sorted_frac[min_err_idx]

        ss_para_a = Attachment(name="Sampling Error Comparison",
                               _data=sub_sample_para,
                               _type=AttachmentType.String)

        # subsample fraction score attachment
        ssf_a = Attachment(name=None,
                           _data=f"K-Marginal score of the deidentified data closely resembles "
                                 f"K-Marginal score of a {int(min_frac * 100)}% sub-sample of "
                                 f"the target data.",
                           _type=AttachmentType.String)

        # sampling error data attachment
        se_data = [{"Sub-Sample Size": f"{int(frac * 100)}%",
                    "Sub-Sample K-Marginal Score": self.subsample_scores[frac],
                    "Deidentified Data K-marginal score": self.kmarginal_score,
                    "Absolute Diff. From Deidentified Data K-marginal Score":
                    f"{round(score_error[i], 2)}"}
                   for i, frac in enumerate(sorted_frac)]
        se_df = pd.DataFrame(se_data)

        k_marg_synopsys_path = Path(self.r_ui_d.output_directory, 'kmarg')
        create_path(k_marg_synopsys_path)

        se_data[min_err_idx]["min_idx"] = True

        sed_a = Attachment(name=None,
                           _data=se_data)


        # Create attachments for UI report
        # k marg para attachment
        kmp_a = Attachment(name=None,
                           _data=k_marg_synopsys_para,
                           _type=AttachmentType.String)
        # k marg score attachment
        kms_a = Attachment(name=None,
                           _data=f"Highlight-K-Marginal Score: {self.kmarginal_score}",
                           _type=AttachmentType.String)

        attachments = [kmp_a, kms_a, ss_para_a, ssf_a, sed_a]

        if self.stable_features:
            # all score attachment
            k_para = k_marg_all_geo_para \
                if self.stable_features[0] in ['PUMA', 'FIPST'] \
                else k_marg_sector_para
            as_para_a = Attachment(name=f'K-Marginal Score in Each '
                                        + '- ' + self.stable_features[0],
                                   _data=k_para
                                   .replace(strs.STABLE_FEATURE, self.stable_features[0]),
                                   _type=AttachmentType.String)
            as_a = Attachment(name=None,
                              _data=self.stable_feature_worst_scores)

            attachments.extend([as_para_a, as_a])

        if self.stable_features and len(self.stable_features) > 1:
            for i, sf in enumerate(self.stable_features[1:]):
                # other stable feature score attachment
                k_para = k_marg_all_geo_para \
                    if self.stable_features[0] in ['PUMA', 'FIPST'] \
                    else k_marg_sector_para
                osf_para_a = Attachment(name=f'K-Marginal Score in Each '
                                             + '- ' + sf,
                                        _data=k_para
                                        .replace(strs.STABLE_FEATURE, sf),
                                        _type=AttachmentType.String)
                osf_a = Attachment(name=None,
                                   _data=self.other_stable_feature_worst_scores[i])

                attachments.extend([osf_para_a, osf_a])

        self.add_report_data(se_df,
                             int(min_frac * 100),
                             k_marg_synopsys_path)
        kmarg_sum_pkt = UtilityScorePacket('K-Marginal Synopsys',
                                           None,
                                           attachments)

        self.r_ui_d.add(kmarg_sum_pkt)

    def add_report_data(self,
                        subsample_comparison: pd.DataFrame,
                        subsample_equivalent: int,
                        output_directory: Path):
        k_marg_rd = dict()  # k marginal synopsys report data

        # add k-marginal subsample and deidentified data scores to json report
        k_marg_rd['stable_feature_scores'] = \
            relative_path(save_data_frame(pd.DataFrame(self.stable_feature_worst_scores),
                                          output_directory,
                                          'scores'))

        k_marg_rd['subsample_error_comparison'] = \
            relative_path(save_data_frame(subsample_comparison,
                                          output_directory,
                                          'err_comparison'))
        k_marg_rd['sub_sampling_percent_equivalent'] = (
            int(subsample_equivalent * 100))
        k_marg_rd['k_marginal_score'] = self.kmarginal_score

        self.rd.add('k_marginal', {
            "k_marginal_synopsys": k_marg_rd
        })

    def add_breakdown_to_ui(self):
        if len(self.worst_kmarginal_attachments) == 0:
            return
        kmarg_det_pkt = UtilityScorePacket(f'Breakdown of {self.stable_features[0]} with least fidelity',
                                           None,
                                           self.worst_kmarginal_attachments)
        self.r_ui_d.add(kmarg_det_pkt)

