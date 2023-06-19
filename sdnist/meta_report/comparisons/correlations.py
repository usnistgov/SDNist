import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
plt.style.use('seaborn-deep')

from sdnist.meta_report.common import *
from sdnist.meta_report.comparisons import BaseComparison

CORRELATIONS = "Correlations"
PEARSON_CORRELATION_DIFFERENCE = "pearson correlation difference"
CORRELATION_DIFFERENCE = "correlation_difference"

pear_corr_para = "The <a href='https://en.wikipedia.org/wiki/Pearson_correlation_coefficient'>Pearson Correlation</a> " \
                 "difference was a popular utility metric during the <a href='https://pages.nist.gov/HLG-MOS_Synthetic_Data_Test_Drive/index.html'>" \
                 "HLG-MOS Synthetic Data Test Drive</a>. Note that darker highlighting indicates pairs of features whose " \
                 "correlations were not well preserved by the deidentified data."


class CorrelationComparison(BaseComparison):
    def __init__(self, *args, **kargs):
        super().__init__(*args, **kargs)
        self.out_dir = Path(self.report_dir, 'correlation_comparison')

        if not self.out_dir.exists():
            self.out_dir.mkdir(parents=True)

        # correlation differences in each report
        self.r_corr = dict()
        self._create()

    def _create(self):
        for r_name, (report, report_path) in self.reports.items():
            # features = report['features']
            corr_path = report[CORRELATIONS] \
                [PEARSON_CORRELATION_DIFFERENCE][CORRELATION_DIFFERENCE]
            corr_path = Path(report_path, corr_path)
            corr_df = pd.read_csv(corr_path, index_col=0)
            labels = report[strs.DATA_DESCRIPTION][DEID][LABELS]
            f_set = labels[FEATURE_SET_NAME]
            features = sorted(report[strs.DATA_DESCRIPTION][FEATURES])
            target_dataset = labels[TARGET_DATASET]
            # _, features = self.compute_feature_space(f_set, features, target_dataset)


            # variant label
            unq_v_label = dict()
            for lk in self.label_keys:
                if lk in labels and lk not in self.filters:
                    if lk == EPSILON:
                        unq_v_label[f'e:{labels[lk]}'] = ''
                    elif lk == VARIANT_LABEL:
                        lbl_str = labels[lk]
                        if len(lbl_str):
                            lbl_str = lbl_str if len(lbl_str) < 30 else lbl_str[:30] + '...'
                            unq_v_label[f'\n{lbl_str}'] = ''
                    elif lk == 'submission number':
                        lbl_str = labels[lk]
                        unq_v_label[f's #[{lbl_str}]'] = ''
                    else:
                        lbl_str = str(labels[lk])
                        if len(lbl_str):
                            unq_v_label[f'{lbl_str}'] = ''
            v_label = ' | '.join(unq_v_label.keys())
            # v_label = labels[VARIANT]
            print('In Corr: ', report_path.parts[-2:], v_label, target_dataset)
            if target_dataset not in self.r_corr:
                self.r_corr[target_dataset] = dict()

            if (f_set, str(features)) not in self.r_corr[target_dataset]:
                self.r_corr[target_dataset][(f_set, str(features))] = [[v_label, corr_df]]
            else:
                self.r_corr[target_dataset][(f_set, str(features))].append([v_label, corr_df])

        # create combined correlation plots
        for t_dataset_name, f_set_data in self.r_corr.items():
            for f_set, corr_data in f_set_data.items():
                plot_save_path = Path(self.out_dir, f'{t_dataset_name}-{f_set[0]}.png')
                self.plot(corr_data, plot_save_path)
                corr_data.append(plot_save_path)


    def plot_paths(self):
        return {t_dataset_name: {f_set: v[-1] for f_set, v in f_set_data.items()}
                for t_dataset_name, f_set_data in self.r_corr.items()}

    def plot(self, correlations_data: List, plot_save_path: Path):
        n_reports = len(correlations_data)
        n_rows = math.ceil(n_reports / 4)
        n_cols = 4
        n_features = len(correlations_data[0][1].columns)
        if n_features < 12:
            cell_size = 0.36
        elif n_features >= 12 and n_features < 16:
            cell_size = 0.30
        else:
            cell_size = 0.20

        fig_width = cell_size * n_features * n_cols
        fig_height = cell_size * n_features * n_rows
        print(fig_width, fig_height, n_features, n_cols, n_rows, plot_save_path)
        fig, ax = plt.subplots(n_rows, n_cols + 1, figsize=(fig_width, fig_height))
        # correlations_data = sorted(correlations_data, key=lambda x: x[0])
        v_max = 0.15
        ax_c = None
        for i, (v_label, corr_df) in enumerate(correlations_data):
            r_i = i // n_cols
            r_j = i % n_cols
            if n_rows > 1:
                ax_i = ax[r_i, r_j]
            else:
                ax_i = ax[i]

            corr_df = corr_df.iloc[::-1]
            corr_df = corr_df.round(2)
            ax_c = ax_i.pcolor(corr_df, cmap='Blues', vmin=0, vmax=v_max)
            if r_j > 0:
                ax_i.set_yticks([float(t)+0.5 for t in range(corr_df.shape[0])],
                                [''] * len(corr_df.index))
            if r_j == 0:
                ax_i.set_yticks([float(t)+0.5 for t in range(corr_df.shape[0])],
                                corr_df.index)

            ax_i.set_xticks([float(t)+0.5 for t in range(corr_df.shape[1])],
                            corr_df.columns, rotation=90)
            if n_features > 16:
                ax_i.tick_params(axis='both', which='major', labelsize=9)
            else:
                ax_i.tick_params(axis='both', which='major', labelsize=10)
            ax_i.set_title(v_label, fontdict={'fontsize': 10, 'fontweight': 'bold'})

        for i in range(n_rows):
            j = n_cols if n_rows > 1 else -1
            if i == n_rows - 1:
                temp_j = n_reports % n_cols
                j = temp_j if temp_j > 0 else j
            if n_rows > 1:
                ax_i = ax[i, j]
            else:
                ax_i = ax[j]
            fmt = lambda x, pos: '{:.2}'.format(x)

            fig.colorbar(ax_c, ax=ax_i, orientation='vertical', pad=.05, fraction=1, format=FuncFormatter(fmt))
            ax_i.axis('off')
            if j > -1 and  j != n_cols:
                j = n_cols
                if n_rows > 1:
                    ax_i = ax[i, j]
                else:
                    ax_i = ax[j]
                cb = fig.colorbar(ax_c, ax=ax_i, orientation='vertical', pad=.05, fraction=1)
                cb.remove()
                ax_i.axis('off')



        for j in range(n_cols):
            idx = n_reports + n_rows
            last_j = idx % (n_cols + 1)

            if 0 < last_j <= j:
                if n_rows > 1:
                    ax[n_rows-1, j].axis('off')
                else:
                    ax[j].axis('off')

        fig.tight_layout()
        plt.savefig(plot_save_path, bbox_inches='tight')
        plt.close()


    def ui_data(self, m_ui_data: ReportUIData):
        p_paths = self.plot_paths()

        attachments = []
        id_cnt = 0
        a_group_id = id_cnt
        id_cnt += 1
        para_a = Attachment(name=None,
                            _data=pear_corr_para,
                            group_id=a_group_id,
                            _type=AttachmentType.String)
        attachments.append(para_a)
        for t_dataset_name, f_set_paths in p_paths.items():
            for f_set, p_path in f_set_paths.items():
                a_group_id = id_cnt
                id_cnt += 1

                rel_p_path = u.relative_path(p_path)
                filter_str = [f'{str(k).capitalize()}: {v[0]}'
                              for k, v in self.filters.items()]
                filter_str = ', '.join(filter_str)
                f_set_str = f'Feature Set: {f_set[0]} | Target Dataset: {t_dataset_name}, ' \
                            f'{filter_str}' if len(filter_str) > 0 \
                    else f' Feature Set: {f_set[0]} | Target Dataset: {t_dataset_name}'
                features_space_size, features = self.compute_feature_space(f_set[0], f_set[1], t_dataset_name)

                head_a = Attachment(name=f_set_str,
                                    _data=f'Features: {features}<br>'
                                             f'Feature Space (possible combinations): '
                                             f'{format(features_space_size, ",")}',
                                    group_id=a_group_id,
                                    _type=AttachmentType.String)
                plot_a = Attachment(name=None,
                                    _data=[{strs.IMAGE_NAME: p_path.stem, strs.PATH: rel_p_path}],
                                    group_id=a_group_id,
                                    _type=AttachmentType.ImageLinks)
                attachments.extend([head_a, plot_a])

        scr_pck = ScorePacket(metric_name='Correlation Comparison',
                              attachment=attachments)
        scr_pck.evaluation_type = EvaluationType.Meta

        m_ui_data.add(scr_pck)
