from pathlib import Path

from sdnist.gui.constants import (
    REPORT_DIR_PREFIX,
    METAREPORT_DIR_PREFIX,
    ARCHIVE_DIR_PREFIX
)

from sdnist.gui.strs import *

def count_path_types(root: Path):
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
                    counts[DEID_CSV_FILES] += 1
                elif f.suffix == '.json':
                    counts[META_DATA_FILES] += 1
                elif f.suffix == '.csv' and 'index' in f.name:
                    counts[INDEX_FILES] += 1
            elif f.is_dir():
                if ARCHIVE_DIR_PREFIX in f.name:
                    counts[ARCHIVE_FILES] += 1
                elif REPORT_DIR_PREFIX in f.name:
                    counts[REPORTS] += 1
                elif METAREPORT_DIR_PREFIX in f.name:
                    counts[METAREPORTS] += 1
                else:
                    _count_files(f)

    _count_files(root)
    return counts