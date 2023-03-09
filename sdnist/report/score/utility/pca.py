import pandas as pd
from pathlib import Path

import strs
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
        tar_path, died_path = pca_m.plot(o_path)

        # Add json report data for pca
        pca_rd = {
         "components_eigenvector": relative_path(
             save_data_frame(pca_m.comp_df,
                             o_path,
                             'components_eigenvector')),
         "target_components": relative_path(
             save_data_frame(pca_m.t_pdf,
                             o_path,
                             'target_components')),
         "deidentified_components": relative_path(
             save_data_frame(pca_m.s_pdf,
                             o_path,
                             'deidentified_components')),
         "target_all_components_plot": relative_path(tar_path),
         "deidentified_all_components_plot": relative_path(died_path)
        }

        self.rd.add('pca', pca_rd)

        # create attachment objects for report UI data
        rel_pca_plot_paths = relative_path([tar_path, died_path])

        # pca paragraph attachment for report UI
        pca_para_a = Attachment(name=None,
                                _data=pca_para,
                                _type=AttachmentType.String)

        # pca feature contribution table attachment for report UI
        pca_tt_a = Attachment(name="Contribution of Features in Each Principal Component",
                              _data=pca_m.t_comp_data,
                              _type=AttachmentType.Table)

        pca_plot_a = Attachment(name=None,
                                _data=[{strs.IMAGE_NAME: Path(p).stem, strs.PATH: p}
                                       for p in rel_pca_plot_paths],
                                _type=AttachmentType.ImageLinks)

        self.attachments.extend([pca_para_a, pca_tt_a, pca_plot_a])

    def add_to_ui(self):
        if len(self.attachments):
            self.r_ui_d.add(UtilityScorePacket("PCA",
                                               None,
                                               self.attachments))

