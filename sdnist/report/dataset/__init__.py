import math
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, field
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

from sdnist.report import ReportUIData, FILE_DIR
from sdnist.report.report_data import \
    DatasetType, DataDescriptionPacket, ScorePacket, \
    Attachment, AttachmentType, ReportData
from sdnist.load import \
    TestDatasetName, load_dataset, build_name
from sdnist.report.dataset.transform import transform
from sdnist.report.dataset.validate import validate
from sdnist.report.dataset.binning import *

import sdnist.strs as strs

import sdnist.utils as u
from sdnist.load import DEFAULT_DATASET

st_code_to_str = {
    '25': 'MA',
    '48': 'TX',
    '01': 'AL',
    '06': 'CA',
    '08': 'CO',
    '13': 'GA',
    '17': 'IL',
    '19': 'IA',
    '24': 'MD',
    '26': 'MI',
    '28': 'MS',
    '29': 'MO',
    '30': 'MT',
    '32': 'NV',
    '36': 'NY',
    '38': 'ND',
    '40': 'OK',
    '51': 'VA'
}

def unavailable_features(config: Dict, synthetic_data: pd.DataFrame):
    """remove features from configuration that are not available in
    the input synthetic data"""
    cnf = config
    fl = synthetic_data.columns.tolist()
    if 'k_marginal' in cnf and 'group_features' in cnf['k_marginal']:
        for f in cnf['k_marginal']['group_features'].copy():
            if f not in fl:
                cnf['k_marginal']['group_features'].remove(f)

    return cnf


def feature_space_size(target_df: pd.DataFrame, data_dict: Dict):
    size = 1

    for col in target_df.columns:
        if col in ['PINCP', 'POVPIP', 'WGTP', 'PWGTP', 'AGEP']:
            size = size * 100
        elif col in ['SEX', 'MSP', 'HISP', 'RAC1P', 'HOUSING_TYPE', 'OWN_RENT',
                     'INDP_CAT', 'EDU', 'PINCP_DECILE', 'DVET', 'DREM', 'DPHY', 'DEYE',
                     'DEAR']:
            size = size * len(data_dict[col]['values'])
        elif col in ['PUMA', 'DENSITY']:
            size = size * len(target_df['PUMA'].unique())
        elif col in ['NOC', 'NPF', 'INDP']:
            size = size * len(target_df[col].unique())

    return size


@dataclass
class Dataset:
    synthetic_filepath: Path
    log: u.SimpleLogger
    test: TestDatasetName = TestDatasetName.NONE
    data_root: Path = Path(DEFAULT_DATASET)
    download: bool = True

    challenge: str = strs.CENSUS
    target_data: pd.DataFrame = field(init=False)
    target_data_path: Path = field(init=False)
    synthetic_data: pd.DataFrame = field(init=False)
    schema: Dict = field(init=False)
    validation_log: Dict = field(init=False)
    feature_space: int = field(init=False)

    def __post_init__(self):
        # load target dataset which is used to score synthetic dataset
        self.target_data, params = load_dataset(
            challenge=strs.CENSUS,
            root=self.data_root,
            download=self.download,
            public=False,
            test=self.test,
            format_="csv"
        )
        self.target_data_path = build_name(
            challenge=strs.CENSUS,
            root=self.data_root,
            public=False,
            test=self.test
        )
        # raw target data
        self.raw_target_data = self.target_data.copy()

        self.schema = params[strs.SCHEMA]
        configs_path = self.target_data_path.parent.parent
        # add config packaged with data and also the config package with sdnist.report package
        config_1 = u.read_json(Path(configs_path, 'config.json'))
        config_2 = u.read_json(Path(FILE_DIR, 'config.json'))
        self.config = {**config_1, **config_2}

        self.mappings = u.read_json(Path(configs_path, 'mappings.json'))
        self.data_dict = u.read_json(Path(configs_path, 'data_dictionary.json'))
        self.features = self.target_data.columns.tolist()

        self.target_data_features = self.features

        drop_features = self.config[strs.DROP_FEATURES] \
            if strs.DROP_FEATURES in self.config else []
        self.features = self._fix_features(drop_features,
                                           self.config[strs.K_MARGINAL][strs.GROUP_FEATURES])

        # load synthetic dataset
        dtypes = {feature: desc["dtype"] for feature, desc in self.schema.items()}
        if str(self.synthetic_filepath).endswith('.csv'):
            self.synthetic_data = pd.read_csv(self.synthetic_filepath)
        elif str(self.synthetic_filepath).endswith('.parquet'):
            self.synthetic_data = pd.read_parquet(self.synthetic_filepath)
        else:
            raise Exception(f'Unknown synthetic data file type: {self.synthetic_filepath}')

        common_columns = list(set(self.synthetic_data.columns.tolist()).intersection(
            set(self.target_data.columns.tolist())
        ))

        if 'Unnamed: 0' in self.target_data.columns:
            self.target_data = self.target_data.drop(columns=['Unnamed: 0'])

        if 'Unnamed: 0' in self.synthetic_data.columns:
            self.synthetic_data = self.synthetic_data.drop(columns=['Unnamed: 0'])

        self.target_data = self.target_data[common_columns]
        self.synthetic_data = self.synthetic_data[common_columns]

        ind_features = [c for c in self.target_data.columns.tolist()
                        if c.startswith('IND_')]
        self.features = list(set(self.features).difference(set(ind_features)))
        self.features = list(set(self.features).intersection(list(common_columns)))

        # raw subset data
        self.target_data = self.target_data[self.features]
        self.synthetic_data = self.synthetic_data[self.features]

        self.feature_space = feature_space_size(self.target_data, self.data_dict)

        # validation and clean data
        self.c_synthetic_data, self.validation_log = \
            validate(self.synthetic_data, self.data_dict, self.features, self.log)
        self.c_target_data, _ = \
            validate(self.target_data, self.data_dict, self.features, self.log)
        self.features = self.c_synthetic_data.columns.tolist()

        # update data after validation and cleaning
        self.synthetic_data = self.synthetic_data[self.features]
        self.target_data = self.target_data[self.features]

        # for f in self.target_data.columns:
        #     if f not in ['PINCP', 'INDP', 'PWGTP', 'WGTP', 'POVPIP', 'DENSITY']:
        #         print('T', f, self.target_data[f].unique().tolist())
        #         print('S', f, self.synthetic_data[f].unique().tolist())
        #         print()

        # sort columns in the data
        self.target_data = self.target_data.reindex(sorted(self.target_data.columns), axis=1)
        self.synthetic_data = self.synthetic_data.reindex(sorted(self.target_data.columns), axis=1)
        self.c_synthetic_data = self.c_synthetic_data.reindex(sorted(self.target_data.columns), axis=1)
        self.c_target_data = self.c_target_data.reindex(sorted(self.target_data.columns), axis=1)
        self.features = self.synthetic_data.columns.tolist()

        # bin the density feature if present in the datasets
        self.density_bin_desc = dict()

        self.density_bin_desc = get_density_bins_description(self.raw_target_data,
                                                             self.data_dict,
                                                             self.mappings)
        if 'DENSITY' in self.features:
            self.target_data = bin_density(self.c_target_data, self.data_dict)
            self.synthetic_data = bin_density(self.c_synthetic_data, self.data_dict)

        self.log.msg(f'Features ({len(self.features)}): {self.features}', level=3, timed=False)
        self.log.msg(f'Deidentified Data Records Count: {self.c_synthetic_data.shape[0]}', level=3, timed=False)
        self.log.msg(f'Target Data Records Count: {self.c_target_data.shape[0]}', level=3, timed=False)

        # update config to contain only available features
        self.config = unavailable_features(self.config, self.synthetic_data)

        # transformed data
        self.t_target_data = transform(self.c_target_data, self.schema)

        self.t_synthetic_data = transform(self.c_synthetic_data, self.schema)

        # binned data
        numeric_features = ['AGEP', 'POVPIP', 'PINCP', 'PWGTP', 'WGTP']
        self.d_target_data = percentile_rank_target(self.c_target_data, numeric_features)
        self.d_target_data = add_bin_for_NA(self.d_target_data,
                                            self.c_target_data, numeric_features)

        self.d_synthetic_data = percentile_rank_synthetic(self.c_synthetic_data,
                                                          self.c_target_data,
                                                          self.d_target_data,
                                                          numeric_features)

        self.d_synthetic_data = add_bin_for_NA(self.d_synthetic_data,
                                               self.c_synthetic_data,
                                               numeric_features)

        non_numeric = [c for c in self.features
                       if c not in numeric_features]

        self.d_target_data[non_numeric] = self.t_target_data[non_numeric]
        self.d_synthetic_data[non_numeric] = self.t_synthetic_data[non_numeric]

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


def data_description(dataset: Dataset,
                     ui_data: ReportUIData,
                     report_data: ReportData,
                     labels: Optional[Dict] = None) -> ReportUIData:
    ds = dataset
    r_ui_d = ui_data

    dataset_report = dict()

    if labels is None:
        labels = dict()

    target_desc = DataDescriptionPacket(ds.target_data_path.stem,
                                                      ds.target_data.shape[0],
                                                      len(ds.target_data_features))
    r_ui_d.add_data_description(DatasetType.Target,
                                target_desc)
    dataset_report['target'] = {"filename": ds.target_data_path.stem,
                                "records": ds.target_data.shape[0],
                                "features": len(ds.target_data_features)}

    deid_desc = DataDescriptionPacket(ds.synthetic_filepath.stem,
                                                      ds.synthetic_data.shape[0],
                                                      ds.synthetic_data.shape[1],
                                                      labels,
                                                      ds.validation_log)
    r_ui_d.add_data_description(DatasetType.Synthetic,
                                deid_desc)
    dataset_report['deid'] = {"filename": ds.synthetic_filepath.stem,
                              "records": ds.synthetic_data.shape[0],
                              "features": ds.synthetic_data.shape[1],
                              "labels": labels,
                              "validations": ds.validation_log}

    f = dataset.features
    f = [_ for _ in dataset.data_dict.keys() if _ in f]
    ft = [dataset.schema[_]['dtype'] for _ in f]
    ft = ['object of type string' if _ == 'object' else _ for _ in ft]
    fd = [dataset.data_dict[_]['description'] for _ in f]
    hn = [True if 'has_null' in dataset.schema[_] else False for _ in f]
    r_ui_d.add_feature_description(f, fd, ft, hn)

    dataset_report['features'] = r_ui_d.feature_desc['Evaluated Data Features'].data

    report_data.add('data_description', dataset_report)

    # create data dictionary appendix attachments
    dd_as = []
    for feat in dataset.data_dict.keys():
        f_desc = dataset.data_dict[feat]['description']
        feat_title = f'{feat}: {f_desc}'
        if 'link' in dataset.data_dict[feat] and feat == 'INDP':
            data_1 = f"<a href={dataset.data_dict[feat]['link']}>" \
                   f"See codes in ACS data dictionary.</a> " \
                   f"Find codes by searching the string: {feat}, in " \
                   f"the ACS data dictionary"
            dd_as.append(Attachment(name=feat_title,
                                    _data=data_1,
                                    _type=AttachmentType.String))
            if "details" in dataset.data_dict[feat]:
                data_2 = dataset.data_dict[feat]['details']
                dd_as.append(Attachment(name=None,
                                        _data=data_2,
                                        _type=AttachmentType.String))

        elif 'values' in dataset.data_dict[feat]:
            f_name = feat_title
            if 'link' in dataset.data_dict[feat] and feat in ['WGTP', 'PWGTP']:
                s_data = f"<a href={dataset.data_dict[feat]['link']}>" \
                       f"See description of weights.</a>"
                dd_as.append(Attachment(name=f_name,
                                        _data=s_data,
                                        _type=AttachmentType.String))
                f_name = None

            data = [{f"{feat} Code": k,
                     f"Code Description": v}
                for k, v in dataset.data_dict[feat]['values'].items()
            ]
            if feat == 'PUMA':
                data = [{f"{feat} Code": k,
                         f"Code Description": f'{st_code_to_str[k.split("-")[0]]}: {v}'}
                        for k, v in dataset.data_dict[feat]['values'].items()
                        ]
            dd_as.append(Attachment(name=f_name,
                                    _data=data,
                                    _type=AttachmentType.Table))
            if feat == 'DENSITY':
                for bin, bdata in dataset.density_bin_desc.items():
                    bdc = bdata[1].columns.tolist()  # bin data columns
                    # report bin data: bin data format for report
                    rbd = [{c: row[j] for j, c in enumerate(bdc)}
                           for i, row in bdata[1].iterrows()]
                    dd_as.append(Attachment(name=None,
                                            _data=f'<b>Density Bin: {bin} | Bin Range: {bdata[0]}</b>',
                                            _type=AttachmentType.String))
                    dd_as.append(Attachment(name=None,
                                            _data=rbd,
                                            _type=AttachmentType.Table))

    r_ui_d.add(ScorePacket(metric_name='Data Dictionary',
                           score=None,
                           attachment=dd_as))

    return r_ui_d
