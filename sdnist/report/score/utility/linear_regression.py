from typing import Dict
from pathlib import Path

import pandas as pd

from sdnist.metrics.regression import LinearRegressionMetric
from sdnist.report import Dataset
from sdnist.report.report_data import \
    ReportData, ReportUIData, UtilityScorePacket, Attachment, AttachmentType, \
    DatasetType, DataDescriptionPacket
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


class LinearRegressionReport:
    REQUIRED_FEATURES = ['EDU', 'PINCP_DECILE', 'RAC1P', 'SEX']

    def __init__(self, dataset: Dataset, ui_data: ReportUIData, report_data: ReportData):
        self.t = to_num(dataset.target_data[self.REQUIRED_FEATURES].copy())
        self.s = to_num(dataset.synthetic_data[self.REQUIRED_FEATURES].copy())
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
            'aian_men': ['AIAN Men', [['RAC1P', [3, 4, 5, 7]], ['SEX', [1]]]],
            'aian_women': ['AIAN Women', [['RAC1P', [3, 4, 5, 7]], ['SEX', [2]]]]
        }

        self.eval_data = {k: [] for k in self.labels.keys()}
        self.attachments = []
        self._create()

    def _create(self):
        # compute linear regression and pair counts
        o_path = Path(self.r_ui_d.output_directory, 'linear_regression')
        create_path(o_path)
        for k, v in self.labels.items():
            k_o_path = Path(o_path, k)
            create_path(k_o_path)
            ts = df_filter(self.t, v[1])
            ss = df_filter(self.s, v[1])
            reg, image_path = compute_linear_regression(ts, ss, k_o_path,
                                                        {k: self.d_dict[k]
                                                            for k in self.REQUIRED_FEATURES[:2]})
            self.eval_data[k] = [reg, image_path]

        # create report attachments
        reg_para_a = Attachment(name=None,
                                _data='This is regression metric',
                                _type=AttachmentType.String)
        self.attachments.append(reg_para_a)
        for k, v in self.eval_data.items():
            reg, img_path = v[0], v[1]
            self.rd.add('linear_regression', {k: reg.report_data})
            rel_reg_paths = ["/".join(list(p.parts)[-3:])
                               for p in img_path]

            reg_m_a = Attachment(name=self.labels[k][0],
                                 _data={"para": [
                                            ["heading", "Target Data Regression Line"],
                                            ["text", f'Slope: {reg.t_slope}, Intercept: {reg.t_intercept}'],
                                            ["heading", "Synthetic Data Regression Line"],
                                            ["text", f'Slope: {reg.s_slope}, Intercept: {reg.s_intercept}']
                                        ],
                                        "image": [{strs.IMAGE_NAME: Path(p).stem, strs.PATH: p}
                                                  for p in rel_reg_paths]
                                        },
                                 _type=AttachmentType.ParaAndImage)
            self.attachments.append(reg_m_a)

    def add_to_ui(self):
        self.r_ui_d.add(UtilityScorePacket("Linear Regression",
                                           None,
                                           self.attachments))
