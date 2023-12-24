import asyncio
from typing import Optional, Dict, List
from pathlib import Path
import shutil
import pygame as pg
import pygame_gui as pggui

from pygame_gui.core import ObjectID

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

from sdnist.gui.panels.headers import Header
from sdnist.gui.panels.menubar import MenuBar
from sdnist.gui.panels.menubar import \
    LOAD_DATA, SETTINGS, TARGET_DATA, NUMERICAL_RESULT
from sdnist.gui.panels.statusbar import StatusBar
from sdnist.gui.panels.toolbar import ToolBar
from sdnist.gui.panels.settings import SettingsPanel
from sdnist.gui.panels.load_deid import \
    LoadDeidData
from sdnist.gui.windows.progress import ReportsProgressPanel
from sdnist.gui.config import load_cfg, save_cfg
from sdnist.gui.constants import DATA_ROOT_PATH
from sdnist.report.dataset import TargetLoader
from sdnist.report.helpers.progress_status import (
    ProgressStatus, ProgressType)
from sdnist.gui.handlers.process import ProcessHandler
from sdnist.gui.windows.filetree.filehelp import count_path_types

from sdnist.metareport.__main__ import (
    run as metareport_run,
    setup as metareport_setup
)

from sdnist.gui.strs import *

# List Windows Controlled by the Window Handler
FILETREE = 'filetree'
METADATA_FORM = 'metadata_form'
TARGET_DATA = TARGET_DATA
ARCHIVE_INFO = 'archive_info'
DEID_CSV = 'deid_csv'
REPORT_INFO = 'report_info'
METAREPORT_INFO = 'metareport_info'
DIRECTORY_INFO = 'directory_info'
METAREPORT_FILTER = METAREPORT_FILTER
INDEX_INFO = 'index_info'
CSV = 'csv'

class WindowHandler:
    def __init__(self,
                 manager: UIManager,
                 root_directory: str,
                 top: int = 0,
                 left: Optional[pg.Rect] = None,
                 right: Optional[pg.Rect] = None,):
        self.manager = manager
        self.w, self.h = manager.window_resolution
        # root directory is needed for drawing filetree
        progress = ProgressStatus(ProgressType.REPORTS)
        self.process_handle = ProcessHandler(progress)
        self.root_directory = root_directory
        self.top = top
        self.left_rect = left
        self.right_rect = right
        self.target_loader = TargetLoader(
            data_root_dir=DATA_ROOT_PATH
        )

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

        # window that stays on top
        self.on_top_window = None

        self.header_height = int(self.h * 0.05)
        self.logo_header = None
        self.toolbar = None
        self.menubar = None
        self.statusbar = None
        self.messages = None

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
            target_loader=self.target_loader,
            rect=self.left_rect,
            manager=self.manager,
            directory=directory
        )

    def handle(self,
               event: pg.event.Event):
        if self.menubar:
            self.menubar.handle_event(event)
        if (self.statusbar.reports_progress is not None and
            self.statusbar.reports_progress.window.visible):
            self.statusbar.handle_event(event)
            if self.statusbar.reports_progress != self.on_top_window:
                self.destroy_on_top()
                self.on_top_window = self.statusbar.reports_progress
        if self.on_top_window:
            self.on_top_window.handle_event(event)
            if isinstance(self.on_top_window, LoadDeidData):
                has_file_dialog = self.on_top_window.file_dialog
                if (has_file_dialog and not
                    self.manager.ui_window_stack.is_window_at_top(
                        self.on_top_window.file_dialog)):
                    self.manager.ui_window_stack.move_window_to_front(
                        self.on_top_window.base
                    )
                    self.manager.ui_window_stack.move_window_to_front(
                        self.on_top_window.file_dialog
                    )
                elif (not has_file_dialog and not
                        self.manager.ui_window_stack.is_window_at_top(
                        self.on_top_window.base)):
                    self.manager.ui_window_stack.move_window_to_front(
                        self.on_top_window.base
                    )
            else:
                if not self.manager.ui_window_stack.is_window_at_top(
                        self.on_top_window.base):
                    self.manager.ui_window_stack.move_window_to_front(
                        self.on_top_window.base)

        if self.filetree:
            if self.filetree.selected is None \
               or self.filetree.selected[0] == str(self.selected_path):
                return

        # set selected path to the current path
        # selected in the filetree
        self.selected_path = Path(self.filetree.selected[0])

        path_type, _ = self.filetree.compute_selected_file_type(
            self.process_handle.progress
        )
        self.destroy_current_window()

        if path_type == PathType.DEID_CSV:
            deid_csv = DeidCSV(
                csv_path=str(self.selected_path),
                rect=self.right_rect,
                manager=self.manager
            )
            self.windows[DEID_CSV] = deid_csv
            self.current_window = DEID_CSV
        elif path_type == PathType.CSV:
            deid_csv = DeidCSV(
                csv_path=str(self.selected_path),
                title='CSV File',
                rect=self.right_rect,
                manager=self.manager
            )
            self.windows[CSV] = deid_csv
            self.current_window = CSV
        elif path_type == PathType.DEID_JSON:
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
        counts = self.filetree.ft_handler.get_counts(self.selected_path)
        dir_window = DirectoryInfo(
            directory_path=str(self.selected_path),
            counts=counts,
            rect=self.right_rect,
            manager=self.manager,
        )
        self.current_window = DIRECTORY_INFO
        self.windows[DIRECTORY_INFO] = dir_window

    def create_metareport_filter(self):
        if self.selected_path is None:
            return

        self.destroy_current_window()

        if Path(self.selected_path).name == 'index.csv':
            index_path = Path(self.selected_path)
        else:
            index_path = Path(self.selected_path, 'index.csv')

        if not index_path.exists():
            return

        mreport_filter = MetaReportFilter(
            create_metareport_callback=self.on_create_metareport,
            index_path=str(index_path),
            rect=self.right_rect,
            manager=self.manager
        )

        self.current_window = METAREPORT_FILTER
        self.windows[METAREPORT_FILTER] = mreport_filter

    def on_create_metareport(self,
                             reports_dir: Path,
                             reports_path: List[str]):

        input_cnf = metareport_setup(reports_dir, reports_path)
        meta_out_dir = input_cnf['metareport_out_dir']

        self.process_handle.metareport(input_cnf)
        self.statusbar.add_progress([meta_out_dir],
                                    ProgressType.METAREPORT)
        self.update_toolbar()
        m_win = self.windows[METAREPORT_FILTER]
        if m_win:
            m_win.header.generate_metareport_btn.disable()
        # out_dir = input_cnf['metareport_out_dir']
        # self.select_path(out_dir)

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
        path = Path(path)
        shutil.rmtree(path)
        self.destroy_current_window()

        new_path = Path(self.selected_path)
        if not new_path.exists():
            new_path = new_path.parent
        self.filetree.selected = (str(new_path), None)
        self.filetree.ft_handler.update_count(path)
        self.update_filetree()
        if self.current_window == DIRECTORY_INFO:
            self.create_deid_dir_info()

    def delete_index_callback(self, path: Path):
        path = Path(path)
        if path.exists() and path.suffix == '.csv':
            try:
                path.unlink()
                new_path = Path(self.selected_path)
                if not new_path.exists():
                    new_path = new_path.parent
                self.filetree.selected = (str(new_path), None)
                self.filetree.ft_handler.update_count(path)
                self.update_filetree()
                if self.current_window == DIRECTORY_INFO:
                    self.create_deid_dir_info()
            except OSError as e:
                print(f"Error: {e.strerror}")

    def select_path(self, new_path: Path):
        if not new_path.exists():
            new_path = new_path.parent
        self.filetree.selected = (str(new_path), None)
        self.update_filetree()

    def destroy_on_top(self):
        if self.on_top_window:
            if isinstance(self.on_top_window, ReportsProgressPanel):
                self.statusbar.reports_progress.window.hide()
            else:
                self.on_top_window.destroy()
            self.on_top_window = None

    def create_header_logo(self):
        header_w = 190
        header_rect = pg.Rect(0, 0,
                              header_w, self.header_height)

        self.logo_header = Header(
            starting_height=2,
            text='SDNIST',
            rect=header_rect,
            manager=self.manager,
            object_id=ObjectID(
                class_id='@header_panel',
                object_id='#main_header_panel'),
            text_object_id=ObjectID(
                class_id="@header_label",
                object_id="#main_header_label")
        )

    def create_toolbar(self, path_header_rect: pg.Rect,
                       toolbar_callbacks: Dict[str, callable]):
        toolbar_rect = pg.Rect(path_header_rect.w,
                               path_header_rect.y,
                               self.w * 0.45, path_header_rect.h)
        self.toolbar = ToolBar(toolbar_callbacks,
                               toolbar_rect,
                               self.manager)

    def update_toolbar(self):
        selected_path_type, selected_path_status = \
        self.filetree.compute_selected_file_type(
            self.process_handle.progress
        )

        if self.current_window == METAREPORT_FILTER:
            selected_path_status[METAREPORT_FILTER] = True
        self.toolbar.update_buttons(selected_path_type, selected_path_status)

    def create_menubar(self):
        menubar_rect = pg.Rect(0, 0,
                               self.w, self.header_height)
        self.menubar = MenuBar(menubar_rect, self.manager, starting_height=1)
        menubar_cb ={
            LOAD_DATA: self.create_load_deid_window,
            TARGET_DATA: self.create_target_data,
            SETTINGS: self.create_settings_window
        }
        self.menubar.set_callbacks(menubar_cb)

    def create_statusbar(self):
        statusbar_rect = pg.Rect(0, self.h - self.header_height,
                                 self.w, self.header_height)
        self.statusbar = StatusBar(self.on_path_open,
                                   statusbar_rect,
                                   self.manager)

    def create_settings_window(self):
        self.destroy_on_top()
        settings_rect = pg.Rect(0, 0,
                                self.w // 1.5,
                                self.h // 1.5)
        self.on_top_window = SettingsPanel(rect=settings_rect,
                                             manager=self.manager,
                                             done_button_visible=True,
                                             done_button_callback=self.update_settings)
        self.menubar.update_settings()
        # if self.statusbar.reports_progress:
        #     self.statusbar.reports_progress.window.hide()

    def create_load_deid_window(self):
        self.destroy_on_top()
        load_data_rect = pg.Rect(0, 0,
                                 self.w // 1.5,
                                 self.h // 2)
        self.on_top_window = LoadDeidData(rect=load_data_rect,
                                          manager=self.manager,
                                          data=self.root_directory,
                                          done_button_visible=True,
                                          done_button_callback=self.update_deid_data_path)
        # if self.statusbar.reports_progress:
        #     self.statusbar.reports_progress.window.hide()

    def update_deid_data_path(self, save_path=True, new_path: str=None):
        if save_path:
            if new_path and Path(new_path).exists():
                self.root_directory = Path(new_path)
            self.create_filetree(str(self.root_directory))
        self.destroy_on_top()

    def update_settings(self):
        self.on_top_window.save_settings()
        self.menubar.update_settings()
        self.destroy_on_top()

    def on_path_open(self, path: Path):
        if not path.exists():
            print('Path does not exist: ', path)
        self.select_path(path)







