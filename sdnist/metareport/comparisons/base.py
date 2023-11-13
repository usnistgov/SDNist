import pandas as pd

from sdnist.metareport.common import *


class BaseComparison(object):
    feature_space = dict()

    def __init__(self, reports: Dict, report_dir: Path, label_keys: List[str],
                 filters: Dict[str, List], data_dict: Dict[str, any],
                 target_datasets: Dict[str, pd.DataFrame]):
        self.reports = reports
        self.report_dir = report_dir
        self.label_keys = label_keys
        self.filters = filters
        self.data_dict = data_dict
        self.target_datasets = target_datasets

    def compute_feature_space(self,
                              feature_set_name: str,
                              features: str,
                              target_dataset_name: str) -> Tuple[int, List[str]]:
        target_df = self.target_datasets[target_dataset_name]
        print(features)
        features = features[2:-2]
        features = features.split('\', \'')
        print(features)
        target_df = target_df[features]
        size = 1

        for col in target_df.columns:
            if col in ['PINCP', 'POVPIP', 'WGTP', 'PWGTP', 'AGEP']:
                size = size * 100
            elif col in ['SEX', 'MSP', 'HISP', 'RAC1P', 'HOUSING_TYPE', 'OWN_RENT',
                         'INDP_CAT', 'EDU', 'PINCP_DECILE', 'DVET', 'DREM', 'DPHY', 'DEYE',
                         'DEAR']:
                size = size * len(self.data_dict[col]['values'])
            elif col in ['PUMA', 'DENSITY']:
                size = size * len(target_df['PUMA'].unique())
            elif col in ['NOC', 'NPF', 'INDP']:
                size = size * len(target_df[col].unique())

        if feature_set_name in self.__class__.feature_space:
            return self.__class__.feature_space[feature_set_name]

        self.__class__.feature_space[feature_set_name] = (size, target_df.columns.tolist())
        # return number of features and sorted list of features
        return self.__class__.feature_space[feature_set_name]