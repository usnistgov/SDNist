import pandas as pd
from pathlib import Path

import sdnist.strs as strs
from sdnist.metrics.pca import PCAMetric
from sdnist.report import Dataset
from sdnist.report.report_data import \
    ReportData, ReportUIData, UtilityScorePacket, Attachment, AttachmentType

from sdnist.utils import *

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
           "depending on which target data set you're using. " \
           "Five dimensions are better than 22, but we actually want to " \
           "get down to two dimensions so we can plot the data " \
           "on simple (x,y) axes the plots below show the data " \
           "across each possible pair combination of our five components. " \
           "You can compare how the shapes change between the target data " \
           "and the deidentified data, and consider what that might mean in light " \
           "of the component definitions. This is a relatively new visualization " \
           "metric that was introduced by the " \
           "<a href='https://pages.nist.gov/HLG-MOS_Synthetic_Data_Test_Drive/submissions.html#ipums_international'>" \
           "IPUMS International team</a> " \
           "during the HLG-MOS Synthetic Data Test Drive."
pca_para_2 = "All of the plots below (for both the target data and " \
             "the deidentified data) use the principle component axes " \
             "taken from the target data (listed in the table). Effectively, " \
             "we're looking at the data from the exact same angles in " \
             "both sets of plots so we can easily compare the target " \
             "data and the deidentified data with respect to those angles."

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

        # List of Attachments to be used by the
        # report UI
        self.attachments = []

        self._create()

    def _create(self):
        # json report data for pca metric
        pca_rd = dict()

        # Path to the directory where pca metric results are
        # dumped
        o_path = Path(self.r_ui_d.output_directory, 'pca')
        create_path(o_path)

        pca_m = PCAMetric(self.dataset.t_target_data,
                          self.dataset.t_synthetic_data)

        pca_m.compute_pca()
        plot_paths = pca_m.plot(o_path)

        # acpp: all components pair-plot paths
        acpp_tar, acpp_deid = plot_paths[strs.ALL_COMPONENTS_PAIR_PLOT]

        # Add json report data for pca
        pca_rd = {
         "components_eigenvector": relative_path(
             save_data_frame(pca_m.comp_df,
                             o_path,
                             'components_eigenvector')),
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
        pca_highlight_head_a = Attachment(name=None,
                                          _data=f'h3PCA Queries',
                                          _type=AttachmentType.String)
        pca_highlight_para_a = Attachment(name=None,
                                _data=pca_highlight_para,
                                _type=AttachmentType.String)
        highlighted_attachments = []
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

        self.attachments.extend([pca_para_a, pca_para_a2, pca_tt_a, pca_plot_a, pca_highlight_head_a, pca_highlight_para_a]
                                + highlighted_attachments)

    def add_to_ui(self):
        if len(self.attachments):
            self.r_ui_d.add(UtilityScorePacket("PCA",
                                               None,
                                               self.attachments))

