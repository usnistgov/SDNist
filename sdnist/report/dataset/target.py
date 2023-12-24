from typing import Tuple, Dict
from pathlib import Path
import pandas as pd

from sdnist.load import \
    TestDatasetName, load_dataset, build_name

from sdnist.load import DEFAULT_DATASET
import sdnist.strs as strs
import sdnist.utils as u


class TargetLoader:
    def __init__(self,
                 data_root_dir: Path,
                 download: bool = True):
        self.root = data_root_dir
        self.download = download
        self.dataset = None
        self.dataset_path = None
        self.schema = None

        self.check_exist()
        self.data_dict = self.load_data_dict()
        self.mappings = self.load_data_mappings()
        self.features = list(self.data_dict.keys())


    def check_exist(self):
        d, dp, sch = self.get_dataset(TestDatasetName.ma2019)
        del d
        del dp
        del sch

    def load_dataset(self, dataset_name: TestDatasetName):
        self.dataset, self.dataset_path, self.schema = \
            self.get_dataset(dataset_name)
        return self.dataset, self.dataset_path, self.schema

    def get_dataset(self, dataset_name: TestDatasetName) \
            -> Tuple[pd.DataFrame, Path, Dict]:
        dataset, params = load_dataset(
            challenge=strs.CENSUS,
            root=self.root,
            download=True,
            public=False,
            test=dataset_name,
            format_="csv"
        )

        dataset_path = Path(
            build_name(
                challenge=strs.CENSUS,
                root=self.root,
                public=False,
                test=dataset_name,
        ))

        schema = params[strs.SCHEMA]

        return dataset, dataset_path, schema

    def load_data_dict(self):
        dict_path = Path(self.root, 'data_dictionary.json')
        data_dict = u.read_json(dict_path)
        return data_dict

    def load_data_mappings(self):
        mappings_path = Path(self.root, 'mappings.json')
        mappings = u.read_json(mappings_path)
        return mappings


    def get_all_datasets(self) -> pd.DataFrame:
        data_names = [TestDatasetName.national2019,
                      TestDatasetName.ma2019,
                      TestDatasetName.tx2019]
        dfs = []
        for dn in data_names:
            df, _, _ = self.get_dataset(dn)
            dfs.append(df)

        return pd.concat(dfs)

    def is_deid_csv(self, df: pd.DataFrame) -> bool:
        """
        Checks if a dataframe is deidentified csv
        file created from the target data
        """
        cols = set(df.columns.to_list())
        if len(cols.intersection(set(self.features))):
            return True
        return False
















