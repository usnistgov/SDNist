from typing import Optional, Dict
from pathlib import Path
import shutil
import pygame as pg
import pygame_gui as pggui

from pygame_gui.ui_manager import UIManager

from sdnist.gui.windows.window import AbstractWindow
from sdnist.gui.windows.metareport.filter import (
    MetaReportFilter)
from sdnist.gui.windows.filetree import (
    FileTree,
    PathType
)
from sdnist.gui.windows.csv import DeidCSV
from sdnist.gui.windows.metadata import \
    MetaDataForm
from sdnist.gui.windows.report import \
    ReportInfo
from sdnist.gui.windows.metareport import \
    MetaReportInfo
from sdnist.gui.windows.directory import (
    DirectoryInfo)
from sdnist.gui.windows.index import (
    IndexInfo)
from sdnist.gui.windows.targetdata import (
    TargetDataWindow)
from sdnist.gui.windows.archive import (
    ArchiveInfo)

from sdnist.gui.config import load_cfg, save_cfg
from sdnist.gui.constants import DATA_ROOT_PATH
from sdnist.report.dataset import TargetLoader

# List Windows Controlled by the Window Handler
FILETREE = 'filetree'
METADATA_FORM = 'metadata_form'
TARGET_DATA = 'target_data'
ARCHIVE_INFO = 'archive_info'
DEID_CSV = 'deid_csv'
REPORT_INFO = 'report_info'
METAREPORT_INFO = 'metareport_info'
DIRECTORY_INFO = 'directory_info'
METAREPORT_FILTER = 'metareport_filter'
INDEX_INFO = 'index_info'

class WindowHandler:
    def __init__(self,
                 manager: UIManager,
                 root_directory: str,
                 top: int = 0,
                 left: Optional[pg.Rect] = None,
                 right: Optional[pg.Rect] = None):
        self.manager = manager

        # root directory is needed for drawing filetree
        self.root_directory = root_directory
        self.top = top
        self.left_rect = left
        self.right_rect = right
        self.target_loader = TargetLoader(
            data_root_dir=DATA_ROOT_PATH)

        # load user settings
        self.settings = load_cfg()

        # current window
        self.current_window = None

        # windows dictionary
        self.windows: Dict[str, AbstractWindow] = dict()

        # For now use left rect for dimensions for
        # drawing filetree
        self.filetree = None

        # path selected in the filetree window
        self.selected_path = None

        self._create()

    def _create(self):
        self.update_filetree()

    def update_filetree(self):
        if self.filetree:
            self.filetree.update_tree()
        else:
            self.create_filetree(self.root_directory)

    def create_filetree(self, directory: str):
        if self.filetree:
            self.filetree.destroy()
            self.filetree = None
        self.filetree = FileTree(
            rect=self.left_rect,
            manager=self.manager,
            directory=directory
        )

    def handle(self,
               event: pg.event.Event):

        if self.filetree:
            if self.filetree.selected is None \
               or self.filetree.selected[0] == str(self.selected_path):
                return

        # set selected path to the current path
        # selected in the filetree
        self.selected_path = Path(self.filetree.selected[0])

        path_type, _ = self.filetree.compute_selected_file_type()
        self.destroy_current_window()

        if path_type == PathType.CSV:
            deid_csv = DeidCSV(
                rect=self.right_rect,
                manager=self.manager,
                csv_path=str(self.selected_path)
            )
            self.windows[DEID_CSV] = deid_csv
            self.current_window = DEID_CSV
        elif path_type == PathType.JSON:
            self.create_metadata_form()

        elif path_type == PathType.REPORT:
            report = ReportInfo(
                delete_callback=self.delete_directory_callback,
                report_path=str(self.selected_path),
                rect=self.right_rect,
                manager=self.manager
            )
            self.current_window = REPORT_INFO
            self.windows[REPORT_INFO] = report
        elif path_type == PathType.METAREPORT:
            metareport = MetaReportInfo(
                delete_callback=self.delete_directory_callback,
                report_path=str(self.selected_path),
                rect=self.right_rect,
                manager=self.manager
            )
            self.current_window = METAREPORT_INFO
            self.windows[METAREPORT_INFO] = metareport
        elif path_type == PathType.ARCHIVE:
            archive = ArchiveInfo(
                delete_callback=self.delete_directory_callback,
                archive_directory=str(self.selected_path),
                rect=self.right_rect,
                manager=self.manager
            )
            self.current_window = ARCHIVE_INFO
            self.windows[ARCHIVE_INFO] = archive
        elif path_type == PathType.INDEX:
            index_window = IndexInfo(
                delete_callback=self.delete_index_callback,
                index_path=str(self.selected_path),
                rect=self.right_rect,
                manager=self.manager
            )
            self.current_window = INDEX_INFO
            self.windows[INDEX_INFO] = index_window
        elif path_type in [
            PathType.DEID_DATA_DIR,
            PathType.METAREPORTS,
            PathType.REPORTS,
            PathType.ARCHIVES]:
            self.create_deid_dir_info()

    def create_deid_dir_info(self):
        if self.selected_path is None:
            return

        if not self.selected_path.is_dir():
            return

        self.destroy_current_window()
        dir_window = DirectoryInfo(
            directory_path=str(self.selected_path),
            rect=self.right_rect,
            manager=self.manager,
        )
        self.current_window = DIRECTORY_INFO
        self.windows[DIRECTORY_INFO] = dir_window

    def create_metareport_filter(self):
        if self.selected_path is None:
            return

        if not self.selected_path.is_dir():
            return

        self.destroy_current_window()
        index_path = Path(self.selected_path, 'index.csv')
        if not index_path.exists():
            return
        mreport_filter = MetaReportFilter(
            index_path=str(index_path),
            rect=self.right_rect,
            manager=self.manager
        )

        self.current_window = METAREPORT_FILTER
        self.windows[METAREPORT_FILTER] = mreport_filter

    def create_target_data(self):
        if self.selected_path is None:
            return

        self.destroy_current_window()
        target_data = TargetDataWindow(
            target=self.target_loader,
            rect=self.right_rect,
            manager=self.manager
        )

        self.current_window = TARGET_DATA
        self.windows[TARGET_DATA] = target_data

    def create_metadata_form(self):
        if self.selected_path is None:
            return

        self.destroy_current_window()
        metaform = MetaDataForm(
            rect=self.right_rect,
            manager=self.manager,
            settings=self.settings,
            file_path=str(self.selected_path)
        )
        self.current_window = METADATA_FORM
        self.windows[METADATA_FORM] = metaform

    def destroy_window(self, window_name: str):
        win = self.windows.get(window_name, None)
        if win:
            win.destroy()
            self.windows.pop(window_name)

    def destroy_current_window(self):
        self.destroy_window(self.current_window)

    def has_window(self, window_name: str):
        return self.windows.get(window_name, None) is not None

    def delete_directory_callback(self, path: Path):
        shutil.rmtree(path)
        self.destroy_current_window()

        new_path = Path(self.selected_path)
        if not new_path.exists():
            new_path = new_path.parent
        self.filetree.selected = (str(new_path), None)

        self.update_filetree()

    def delete_index_callback(self, path: Path):
        path = Path(path)
        if path.exists() and path.suffix == '.csv':
            try:
                path.unlink()

                new_path = Path(self.selected_path)
                if not new_path.exists():
                    new_path = new_path.parent
                self.filetree.selected = (str(new_path), None)

                self.update_filetree()
            except OSError as e:
                print(f"Error: {e.strerror}")

    def select_path(self, new_path: Path):
        if not new_path.exists():
            new_path = new_path.parent
        self.filetree.selected = (str(new_path), None)
        self.update_filetree()







