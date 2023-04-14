from typing import Dict
from pathlib import Path

import pandas as pd

from sdnist.metrics.regression import LinearRegressionMetric
from sdnist.report import Dataset
from sdnist.report.report_data import \
    ReportData, ReportUIData, UtilityScorePacket, Attachment, AttachmentType
import sdnist.strs as strs
from sdnist.utils import *


def compute_linear_regression(target: pd.DataFrame,
                              synthetic: pd.DataFrame,
                              output_dir: Path,
                              data_dictionary: Dict):
    tar = target
    syn = synthetic
    o_dir = output_dir

    reg_m = LinearRegressionMetric(tar, syn, data_dictionary, o_dir)

    reg_m.compute()
    reg_m_paths = reg_m.plots()

    return reg_m, reg_m_paths


# linear regression UI report paragraphs
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
        "<li>PINCP_DECILE: The individual's income rank relative to other incomes from "
        "their state, discretized into ten equal-width range bins. "
        "This helps us account for differences in cost of living across the country. "
        "If an individual makes a moderate income but lives in a lower income area, "
        "they may have a high value for PINCP_DECILE indicating that they have a high "
        "income for their state. </li>"
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


class LinearRegressionReport:
    REQUIRED_FEATURES = ['EDU', 'PINCP_DECILE']
    OTHER_REQ_FEATURES = ['RAC1P', 'SEX']
    AIANNH = 'American Indian, Alaskan Native and Native Hawaiians (AIANNH)'

    def __init__(self, dataset: Dataset, ui_data: ReportUIData, report_data: ReportData):
        # required features
        req_f = self.REQUIRED_FEATURES + self.OTHER_REQ_FEATURES
        # available features
        available_f = list(set(req_f).intersection(set(dataset.target_data.columns.tolist())))

        # take subset of target and deidentified data and convert
        # features to numerical values
        self.t = to_num(dataset.target_data[available_f].copy())
        self.s = to_num(dataset.c_synthetic_data[available_f].copy())
        # data dictionary
        self.d_dict = dataset.data_dict
        self.r_ui_d = ui_data  # report ui data
        self.rd = report_data

        self.labels = {
            'total_population': ['Total Population', []],
            'white_men': ['White Men', [['RAC1P', [1]], ['SEX', [1]]]],
            'white_women': ['White Women', [['RAC1P', [1]], ['SEX', [2]]]],
            'black_men': ['Black Men', [['RAC1P', [2]], ['SEX', [1]]]],
            'black_women': ['Black Women', [['RAC1P', [2]], ['SEX', [2]]]],
            'asian_men': ['Asian Men', [['RAC1P', [6]], ['SEX', [1]]]],
            'asian_women': ['Asian Women', [['RAC1P', [6]], ['SEX', [2]]]],
            'aiannh_men': [f'{self.AIANNH} Men', [['RAC1P', [3, 4, 5, 7]], ['SEX', [1]]]],
            'aiannh_women': [f'{self.AIANNH} Women', [['RAC1P', [3, 4, 5, 7]], ['SEX', [2]]]]
        }
        self.eval_data = {k: [] for k in self.labels.keys()}
        self.attachments = []
        self._create()

    def _create(self):
        # compute linear regression and pair counts
        if not self.can_compute():
            return
        o_path = Path(self.r_ui_d.output_directory, 'linear_regression')
        create_path(o_path)
        for k, v in self.labels.items():
            if k != 'total_population' and not self.can_compute_demographics():
                continue
            k_o_path = Path(o_path, k)
            create_path(k_o_path)
            ts = df_filter(self.t, v[1])
            ss = df_filter(self.s, v[1])
            reg, image_path = compute_linear_regression(ts, ss, k_o_path,
                                                        {k: self.d_dict[k]
                                                            for k in self.REQUIRED_FEATURES})
            self.eval_data[k] = [reg, image_path]

        # create report attachments
        for p in lr_paragraphs:
            para_a = Attachment(name=None,
                                _data=p,
                                _type=AttachmentType.String)
            self.attachments.append(para_a)

        for k, v in self.eval_data.items():
            if not len(v):
                continue
            reg, img_path = v[0], v[1]
            self.rd.add('linear_regression', {k: reg.report_data})
            rel_reg_paths = ["/".join(list(p.parts)[-3:])
                             for p in img_path]

            # attachment data
            a_data = {
                "para": [["heading", 'Target Data'],
                         ["text", f'{reg.ts.shape[0]} records, '
                                  f'{round(reg.ts.shape[0]/self.t.shape[0] * 100, 2)}% of adult (>15) data'],
                         ["text", f'Regression: {reg.t_slope} slope,'
                                  f' {reg.t_intercept} intercept'],
                         ["heading", 'Deidentified Data'],
                         ["text", f'{reg.ss.shape[0]} records, '
                                  f'{round(reg.ss.shape[0]/self.s.shape[0] * 100, 2)}% of adult (>15) data'],
                         ["text", f'Regression: {reg.s_slope} slope, '
                                  f'{reg.s_intercept} intercept']],
                "image": [{strs.IMAGE_NAME: Path(p).stem, strs.PATH: p}
                          for p in rel_reg_paths]
            }
            reg_m_a = Attachment(name=self.labels[k][0],
                                 _data=a_data,
                                 _type=AttachmentType.ParaAndImage)
            self.attachments.append(reg_m_a)

    def can_compute(self):
        return set(self.REQUIRED_FEATURES).issubset(set(self.s.columns.tolist()))

    def can_compute_demographics(self):
        return set(self.OTHER_REQ_FEATURES).issubset(set(self.s.columns.tolist()))

    def add_to_ui(self):
        if len(self.attachments):
            self.r_ui_d.add(UtilityScorePacket("Linear Regression",
                                               None,
                                               self.attachments))
