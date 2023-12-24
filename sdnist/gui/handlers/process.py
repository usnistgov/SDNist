from typing import List
from pathlib import Path
import pandas as pd
import sys
import os

from multiprocessing import Pool
from multiprocessing.managers import BaseManager

from sdnist.report.helpers.progress_status import (
    ProgressStatus, ProgressType)

from sdnist.metareport.__main__ import (
    run as metareport_run
)

from sdnist.report.__main__ import (
    run as report_run
)

from sdnist.index import (
    index, get_metadata_files
)

from sdnist.archive import (
    archive, create_archive_dir_path
)
from contextlib import contextmanager

def suppress_output():
    sys.stdout.flush()
    sys.stderr.flush()
    devnull = os.open(os.devnull, os.O_WRONLY)
    os.dup2(devnull, sys.stdout.fileno())
    os.dup2(devnull, sys.stderr.fileno())

class ProcessHandler:
    def __init__(self, progress: ProgressStatus):
        self.progress = progress
    def get_pool(self, n_pool: int = 1):
        return Pool(n_pool)

    def metareport(self, input_cnf):
        BaseManager.register('ProgressStatus', ProgressStatus)
        self.manager = BaseManager()
        self.manager.start()
        self.progress = self.manager.ProgressStatus(ProgressType.METAREPORT)

        pool = self.get_pool()
        input_cnf = (
            self.progress,
            input_cnf['reports_path'],
            input_cnf['metareport_out_dir'],
            input_cnf['data_dict'],
            input_cnf['density_bins_description'],
            input_cnf['report_title']
        )
        str_path = str(input_cnf[2])
        self.progress.add_item(str_path)
        pool.apply_async(metareport_run, (*input_cnf,))

    def reports(self, inputs: List):
        BaseManager.register('ProgressStatus', ProgressStatus)
        self.manager = BaseManager()
        self.manager.start()
        self.progress = self.manager.ProgressStatus(ProgressType.REPORTS)
        pool_size = len(inputs) if len(inputs) < 5 else 5

        pool = self.get_pool(pool_size)

        for i in inputs:
            i = (self.progress, ) + i
            str_path = str(i[2])
            self.progress.add_item(str_path)
            pool.apply_async(report_run, (*i,))


    def archive(self, archive_dir: Path, archive_path: Path):
        BaseManager.register('ProgressStatus', ProgressStatus)
        self.manager = BaseManager()
        self.manager.start()
        self.progress = self.manager.ProgressStatus(ProgressType.ARCHIVE)

        pool = self.get_pool()
        index_path = Path(archive_dir, 'index.csv')
        idx_df = pd.read_csv(index_path)
        input_cnf = (self.progress, archive_dir, archive_path, index_path)
        self.progress.add_item(str(archive_path), idx_df.shape[0])
        pool.apply_async(archive, (*input_cnf,))

    def index(self, index_dir: Path):
        BaseManager.register('ProgressStatus', ProgressStatus)
        self.manager = BaseManager()
        self.manager.start()
        self.progress = self.manager.ProgressStatus(ProgressType.INDEX)

        pool = self.get_pool()
        index_path = Path(index_dir, 'index.csv')
        metadata_files = get_metadata_files(str(index_dir))
        self.progress.add_item(str(index_path), len(metadata_files))
        input_cnf = (self.progress, str(index_dir))
        pool.apply_async(index, (*input_cnf,))


