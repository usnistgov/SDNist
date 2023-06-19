from sdnist.meta_report.common import \
    json, Dict, List, Path, pd, Optional

ALGORITHM_NAME = 'algorithm name'
ALGORITHM_TYPE = 'algorithm type'
DATA_PATH = 'data path'
DEID_DATA_ID = 'deid data id'
DELTA = 'delta'
EPSILON = 'epsilon'
FEATURE_SET_NAME = 'feature set name'
FEATURE_SPACE_SIZE = 'feature space size'
FEATURES_LIST = 'features list'
INDEX = 'index'
LABELS_PATH = 'labels path'
LIBRARY_NAME = 'library name'
PRAM_FEATURES = 'pram features'
PRAM_FEATURES_EXCEPTION = 'pram features exception'
PRIVACY_CATEGORY = 'privacy category'
PRIVACY_LABEL_DETAIL = 'privacy label detail'
REPORT_PATH = 'report path'
RESEARCH_PAPERS = 'research papers'
SUBMISSION_NUMBER = 'submission number'
SUBMISSION_TIMESTAMP = 'submission timestamp'
QUASI_IDENTIFIERS_SUBSET = 'quasi identifiers subset'
TARGET_DATASET = 'target dataset'
TEAM = 'team'
VARIANT_LABEL = 'variant label'
VARIANT_LABEL_DETAIL = 'variant label detail'

column_order = [
    LIBRARY_NAME,
    ALGORITHM_NAME,
    ALGORITHM_TYPE,
    TARGET_DATASET,
    FEATURE_SET_NAME,
    FEATURE_SPACE_SIZE,
    FEATURES_LIST,
    PRIVACY_CATEGORY,
    PRIVACY_LABEL_DETAIL,
    EPSILON,
    DELTA,
    VARIANT_LABEL,
    VARIANT_LABEL_DETAIL,
    RESEARCH_PAPERS,
    DATA_PATH,
    LABELS_PATH,
    REPORT_PATH,
    TEAM,
    SUBMISSION_NUMBER,
    SUBMISSION_TIMESTAMP,
    QUASI_IDENTIFIERS_SUBSET,
    DEID_DATA_ID
]


def create_label(labels: Dict, label_props: List[str]) -> str:
    res_labels = []
    for lk in label_props:
        if lk not in labels:
            res_labels.append('')
            continue
        if lk == EPSILON:
            res_labels.append(f'{lk}:{labels[lk]}')
        elif lk == VARIANT_LABEL:
            lbl_str = labels[lk]
            if len(lbl_str):
                lbl_str = lbl_str if len(lbl_str) < 30 else lbl_str[:30] + '...'
                res_labels.append(f'{lbl_str}')
        elif lk == SUBMISSION_NUMBER:
            lbl_str = labels[lk]
            res_labels.append(f's #[{lbl_str}]')
        else:
            lbl_str = str(labels[lk])
            if len(lbl_str):
                res_labels.append(f'{lbl_str}')
    res_labels = [l for l in res_labels if len(l)]
    return ' | '.join(res_labels)


def update_keys(paths: List[Path], key_to_change: str, new_key: str):
    """
    For each directory path in the paths parameter:
        For every json in the directory and subdirectory path:
            Load json file:
            if key_to_change exist in the json file:
                change the key_to_change to new_key
            save the json file at same path
    """
    for path in paths:
        print('Processing path: {}'.format(path))
        for file in path.glob('**/*.json'):
            # check if file str contain report word
            if 'report' in str(file):
                continue
            print('--Processing file: {}'.format(file))
            with open(file, 'r') as f:
                data = json.load(f)
            if key_to_change in data.keys():
                data[new_key] = data.pop(key_to_change)
            for k in data.keys():
                if isinstance(data[k], dict):
                    if key_to_change in data[k].keys():
                        data[k][new_key] = data[k].pop(key_to_change)

            with open(file, 'w') as f:
                json.dump(data, f, indent=4)


def reports_from_index(index: pd.DataFrame, filters: Dict[str, Dict],
                       sort_by: Optional[Dict[str, List]] = None):
    """
    Filter index dataframe by filters
    Return a list of reports
    """
    res_df = pd.DataFrame([], columns=index.columns)
    for f_name, filter in filters.items():
        fdf = index.copy()
        if f_name.startswith('f'):  # that means inclusion
            for f, vals in filter.items():
                fdf = fdf[fdf[f].isin(vals)]
            res_df = pd.concat([res_df, fdf])

    for f_name, filter in filters.items():
        if f_name.startswith('e'): # that means exclusion
            for f, vals in filter.items():
                res_df = res_df[~res_df[f].isin(vals)]

    default_sort_keys = ['feature set name', 'target dataset']
    res_df = res_df.sort_values(by=default_sort_keys)
    if sort_by:

        for feat, vals in sort_by.items():
            if feat not in res_df.columns:
                continue
            if type(vals) == list:
                v_dict = {v: i for i, v in enumerate(vals)}
                res_df = res_df.sort_values(by=[feat],
                                            key=lambda x: x.map(v_dict))
            elif type(vals) == str and vals in ['asc', 'desc']:
                asc = True if vals == 'asc' else False
                res_df = res_df.sort_values(by=[feat], ascending=asc)
    for i, row in res_df.iterrows():
        print(row[LIBRARY_NAME], row[ALGORITHM_NAME], row['feature set name'], row['target dataset'], row['report path'], row['data path'])

    return res_df['report path'].tolist()


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


def index_data(paths: List[Path], out_dir: Path):
    """
    path_dataframes = []
    For each directory path in the paths parameter:
        row_dataframes = []
        For every json in the directory path:
            Load json file:
                create a new dict with keys that are child dictionary of the json file
                create a dataframe from the new dict
                add the dataframe to a row_dataframes list
        path_dataframe = pd.concat(row_dataframes)
    index_df = pd.concat(path_dataframes)
    save index df csv
    """

    # Load target data
    TARGET_DATA_DIR = Path( out_dir, 'diverse_communities_data_excerpts')
    T_P_MA = Path(TARGET_DATA_DIR, 'massachusetts', 'ma2019.csv')
    T_P_TX = Path(TARGET_DATA_DIR, 'texas', 'tx2019.csv')
    T_P_NA = Path(TARGET_DATA_DIR, 'national', 'national2019.csv')

    DATA_DICT_PATH = Path(TARGET_DATA_DIR, 'data_dictionary.json')

    ma_df = pd.read_csv(T_P_MA)
    tx_df = pd.read_csv(T_P_TX)
    na_df = pd.read_csv(T_P_NA)

    with open(DATA_DICT_PATH, 'r') as f:
        data_dict = json.load(f)

    path_dataframes = []
    label_props = [TEAM, ALGORITHM_NAME, EPSILON, SUBMISSION_NUMBER,
                   TARGET_DATASET, FEATURE_SET_NAME, VARIANT_LABEL]
    for path in paths:
        print('Processing path: {}'.format(path))
        row_dataframes = []
        for file in path.glob('**/*.json'):
            # check if file str contain report word
            if 'report' in str(file) or 'ui' in str(file):
                continue
            print('--Processing file: {}'.format(file))
            with open(file, 'r') as f:
                data = json.load(f)
                flatten_data = dict()
                for k in data.keys():
                    if not isinstance(data[k], dict):
                        flatten_data[k] = data[k]
                    else:
                        for ck in data[k].keys():
                            flatten_data[ck] = data[k][ck]
                # flatten_data[UNIQUE_LABEL] = create_label(flatten_data, label_props)
                flatten_data[DATA_PATH] = str(Path(*file.parts[-4:])).replace('.json', '.csv')
                flatten_data[LABELS_PATH] = str(Path(*file.parts[-4:]))
                print('Report Parent: {}'.format(file.parent))
                print([p.stem for p in file.parent.iterdir() if p.is_dir()])
                report_path = [Path(*p.parts[-4:]) for p in file.parent.iterdir()
                                if p.is_dir() and
                               (str(p.stem).startswith(str(file.stem))
                                or
                                str(p.stem).startswith((str('report_' + file.stem))))][0]
                print(report_path)
                print()
                flatten_data[REPORT_PATH] = str(report_path)
                if flatten_data[TARGET_DATASET] == 'ma2019':
                    target_df = ma_df
                elif flatten_data[TARGET_DATASET] == 'tx2019':
                    target_df = tx_df
                elif flatten_data[TARGET_DATASET] == 'national2019':
                    target_df = na_df

                features = flatten_data[FEATURES_LIST].split(', ')
                print(features)
                sub_target_df = target_df[features]
                flatten_data[FEATURE_SPACE_SIZE] = feature_space_size(sub_target_df, data_dict)

                row_dataframes.append(pd.DataFrame(flatten_data, index=[0]))
        path_dataframe = pd.concat(row_dataframes)
        path_dataframes.append(path_dataframe)
        print('Processed path: {}'.format(path))
    index_df = pd.concat(path_dataframes)
    # assert len(index_df[DEID_DATA_ID].unique()) == len(index_df)
    # reorder columns

    index_df = index_df[column_order]
    index_df = index_df.sort_values(by=column_order[:5])
    index_df.to_csv(str(Path(out_dir, 'index.csv')), index=False)
    return index_df

# paths = [Path("toy_synthetic_data/syn/synthetic"),
#          Path("toy_synthetic_data/syn/teams")]
# out_dir = Path('')

paths = [Path("crc_acceleration_bundle_1.0/crc_data_and_metric_bundle_1.1/deid_data")]
out_dir = Path('crc_acceleration_bundle_1.0/crc_data_and_metric_bundle_1.1')

# uncomment to update any key in the json files
# update_keys([paths[0]], 'variant', 'variant label')
if __name__ == "__main__":
    index_data(paths, out_dir)


