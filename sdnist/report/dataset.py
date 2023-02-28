import math
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
        else:
            nna_mask = data[~data[c].isin(['N'])].index  # not na mask
        d_temp = pd.DataFrame(pd.to_numeric(data.loc[nna_mask, c]).astype(int), columns=[c])
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
        if f not in to.columns.tolist():
            continue
        nna_mask = s[~s[f].isin(['N'])].index  # not na mask
        st = pd.DataFrame(pd.to_numeric(s.loc[nna_mask, f]).astype(int), columns=[f])
        final_st = st.copy()
        max_b = 0
        for b, g in target_binned.sort_values(by=[f]).groupby(by=f):
            if b == -1:
                continue
            t_bp = pd.DataFrame(pd.to_numeric(to.loc[g.index, f]).astype(int), columns=[f])
            if b == 0:
                max_b = max(t_bp[f])
                final_st.loc[(st[f] <= max_b), f] = b
            else:
                min_b = max_b
                max_b = max(t_bp[f])
                final_st.loc[(st[f] > min_b) & (st[f] <= max_b), f] = b
        s.loc[nna_mask, f] = final_st
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


def bin_density(data: pd.DataFrame, data_dict: Dict, update: bool = True) -> pd.DataFrame:
    """
    data: Data containing density feature
    data_dict: Dictionary containing values range for density feature
    update: if True, update the input data's density feature and return
            else, create two new columns: binned_density and bin_range
            and return the data
    """
    def get_bin_range_log(x):
        for i, v in enumerate(bins):
            if i == x:
                return f'({round(v, 2)}, {round(bins[i + 1], 2)}]'
    d = data
    dd = data_dict
    base = 10
    # we remove first 8 bins from this bins list, and prepend
    # two bins. So effective bins are 12. This is done to bottom
    # code density category for the PUMAs with small density.
    n_bins = 20  # number of bins
    # max of range
    n_max = dd['DENSITY']['values']['max'] + 500

    bins = np.logspace(start=math.log(10, base), stop=math.log(n_max, base), num=n_bins+1)
    # remove first 8 bins and prepend two new bins
    bins = [0, 150] + list(bins[8:])
    # print('Bins', bins)
    # print('Densities', d['DENSITY'].unique().tolist())
    n_bins = len(bins)  # update number of bins to effective bins
    labels = [i for i in range(n_bins-1)]

    # top code values to n_max and bottom code values to 0 in the data
    d.loc[d['DENSITY'] < 0, 'DENSITY'] = float(0)
    d.loc[d['DENSITY'] > n_max, 'DENSITY'] = float(n_max) - 100

    if update:
        d['DENSITY'] = pd.cut(d['DENSITY'], bins=bins, labels=labels)
        return d
    else:
        d['binned_density'] = pd.cut(d['DENSITY'], bins=bins, labels=labels)

        d['bin_range'] = d['binned_density'].apply(lambda x: get_bin_range_log(x))
        return d


def get_density_bins_description(data: pd.DataFrame, data_dict: Dict, mappings: Dict) -> Dict:
    bin_desc = dict()
    # If puma is not available in the features, return empty description dictionary
    if 'PUMA' not in data:
        return bin_desc

    d = bin_density(data.copy(), data_dict, update=False)

    for dbin, g in d.groupby(by=['binned_density']):
        if g.shape[0] == 0:
            continue

        density_range = g['bin_range'].unique()[0]
        bin_data = []
        for puma, pg in g.groupby(by='PUMA'):
            density = pg['DENSITY'].unique()[0]
            bin_data.append([puma, density, mappings["PUMA"][puma]["name"]])
        bin_df = pd.DataFrame(bin_data, columns=['PUMA', 'DENSITY', 'PUMA NAME'])
        bin_desc[dbin] = (density_range, bin_df)
    del d
    # print(bin_desc)
    return bin_desc


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


@dataclass
class Dataset:
    synthetic_filepath: Path
    log: u.SimpleLogger
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
            format_="csv"
        )
        self.target_data_path = build_name(
            challenge=strs.CENSUS,
            root=self.data_root,
            public=False,
            test=self.test
        )
        self.schema = params[strs.SCHEMA]
        configs_path = self.target_data_path.parent.parent
        # add config packaged with data and also the config package with sdnist.report package
        config_1 = u.read_json(Path(configs_path, 'config.json'))
        config_2 = u.read_json(Path(FILE_DIR, 'config.json'))
        self.config = {**config_1, **config_2}

        self.mappings = u.read_json(Path(configs_path, 'mappings.json'))
        self.data_dict = u.read_json(Path(configs_path, 'data_dictionary.json'))
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

        self.log.msg(f'Features ({len(self.features)}): {self.features}', level=3, timed=False)
        self.log.msg(f'Deidentified Data Records Count: {self.synthetic_data.shape[0]}', level=3, timed=False)
        self.log.msg(f'Target Data Records Count: {self.target_data.shape[0]}', level=3, timed=False)

        validate(self.synthetic_data, self.schema, self.features)

        # raw data
        self.target_data = self.target_data[self.features]
        self.synthetic_data = self.synthetic_data[self.features]

        # bin the density feature if present in the datasets
        self.density_bin_desc = dict()
        if 'DENSITY' in self.features:
            self.density_bin_desc = get_density_bins_description(self.target_data,
                                                                 self.data_dict,
                                                                 self.mappings)
            self.target_data = bin_density(self.target_data, self.data_dict)
            self.synthetic_data = bin_density(self.synthetic_data, self.data_dict)

        # update config to contain only available features
        self.config = unavailable_features(self.config, self.synthetic_data)

        # transformed data
        self.t_target_data = transform(self.target_data, self.schema)

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
