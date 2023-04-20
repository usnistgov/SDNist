from sdnist.meta_report.common import *
from sdnist.meta_report.comparisons import BaseComparison

UNIQUE_EXACT_MATCHES = "unique_exact_matches"
RECORDS_MATCHED_IN_TARGET_DATA = "records matched in target data"
PERCENT_RECORDS_MATCHED_IN_TARGET_DATA = "percent records matched in target data"
UNIQUE_TARGET_RECORDS = "unique target records"
PERCENT_UNIQUE_TARGET_RECORDS = "percent unique target records"


unique_exact_match_para = "This is a count of unique records in the target data that were exactly reproduced " \
                          "in the deidentified data. Because these records were unique outliers in the " \
                          "target data, and they still appear unchanged in the deidentified data, " \
                          "they are potentially vulnerable to reidentification."
class UniqueExactMatchesComparison(BaseComparison):
    def __init__(self, reports: Dict, report_dir: Path, label_keys: List[str],
                 filters: Dict[str, List], data_dict: Dict[str, any]):
        super().__init__(reports, report_dir, label_keys, filters, data_dict)

        self.out_dir = Path(report_dir, 'unique_exact_matches_comparison')
        if not self.out_dir.exists():
            self.out_dir.mkdir(parents=True)
        # unique exact matches differences in each report
        self.r_uem = dict()
        self._create()

    def _create(self):
        for r_name, (report, report_path) in self.reports.items():
            rec_matched = report[UNIQUE_EXACT_MATCHES][RECORDS_MATCHED_IN_TARGET_DATA]
            perc_rec_matched = report[UNIQUE_EXACT_MATCHES][PERCENT_RECORDS_MATCHED_IN_TARGET_DATA]
            u_t_matched = report[UNIQUE_EXACT_MATCHES][UNIQUE_TARGET_RECORDS]
            perc_u_t_matched = report[UNIQUE_EXACT_MATCHES][PERCENT_UNIQUE_TARGET_RECORDS]

            labels = report[strs.DATA_DESCRIPTION][DEID][LABELS]
            f_set = labels[FEATURE_SET]
            features = sorted(report[strs.DATA_DESCRIPTION][FEATURES])
            _, features = self.compute_feature_space(f_set, features)
            target_dataset = labels[TARGET_DATASET]

            # variant label
            unq_v_label = dict()
            for lk in self.label_keys:
                if lk in labels and lk not in self.filters:
                    if lk == EPSILON:
                        unq_v_label[f'{lk}:{labels[lk]}'] = ''
                    elif lk == VARIANT_LABEL:
                        lbl_str = labels[lk]
                        if len(lbl_str):
                            unq_v_label[f'\n{lbl_str}'] = ''
                    else:
                        lbl_str = str(labels[lk])
                        if len(lbl_str):
                            unq_v_label[f'{lbl_str}'] = ''
            v_label = ' | '.join(unq_v_label.keys())

            if target_dataset not in self.r_uem:
                self.r_uem[target_dataset] = dict()

            if (f_set, str(features)) not in self.r_uem[target_dataset]:
                self.r_uem[target_dataset][(f_set, str(features))] = [[v_label, rec_matched,
                                                       perc_rec_matched,
                                                       u_t_matched,
                                                       perc_u_t_matched]]
            else:
                self.r_uem[target_dataset][(f_set, str(features))].append([v_label,
                                                           rec_matched,
                                                           perc_rec_matched,
                                                           u_t_matched,
                                                           perc_u_t_matched])

    def ui_data(self, m_ui_data: ReportUIData):
        attachments = []
        id_cnt = 0
        a_group_id = id_cnt
        id_cnt += 1
        para_a = Attachment(name=None,
                            _data=unique_exact_match_para,
                            group_id=a_group_id,
                            _type=AttachmentType.String)
        attachments.append(para_a)

        for t_dataset_name, f_set_uem in self.r_uem.items():
            for f_set, uem_data in f_set_uem.items():
                a_group_id = id_cnt
                id_cnt += 1
                d_table = [{'Variant': v_label,
                            'Records Matched In Target Data': rec_matched,
                            'Percent Records Matched In Target Data': perc_rec_matched}
                            for v_label, rec_matched, perc_rec_matched, _, _ in uem_data]
                u_t_matched = uem_data[0][3]
                perc_u_t_matched = uem_data[0][4]

                filter_str = [f'{str(k).capitalize()}: {v[0]}'
                              for k, v in self.filters.items()]
                filter_str = ', '.join(filter_str)
                f_set_str = f'Feature Set: {f_set[0]} | Target Dataset: {t_dataset_name}, ' \
                            f'{filter_str}' if len(filter_str) > 0 \
                    else f' Feature Set: {f_set[0]} | Target Dataset: {t_dataset_name}'
                features_space_size, features = self.compute_feature_space(f_set[0], f_set[1])

                head_a = Attachment(name=f_set_str,
                                       _data=f'Features: {features}<br>'
                                             f'Feature Space (possible combinations): '
                                             f'{format(features_space_size, ",")}',
                                       group_id=a_group_id,
                                       _type=AttachmentType.String)
                para_a = Attachment(name=None,
                                    _data=f"Number of Unique Records in Target Data: {u_t_matched} ({perc_u_t_matched}%)",
                                    group_id=a_group_id,
                                    _type=AttachmentType.String)
                table_a = Attachment(name=None,
                                     _data=d_table,
                                     group_id=a_group_id,
                                     _type=AttachmentType.Table)
                attachments.extend([head_a, para_a, table_a])
        scr_pck = ScorePacket(metric_name='Unique Exact Matches Comparison',
                              attachment=attachments)
        scr_pck.evaluation_type = EvaluationType.Meta
        m_ui_data.add(scr_pck)