from typing import Tuple, Dict
from pathlib import Path
import pandas as pd

from sdnist.metrics.inconsistency import Inconsistencies
from sdnist.report import Dataset
from sdnist.report.report_data import \
    ReportData, ReportUIData, UtilityScorePacket, Attachment, AttachmentType

from sdnist.utils import *

ic_paragraphs = [
    "In real world tabular data, it's common for record features to have "
    "some deterministic, publicly known dependencies on each other: "
    "knowing someone's AGEP= 3 necessarily tells you something about "
    "their marital status, income and educational attainment. "
    "Different deidentification methods may be better or worse at "
    "automatically preserving these relationships. "
    "When they fail (ex: producing toddlers with PhDs) we say "
    "those records contain \"inconsistencies\". Our consistency "
    "check metric below is not exhaustive, we don't catch everything "
    "the way a production-grade system should, but this will give you "
    "a sense of how consistency is preserved for age, work and household "
    "features. Note that different deidentification approaches may do "
    "better or worse with different types of inconsistencies."
]


class InconsistenciesReport:
    """
    Helper class for creating UI and json report data for the inconsistencies found
    in the deidentified data.
    """

    def __init__(self, dataset: Dataset, ui_data: ReportUIData, report_data: ReportData):
        self.s = dataset.c_synthetic_data
        self.r_ui_d = ui_data
        self.rd = report_data
        self.ic = None

        self.attachments = []

        self._create()

    def _create(self):
        """
        Creates and arrange inconsistencies metrics data for the UI and json
        data evaluation report.
        """
        # path for storing report outputs related to inconsistency metric
        o_path = Path(self.r_ui_d.output_directory, 'inconsistencies')
        create_path(o_path)  # create path if does not already exist

        # initialize an instance of inconsistencies metric
        self.ic = Inconsistencies(self.s, o_path)
        self.ic.compute()  # compute inconsistencies in deidentified data

        # add inconsistencies stats and data to json report data
        self.rd.add('inconsistencies', self.ic.report_data)

        # create report attachments
        for p in ic_paragraphs:
            para_a = Attachment(name=None,
                                _data=p,
                                _type=AttachmentType.String)
            self.attachments.append(para_a)

        # --------- Add inconsistencies stats and dat to ui report data
        # UI attachment for summary of inconsistencies found in the deidentified data
        a_sum_h = Attachment(name='Summary',
                             _data={
                                 'table': self.ic.stats['summary'],
                                 'size': 60
                             },
                             _type=AttachmentType.WideTable)
        # add summary attachment to the UI report data
        self.attachments.append(a_sum_h)

        # -----------Add UI attachments for each of the inconsistency group: AGE, WORK and Housing
        for k, v in self.ic.report_help.items():
            # attachment header for inconsistency group
            ah = Attachment(name=v[0],
                            _data=v[1],
                            _type=AttachmentType.String)
            self.attachments.append(ah)

            # Create table attachment for each of the inconsistency found
            # in an inconsistency group
            for stat in self.ic.stats[k]:
                name = stat[0]
                desc = stat[1]
                features = stat[2]
                s_data = stat[3]
                s_example = stat[4]

                # Create attachment for inconsistency name and description
                an = Attachment(name=None,
                                _data=f'h4{name}: {desc}',
                                _type=AttachmentType.String)
                # Create attachment for number of violations by this inconsistency
                a_data = Attachment(name='--no-brake--',
                                    _data=f'Highlight-{s_data}',
                                    _type=AttachmentType.String)
                # Create a text attachment
                a_ex_txt = Attachment(name=None,
                                      _data='Example Record:',
                                      _type=AttachmentType.String)

                def to_serializable(value):
                    """convert pandas int to python int"""
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

                # Create a table attachment for displaying an example
                # of inconsistent record in the report UI.
                a_example = Attachment(name=None,
                                       _data=e_d,
                                       _type=AttachmentType.WideTable,
                                       dotted_break=True)
                self.attachments.extend([an, a_data, a_ex_txt, a_example])

    def add_to_ui(self):
        """
        Adds a UtilityScorePacket instance containing all the attachments with
        inconsistencies information to the UI report data.
        """
        self.r_ui_d.add(UtilityScorePacket('Inconsistencies',
                                           None,
                                           self.attachments))

