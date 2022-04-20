import json
from typing import List, Dict
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class DatasetType(Enum):
    Target = "target"
    Synthetic = "synthetic"


class AttachmentType(Enum):
    Table = "table"


@dataclass
class Attachment:
    name: str
    _data: any
    _type: AttachmentType = field(default=AttachmentType.Table)

    @property
    def data(self) -> Dict[str, any]:
        return {
            'name': self.name,
            'data': self._data,
            'type': self._type.value
        }


@dataclass
class ScorePacket:
    metric_name: str
    score: int
    attachment: List[Attachment] = field(default_factory=list)

    @property
    def data(self) -> Dict[str, any]:
        return {
            'metric_name': self.metric_name,
            'scores': self.score,
            'attachments': [a.data for a in self.attachment]
        }


@dataclass
class DataDescriptionPacket:
    filename: str
    records: int
    columns: int

    @property
    def data(self) -> Dict[str, any]:
        return {'filename': self.filename,
                'records': self.records,
                'columns': self.columns}


class ReportData:
    # dictionary containing description of datasets
    datasets: Dict[str, DataDescriptionPacket] = dict()
    # list containing ScorePacket objects
    scores: List[ScorePacket] = []

    def __init__(self, output_path: Path):
        self.output_path = output_path

    def add(self, score_packet: ScorePacket):
        self.scores.append(score_packet)

    def add_data_description(self,
                             dataset_type: DatasetType,
                             data_description: DataDescriptionPacket):
        self.datasets[dataset_type.value] = data_description

    @property
    def data(self) -> Dict[str, any]:
        d = dict()
        d['data_description'] = dict()
        for d_type_name, d_desc in self.datasets.items():
            d['data_description'][d_type_name] = d_desc.data

        d['evaluation'] = []
        for s_pkt in self.scores:
            d['evaluation'].append(s_pkt.data)

        return d

    def save(self):
        d = self.data
        with open(self.output_path, 'w') as f:
            json.dump(d, f, indent=4)


