import queue
from typing import List
from multiprocessing import Lock
from enum import Enum

from queue import Queue


class ProgressLabels(Enum):
    # only an indicator that report generation is started
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


class ProgressStatus:
    def __init__(self):
        # -1 because STARTED label is not a progress number.
        self.single_report_max_progress = \
            len(list(ProgressLabels)) - 1
        self.reports = dict()
        self.max_progress = 0
        self.last_progress = 0
        self.current_progress = 0
        self.completed_reports: List[str] = []
        self.progress_label = ''
        self.updates = Queue()
        self.lock = Lock()

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
        return (self.current_progress/self.max_progress)*100

    def get_completed_reports(self):
        return self.completed_reports

    def add_report(self, report_name: str):
        with self.lock:
            self.reports[report_name] = (0, None)
            self.max_progress = self.single_report_max_progress * len(self.reports)

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

    def update(self, report_name: str, label: ProgressLabels):
        with self.lock:
            progress = list(ProgressLabels).index(label)
            self.reports[report_name] = (progress, label)
            self.last_progress = self.current_progress
            self.current_progress = sum([x[0] for x in self.reports.values()])
            self.progress_label = label
            progress_percent = (progress
                                / self.single_report_max_progress) \
                * 100
            self.updates.put((report_name, label, progress_percent))
            if label == ProgressLabels.CREATING_EVALUATION_REPORT:
                self.completed_reports.append(report_name)

