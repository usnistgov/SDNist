from pathlib import Path
from typing import Dict, List
from dataclasses import dataclass, field

import pandas as pd
import numpy as np

from sdnist.report import ReportUIData, FILE_DIR
from sdnist.report.report_data import \
    DatasetType, DataDescriptionPacket, ScorePacket,\
    Attachment, AttachmentType
from sdnist.load import \
    TestDatasetName, load_dataset, build_name

import sdnist.strs as strs

import sdnist.utils as u


def validate(synth_data: pd.DataFrame, schema, features):
    sd = synth_data.copy()
    missing_feature = []
    nan_features = []
    vob_features = []  # value out of bound

    for f in features:
        # check feature exists
        if f not in sd.columns:
            missing_feature.append(f)
            raise Exception(f'Missing Feature: {f} in Synthetic Data')
        # check feature doesn't have nans
        if any(sd[f].isna()):
            nan_features.append(f)

        # check feature has out of bound value
        f_data = schema[f]
        if 'min' in f_data:
            if f in ['POVPIP', 'PINCP']:
                nna_mask = sd[sd[f] != 'N'].index
                try:
                    sd[f] = pd.to_numeric(sd.loc[nna_mask, f]).astype(int)
                except Exception as e:
                    vob_features.append((f, []))
            else:
                try:
                    sd[f] = pd.to_numeric(sd[f]).astype(int)
                except Exception as e:
                    vob_features.append((f, []))
        else:
            d_vals = set(synth_data[f].unique().tolist())
            diff = d_vals.difference(set(f_data['values']))
            if len(diff):
                vob_features.append((f, list(diff)))

    if len(missing_feature):
        raise Exception(f'Error: Missing features in synthetic data: {missing_feature}')
    if len(nan_features):
        raise Exception(f'Error: nan value in synthetic data features: {nan_features}')
    if len(vob_features):
        for f, vals in vob_features:
            if f in ['POVPIP', 'PINCP']:
                print(f'Error: No non-numeric value other than N is allowed in feature {f}')
            else:
                print(f'Error: Value out of bound for feature {f}, out of bound values: {vals}')

        raise Exception(f'Values out of bound for features: {[f for f, v in vob_features]}')


def transform(data: pd.DataFrame, schema: Dict):
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
                    data[c] = data[c].replace(null_val, 9999999)
                elif c == 'POVPIP':
                    data[c] = data[c].replace(null_val, 999)
        if c == 'PUMA':
            data[c] = data[c].astype(pd.CategoricalDtype(desc["values"])).cat.codes
            if "N" in desc['values']:
                data[c] = data[c].replace(0, -1)
        else:
            data[c] = pd.to_numeric(data[c])

    return data


def percentile_rank_target(data: pd.DataFrame, features: List[str]):
    data = data.copy()
    for c in features:
        if c not in data.columns:
            continue

        if c == 'POVPIP':
            nna_mask = data[~data[c].isin(['N', '501'])].index
            # print()
            # print('POVPIP PERCNT RANK')
            # print(sorted(data.loc[nna_mask, c].unique()))
        else:
            nna_mask = data[~data[c].isin(['N'])].index  # not na mask
        d_temp = pd.DataFrame(pd.to_numeric(data.loc[nna_mask, c]).astype(int), columns=[c])
        # print(d_temp.shape)
        # print(d_temp.dtypes)
        # print(d_temp.columns.tolist())
        # if c == 'POVPIP':
        #     # print(sorted(d_temp[c].unique()))
        #     d_temp['rank'] = d_temp[c].rank(pct=True, numeric_only=True).apply(lambda x: round(x, 2))
        #     tdf = d_temp.groupby(by=c)[c].size().reset_index(name='count_target')
            # for r, g in d_temp.groupby(by=['rank']):
            #     print(r, sorted(g[c].unique()))
            # for i, r in tdf.sort_values(by=[c], ascending=False).iterrows():
            #     print(r[c], r['count_target'], r['rank'])
            # print(sorted(d_temp[c].rank(pct=True, numeric_only=True).apply(lambda x: round(x, 2)).unique()))
        data.loc[nna_mask, c] = d_temp[c]\
            .rank(pct=True).apply(lambda x: int(20 * x) if x < 1 else 19)
        if c == 'POVPIP':
            data[c] = data[c].apply(lambda x: int(x) if x == '501' else x)
    return data


def percentile_rank_synthetic(synthetic: pd.DataFrame,
                              target_orig: pd.DataFrame,
                              target_binned: pd.DataFrame,
                              features: List[str]):
    s, to, tb = synthetic.copy(), target_orig, target_binned

    for f in features:
        if f not in target_orig:
            continue
        nna_mask = s[~s[f].isin(['N'])].index  # not na mask
        st = pd.DataFrame(pd.to_numeric(s.loc[nna_mask, f]).astype(int), columns=[f])
        if f not in to.columns.tolist():
            continue
        min_b = 0
        max_b = 0
        for b, g in target_binned.groupby(by=[f]):
            if b == -1:
                continue
            t_bp = pd.DataFrame(pd.to_numeric(to.loc[g.index, f]).astype(int), columns=[f])
            if b == 0:
                min_b = min(t_bp[f])
                max_b = max(t_bp[f])
            else:
                min_b = max_b
                max_b = max(t_bp[f])
            st.loc[(st[f] >= min_b) & (st[f] <= max_b), f] = b
        s.loc[nna_mask, f] = st
    return s


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
        self.mappings = u.read_json(Path(self.target_data_path.parent, 'mappings.json'))
        self.data_dict = u.read_json(Path(self.target_data_path.parent, 'data_dictionary.json'))
        self.features = self.target_data.columns.tolist()

        drop_features = self.config[strs.DROP_FEATURES] \
            if strs.DROP_FEATURES in self.config else []
        self.features = self._fix_features(drop_features,
                                           self.config[strs.K_MARGINAL][strs.GROUP_FEATURES])

        # load synthetic dataset
        dtypes = {feature: desc["dtype"] for feature, desc in self.schema.items()}
        if str(self.synthetic_filepath).endswith('.csv'):
            self.synthetic_data = pd.read_csv(self.synthetic_filepath, dtype=dtypes)
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

        validate(self.synthetic_data, self.schema, self.features)
        # raw data
        self.target_data = self.target_data[self.features]
        self.synthetic_data = self.synthetic_data[self.features]

        # transformed data
        self.t_target_data = transform(self.target_data, self.schema)
        # print()
        # print('SYNTHETIC')
        # print()
        self.t_synthetic_data = transform(self.synthetic_data, self.schema)

        # binned data
        numeric_features = ['AGEP', 'POVPIP', 'PINCP']
        self.d_target_data = percentile_rank_target(self.target_data, numeric_features)
        self.d_target_data = add_bin_for_NA(self.d_target_data,
                                            self.target_data, numeric_features)

        self.d_synthetic_data = percentile_rank_synthetic(self.synthetic_data,
                                                          self.target_data,
                                                          self.d_target_data,
                                                          numeric_features)
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


def data_description(dataset: Dataset, ui_data: ReportUIData) -> ReportUIData:
    ds = dataset
    r_ui_d = ui_data

    r_ui_d.add_data_description(DatasetType.Target,
                            DataDescriptionPacket(ds.target_data_path.stem,
                                                  ds.target_data.shape[0],
                                                  ds.target_data.shape[1]))

    r_ui_d.add_data_description(DatasetType.Synthetic,
                            DataDescriptionPacket(ds.synthetic_filepath.stem,
                                                  ds.synthetic_data.shape[0],
                                                  ds.synthetic_data.shape[1]))

    f = dataset.features
    f = [_ for _ in dataset.data_dict.keys() if _ in f]
    ft = [dataset.schema[_]['dtype'] for _ in f]
    ft = ['object of type string' if _ == 'object' else _ for _ in ft]
    fd = [dataset.data_dict[_]['description'] for _ in f]
    hn = [True if 'has_null' in dataset.schema[_] else False for _ in f]
    r_ui_d.add_feature_description(f, fd, ft, hn)

    # create data dictionary appendix attachments
    dd_as = []
    for feat in dataset.data_dict.keys():
        f_desc = dataset.data_dict[feat]['description']
        feat_title = f'{feat}: {f_desc}'
        if 'link' in dataset.data_dict[feat] and feat == 'INDP':
            data = f"<a href={dataset.data_dict[feat]['link']}>" \
                   f"See codes in ACS data dictionary.</a> " \
                   f"Find codes by searching the string: {feat}, in " \
                   f"the ACS data dictionary"
            dd_as.append(Attachment(name=feat_title,
                                    _data=data,
                                    _type=AttachmentType.String))

        elif 'values' in dataset.data_dict[feat]:
            data = [{f"{feat} Code": k,
                     f"Code Description": v}
                for k, v in dataset.data_dict[feat]['values'].items()
            ]
            f_name = feat_title
            if 'link' in dataset.data_dict[feat] and feat in ['WGTP', 'PWGTP']:
                s_data = f"<a href={dataset.data_dict[feat]['link']}>" \
                       f"See description of weights.</a>"
                dd_as.append(Attachment(name=f_name,
                                        _data=s_data,
                                        _type=AttachmentType.String))
                f_name = None
            dd_as.append(Attachment(name=f_name,
                                    _data=data,
                                    _type=AttachmentType.Table))

    r_ui_d.add(ScorePacket(metric_name='Data Dictionary',
                           score=None,
                           attachment=dd_as))

    return r_ui_d
