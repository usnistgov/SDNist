from pathlib import Path
import pandas as pd
import json
import datetime
import shutil
import traceback

from sdnist.index import index, TARGET_DATASET
from sdnist.gui.constants import \
    REPORT_DIR_PREFIX, ARCHIVE_DIR_PREFIX, METAREPORT_DIR_PREFIX

from sdnist.report.helpers.progress_status import (
    ProgressStatus, ProgressLabels)

def create_archive_dir_path(data_root: Path):
    time_now = datetime.datetime.now().strftime('%m-%d-%YT%H.%M.%S')
    archive_dir = Path(data_root, 'archives',
                       f'{ARCHIVE_DIR_PREFIX}'
                       f'_{data_root.name}'
                       f'_{time_now}')

    return archive_dir

def archive(progress: ProgressStatus,
            data_root: Path,
            archive_path: Path,
            index_file: Path) -> Path:
    """
    Creates an SDNIST archive of deid csv files, their labels/metadata
    and SDNIST Data Evaluation Reports (DERs) for each deid csv file.
    data_root: path to the root directory of the deid datasets
    """
    try:
        # Check if index file exists. If not
        # then create an index file
        progress.update(str(archive_path),
                        ProgressLabels.STARTED)

        idx_df = pd.read_csv(index_file)

        # Create empty archive structure
        # data root dir
        # -- ma
        # ---- ma csv, labels and reports
        # -- tx
        # ---- tx csv, labels and reports
        # -- national
        # ---- national csv, labels and reports

        if not archive_path.exists():
            archive_path.mkdir(parents=True, exist_ok=True)

        ma_archive_dir = Path(archive_path, 'ma')
        tx_archive_dir = Path(archive_path, 'tx')
        na_archive_dir = Path(archive_path, 'national')

        target_dict = {
            'ma': ma_archive_dir,
            'tx': tx_archive_dir,
            'national': na_archive_dir
        }
        for target_name, target_archive_path in target_dict.items():
            if target_archive_path.exists():
                continue
            target_archive_path.mkdir()

        # archive csv files
        a_csv_files = data_root.glob('**/*.csv')

        # deid_csvs = [f for f in a_csv_files
        #              if ARCHIVE_DIR_PREFIX not in str(f) and
        #              REPORT_DIR_PREFIX not in str(f) and
        #              METAREPORT_DIR_PREFIX not in str(f) and
        #              f.name != 'index.csv']
        # # only deid csv file for which json metadata file also exists
        # deid_csvs = [
        #     f for f in deid_csvs
        #     if Path(str(f).replace('.csv', '.json')).exists()
        # ]
        idx_df = idx_df.reset_index(drop=True)
        for i, row in idx_df.iterrows():
            csv_file = Path(row['data path'])
            # labels path
            lbl_path = Path(str(csv_file).replace('.csv', '.json'))
            # report directory
            csv_parent = csv_file.parent
            rep_path = Path(row['report path'])

            # reports_path = Path(csv_parent, 'reports')
            # rep_path = Path(reports_path, REPORT_DIR_PREFIX)
            # if reports_path.exists():
            #     rep_path = [d
            #                 for d in reports_path.iterdir()
            #                 if REPORT_DIR_PREFIX in str(d) and
            #                 csv_file.stem in str(d)]
            #     rep_path = sorted(rep_path, key=lambda x: str(x),
            #                       reverse=True)
            #     rep_path = rep_path[-1]

            # Do not include this csv_file if
            # SDNIST DER is not available
            if rep_path.exists():
                with open(lbl_path, 'r') as f:
                    labels = json.load(f)
                target_dataset = labels['labels'][TARGET_DATASET]
                target_dataset = target_dataset.lower()[:-4]

                target_archive_path = target_dict[target_dataset]

                # copy csv file to target archive path
                shutil.copy(csv_file, target_archive_path)
                # copy labels file to target archive path
                shutil.copy(lbl_path, target_archive_path)
                # copy report directory to target archive path
                shutil.copytree(rep_path, Path(target_archive_path, rep_path.name))
            progress.update(str(archive_path),
                            ProgressLabels.PROCESSING_FILES,
                            str(i))
        # copy index file to archive dir
        shutil.copy(index_file, archive_path)
        progress.update(str(archive_path),
                        ProgressLabels.CREATING_ARCHIVE)
    except Exception as e:
       traceback.print_exc()
    return archive_path



