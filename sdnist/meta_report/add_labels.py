from meta_report.common import \
    json, Dict, List, Path, pd, Optional
import hashlib

# SDC = 'Statistical Disclosure Control'
# DP = 'Differential Privacy'
# NON_DP = 'Synthetic Data (Non-differentially Private)'
# DP_KANON = 'Differential Privacy, k-anonymity'
# SDC = 'Statistical Disclosure Control anonymization techniques-- Does direct perturbation, anonymization, redaction or generalization on individual records of target data'
# QUERY_MATCHING = 'Query Matching based synthetic data techniques-- Initializes a default synthetic data distribution and iteratively updates it to mimic query results on target data, using optimization or constraint satisfaction approaches'
# NEURAL_NET = 'Neural Network based synthetic data techniques-- Includes both GAN and Transformer Networks / Autoencoders'
# STAT_MODEL = 'Statistical Model based synthetic data techniques-- Uses some approach, other than a neural network, to construct a model of the feature relationships in the target data and uses this model to generate new records.'
# GEOMETRIC = 'Geometric based sampling techniques-- Samples new records directly from the feature space based on the geometry of the target distribution.  May involve interpolation or clustering of records in the target data.'
# HISTOGRAM = 'Histogram based generation techniques-- Transforms the target data into a set of counts of record occurrences, then adds noise to these counts to produce new data'.

SDC = 'sdc'
DP = 'dp'
NON_DP = 'non_dp'


privacy_map = {
    "kanonymity": SDC,
    "pram": SDC,
    "subsample_40pcnt": SDC,
    "subsample_5pcnt": SDC,
    "subsample_1pcnt": SDC,
    "mwem": DP,
    "cart": NON_DP,
    "ctgan": NON_DP,
    "tvae": NON_DP,
    "DPHist": DP,
    "patectgan": DP,
    "pacsynth": DP,
    "fastml": NON_DP,
    "mst": DP,
    "copula-gan": NON_DP,
    "MostlyAI SD": NON_DP,
    "Sarus SDG": DP,
    "gaussian-copula": NON_DP,
    "dpgan": DP,
    "pategan": DP,
    "adsgan": NON_DP,
    "MWEM+PGM": DP,
    "Genetic SD": DP,
    "catall": DP,
    "ipf": DP,
    "catall_NonDP": NON_DP,
    "ipf_NonDP": NON_DP,
    "privbayes": DP,
    "bayesian_network": NON_DP,
}

QUERY_MATCHING = 'query matching'
STAT_MODEL = 'stat model'
NEURAL_NET = 'neural net'
HISTOGRAM = 'histogram'


algorithm_type_map = {
    "kanonymity": SDC,
    "pram": SDC,
    "subsample_40pcnt": SDC,
    "subsample_5pcnt": SDC,
    "subsample_1pcnt": SDC,
    "mwem": QUERY_MATCHING,
    "cart": STAT_MODEL,
    "ctgan": NEURAL_NET,
    "tvae": NEURAL_NET,
    "DPHist": HISTOGRAM,
    "patectgan": NEURAL_NET,
    "pacsynth": QUERY_MATCHING,
    "fastml": NEURAL_NET,
    "mst": STAT_MODEL,
    "copula-gan": NEURAL_NET,
    "MostlyAI SD": NEURAL_NET,
    "Sarus SDG": NEURAL_NET,
    "gaussian-copula": STAT_MODEL,
    "dpgan": NEURAL_NET,
    "pategan": NEURAL_NET,
    "adsgan": NEURAL_NET,
    "MWEM+PGM": QUERY_MATCHING,
    "Genetic SD": QUERY_MATCHING,
    "catall": HISTOGRAM,
    "ipf": QUERY_MATCHING,
    "catall_NonDP": HISTOGRAM,
    "ipf_NonDP": QUERY_MATCHING,
    "privbayes": STAT_MODEL,
    "bayesian_network": STAT_MODEL,
}

team_map = {
    "DPSyn": "DPSyn-synthpop"
}

algorithm_map = {
    "MOSTLY AI SD Platform": "MostlyAI SD",
    "GeneticSD": "Genetic SD",
}

library_map = {
    "MostlyAI SD": "MostlyAI SD",
    "MWEM+PGM": "LostInTheNoise",
    "Genetic SD": "Genetic SD",
    "Sarus SDG": "Sarus SDG",
}

# map for renaming label names in labels.json
label_rename_map = {
    "library": "library name",
    "feature set": "feature set name",
    "custom features": "features list",
    "privacy": "privacy category"
}

privacy_label_detail_map = {
    "kanonymity": '',
    "pram": '',
    "subsample_40pcnt": '',
    "subsample_5pcnt": '',
    "subsample_1pcnt": '',
    "mwem": '',
    "cart": '',
    "ctgan": '',
    "tvae": '',
    "DPHist": '',
    "patectgan": '',
    "pacsynth": '',
    "fastml": '',
    "mst": '',
    "copula-gan": '',
    "MostlyAI SD": '',
    "Sarus SDG": '',
    "gaussian-copula": '',
    "dpgan": '',
    "pategan": '',
    "adsgan": '',
    "MWEM+PGM": '',
    "Genetic SD": '',
    "catall": '',
    "ipf": '',
    "catall_NonDP": '',
    "ipf_NonDP": '',
    "privbayes": '',
    "bayesian_network": '',
}


def labels_hash(data_str: str) -> str:
    hasher = hashlib.sha1()
    hasher.update(data_str.encode('utf-8'))
    return hasher.hexdigest()


def add_privacy(paths: List[Path]):
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
    data_dict_path = Path('diverse_communities_data_excerpts/data_dictionary.json')
    with open(data_dict_path, 'r') as f:
        data_dict = json.load(f)

    # detailed privacy labels dataframe
    dp_df = pd.read_csv('detail_privacy_labels.csv')

    # check nan in dp_df and replace with string 'CRC'
    dp_df = dp_df.fillna('CRC')

    all_features = data_dict.keys()

    path_dataframes = []
    for path in paths:
        print('Processing path: {}'.format(path))
        row_dataframes = []
        for file in path.glob('**/*.json'):
            # print(file)
            if 'report' in str(file) or 'ui' in str(file):
                continue
            # check if file str contain report word
            print('--Processing file: {}'.format(file))
            deid_data_path = file.parent / f'{file.stem}.csv'
            deid_data = pd.read_csv(deid_data_path)
            with open(deid_data_path, 'r') as f:
                data_lines = f.readlines()
            data_str = ''
            for l in data_lines:
                data_str += l
            deid_data = deid_data.loc[:, ~deid_data.columns.str.contains('^Unnamed')]
            # sort deid_data columns with all_features
            deid_data_features = deid_data.columns.tolist()
            features_list = [x for x in all_features if x in deid_data_features]

            with open(file, 'r') as f:
                data = json.load(f)
            if 'labels' not in data.keys():
                d_c = data.copy()
                data = dict()
                data['labels'] = d_c
            if 'team' in data['labels'].keys():
                if data['labels']['team'] in team_map.keys():
                    print('Update Team: ', data['labels']['team'])
                    data['labels']['team'] = team_map[data['labels']['team']]
            if 'algorithm name' in data['labels'].keys():
                if data['labels']['algorithm name'] in algorithm_map.keys():
                    print('Update Algo: ', data['labels']['team'])
                    data['labels']['algorithm name'] = \
                        algorithm_map[data['labels']['algorithm name']]

            if 'library name' not in data['labels'].keys():
                data['labels']['library name'] = library_map[data['labels']['algorithm name']]
                print('Added Library: ', data['labels']['library name'])
            # if 'privacy' in data['labels'].keys():
            #     continue
            algo = data['labels']['algorithm name']
            data['labels']['algorithm type'] = algorithm_type_map[algo]
            data['labels']['privacy category'] = privacy_map[algo]
            data['labels']['features list'] = ', '.join(features_list)
            # data['labels']['privacy label detail'] = privacy_label_detail_map[algo]

            # change columns names
            for k in list(data['labels'].keys()):
                if k in label_rename_map.keys():
                    old_k = k
                    new_k = label_rename_map[k]
                    data['labels'][new_k] = data['labels'].pop(old_k)

            # if 'deid data id' in data['labels'].keys():
            #     old_data_id = data['labels']['deid data id']
            #     new_data_id = labels_hash(data_str)
            #     if old_data_id == new_data_id:
            #         print('EQUAL')
            if 'deid data id' not in data['labels'].keys():
                data_id = labels_hash(data_str)
                data['labels']['deid data id'] = data_id

            if "pram features exception" in data['labels'].keys():
                data['labels'].pop("pram features exception")

            if "pram features" in data['labels'].keys():
                data['labels']['quasi identifiers subset'] = data['labels']["pram features"]
                data['labels'].pop("pram features")

            if "submission timestamp" not in data['labels'].keys():
                data['labels']['submission timestamp'] = '5/20/2023 00:00:00'

            if "team" not in data['labels'].keys():
                data['labels']['team'] = 'CRC'

            team = data['labels']['team']
            algo = data['labels']['algorithm name']
            lib = data['labels']['library name']

            if "privacy label detail" not in data['labels'].keys():
                m1 = dp_df['team'] == team
                m2 = dp_df['algorithm name'] == algo
                m3 = dp_df['library name'] == lib

                m = m1 & m2 & m3
                sub_dp_df = dp_df[m]
                if sub_dp_df.shape[0] == 1:
                    data['labels']['privacy label detail'] = sub_dp_df['privacy properties'].values[0]

            # if "research papers" not in data['labels'].keys():
            m1 = dp_df['team'] == team
            m2 = dp_df['algorithm name'] == algo
            m3 = dp_df['library name'] == lib

            m = m1 & m2 & m3
            sub_dp_df = dp_df[m]
            print('Trying to add research paper')
            if sub_dp_df.shape[0] == 1:
                print('Added research paper')
                data['labels']['research papers'] = sub_dp_df['Research Papers'].values[0]

            with open(file, 'w') as f:
                json.dump(data, f, indent=4)
        print('Processed path: {}'.format(path))


paths = [Path("crc_acceleration_bundle_1.0",
              "crc_data_and_metric_bundle_1.1",
              "deid_data")]
# out_dir = Path('')


# paths = [Path("data/internal"),
#          Path("data/crc_teams")]
# out_dir = Path('data')

# uncomment to update any key in the json files
# update_keys([paths[0]], 'variant', 'variant label')
if __name__ == "__main__":
    add_privacy(paths)
