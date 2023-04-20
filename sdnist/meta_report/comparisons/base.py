from sdnist.meta_report.common import *

class BaseComparison(object):
    feature_space = dict()

    def __init__(self, reports: Dict, report_dir: Path, label_keys: List[str],
                 filters: Dict[str, List], data_dict: Dict[str, any]):
        self.reports = reports
        self.report_dir = report_dir
        self.label_keys = label_keys
        self.filters = filters
        self.data_dict = data_dict

    def compute_feature_space(self,
                              feature_set_name: str,
                              features: List[str]) -> Tuple[int, List[str]]:
        if feature_set_name in self.__class__.feature_space:
            return self.__class__.feature_space[feature_set_name]
        # list of features and their value length
        f_list = []
        for f in features:
            if "values" not in self.data_dict[f]:
                vals = [0] * 269  # in case of INDP feature
            else:
                vals = self.data_dict[f]["values"]
            if "min" in vals and f != 'AGEP':
                continue
            if f == 'AGEP':
                f_list.append([f, 100])
            else:
                f_list.append([f, len(vals)])

        f_df = pd.DataFrame(f_list, columns=['feature', 'len'])
        f_df = f_df.sort_values(by='len')

        # get product of all feature lengths
        n_features = f_df['len'].astype(object).product()
        sorted_features = f_df['feature'].tolist()
        sorted_features = sorted_features + list(set(features) - set(sorted_features))
        self.__class__.feature_space[feature_set_name] = (n_features, sorted_features)
        # return number of features and sorted list of features
        return self.__class__.feature_space[feature_set_name]