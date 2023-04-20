import random
import copy
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import matplotlib as mpl
from matplotlib.colors import Normalize
plt.style.use('seaborn-deep')

from sdnist.meta_report.common import *
from sdnist.meta_report.comparisons import BaseComparison

LINEAR_REGRESSION = "linear_regression"
BLACK_WOMEN = 'black_women'
TARGET_COUNTS = 'target_counts'
TARGET_DEIDENTIFIED_COUNTS_DIFFERENCE = 'target_deidentified_counts_difference'
TARGET_REGRESSION_SLOPE_AND_INTERCEPT = "target_regression_slope_and_intercept"
DEIDENTIFIED_REGRESSION_SLOPE_AND_INTERCEPT = "deidentified_regression_slope_and_intercept"

lr_paragraphs = [
        "Linear regression is a fundamental data analysis technique that condenses "
        "a multi-dimensional data distribution  down to a one dimensional (line) representation. "
        "It works by finding the line that sits in the 'middle' of the data, in some sense-- "
        "<a href='https://en.wikipedia.org/wiki/Linear_regression#Formulation'>"
        "it minimizes the total distance between the points of the data and the line.</a> "
        "There are more advanced forms of regression, but here we're focusing on the "
        "simplest case-- we fit a simple straight line to the data, getting "
        "the slope and y-intercept value of that line.",

        "For this metric we're just looking at data from adults (AGEP > 15) and "
        "we're only considering the distribution of the data across two features:"
        "<ul>"
        "<li>EDU: The highest education level this individual has attained, ranging "
        "from 1 (elementary school) to 12 (PhD). See Appendix of this report for "
        "the full list of code values.</li>"
        "<li>PINCP_DECILE: The individual's income decile relative to their PUMA. "
        "This helps us account for differences in cost of living across the country. "
        "If an individual makes a moderate income but lives in a very low income area, "
        "they may have a high value for PINCP_DECILE indicating that they have a high "
        "income for their PUMA).</li>"
        "</ul>",

        "The basic idea is that higher values of EDU should lead to higher values of "
        "PINCP_DECILE, and this is broadly true. However, it is known that the relationship "
        "between EDU and PINCP_DECILE is different for different demographic subgroups. "
        "The heatmaps in the left column below show the density distribution of the true "
        "data for each subgroup, normalized by education category (so the density values "
        "in each column sum to 1; note that when a cell in the heatmap contains too few "
        "people (< 20 ), it is left blank; its not expected that the deidentified data will "
        "match the original distribution precisely). The regression line is drawn in "
        "red over the heatmap, so you can see the relationship between the target data "
        "distribution and its linear regression analysis. In the right column for each "
        "subgroup we show how the deidentified data's regression line compares to the "
        "target data's regression line, along with a heatmap of the density differences between the two "
        "distributions. Redder areas are where the deidentified data has created too many "
        "people, bluer areas are where it's created too few people.",

        "We've broken this metric down into demographic subgroups so we can see not only how "
        "well the privacy techniques preserve the overall relationship between these features, "
        "but also whether they preserve how that overall relationship is built up from the "
        "different relationships that hold at each major demographic subgroup. "
        "It's important that deidentification techniques preserve these distinct "
        "subgroup patterns for analysis."
]
class LinearRegressionComparison(BaseComparison):
    def __init__(self, reports: Dict, report_dir: Path, label_keys: List[str],
                 filters: Dict[str, List], data_dict: Dict[str, any],
                 population_type: str):
        super().__init__(reports, report_dir, label_keys, filters, data_dict)
        self.pop_type = population_type
        self.out_dir = Path(report_dir, f'linear_regression_{self.pop_type}_comparison')

        if not self.out_dir.exists():
            self.out_dir.mkdir(parents=True)

        # linear regression in each report
        self.r_lr = dict()
        self._create()

    def _create(self):
        for r_name, (report, report_path) in self.reports.items():
            if 'linear_regression' not in report:
                continue
            lr_data = report['linear_regression']
            lr_data = lr_data[self.pop_type]
            tar_bw_density_path = lr_data[TARGET_COUNTS]

            deid_bw_density_path = lr_data[TARGET_DEIDENTIFIED_COUNTS_DIFFERENCE]
            tar_bw_density_path = Path(report_path, LINEAR_REGRESSION, tar_bw_density_path)
            deid_bw_density_path = Path(report_path, LINEAR_REGRESSION, deid_bw_density_path)
            tar_bw_df = pd.read_csv(tar_bw_density_path, index_col=0)
            deid_bw_df = pd.read_csv(deid_bw_density_path, index_col=0)

            tar_slope_intercept = lr_data[TARGET_REGRESSION_SLOPE_AND_INTERCEPT]
            deid_slope_intercept = lr_data[DEIDENTIFIED_REGRESSION_SLOPE_AND_INTERCEPT]

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
                            lbl_str = lbl_str if len(lbl_str) < 30 else lbl_str[:30] + '...'
                            unq_v_label[f'\n{lbl_str}'] = ''
                    else:
                        lbl_str = str(labels[lk])
                        if len(lbl_str):
                            unq_v_label[f'{lbl_str}'] = ''
            v_label = ' | '.join(unq_v_label.keys())

            if target_dataset not in self.r_lr:
                self.r_lr[target_dataset] = dict()

            if (f_set, str(features)) not in self.r_lr[target_dataset]:
                self.r_lr[target_dataset][(f_set, str(features))] = [['Target Data', tar_bw_df, tar_slope_intercept, tar_slope_intercept]]
                self.r_lr[target_dataset][(f_set, str(features))].append([v_label, deid_bw_df,
                                         tar_slope_intercept, deid_slope_intercept])
            else:
                self.r_lr[target_dataset][(f_set, str(features))].append([v_label, deid_bw_df,
                                         tar_slope_intercept, deid_slope_intercept])

        for t_dataset_name, f_set_data in self.r_lr.items():
            for f_set, lr_data in f_set_data.items():
                plot_save_path = Path(self.out_dir, f'{t_dataset_name}-{f_set[0]}.png')
                self.plot(lr_data, plot_save_path)
                lr_data.append(plot_save_path)

    def plot_paths(self):
        return {t_dataset_name: {f_set: v[-1] for f_set, v in f_set_data.items()}
                for t_dataset_name, f_set_data in self.r_lr.items()}

    def plot(self, linear_regression_data: List, plot_save_path: Path):
        n_reports = len(linear_regression_data)
        n_rows = math.ceil(n_reports / 4)
        n_cols = 4
        fig, ax = plt.subplots(n_rows, n_cols + 1, figsize=(5 * n_cols, 3.2 * n_rows))
        ax_c = None
        df_c = None
        line1 = None
        line2 = None
        for i, (v_label, d_df, tar_slope_intercept, deid_slope_intercept) \
            in enumerate(linear_regression_data):
            r_i = i // n_cols
            r_j = i % n_cols
            if n_rows > 1:
                ax_i = ax[r_i, r_j]
            else:
                ax_i = ax[i]

            vals = [random.randint(0, 12) for i in range(5000)]
            t_intercept = tar_slope_intercept[1]
            t_slope = tar_slope_intercept[0]
            s_intercept = deid_slope_intercept[1]
            s_slope = deid_slope_intercept[0]
            r_tx_df = pd.DataFrame([[_ + 0.5, t_intercept + t_slope * (_ + 0.5)]
                                    for _ in vals], columns=['x', 'y'])

            r_tx_df = r_tx_df[(r_tx_df['y'] >= 0) & (r_tx_df['y'] <= 10)]
            if i == 0:
                df_c = d_df.copy()
                apc0 = ax_i.pcolor(d_df, cmap='rainbow', vmin=0, vmax=0.5)
                fig.colorbar(apc0, ax=ax_i)
                ax_i.plot(r_tx_df['x'],
                         r_tx_df['y'], color='red', label='Target')
                ax_i.set_xlabel('EDU')
                ax_i.set_ylabel('PINCP_DECILE')
            else:
                apc1 = ax_i.pcolor(d_df, cmap='PuOr', vmin=-0.3, vmax=0.3)
                ax_c = apc1
                fig.colorbar(apc1, ax=ax_i)

                r_sx_df = pd.DataFrame([[_ + 0.5, s_intercept + s_slope * (_ + 0.5)]
                                        for _ in vals], columns=['x', 'y'])
                r_sx_df = r_sx_df[(r_sx_df['y'] >= 0) & (r_sx_df['y'] <= 10)]
                line1, = ax_i.plot(r_tx_df['x'],
                         r_tx_df['y'], color='red', label='Target')
                line2, = ax_i.plot(r_sx_df['x'],
                         r_sx_df['y'], color='green', label='Deid.')

            ax_i.set_title(v_label, fontsize=10, fontweight='bold')

        for i in range(n_rows):
            j = n_cols if n_rows > 1 else -1
            if i == n_rows - 1:
                temp_j = n_reports % n_cols
                j = temp_j if temp_j > 0 else j
            if n_rows > 1:
                ax_i = ax[i, j]
            else:
                ax_i = ax[j]
            if j == n_cols:
                v_min = 2
                v_max = 20
                norm = Normalize(v_min, v_max)
                cmap = cm.get_cmap('Blues')
                # temp fix reduce axes width by adding a colorbar and then removing it.
                cb = fig.colorbar(mpl.cm.ScalarMappable(norm=norm, cmap=cmap),
                                  ax=ax_i, orientation='vertical', pad=.05, fraction=1)
                cb.remove()
            ax_i.legend(handles=[line1, line2], loc='center left', title='Regression')
            ax_i.axis('off')
            if j != n_cols:
                j = n_cols
                if n_rows > 1:
                    ax_i = ax[i, j]
                else:
                    ax_i = ax[j]
                ax_i.set_visible(False)

        for j in range(n_cols):
            idx = n_reports + n_rows
            last_j = idx % (n_cols + 1)

            if 0 < last_j <= j:
                if n_rows > 1:
                    ax[n_rows-1, j].axis('off')
                else:
                    ax[j].axis('off')

        # for i in range(n_rows):
        #     for j in range(n_cols):
        #         idx = i * n_cols + j
        #         if idx >= n_reports:
        #             if n_rows > 1:
        #                 ax[i, j].axis('off')
        #             else:
        #                 ax[j].axis('off')

        plt.tight_layout()
        fig.subplots_adjust(right=0.88)
        plt.savefig(plot_save_path, bbox_inches='tight')
        plt.close()

    def ui_data(self, m_ui_data: ReportUIData):
        p_paths = self.plot_paths()

        attachments = []
        id_cnt = 0
        a_group_id = id_cnt
        id_cnt += 1
        for p in lr_paragraphs:
            a_group_id = id_cnt
            id_cnt += 1
            para_a = Attachment(name=None,
                                _data=p,
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
                features_space_size, features = self.compute_feature_space(f_set[0], f_set[1])

                head_a = Attachment(name=f_set_str,
                                       _data=f'Features: {features}<br>'
                                             f'Feature Space (possible combinations): '
                                             f'{format(features_space_size, ",")}',
                                       group_id=a_group_id,
                                       _type=AttachmentType.String)
                plot_a =  Attachment(name=None,
                                       _data=[{strs.IMAGE_NAME: p_path.stem, strs.PATH: rel_p_path}],
                                       group_id=a_group_id,
                                       _type=AttachmentType.ImageLinks)
                attachments.extend([head_a, plot_a])

        population = ' '.join([s.capitalize() for s in self.pop_type.split('_')])
        scr_pck = ScorePacket(metric_name=f'Regression Comparison: {population} Data',
                              attachment=attachments)
        scr_pck.evaluation_type = EvaluationType.Meta

        m_ui_data.add(scr_pck)