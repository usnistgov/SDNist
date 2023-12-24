from pathlib import Path
import pandas as pd
import json

from sdnist.index.feature_space import feature_space_size
from sdnist.gui.constants import (
    REPORT_DIR_PREFIX,
    METAREPORT_DIR_PREFIX,
    ARCHIVE_DIR_PREFIX
)

from sdnist.report.helpers.progress_status import (
    ProgressStatus, ProgressLabels)
import sdnist.strs as strs


# index lables
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
ONLY_NUMERICAL_RESULTS = 'only numerical results'

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
    ONLY_NUMERICAL_RESULTS,
    DEID_DATA_ID
]

def get_metadata_files(data_root: str):
    data_root = Path(data_root)
    json_files = data_root.glob('**/*.json')
    metadata_files = [f for f in json_files
                      if (REPORT_DIR_PREFIX not in str(f) and
                           ARCHIVE_DIR_PREFIX not in str(f) and
                           METAREPORT_DIR_PREFIX not in str(f))]
    # keep only files that has csv file
    metadata_files = [f for f in metadata_files
                      if Path(str(f).replace('.json', '.csv')).exists()]
    return metadata_files

def index(progress: ProgressStatus, data_root: str):
    """
    Creates an index csv file indexing all the
    deid dataset available in the data_root or subdirectories
    of the data_root:
    data_root: path to the root directory of the deid datasets
    """
    out_path = Path(data_root, 'index.csv')

    progress.update(str(out_path),
                    ProgressLabels.STARTED)

    data_dir = Path(__file__).parent.parent.parent
    TARGET_DATA_DIR = Path(data_dir, 'diverse_communities_data_excerpts')

    T_P_MA = Path(TARGET_DATA_DIR, 'massachusetts', 'ma2019.csv')
    T_P_TX = Path(TARGET_DATA_DIR, 'texas', 'tx2019.csv')
    T_P_NA = Path(TARGET_DATA_DIR, 'national', 'national2019.csv')

    DATA_DICT_PATH = Path(TARGET_DATA_DIR, 'data_dictionary.json')

    ma_df = pd.read_csv(T_P_MA)
    tx_df = pd.read_csv(T_P_TX)
    na_df = pd.read_csv(T_P_NA)

    with open(DATA_DICT_PATH, 'r') as f:
        data_dict = json.load(f)

    index_rows = []

    # remove all files that SDNIST_DER in their path
    metadata_files = get_metadata_files(data_root)

    for i, metadata_file in enumerate(metadata_files):
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)

        metadata = metadata['labels']
        #TODO FIX PATH
        metadata[DATA_PATH] = str(metadata_file)\
            .replace('.json', '.csv')
        metadata[LABELS_PATH] = str(metadata_file)

        # get report path
        reports_path = Path(metadata_file.parent, 'reports')
        report_json_path = Path(reports_path, 'report.json')
        if reports_path.exists():
            report_dirs = [p
                           for p in reports_path.iterdir()
                           if 'SDNIST_DER' in str(p)]

            report_dirs = [d for d in report_dirs
                          if metadata_file.stem in str(d)]
            report_dirs = [str(r) for r in report_dirs]
            report_dirs = sorted(report_dirs, reverse=True)

            metadata[REPORT_PATH] = str(report_dirs[0])

            report_json_path = Path(report_dirs[0], 'report.json')
            k = 1
            while not report_json_path.exists() and k < len(report_dirs):
                report_json_path = Path(report_dirs[k], 'report.json')
                k += 1

        if report_json_path.exists():
            with open(report_json_path, 'r') as f:
                report_json = json.load(f)
            target_df = None
            if metadata[TARGET_DATASET] == 'ma2019':
                target_df = ma_df
            elif metadata[TARGET_DATASET] == 'tx2019':
                target_df = tx_df
            elif metadata[TARGET_DATASET] == 'national2019':
                target_df = na_df

            features = metadata[FEATURES_LIST].split(', ')
            sub_target_df = target_df[features]

            metadata[FEATURE_SPACE_SIZE] = metadata[FEATURE_SPACE_SIZE]
            metadata[ONLY_NUMERICAL_RESULTS] = \
                report_json[strs.CONTAINS_ONLY_NUMERICAL_RESULTS]
            index_rows.append(pd.DataFrame(metadata, index=[0]))
        progress.update(str(out_path),
                        ProgressLabels.PROCESSING_FILES,
                        str(i))
        # get the target dataset
    index_df = pd.concat(index_rows, ignore_index=True)

    # columns in index
    c_in_idx = [c for c in index_df.columns
                if c in column_order]
    index_df = index_df[c_in_idx]
    index_df = index_df.sort_values(by=c_in_idx[:5])
    index_df = index_df.reset_index(drop=True)

    index_df.to_csv(out_path, index=False)

    progress.update(str(out_path),
                    ProgressLabels.CREATING_INDEX)
    return index_df





