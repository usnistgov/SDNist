from pathlib import Path
from typing import Dict, List
from dataclasses import dataclass, field

import pandas as pd

from sdnist.report import ReportData, FILE_DIR
from sdnist.report.report_data import \
    DatasetType, DataDescriptionPacket
from sdnist.load import \
    TestDatasetName, load_dataset, build_name

import sdnist.strs as strs

import sdnist.utils as u


@dataclass
class Dataset:
    synthetic_filepath: Path
    test: TestDatasetName = TestDatasetName.NONE
    data_root: Path = Path('sdnist_toy_data')
    download: bool = True

    challenge: str = strs.CENSUS
    target_data: pd.DataFrame = field(init=False)
    target_data_path: Path = field(init=False)
    synthetic_data: pd.DataFrame = field(init=False)
    schema: Dict = field(init=False)

    def __post_init__(self):
        # load target dataset which is used to score synthetic dataset
        self.target_data, params = load_dataset(
            challenge=strs.CENSUS,
            root=self.data_root,
            download=self.download,
            public=False,
            test=self.test,
            format_="csv",
            data_name="toy-data"
        )
        self.target_data_path = build_name(
            challenge=strs.CENSUS,
            root=self.data_root,
            public=False,
            test=self.test,
            data_name="toy-data"
        )
        self.schema = params[strs.SCHEMA]

        # add config packaged with data and also the config package with sdnist.report package
        config_1 = u.read_json(Path(self.target_data_path.parent, 'config.json'))
        config_2 = u.read_json(Path(FILE_DIR, 'config.json'))
        self.config = {**config_1, **config_2}
        self.data_dict = u.read_json(Path(self.target_data_path.parent, 'data_dictionary.json'))
        self.features = self.target_data.columns.tolist()

        drop_features = self.config[strs.DROP_FEATURES] \
            if strs.DROP_FEATURES in self.config else []
        self.features = self._fix_features(drop_features,
                                           self.config[strs.K_MARGINAL][strs.GROUP_FEATURES])

        # load synthetic dataset
        dtypes = {feature: desc["dtype"] for feature, desc in self.schema.items()}
        if str(self.synthetic_filepath).endswith('.csv'):
            self.synthetic_data = pd.read_csv(self.synthetic_filepath, dtype=dtypes, index_col=0)
        elif str(self.synthetic_filepath).endswith('.parquet'):
            self.synthetic_data = pd.read_parquet(self.synthetic_filepath)
        self.synthetic_data = self.synthetic_data[self.target_data.columns]

        self.target_data = self.target_data[self.features]
        self.synthetic_data = self.synthetic_data[self.features]
        if strs.BINS in self.config:
            bins_ranges = self.config[strs.BINS]
        else:
            bins_ranges = dict()
        self.d_target_data = u.discretize(self.target_data, self.schema, bins_ranges)
        self.d_synthetic_data = u.discretize(self.synthetic_data, self.schema, bins_ranges)

        self.config[strs.CORRELATION_FEATURES] = \
            self._fix_corr_features(self.features,
                                    self.config[strs.CORRELATION_FEATURES])

    def _fix_features(self, drop_features: List[str], group_features: List[str]):
        t_d_f = []
        for f in drop_features:
            if f not in ['PUMA'] + group_features:
                t_d_f.append(f)
        drop_features = t_d_f

        res_f = list(set(self.features).difference(drop_features))

        return res_f

    @staticmethod
    def _fix_corr_features(features, corr_features):
        unavailable_features = set(corr_features).difference(features)
        return list(set(corr_features).difference(unavailable_features))


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
