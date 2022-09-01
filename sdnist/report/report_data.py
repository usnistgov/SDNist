import json
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from sdnist.report import REPORTS_DIR


class DatasetType(Enum):
    Target = "target"
    Synthetic = "synthetic"


class EvaluationType(Enum):
    Utility = "utility"
    Privacy = "privacy"


class AttachmentType(Enum):
    Table = "table"
    ImageLinks = "image_links"
    String = 'string'


@dataclass
class Attachment:
    name: Optional[str]
    _data: any
    _type: AttachmentType = field(default=AttachmentType.Table)

    @property
    def data(self) -> Dict[str, any]:
        d = self._data
        return {
            'name': self.name,
            'data': d,
            'type': self._type.value
        }


@dataclass
class ScorePacket:
    metric_name: str
    score: Optional[float] = None
    attachment: List[Attachment] = field(default_factory=list)
    evaluation_type = None

    @property
    def data(self) -> Dict[str, any]:
        d = {
            'metric_name': self.metric_name,
            'scores': self.score,
            'attachments': [a.data for a in self.attachment]
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

    @property
    def data(self) -> Dict[str, any]:
        return {'filename': self.filename,
                'records': self.records,
                'features': self.columns}


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
                for f,fd, ft, hn
                in zip(self.features, self.feature_desc, self.feature_types, self.has_nans)]


@dataclass
class ReportUIData:
    output_directory: Path = REPORTS_DIR
    # dictionary containing description of datasets
    datasets: Dict[str, DataDescriptionPacket] = field(default_factory=dict, init=False)
    feature_desc: Dict[str, any] = field(default_factory=dict, init=False)
    # list containing ScorePacket objects
    scores: List[ScorePacket] = field(default_factory=list, init=False)

    def add(self, score_packet: ScorePacket):
        self.scores.append(score_packet)

    def add_data_description(self,
                             dataset_type: DatasetType,
                             data_description: DataDescriptionPacket):
        self.datasets[dataset_type.value] = data_description

    def add_feature_description(self,
                                features: List[str],
                                feature_desc: List[str],
                                dtypes: List[str],
                                has_nans: List[bool]):
        dp = FeatureDescriptionPacket(features=features,
                                      feature_desc=feature_desc,
                                      feature_types=dtypes,
                                      has_nans=has_nans)
        self.feature_desc["Data Features"] = dp

    @property
    def data(self) -> Dict[str, any]:
        d = dict()
        d['data_description'] = dict()
        for d_type_name, d_desc in self.datasets.items():
            d['data_description'][d_type_name] = d_desc.data

        for k, v in self.feature_desc.items():
            d['data_description'][k] = v.data

        d[EvaluationType.Utility.value] = []
        d[EvaluationType.Privacy.value] = []

        for s_pkt in self.scores:
            if s_pkt.evaluation_type == EvaluationType.Utility:
                d[EvaluationType.Utility.value].append(s_pkt.data)
            elif s_pkt.evaluation_type == EvaluationType.Privacy:
                d[EvaluationType.Privacy.value].append(s_pkt.data)
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
        self.data[metric_name] = data

    def save(self):
        o_path = Path(self.output_directory, 'report.json')

        d = self.data
        with open(o_path, 'w') as f:
            json.dump(d, f, indent=4)

