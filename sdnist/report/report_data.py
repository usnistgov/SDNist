import json
import time
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import datetime

from sdnist.version import __version__
from sdnist.report import REPORTS_DIR
import sdnist.strs as strs


class DatasetType(Enum):
    Target = "target"
    Synthetic = "synthetic"


class EvaluationType(Enum):
    Utility = "utility"
    Privacy = "privacy"
    Meta = "meta"
    Motivation = "motivation"
    Observations = "observations"


class AttachmentType(Enum):
    Table = "table"
    WideTable = 'wide_table'
    ImageLinks = "image_links"
    ImageLinksHorizontal = "image_links_horizontal"
    String = 'string'
    ParaAndImage = 'para_and_image'



@dataclass
class Attachment:
    name: Optional[str]
    _data: any
    group_id: int = -1
    _type: AttachmentType = field(default=AttachmentType.Table)
    dotted_break: bool = field(default=False)

    def __post_init(self):
        if self.group_id == -1:
            self.group_id = int(time.time() * 100)

    @property
    def data(self) -> Dict[str, any]:
        d = self._data
        return {
            'name': self.name,
            'data': d,
            'type': self._type.value,
            'dotted_break': self.dotted_break
        }


@dataclass
class ScorePacket:
    metric_name: str
    score: Optional[float] = None
    attachment: List[Attachment] = field(default_factory=list)
    evaluation_type = None

    @property
    def data(self) -> Dict[str, any]:
        attachments = dict()
        for a in self.attachment:
            if a.group_id in attachments:
                attachments[a.group_id].append(a.data)
            else:
                attachments[a.group_id] = [a.data]
        d = {
            'metric_name': self.metric_name,
            'scores': self.score,
            'attachments': attachments
        }
        if self.score is None:
            del d['scores']
        return d


class UtilityScorePacket(ScorePacket):
    evaluation_type: EvaluationType = EvaluationType.Utility


class PrivacyScorePacket(ScorePacket):
    evaluation_type: EvaluationType = EvaluationType.Privacy


@dataclass
class DataDescriptionPacket:
    filename: str
    records: int
    columns: int
    labels: Dict = field(default_factory=dict)
    validations: Dict = field(default_factory=dict)

    @property
    def data(self) -> Dict[str, any]:
        dd_dict = dict()   # data description dict
        d = {'filename': self.filename,
             'records': self.records,
             'features': self.columns}
        d_list = []  # data list
        for k, v in d.items():
            d_list.append({
                'Property': str(k).title(),
                'Value': v
            })
        dd_dict['data'] = d_list

        if 'label' in self.labels:
            dd_dict['label'] = self.labels['label']
        elif len(self.labels):
            l_list = []  # labels data list
            for k, v in self.labels.items():
                l_list.append({
                    'Label Name': str(k).title(),
                    'Label Value': v
                })
            dd_dict['labels'] = l_list

        v_list = []
        dd_dict['validations'] = v_list
        if self.validations is not None:
            if 'values_out_of_bound' in self.validations:
                for k, v in self.validations['values_out_of_bound'].items():
                    v = str(v) if len(v) <= 5 \
                        else str(v + [f' and other {len(v) - 5} values'])
                    v = v[1:-1]
                    v_list.append({
                        'Dropped Feature': k,
                        'Out of Bound Values': v
                    })
        dd_dict['validations'] = v_list

        return dd_dict


@dataclass
class FeatureDescriptionPacket:
    features: List[str]
    feature_types: List[str]
    feature_desc: List[str]
    has_nans: List[bool]

    @property
    def data(self) -> List[Dict[str, any]]:
        return [{"Feature Name": f,
                 "Feature Description": fd,
                 "Feature Type": ft,
                 "Feature Has 'N' (N/A) values?": hn}
                for f, fd, ft, hn
                in zip(self.features, self.feature_desc, self.feature_types, self.has_nans)]


@dataclass
class ReportUIData:
    output_directory: Path = REPORTS_DIR
    # dictionary containing description of datasets
    datasets: Dict[str, List[DataDescriptionPacket]] = field(default_factory=dict, init=False)
    feature_desc: Dict[str, any] = field(default_factory=dict, init=False)
    # list containing ScorePacket objects
    scores: List[ScorePacket] = field(default_factory=list, init=False)
    key_val_pairs: Dict[str, any] = field(default_factory=dict, init=False)

    def add(self, score_packet: ScorePacket):
        self.scores.append(score_packet)
    def add_key_val(self, key: str, val: any):
        self.key_val_pairs[key] = val

    def add_data_description(self,
                             dataset_type: DatasetType,
                             data_description: DataDescriptionPacket):
        if dataset_type.value in self.datasets:
            self.datasets[dataset_type.value].append(data_description)
        else:
            self.datasets[dataset_type.value] = [data_description]

    def add_feature_description(self,
                                features: List[str],
                                feature_desc: List[str],
                                dtypes: List[str],
                                has_nans: List[bool]):
        dp = FeatureDescriptionPacket(features=features,
                                      feature_desc=feature_desc,
                                      feature_types=dtypes,
                                      has_nans=has_nans)
        self.feature_desc["Evaluated Data Features"] = dp

    @property
    def data(self) -> Dict[str, any]:
        d = dict()
        d['Created on'] = datetime.datetime.now().strftime("%B %d, %Y %H:%M:%S")
        d['version'] = __version__
        d[strs.DATA_DESCRIPTION] = dict()
        for d_type_name, d_desc in self.datasets.items():
            d[strs.DATA_DESCRIPTION][d_type_name] = [desc.data for desc in d_desc]

        for k, v in self.feature_desc.items():
            d[strs.DATA_DESCRIPTION][k] = v.data

        d[EvaluationType.Utility.value] = []
        d[EvaluationType.Privacy.value] = []
        d['comparisons'] = []
        d['motivation'] = []
        d['observations'] = []
        for k, v in self.key_val_pairs.items():
            d[k] = v

        for s_pkt in self.scores:
            if s_pkt.evaluation_type == EvaluationType.Utility:
                d[EvaluationType.Utility.value].append(s_pkt.data)
            elif s_pkt.evaluation_type == EvaluationType.Privacy:
                d[EvaluationType.Privacy.value].append(s_pkt.data)
            elif s_pkt.evaluation_type == EvaluationType.Meta:
                d['comparisons'].append(s_pkt.data)
            elif s_pkt.evaluation_type == EvaluationType.Motivation:
                d['motivation'].append(s_pkt.data)
            elif s_pkt.evaluation_type == EvaluationType.Observations:
                d['observations'].append(s_pkt.data)
            elif s_pkt.evaluation_type == None:
                d['Appendix'] = [s_pkt.data]
        return d

    def save(self, output_path: Optional[Path] = None):
        o_path = Path(self.output_directory, 'ui.json')

        if output_path:
            o_path = output_path

        d = self.data
        with open(o_path, 'w') as f:
            json.dump(d, f, indent=4)


@dataclass
class ReportData:
    output_directory: Path = REPORTS_DIR
    data: Dict[str, any] = field(default_factory=dict, init=False)

    def add(self, metric_name: str, data: Dict[str, any]):
        if metric_name not in self.data:
            self.data[metric_name] = data
        else:
            for k, v in data.items():
                self.data[metric_name][k] = v

    def save(self):
        o_path = Path(self.output_directory, 'report.json')

        d = self.data
        with open(o_path, 'w') as f:
            json.dump(d, f, indent=4)

