from enum import Enum

class PathType(Enum):
    CSV = 'csv'  # is a deid csv file
    JSON = 'json'  # is json metadata file
    REPORT = 'report'  # is a sdnist report directory
    METAREPORT = 'metareport'  # is a sdnist metareport directory
    ARCHIVE = 'archive'  # is a sdnist deid data archive directory
    INDEX = 'index'  # is a sdnist deid data index csv file
    DEID_DATA_DIR = 'deid_data_dir' # is a sdnist deid data directory
    METAREPORTS = 'metareports'  # is a sdnist metareports directory
    REPORTS = 'reports'  # is a sdnist reports directory
    ARCHIVES = 'archives'  # is a sdnist archives directory
