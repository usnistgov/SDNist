from enum import Enum

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
LIBRARY_VERSION = 'library version'
LIBRARY_LINK = 'library link'
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

# Label Categories
BASE_LABELS = 'base labels'
REQUIRED_LABELS = 'required labels'
OPTIONAL_LABELS = 'optional labels'

label_titles = [
    TEAM,
    DEID_DATA_ID,
    TARGET_DATASET,
    ALGORITHM_TYPE,
    ALGORITHM_NAME,
    LIBRARY_NAME,
    LIBRARY_VERSION,
    LIBRARY_LINK,
    VARIANT_LABEL,
    VARIANT_LABEL_DETAIL,
    EPSILON,
    DELTA,
    FEATURE_SET_NAME,
    FEATURES_LIST,
    QUASI_IDENTIFIERS_SUBSET,
    PRIVACY_CATEGORY,
    PRIVACY_LABEL_DETAIL,
    RESEARCH_PAPERS,
    SUBMISSION_NUMBER,
    SUBMISSION_TIMESTAMP,
]


class LabelType(Enum):
    DROPDOWN = "dropdown"
    MULTI_DROPDOWN = "multi-dropdown"
    STRING = "string"
    LONG_STRING = "long-string"
    INT = "int"
    FLOAT = "float"

