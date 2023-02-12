from typing import Tuple, Dict
from pathlib import Path
import pandas as pd

from sdnist.metrics.inconsistency import Inconsistencies
from sdnist.report import Dataset
from sdnist.report.report_data import \
    ReportData, ReportUIData, UtilityScorePacket, Attachment, AttachmentType, \
    DatasetType, DataDescriptionPacket

from sdnist.utils import *


class InconsistenciesReport:
    def __init__(self, dataset: Dataset, ui_data: ReportUIData, report_data: ReportData):
        self.s = dataset.synthetic_data
        self.r_ui_d = ui_data
        self.rd = report_data
        self.ic = None

        self.attachments = []

        self._create()

    def _create(self):
        o_path = Path(self.r_ui_d.output_directory, 'inconsistencies')
        create_path(o_path)
        self.ic = Inconsistencies(self.s, o_path)
        self.ic.compute()

        # add json report data
        self.rd.add('inconsistencies', self.ic.report_data)
        # add ui report data
        a_sum_h = Attachment(name='Summary',
                             _data={
                                 'table': self.ic.stats['summary'],
                                 'size': 60
                             },
                             _type=AttachmentType.WideTable)
        self.attachments.append(a_sum_h)
        for k, v in self.ic.report_help.items():
            # attachment header
            ah = Attachment(name=v[0],
                            _data=v[1],
                            _type=AttachmentType.String)
            self.attachments.append(ah)
            for stat in self.ic.stats[k]:
                name = stat[0]
                desc = stat[1]
                features = stat[2]
                s_data = stat[3]
                s_example = stat[4]

                an = Attachment(name=None,
                                _data=f'h4{name}: {desc}',
                                _type=AttachmentType.String)
                a_data = Attachment(name='--no-brake--',
                                    _data=f'Highlight-{s_data}',
                                    _type=AttachmentType.String)
                a_ex_txt = Attachment(name=None,
                                      _data='Example Record:',
                                      _type=AttachmentType.String)

                # example data PREVIOUS VERSION, FEATURES VERTICAL
                # def build_row_dict(r, add_min=False):
                #     res = {'Feature': str(r[0]),
                #            'Value': int(r[1]) if str(r[1]).isnumeric() else str(r[1])}
                #     if add_min:
                #         res['min_idx'] = True
                #     return res
                #
                # e_d = [build_row_dict(r, True)
                #        if r[0] in features else build_row_dict(r)
                #        for i, r in s_example.iterrows()]`

                def to_serializable(value):
                    v = value
                    return int(v) if str(v).isnumeric() else str(v)

                # example data FEATURES HORIZONTAL
                # sort dataframe columns by column name
                s_example = s_example.reindex(sorted(s_example.columns), axis=1)
                e_d = [{c: to_serializable(s_example[c].values[0])
                       for c in s_example.columns}]
                e_d = {'table': e_d,
                       'highlight': {'columns': features},
                       'size': 98}  # size in percent of screen width

                a_example = Attachment(name=None,
                                       _data=e_d,
                                       _type=AttachmentType.WideTable,
                                       dotted_break=True)
                self.attachments.extend([an, a_data, a_ex_txt, a_example])

    def add_to_ui(self):
        self.r_ui_d.add(UtilityScorePacket('Inconsistencies',
                                           None,
                                           self.attachments))

