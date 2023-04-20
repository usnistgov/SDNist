from meta_report.common import \
    json, Dict, List, Path, pd, Optional

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

    default_sort_keys = ['feature set', 'target dataset']
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

    return res_df['report_path'].tolist()

def index_data(paths: List[Path]):
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
    path_dataframes = []
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
                flatten_data['file_path'] = str(file).replace('.json', '.csv')
                flatten_data['labels_path'] = str(file)
                print('Report Parent: {}'.format(file.parent))
                print([p.stem for p in file.parent.iterdir() if p.is_dir()])
                report_path = [p for p in file.parent.iterdir()
                                if p.is_dir() and
                               (str(p.stem).startswith(str(file.stem))
                                or
                                str(p.stem).startswith((str('report_' + file.stem))))][0]
                print(report_path)
                print()
                flatten_data['report_path'] = str(report_path)
                row_dataframes.append(pd.DataFrame(flatten_data, index=[0]))
        path_dataframe = pd.concat(row_dataframes)
        path_dataframes.append(path_dataframe)
        print('Processed path: {}'.format(path))
    index_df = pd.concat(path_dataframes)
    index_df.to_csv('index.csv')
    return index_df

paths = [Path("toy_synthetic_data/syn/synthetic"),
         Path("toy_synthetic_data/syn/teams")]

# uncomment to update any key in the json files
# update_keys([paths[0]], 'variant', 'variant label')
if __name__ == "__main__":
    index_data(paths)


