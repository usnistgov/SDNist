import json
import os
import pickle
from typing import Tuple, Dict
import numpy as np
import pandas as pd
import yaml
from loguru import logger

from config.path import CONFIG_DATA, PICKLE_DIRECTORY, DATA_DIRECTORY, INPUT
from config.data_type import COLS

import sdnist


class DataLoader:
    def __init__(self):
        self.public_data = None
        self.private_data = None
        self.all_attrs = []

        self.encode_mapping = {}
        self.decode_mapping = {}

        self.pub_marginals = {}
        self.priv_marginals = {}

        self.encode_schema = {}

        self.general_schema = {}
        self.filter_values = {}

        self.config = None

    def load_data(self, pub_only=False):
        # load public data and get grouping mapping and filter values

        with open(CONFIG_DATA, 'r') as f:
            config = yaml.load(f, Loader=yaml.FullLoader)
        self.config = config

        # load public data
        logger.info("Loading public data")
        self.public_data, self.general_schema = sdnist.census(root="~/datasets", public=False)
        self.public_data = self.binning_attributes(config['numerical_binning'], self.public_data)
        self.public_data = self.grouping_attributes(config['grouping_attributes'], self.public_data)
        self.public_data = self.remove_determined_attributes(config['determined_attributes'], self.public_data)
        self.public_data = self.recode_remain(self.general_schema, config, self.public_data)
        # pickle.dump([self.public_data, self.encode_mapping], open(public_pickle_path, 'wb'))

        # load private data
        logger.info("Loading private data")
        self.private_data, self.general_schema = sdnist.census(root="~/datasets", public=True)
        self.private_data = self.binning_attributes(config['numerical_binning'], self.private_data)
        self.private_data = self.grouping_attributes(config['grouping_attributes'], self.private_data)
        self.private_data = self.remove_determined_attributes(config['determined_attributes'], self.private_data)
        self.private_data = self.recode_remain(self.general_schema, config, self.private_data, is_private=True)
        # pickle.dump([self.private_data, self.encode_mapping], open(priv_pickle_path, 'wb'))

        for attr, encode_mapping in self.encode_mapping.items():
            self.encode_schema[attr] = sorted(encode_mapping.values())

        logger.info(f"public data size {self.public_data.shape}, priv data size {self.private_data.shape}")

    def obtain_attrs(self):
        if not self.all_attrs:
            all_attrs = list(self.public_data.columns)
            try:
                all_attrs.remove("sim_individual_id")
            except:
                pass
            self.all_attrs = all_attrs
        return self.all_attrs

    def binning_attributes(self, binning_info, data):
        """
            Numerical attributes can be binned
        """
        for attr, spec_list in binning_info.items():
            if attr == "DEPARTS" or attr == "ARRIVES":
                bins = np.r_[-np.inf, [h * 100 + m for h in range(24) for m in spec_list], np.inf]
            else:
                [s, t, step] = spec_list
                bins = np.r_[-np.inf, np.arange(s, t, step), np.inf]
            data[attr] = pd.cut(data[attr], bins).cat.codes
            self.encode_mapping[attr] = {(bins[i], bins[i + 1]): i for i in range(len(bins) - 1)}
            self.decode_mapping[attr] = [i for i in range(len(bins) - 1)]
        return data

    def grouping_attributes(self, grouping_info, data):
        """
            Some attributes can be grouped
        """
        for grouping in grouping_info:
            attributes = grouping['attributes']
            new_attr = grouping['grouped_name']

            # group attribute values into tuples
            data[new_attr] = data[attributes].apply(tuple, axis=1)

            # map tuples to new values in new columns
            encoding = {v: i for i, v in enumerate(grouping['combinations'])}
            data[new_attr] = data[attributes].apply(tuple, axis=1)
            data[new_attr] = data[new_attr].map(encoding)
            self.encode_mapping[new_attr] = encoding
            self.decode_mapping[new_attr] = grouping['combinations']

            # drop grouped columns
            data = data.drop(attributes, axis=1)
        return data

    @staticmethod
    def remove_determined_attributes(determined_info, data):
        """
            Some dataset are determined by other attributes
        """
        for determined_attr in determined_info.keys():
            data = data.drop(determined_attr, axis=1)
            # print("remove", determined_attr)
        data = data.drop('sim_individual_id', axis=1)
        return data

    # recode the remaining single attributes to save storage
    def recode_remain(self, schema, config, data, is_private=False):
        encoded_attr = list(config['numerical_binning'].keys()) + [grouping['grouped_name'] for grouping in config['grouping_attributes']]
        for attr in data.columns:
            if attr in ['sim_individual_id'] or attr in encoded_attr:
                continue
            # print("encode remain:", attr)
            assert attr in schema and 'values' in schema[attr]
            if is_private and attr == 'PUMA':
                mapping = data[attr].unique()
            else:
                mapping = schema[attr]['values']
            encoding = {v: i for i, v in enumerate(mapping)}
            data[attr] = data[attr].map(encoding)
            self.encode_mapping[attr] = encoding
            self.decode_mapping[attr] = mapping
        return data

    def generate_all_pub_marginals(self):
        pub_marginal_pickle = PICKLE_DIRECTORY / f"pub_all_marginals.pkl"

        if pub_marginal_pickle is not None and os.path.isfile(pub_marginal_pickle):
            self.pub_marginals = pickle.load(open(pub_marginal_pickle, 'rb'))
            return self.pub_marginals

        all_attrs = list(self.public_data.columns)
        # all_attrs.remove("sim_individual_id")
        # one-way marginals except PUMA and YEAR
        for attr in all_attrs:
            if attr == 'PUMA' or attr == 'YEAR':
                continue
            self.pub_marginals[frozenset([attr])] = self.generate_one_way_marginal(self.public_data, attr)
        # two_way marginals except PUMA and YEAR
        for i, attr in enumerate(all_attrs):
            if attr == 'PUMA' or attr == 'YEAR':
                continue
            for j in range(i + 1, len(all_attrs)):
                if all_attrs[j] == 'PUMA' or all_attrs[j] == 'YEAR':
                    continue
                self.pub_marginals[frozenset([all_attrs[i], all_attrs[j]])] = self.generate_two_way_marginal(
                    self.public_data, all_attrs[i], all_attrs[j])

        if pub_marginal_pickle is not None:
            pickle.dump(self.pub_marginals, open(pub_marginal_pickle, 'wb'))

        return self.pub_marginals

    def generate_one_way_marginal(self, records: pd.DataFrame, index_attribute: list):
        marginal = records.assign(n=1).pivot_table(values='n', index=index_attribute, aggfunc=np.sum, fill_value=0)
        indices = sorted([i for i in self.encode_mapping[index_attribute].values()])
        marginal = marginal.reindex(index=indices).fillna(0).astype(np.int32)
        return marginal

    def generate_two_way_marginal(self, records: pd.DataFrame, index_attribute: list, column_attribute: list):
        marginal = records.assign(n=1).pivot_table(values='n', index=index_attribute, columns=column_attribute,
                                                   aggfunc=np.sum, fill_value=0)
        indices = sorted([i for i in self.encode_mapping[index_attribute].values()])
        columns = sorted([i for i in self.encode_mapping[column_attribute].values()])
        marginal = marginal.reindex(index=indices, columns=columns).fillna(0).astype(np.int32)
        return marginal

    def generate_all_one_way_marginals_except_PUMA_YEAR(self, records: pd.DataFrame):
        all_attrs = self.obtain_attrs()
        marginals = {}
        for attr in all_attrs:
            if attr == 'PUMA' or attr == 'YEAR':
                continue
            marginals[frozenset([attr])] = self.generate_one_way_marginal(records, attr)
        return marginals

    def generate_all_two_way_marginals_except_PUMA_YEAR(self, records: pd.DataFrame):
        all_attrs = self.obtain_attrs()
        marginals = {}
        for i, attr in enumerate(all_attrs):
            if attr == 'PUMA' or attr == 'YEAR':
                continue
            for j in range(i + 1, len(all_attrs)):
                if all_attrs[j] == 'PUMA' or all_attrs[j] == 'YEAR':
                    continue
                marginals[frozenset([attr, all_attrs[j]])] = self.generate_two_way_marginal(records, attr, all_attrs[j])
        return marginals

    def generate_marginal_by_config(self, records: pd.DataFrame, config: dict) -> Tuple[Dict, Dict]:
        marginal_sets = {}
        epss = {}
        for marginal_key, marginal_dict in config.items():
            marginals = {}
            if marginal_key == 'priv_all_one_way':
                # merge the returned marginal dictionary
                marginals.update(self.generate_all_one_way_marginals_except_PUMA_YEAR(records))
            elif marginal_key == 'priv_all_two_way':
                # merge the returned marginal dictionary
                marginals.update(self.generate_all_two_way_marginals_except_PUMA_YEAR(records))
            else:
                attrs = marginal_dict['attributes']
                if len(attrs) == 1:
                    marginals[frozenset(attrs)] = self.generate_one_way_marginal(records, attrs[0])
                elif len(attrs) == 2:
                    marginals[frozenset(attrs)] = self.generate_two_way_marginal(records, attrs[0], attrs[1])
                else:
                    raise NotImplementedError
            epss[marginal_key] = marginal_dict['total_eps']
            marginal_sets[marginal_key] = marginals
        return marginal_sets, epss

    def get_marginal_grouping_info(self, cur_attrs):
        info = {}
        grouping_info = self.config['grouping_attributes']
        for attr in cur_attrs:
            for grouping in grouping_info:
                new_attr = grouping['grouped_name']
                if new_attr == attr:
                    info[new_attr] = grouping['attributes']
                    break
            if attr not in info:
                info[attr] = [attr]
        return info
