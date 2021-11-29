import numpy as np
import pandas as pd
import yaml

COLS = {
    "PUMA": "str",
    "YEAR": "uint32",
    "HHWT": "float",
    "GQ": "uint8",
    "PERWT": "float",
    "SEX": "uint8",
    "AGE": "uint8",
    "MARST": "uint8",
    "RACE": "uint8",
    "HISPAN": "uint8",
    "CITIZEN": "uint8",
    "SPEAKENG": "uint8",
    "HCOVANY": "uint8",
    "HCOVPRIV": "uint8",
    "HINSEMP": "uint8",
    "HINSCAID": "uint8",
    "HINSCARE": "uint8",
    "EDUC": "uint8",
    "EMPSTAT": "uint8",
    "EMPSTATD": "uint8",
    "LABFORCE": "uint8",
    "WRKLSTWK": "uint8",
    "ABSENT": "uint8",
    "LOOKING": "uint8",
    "AVAILBLE": "uint8",
    "WRKRECAL": "uint8",
    "WORKEDYR": "uint8",
    "INCTOT": "int32",
    "INCWAGE": "int32",
    "INCWELFR": "int32",
    "INCINVST": "int32",
    "INCEARN": "int32",
    "POVERTY": "uint32",
    "DEPARTS": "uint32",
    "ARRIVES": "uint32",
}

class RecordPostprocessor:
    def __init__(self):
        self.config = None
        pass

    def post_process(self, data: pd.DataFrame, config_file_path: str, grouping_mapping: dict):
        assert isinstance(data, pd.DataFrame)
        with open(config_file_path, 'r') as f:
            self.config = yaml.load(f, Loader=yaml.BaseLoader)

        data = self.ungrouping_attributes(data, grouping_mapping)
        data = self.unbinning_attributes(data)
        data = self.add_determined_attrs(data)
        data = self.decode_other_attributes(data, grouping_mapping)
        data = self.ensure_types(data)
        return data

    def unbinning_attributes(self, data: pd.DataFrame):
        binning_info = self.config['numerical_binning']
        print(binning_info)
        for att, spec_list in binning_info.items():
            if att == "DEPARTS" or att == "ARRIVES":
                bins = np.r_[-np.inf, [int(h) * 100 + int(m) for h in range(24) for m in spec_list], np.inf]
            else:
                [s, t, step] = spec_list
                bins = np.r_[-np.inf, np.arange(int(s), int(t), int(step)), np.inf]

            # remove np.inf
            bins[0] = bins[1] - 1
            bins[-1] = bins[-2] + 2

            values_map = {i: int((bins[i] + bins[i + 1]) / 2) for i in range(len(bins) - 1)}
            data[att] = data[att].map(values_map)
        return data

    def ungrouping_attributes(self, data: pd.DataFrame, decode_mapping: dict):
        grouping_info = self.config['grouping_attributes']
        for grouping in grouping_info:
            grouped_attr = grouping['grouped_name']
            attributes = grouping['attributes']

            data[grouped_attr] = [decode_mapping[grouped_attr][i] for i in data[grouped_attr]]

            # mapping = pd.Index(decode_mapping[grouped_attr])
            # data[grouped_attr] = mapping[data[grouped_attr]]  # somehow this raises an error

            data[attributes] = pd.DataFrame(data[grouped_attr].tolist(), index=data.index)
            data = data.drop(grouped_attr, axis=1)
        return data

    def decode_other_attributes(self, data: pd.DataFrame, decode_mapping: dict):
        grouping_attr = [info["grouped_name"] for info in self.config['grouping_attributes']]
        binning_attr = [attr for attr in self.config['numerical_binning'].keys()]
        for attr, mapping in decode_mapping.items():
            if attr in grouping_attr or attr in binning_attr:
                continue
            else:
                mapping = pd.Index(mapping)
                data[attr] = mapping[data[attr]]
        return data

    def add_determined_attrs(self, data: pd.DataFrame):
        """
             Some dataset are determined by other attributes
        """
        determined_info = self.config['determined_attributes']
        for determined_attr in determined_info.keys():
            control_attr = determined_info[determined_attr]['by']
            mapping = determined_info[determined_attr]['mapping']
            default = determined_info[determined_attr]['default']
            # type = data[control_attr].dtype
            mapping = {int(k): int(v) for k, v in mapping.items()}
            data[determined_attr] = data.apply(lambda row: mapping.get(row[control_attr], default), axis=1)
        return data

    def ensure_types(self, data: pd.DataFrame):
        for col, data_type in COLS.items():
            data[col] = data[col].astype(data_type)
        return data
