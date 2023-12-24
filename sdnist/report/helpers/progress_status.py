import queue
from typing import List, Optional
from multiprocessing import Lock
from enum import Enum

from queue import Queue


class ProgressType(Enum):
    REPORTS = 'reports'
    METAREPORT = 'metareport'
    ARCHIVE = 'archive'
    INDEX = 'index'

class ProgressLabels(Enum):
    # indicator that report generation is started
    STARTED = 'STARTED'
    UNIVARIATES = 'Univariates'
    CORRELATIONS = 'Correlations'
    K_MARGINAL = 'K-Marginal'
    PROPENSITY_MSE = 'PropensityMSE'
    LINEAR_REGRESSION = 'Linear Regression'
    PCA = 'PCA'
    INCONSISTENCIES = 'Inconsistencies'
    UNIQUE_EXACT_MATCHES = 'Unique Exact Matches'
    APPARENT_MATCH_DISTRIBUTION = 'Apparent Match Distribution'
    SAVING_REPORT_DATA = 'Saving Report Data'
    CREATING_EVALUATION_REPORT = 'Creating Evaluation Report'
    # METAREPORT progress indicators
    COPYING_REPORTS = 'Copying Reports'
    CREATING_METAREPORT = 'Creating Meta Report'
    # Index and Archive progess indicators
    PROCESSING_FILES = 'Processing Files'
    CREATING_INDEX = 'Creating Index'
    CREATING_ARCHIVE = 'Creating Archive'

report_progress = [
    ProgressLabels.STARTED,
    ProgressLabels.UNIVARIATES,
    ProgressLabels.CORRELATIONS,
    ProgressLabels.K_MARGINAL,
    ProgressLabels.PROPENSITY_MSE,
    ProgressLabels.LINEAR_REGRESSION,
    ProgressLabels.PCA,
    ProgressLabels.INCONSISTENCIES,
    ProgressLabels.UNIQUE_EXACT_MATCHES,
    ProgressLabels.APPARENT_MATCH_DISTRIBUTION,
    ProgressLabels.SAVING_REPORT_DATA,
    ProgressLabels.CREATING_EVALUATION_REPORT
]

metareport_progress = [
    ProgressLabels.STARTED,
    ProgressLabels.COPYING_REPORTS,
    ProgressLabels.CORRELATIONS,
    ProgressLabels.UNIQUE_EXACT_MATCHES,
    ProgressLabels.PCA,
    ProgressLabels.LINEAR_REGRESSION,
    ProgressLabels.CREATING_METAREPORT
]

progress_labels_dict = {
    ProgressType.REPORTS: report_progress,
    ProgressType.METAREPORT: metareport_progress,
    ProgressType.INDEX: [ProgressLabels.STARTED,
                         ProgressLabels.PROCESSING_FILES,
                         ProgressLabels.CREATING_INDEX],
    ProgressType.ARCHIVE: [ProgressLabels.STARTED,
                           ProgressLabels.PROCESSING_FILES,
                           ProgressLabels.CREATING_ARCHIVE]
}

max_progress_dict = {
    ProgressType.REPORTS: len(report_progress),
    ProgressType.METAREPORT: len(metareport_progress),
    ProgressType.INDEX: 1,
    ProgressType.ARCHIVE: 1
}

class ProgressStatus:
    def __init__(self,
                 progress_type: ProgressType,
                 ):
        # -1 because STARTED label is not a progress number.
        self.progress_type = progress_type
        self.single_item_max_progress = max_progress_dict[progress_type] - 1

        self.items = dict()
        self.max_progress = 0
        self.last_progress = 0
        self.current_progress = 0
        self.completed = False
        self.completed_items: List[str] = []
        self.progress_label = ''
        self.updates = Queue()
        self.lock = Lock()

    def get_progress_type(self):
        return self.progress_type

    def get_max_progress(self):
        return self.max_progress

    def get_current_progress(self):
        return self.current_progress

    def set_current_progress(self, value: int):
        self.current_progress = value

    def get_last_progress(self):
        return self.last_progress

    def set_last_progress(self, value):
        self.last_progress = value

    def get_progress_label(self):
        return self.progress_label

    def get_progress_percent(self):
        prog =  (self.current_progress/self.max_progress)*100
        return prog

    def get_completed_items(self):
        return self.completed_items

    def add_item(self, item_name: str,
                   max_progress: Optional[int] = None):
        with self.lock:
            self.completed = False
            self.items[item_name] = (0, None)
            if max_progress is not None:
                self.single_item_max_progress = max_progress
            self.max_progress = self.single_item_max_progress * len(self.items)

    def is_busy(self):
        busy = (self.current_progress < self.max_progress
                or not self.updates.empty())
        return busy

    def is_completed(self):
        res = self.completed
        self.completed = False
        return res

    def has_updates(self):
        with self.lock:
            return not self.updates.empty()

    def get_updates(self):
        with self.lock:
            updates = []
            while not self.updates.empty():
                try:
                    updates.append(self.updates.get())
                except queue.Empty:
                    break
            return updates

    def update(self,
               item_name: str,
               label: ProgressLabels,
               extra_label: str = ''):
        with self.lock:
            if len(extra_label) and extra_label.isnumeric():
                progress = int(extra_label)
            else:
                prog_list = progress_labels_dict[self.progress_type]
                progress = prog_list.index(label)

            self.last_progress = self.current_progress
            self.progress_label = label
            if label in [
                ProgressLabels.CREATING_ARCHIVE,
                ProgressLabels.CREATING_INDEX]:
                self.current_progress = self.current_progress + 1
                progress_percent = 100
            else:
                self.items[item_name] = (progress, label)
                self.last_progress = self.current_progress
                self.current_progress = sum([x[0] for x in self.items.values()])

                progress_percent = (progress
                                    / self.single_item_max_progress) \
                    * 100

            self.updates.put((item_name, label, extra_label, progress_percent))
            if label in [
                ProgressLabels.CREATING_EVALUATION_REPORT,
                ProgressLabels.CREATING_METAREPORT,
                ProgressLabels.CREATING_ARCHIVE,
                ProgressLabels.CREATING_INDEX]:
                self.completed_items.append(item_name)
            if (self.current_progress > 0
                    and self.current_progress == self.max_progress):
                self.completed = True


