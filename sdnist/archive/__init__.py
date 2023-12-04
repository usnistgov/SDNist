from pathlib import Path
import pandas as pd
import json
import datetime
import shutil

from sdnist.index import index, TARGET_DATASET
from sdnist.gui.constants import \
    REPORT_DIR_PREFIX, ARCHIVE_DIR_PREFIX


def archive(data_root: str):
    """
    Creates an SDNIST archive of deid csv files, their labels/metadata
    and SDNIST Data Evaluation Reports (DERs) for each deid csv file.
    data_root: path to the root directory of the deid datasets
    """
    data_root = Path(data_root)

    # Check if index file exists. If not
    # then create an index file
    index_path = Path(data_root, 'index.csv')
    if not index_path.exists():
        index_df = index(str(data_root))
        index_df.to_csv(index_path)

    # Create empty archive structure
    # data root dir
    # -- ma
    # ---- ma csv, labels and reports
    # -- tx
    # ---- tx csv, labels and reports
    # -- national
    # ---- national csv, labels and reports
    time_now = datetime.datetime.now().strftime('%m-%d-%YT%H.%M.%S')
    archive_dir = Path(data_root, 'archives',
                       f'{ARCHIVE_DIR_PREFIX}'
                       f'_{data_root.name}'
                       f'_{time_now}')

    if not archive_dir.exists():
        archive_dir.mkdir(parents=True, exist_ok=True)

    ma_archive_dir = Path(archive_dir, 'ma')
    tx_archive_dir = Path(archive_dir, 'tx')
    na_archive_dir = Path(archive_dir, 'national')

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

    for csv_file in a_csv_files:
        if ARCHIVE_DIR_PREFIX in str(csv_file):
            continue
        # labels path
        lbl_path = Path(str(csv_file).replace('.csv', '.json'))

        # report directory
        rep_path = [d
                    for d in csv_file.parent.iterdir()
                    if REPORT_DIR_PREFIX in str(d) and
                    csv_file.stem in str(d)]

        # Do not include this csv_file if
        # labels are not available
        if not lbl_path.exists():
            continue

        # Do not include this csv_file if
        # SDNIST DER is not available
        if len(rep_path) == 0:
            continue

        rep_path = sorted(rep_path, key=lambda x: str(x),
                          reverse=True)
        rep_path = rep_path[-1]

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

    # copy index file to archive dir
    shutil.copy(index_path, archive_dir)



