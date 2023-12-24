from typing import Optional, Dict, Tuple, List
import pandas as pd
import shutil

from pathlib import Path

from sdnist.gui.constants import (
    REPORT_DIR_PREFIX,
    METAREPORT_DIR_PREFIX,
    ARCHIVE_DIR_PREFIX
)

from sdnist.gui.helper import PathType


from sdnist.gui.strs import *
from sdnist.index import ONLY_NUMERICAL_RESULTS

from sdnist.report.helpers import (
    ProgressStatus
)
from sdnist.gui.handlers.files import FilesTreeHandler
from sdnist.report.dataset.target import TargetLoader

IS_BUSY = 'is busy'

def get_path_types(path: Path,
                   progress: Optional[ProgressStatus] = None,
                   file_handler: Optional[FilesTreeHandler] = None) -> \
        Optional[Tuple[PathType, Dict]]:
    path_status = dict()
    path_type = None
    if progress and progress.is_busy():
        # can create item only if not currently busy
        path_status[IS_BUSY] = True
    if path.is_file():
        if path.suffix == '.csv' and 'index' not in path.name:
            df = pd.read_csv(path, nrows=0)
            is_deid_csv = file_handler.target_loader.is_deid_csv(df)
            del df
            if is_deid_csv:
                path_type = PathType.DEID_CSV
                metadata_path = Path(str(path).replace('.csv', '.json'))
                path_status[METADATA] = metadata_path.exists()
            else:
                path_type = PathType.CSV
        elif path.suffix == '.json':
            d_csv = Path(str(path).replace('.json', '.csv'))
            if d_csv.exists():
                path_type = PathType.DEID_JSON
            else:
                path_type = PathType.JSON

        elif path.suffix == '.csv' and 'index' in path.name:
            path_type = PathType.INDEX
            has_non_numerical_reports = check_has_non_numerical_reports(path)
            path_status[NUMERICAL_METRIC_RESULTS] = has_non_numerical_reports
    elif path.is_dir():
        if REPORT_DIR_PREFIX in str(path):
            path_type = PathType.REPORT
        elif METAREPORT_DIR_PREFIX in str(path):
            path_type = PathType.METAREPORT
        elif ARCHIVE_DIR_PREFIX in str(path):
            path_type = PathType.ARCHIVE
        elif METAREPORTS.lower() in str(path):
            path_type = PathType.METAREPORTS
        elif REPORTS.lower() in str(path):
            path_type = PathType.REPORTS
        elif ARCHIVES in str(path):
            path_type = PathType.ARCHIVES
        else:
            path_type = PathType.DEID_DATA_DIR
            path_type_counts = file_handler.get_counts(path)
            counts = path_type_counts
            index_path = Path(path, 'index.csv')

            has_non_numerical_reports = check_has_non_numerical_reports(index_path)
            path_status[NUMERICAL_METRIC_RESULTS] = has_non_numerical_reports

            path_status[NUMERICAL_METRIC_RESULTS] = has_non_numerical_reports
            path_status[INDEX_FILES] = 1 if index_path.exists() else 0
            path_status[DEID_CSV_FILES] = counts[DEID_CSV_FILES]
            path_status[REPORTS] = counts[REPORTS]
            path_status[META_DATA_FILES] = counts[META_DATA_FILES]

    return path_type, path_status


def check_has_non_numerical_reports(path: Path) -> bool:
    if path.exists():
        idx_df = pd.read_csv(path)
        if ONLY_NUMERICAL_RESULTS in idx_df.columns.to_list():
            non_num_id = idx_df[idx_df[ONLY_NUMERICAL_RESULTS] == False]
            if len(non_num_id):
                return True
    return False

def count_path_types(root: Path, target_loader: TargetLoader):
    """
    This method counts each type of path in the
    root directory. And also remove unfinished
    reports, metareports and archives.
    """
    # recursively count files in directory
    counts = {
        DEID_CSV_FILES: 0,
        META_DATA_FILES: 0,
        REPORTS: 0,
        METAREPORTS: 0,
        INDEX_FILES: 0,
        ARCHIVE_FILES: 0
    }

    def _count_files(root: Path):
        for f in root.iterdir():
            if f.is_file():
                if f.suffix == '.csv' and 'index' not in f.name:
                    df = pd.read_csv(f, nrows=0)
                    is_deid_csv = target_loader.is_deid_csv(df)
                    del df
                    if is_deid_csv:
                        counts[DEID_CSV_FILES] += 1
                elif f.suffix == '.json':
                    d_csv = Path(str(f).replace('.json', '.csv'))
                    if d_csv.exists():
                        counts[META_DATA_FILES] += 1
                elif f.suffix == '.csv' and 'index' in f.name:
                    counts[INDEX_FILES] += 1
            elif f.is_dir():
                if ARCHIVE_DIR_PREFIX in f.name:
                    index_path = Path(f, 'index.csv')
                    if index_path.exists():
                        counts[ARCHIVE_FILES] += 1
                    # else:
                    #     shutil.rmtree(f)
                elif REPORT_DIR_PREFIX in f.name:
                    report_json = Path(f, 'report.json')
                    report_html = Path(f, 'report.html')
                    if report_html.exists() and report_json.exists():
                        counts[REPORTS] += 1
                    else:
                        shutil.rmtree(f)
                elif METAREPORT_DIR_PREFIX in f.name:
                    metareport_json = Path(f, 'report.json')
                    ui_json = Path(f, 'ui.json')
                    if metareport_json.exists() and ui_json.exists():
                        counts[METAREPORTS] += 1
                    else:
                        shutil.rmtree(f)
                else:
                    _count_files(f)

    _count_files(root)

    return counts