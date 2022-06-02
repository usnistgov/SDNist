from pathlib import Path
from typing import Dict
from dataclasses import dataclass, field

import pandas as pd

from sdnist.report import ReportData
from sdnist.report.report_data import \
    DatasetType, DataDescriptionPacket
from sdnist.load import \
    TestDatasetName, load_dataset, build_name


@dataclass
class Dataset:
    synthetic_filepath: Path
    challenge: str
    public: bool = True
    test: TestDatasetName = TestDatasetName.NONE
    data_root: Path = Path('data')

    target_data: pd.DataFrame = field(init=False)
    target_data_path: Path = field(init=False)
    synthetic_data: pd.DataFrame = field(init=False)
    schema: Dict = field(init=False)

    def __post_init__(self):
        # load target dataset which is used to score synthetic dataset
        self.target_data, self.schema = load_dataset(
            challenge=self.challenge,
            root=self.data_root,
            download=True,
            public=self.public,
            test=self.test,
            format_="csv"
        )
        self.target_data_path = build_name(
            challenge=self.challenge,
            root=self.data_root,
            public=self.public,
            test=self.test
        )

        # load synthetic dataset
        dtypes = {feature: desc["dtype"] for feature, desc in self.schema.items()}
        self.synthetic_data = pd.read_csv(self.synthetic_filepath, dtype=dtypes, index_col=0)


def data_description(dataset: Dataset, report_data: ReportData) -> ReportData:
    ds = dataset
    rd = report_data

    rd.add_data_description(DatasetType.Target,
                            DataDescriptionPacket(ds.target_data_path.stem,
                                                  ds.target_data.shape[0],
                                                  ds.target_data.shape[1]))

    rd.add_data_description(DatasetType.Synthetic,
                            DataDescriptionPacket(ds.synthetic_filepath.stem,
                                                  ds.synthetic_data.shape[0],
                                                  ds.synthetic_data.shape[1]))

    return rd
