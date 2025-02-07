import sdnist.strs as strs
from sdnist.metrics.pca import PCAMetric
from sdnist.report.report_data import \
    ReportData, ReportUIData, UtilityScorePacket, Attachment, AttachmentType
from sdnist.report.dataset import Dataset
from sdnist.load import TestDatasetName
from sdnist.report.dataset.transform import transform_old
from sdnist.utils import *

pca_para = "This is another approach for visualizing where the distribution of the deidentified data has shifted away from the target data.  In this case we're directly comparing the shape of the two data distributions as two dimensional scatter plots.  Each point is a record in the data.  The goal of deidentified data is to recreate the same basic shape as the target data distribution, using different points (ie, with new or altered records).  If the fidelity of the deidentified data is bad, the shapes will be very different.  If the privacy is bad, the points will be the same."

pca_para_2 = "We use principal Component Analysis to reduce the full feature set of the original data down to these two-dimensional snapshots. Descriptions of the top five principal components are given in the components table; the components will change depending on which target data set you're using. The plots below show the data across every pair of components.  All of the plots below (for both the target data and the deidentified data) use the principal component axes taken from the target data. Effectively, we're looking at the data from the exact same angles in both sets of plots.  This visualization was introduced by the IPUMS International team during the HLG-MOS Synthetic Data Test Drive."

pca_highlight_para = "The queries below explore the PCA metric results in more detail " \
                     "by zooming in on a single component-pair panel and highlighting " \
                     "all individuals that satisfy a given constraint (such as MSP='N', " \
                     "individuals who are unmarried because they are children). " \
                     "If the deidentified data preserves the structure and feature " \
                     "correlations of the target data, the highlighted areas should have " \
                     "similar shape. "

class PCAReport:
    def __init__(self,
                 dataset: Dataset,
                 ui_data: ReportUIData,
                 report_data: ReportData):
        self.dataset = dataset
        # For holding report data to create
        # machine-readable json
        self.rd = report_data
        # For holding report data to create report UI
        self.r_ui_d = ui_data

        self.log_scale_continuous = self.get_log_scale_continuous()
        # List of Attachments to be used by the
        # report UI
        self.attachments = []

        self._create()

    def get_log_scale_continuous(self) -> bool:
        if ('pca' in self.dataset.config
                and 'log_scale_continuous_features' in self.dataset.config['pca']):
            return self.dataset.config['pca']['log_scale_continuous_features']
        return False

    def _create(self):
        # json report data for pca metric
        pca_rd = dict()

        # Path to the directory where pca metric results are
        # dumped
        o_path = Path(self.r_ui_d.output_directory, 'pca')
        create_path(o_path)
        if self.dataset.test == TestDatasetName.sbo_target:
            t_target = self.dataset.t_target_data
            t_synthetic = self.dataset.t_synthetic_data
        else:
            t_target = transform_old(self.dataset.c_target_data,
                                     self.dataset.data_dict)
            t_synthetic = transform_old(self.dataset.c_synthetic_data,
                                        self.dataset.data_dict)
        pca_m = PCAMetric(t_target,
                          t_synthetic,
                          self.dataset.continuous_features,
                          self.log_scale_continuous)

        pca_m.compute_pca()
        plot_paths = pca_m.plot(o_path)

        # acpp: all components pair-plot paths
        acpp_tar, acpp_deid = plot_paths[strs.ALL_COMPONENTS_PAIR_PLOT]

        # Add json report data for pca
        pca_rd = {
         "components_eigenvector": relative_path(
             save_data_frame(pca_m.comp_df,
                             o_path,
                             'eigenvecs')),
         "target_all_components_plot": relative_path(acpp_tar),
         "deidentified_all_components_plot": relative_path(acpp_deid),
         "highlighted_plots": {f'{k[0]}-{k[1]}-{k[2]}':
                                   [relative_path(v[0], 3), relative_path(v[1], 3)]
             for k, v in plot_paths[strs.HIGHLIGHTED].items()}
        }

        self.rd.add('pca', pca_rd)

        # create attachment objects for report UI data
        rel_pca_plot_paths = relative_path([acpp_tar, acpp_deid])

        # pca paragraph attachment for report UI
        pca_para_a = Attachment(name=None,
                                _data=pca_para,
                                _type=AttachmentType.String)
        pca_para_a2 = Attachment(name=None,
                                _data=pca_para_2,
                                _type=AttachmentType.String)
        # pca feature contribution table attachment for report UI
        t_d = {'table': pca_m.t_comp_data,
               'size': 80,
               'column_widths': {
                   0: 20,
                   1: 80,
               }}
        pca_tt_a = Attachment(name="Contribution of Features in Each Principal Component",
                              _data=t_d,
                              _type=AttachmentType.WideTable)

        pca_plot_a = Attachment(name=None,
                                _data=[{strs.IMAGE_NAME: Path(p).stem, strs.PATH: p}
                                       for p in rel_pca_plot_paths],
                                _type=AttachmentType.ImageLinksHorizontal)
        self.attachments.extend([pca_para_a, pca_para_a2, pca_tt_a, pca_plot_a])

        highlighted_attachments = []
        if len(plot_paths[strs.HIGHLIGHTED]):
            pca_highlight_head_a = Attachment(name=None,
                                              _data=f'h3PCA Queries',
                                              _type=AttachmentType.String)
            pca_highlight_para_a = Attachment(name=None,
                                    _data=pca_highlight_para,
                                    _type=AttachmentType.String)
            highlighted_attachments.extend([pca_highlight_head_a, pca_highlight_para_a])

        for k, v in plot_paths[strs.HIGHLIGHTED].items():
            name = k[1]
            desc = k[2]

            # highlighted attachment header
            h_a_h = Attachment(name=None,
                               _data=f'h4{name}: {desc}',
                               _type=AttachmentType.String)
            hcp_tar, hcp_deid = v
            rel_pca_plot_paths = relative_path([hcp_tar, hcp_deid], level=3)

            # highlighted attachment plots
            h_a_p = Attachment(name=None,
                               _data=[{strs.IMAGE_NAME: Path(p).stem, strs.PATH: p}
                                      for p in rel_pca_plot_paths],
                               _type=AttachmentType.ImageLinksHorizontal)
            highlighted_attachments.extend([h_a_h, h_a_p])

        if len(highlighted_attachments):
            self.attachments.extend(highlighted_attachments)


    def add_to_ui(self):
        if len(self.attachments):
            self.r_ui_d.add(UtilityScorePacket("PCA",
                                               None,
                                               self.attachments))

