from typing import Optional, List
from pathlib import Path

import pandas as pd
import json

# Check to see which target dataset is used in the deid data
# These are string check which are applied on the deid data (csv or json)
# path
# "in" checks if the string is in the path
# "starts_with" checks if the path starts with the string
# "ends_with" checks if the path ends with the string

checks = {
    "ma2019": {
        "in": ['_ma_', '-ma-', 'ma2019', 'ma2018'],
        "starts_with": ['ma_', 'ma-', 'ma2019_', 'ma2019-', 'ma2018_', 'ma2018-'],
        "ends_with": ['_ma', '-ma', '_ma2019', '-ma2019', '_ma2018', '-ma2018']
    },
    "tx2019": {
        "in": ['_tx_', '-tx-', 'tx2019', 'tx2018'],
        "starts_with": ['tx_', 'tx-', 'tx2019_', 'tx2019-', 'tx2018_', 'tx2018-'],
        "ends_with": ['_tx', '-tx', '_tx2019', '-tx2019', '_tx2018', '-tx2018']
    },
    "national2019": {
        "in": ['_na_', '-na-', 'na2019', '_national_', '-national-', 'national2019'],
        "starts_with": ['na_', 'na-', 'national_', 'national-', 'na2019_', 'na2019-', 'national2019_', 'national2019-'],
        "ends_with": ['_na', '-na', '_national', '-national', '_na2019', '-na2019', '_national2019', '-national2019']
    }
}


class TargetData:
    def __init__(self, root_dir: Optional[Path] = None):
        self.root_dir = root_dir
        self.target_paths = {
            'ma2019': Path(self.root_dir, 'massachusetts', 'ma2019.csv'),
            'tx2019': Path(self.root_dir, 'texas', 'tx2019.csv'),
            'national2019': Path(self.root_dir, 'national', 'national2019.csv'),
            'ma2018': Path(self.root_dir, 'massachusetts', 'ma2018.csv'),
            'tx2018': Path(self.root_dir, 'texas', 'tx2018.csv'),
            'national2018': Path(self.root_dir, 'national', 'national2018.csv'),
        }

    def get(self,
            target_name: str,
            features: Optional[List[str]] = None):

        if target_name in self.target_paths:
            df_path = self.target_paths[target_name]
            df = pd.read_csv(df_path)
            df = df.loc[:, ~df.columns.str.startswith('Unnamed')]
            df = df.reset_index(drop=True)

            df_schema_path = df_path.parent / f'{df_path.stem}.json'
            with open(df_schema_path, 'r') as f:
                schema = json.load(f)

            d_dict_path = self.root_dir / 'data_dictionary.json'
            with open(d_dict_path, 'r') as f:
                d_dict = json.load(f)

            if features:
                all_feats = df.columns.tolist()
                avail_feats = list(set(features).intersection(set(all_feats)))
                df = df[avail_feats]

            return df, schema, d_dict
        else:
            return None, None, None

    @staticmethod
    def deduce_target_data(deid_data_path: str) -> \
            Optional[str]:
        """
        From a given deid_data_path (csv or json) what target dataset
        is used in the deid data.
        """
        for k, v in checks.items():
            for i in v['in']:
                if i in deid_data_path:
                    return k
                for p in Path(deid_data_path).parts[:-1]:
                    if i in p or k[:-4] in p:
                        return k
            for i in v['starts_with']:
                if deid_data_path.startswith(i):
                    return k
            for i in v['ends_with']:
                if deid_data_path.endswith(i):
                    return k
        return None
