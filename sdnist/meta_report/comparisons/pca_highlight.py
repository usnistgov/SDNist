import matplotlib.pyplot as plt
import matplotlib.image as mpimg
plt.style.use('seaborn-deep')

from sdnist.meta_report.common import *
from sdnist.meta_report.comparisons import BaseComparison

PCA = 'pca'
HIGHLIGHTED_PLOTS = 'highlighted_plots'

pca_para = "This is another approach for visualizing where the distribution of the " \
           "deidentified data has shifted away from the target data. " \
           "In this approach, we begin by using " \
           "<a href='https://en.wikipedia.org/wiki/Principal_component_analysis'>" \
           "Principle Component Analysis</a> " \
           "to find a way of representing the target data in a lower dimensional " \
           "space (in 5 dimensions rather than the full 22 " \
           "dimensions of the original feature space). Descriptions " \
           "of these new five dimensions (components) are " \
           "given in the components table; the components will change " \
           "depending on which target data set you’re using. " \
           "Five dimensions are better than 22, but we actually want to " \
           "get down to two dimensions so we can plot the data " \
           "on simple (x,y) axes– the plots below show the data " \
           "across each possible pair combination of our five components. " \
           "You can compare how the shapes change between the target data " \
           "and the deidentified data, and consider what that might mean in light " \
           "of the component definitions. This is a relatively new visualization " \
           "metric that was introduced by the " \
           "<a href='https://pages.nist.gov/HLG-MOS_Synthetic_Data_Test_Drive/submissions.html#ipums_international'>" \
           "IPUMS International team</a> " \
           "during the HLG-MOS Synthetic Data Test Drive."

class PCAHighlightComparison(BaseComparison):
    def __init__(self, *args, **kargs):
        super().__init__(*args, **kargs)
        self.out_dir = Path(self.report_dir, 'pca_highlight_comparison')

        if not self.out_dir.exists():
            self.out_dir.mkdir(parents=True)

        self.r_pca_h = dict()
        self._create()

    def _create(self):
        for r_name, (report, report_path) in self.reports.items():
            highlight_path = report[PCA][HIGHLIGHTED_PLOTS]
            pca_highlight_path = highlight_path[list(highlight_path.keys())[0]][1]
            tar_pca_highlight_path = highlight_path[list(highlight_path.keys())[0]][0]
            pca_highlight_path = Path(report_path, pca_highlight_path)
            tar_pca_highlight_path = Path(report_path, tar_pca_highlight_path)
            labels = report[strs.DATA_DESCRIPTION][DEID][LABELS]
            f_set = labels[FEATURE_SET_NAME]
            features = report[strs.DATA_DESCRIPTION][FEATURES]
            # _, features = self.compute_feature_space(f_set, features)
            target_dataset = labels[TARGET_DATASET]

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

            if target_dataset not in self.r_pca_h:
                self.r_pca_h[target_dataset] = dict()

            if (f_set, str(features)) not in self.r_pca_h[target_dataset]:
                self.r_pca_h[target_dataset][(f_set, str(features))] = [['Target Data', tar_pca_highlight_path]]
                self.r_pca_h[target_dataset][(f_set, str(features))].append([v_label, pca_highlight_path])
            else:
                self.r_pca_h[target_dataset][(f_set, str(features))].append([v_label, pca_highlight_path])

        for t_dataset_name, f_set_data in self.r_pca_h.items():
            for f_set, pca_h_data in f_set_data.items():
                plot_save_path = Path(self.out_dir, f'{t_dataset_name}-{f_set[0]}.png')
                self.plot(pca_h_data, plot_save_path)
                pca_h_data.append(plot_save_path)

    def plot_paths(self):
        return {t_dataset_name: {f_set: v[-1] for f_set, v in f_set_data.items()}
                for t_dataset_name, f_set_data in self.r_pca_h.items()}

    def plot(self, pca_highlight_data: List, plot_save_path: Path):
        n_reports = len(pca_highlight_data)
        n_rows = math.ceil(n_reports / 4)
        n_cols = 4
        fig, ax = plt.subplots(n_rows, n_cols, figsize=(3.2 * n_cols, 3.2 * n_rows))
        # pca_highlight_data[1:] = sorted(pca_highlight_data[1:], key=lambda x: x[0])
        for i, (v_label, pca_highlight_path) in enumerate(pca_highlight_data):
            r_i = i // n_cols
            r_j = i % n_cols
            if n_rows > 1:
                ax_i = ax[r_i, r_j]
            else:
                ax_i = ax[i]
            img = mpimg.imread(pca_highlight_path)
            ax_i.imshow(img)
            ax_i.set_title(v_label, fontsize=10, fontweight='bold')
            # ax_i.axis('off')
            ax_i.set_xticks([])
            ax_i.set_yticks([])
            # remove axes spines
            for d in ['top', 'bottom', 'left', 'right']:
                ax_i.spines[d].set_visible(False)
            if r_j == 0:
                ax_i.set_ylabel('PC-1')
            ax_i.set_xlabel('PC-0')

        for i in range(n_rows):
            for j in range(n_cols):
                idx = i * n_cols + j
                if idx >= n_reports:
                    if n_rows > 1:
                        ax[i, j].axis('off')
                    else:
                        ax[j].axis('off')
        fig.subplots_adjust(hspace=1.3, wspace=0.5)
        # fig.subplots_adjust(right=2.5, bottom=0.2, top=0.8)
        fig.tight_layout()
        fig.savefig(plot_save_path, bbox_inches='tight')
        plt.close(fig)

    def ui_data(self, m_ui_data: ReportUIData):
        p_paths = self.plot_paths()
        attachments = []
        id_cnt = 0
        a_group_id = id_cnt
        id_cnt += 1
        para_a = Attachment(name=None,
                            _data=pca_para,
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
        scr_pck = ScorePacket(metric_name='PCA Comparison: (PC-0 & PC-1) with highlighted MSP-N (AGE < 15)',
                              attachment=attachments)
        scr_pck.evaluation_type = EvaluationType.Meta
        m_ui_data.add(scr_pck)