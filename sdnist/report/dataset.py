from pathlib import Path
from typing import Dict, List
from dataclasses import dataclass, field

import pandas as pd
import numpy as np

from sdnist.report import ReportData, FILE_DIR
from sdnist.report.report_data import \
    DatasetType, DataDescriptionPacket
from sdnist.load import \
    TestDatasetName, load_dataset, build_name

import sdnist.strs as strs

import sdnist.utils as u


def transform(data, schema):
    # replace categories with codes
    # replace N: NA with -1 for categoricals
    # replace N: NA with mean for numericals
    data = data.copy()
    for c in data.columns.tolist():
        desc = schema[c]
        if "values" in desc:
            if "has_null" in desc:
                null_val = desc["null_value"]
                data[c] = data[c].replace(null_val, -1)
        elif "min" in desc:
            if "has_null" in desc:
                null_val = desc["null_value"]
                nna_mask = data[~data[c].isin(['N'])].index  # not na mask
                if c == 'PINCP':
                    data[c] = data[c].replace(null_val, 999999)
                elif c == 'POVPIP':
                    data[c] = data[c].replace(null_val, 999)
        if c == 'PUMA':
            data[c] = data[c].astype(pd.CategoricalDtype(desc["values"])).cat.codes
            if "N" in desc['values']:
                data[c] = data[c].replace(0, -1)
        else:
            data[c] = pd.to_numeric(data[c])
        print(c, sorted(data[c].unique()))
    return data


def percentile_rank(data, features):
    data = data.copy()
    for c in features:
        if c not in data.columns:
            continue
        nna_mask = data[~data[c].isin(['N'])].index  # not na mask
        d_temp = pd.DataFrame(pd.to_numeric(data.loc[nna_mask, c]).astype(int), columns=[c])
        # print(d_temp.shape)
        # print(d_temp.dtypes)
        # print(d_temp.columns.tolist())
        if c == 'POVPIP':
            # print(sorted(d_temp[c].unique()))
            d_temp['rank'] = d_temp[c].rank(pct=True, numeric_only=True).apply(lambda x: round(x, 2))
            tdf = d_temp.groupby(by=c)[c].size().reset_index(name='count_target')
            # for r, g in d_temp.groupby(by=['rank']):
            #     print(r, sorted(g[c].unique()))
            # for i, r in tdf.sort_values(by=[c], ascending=False).iterrows():
            #     print(r[c], r['count_target'], r['rank'])
            # print(sorted(d_temp[c].rank(pct=True, numeric_only=True).apply(lambda x: round(x, 2)).unique()))
        data.loc[nna_mask, c] = d_temp[c]\
            .rank(pct=True).apply(lambda x: int(20 * x) if x < 1 else 19)
    return data


def add_bin_for_NA(data, reference_data, features):
    d = data
    rd = reference_data

    for c in features:
        if c not in data.columns:
            continue
        na_mask = rd[rd[c].isin(['N'])].index
        if len(na_mask):
            d.loc[na_mask, c] = -1
    return d


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
        common_columns = list(set(self.synthetic_data.columns.tolist()).intersection(
            set(self.target_data.columns.tolist())
        ))
        self.target_data = self.target_data[common_columns]
        self.synthetic_data = self.synthetic_data[common_columns]

        ind_features = [c for c in self.target_data.columns.tolist()
                        if c.startswith('IND_')]
        self.features = list(set(self.features).difference(set(ind_features)))
        self.features = list(set(self.features).intersection(list(common_columns)))
        # raw data
        self.target_data = self.target_data[self.features]
        self.synthetic_data = self.synthetic_data[self.features]

        # transformed data
        self.t_target_data = transform(self.target_data, self.schema)
        print()
        print('SYNTHETIC')
        print()
        self.t_synthetic_data = transform(self.synthetic_data, self.schema)

        # binned data
        numeric_features = ['AGEP', 'POVPIP', 'PINCP']
        self.d_target_data = percentile_rank(self.target_data, numeric_features)
        self.d_synthetic_data = percentile_rank(self.synthetic_data, numeric_features)

        self.d_target_data = add_bin_for_NA(self.d_target_data,
                                            self.target_data, numeric_features)
        self.d_synthetic_data = add_bin_for_NA(self.d_synthetic_data,
                                               self.synthetic_data,
                                               numeric_features)
        # print(sorted(self.d_synthetic_data['POVPIP'].unique()))
        # print(sorted(self.d_synthetic_data['AGEP'].unique()))
        non_numeric = [c for c in self.features
                       if c not in numeric_features]

        self.d_target_data[non_numeric] = self.t_target_data[non_numeric]
        self.d_synthetic_data[non_numeric] = self.t_synthetic_data[non_numeric]
        # print('AGEP', self.d_synthetic_data['AGEP'].unique())
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
