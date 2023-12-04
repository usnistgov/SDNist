import glob
import json
from typing import Optional
from multiprocessing import Process, Manager
from multiprocessing.managers import BaseManager

import pygame as pg
import pygame_gui as pggui
from pathlib import Path
from multiprocessing import Pool

from pygame_gui.core import ObjectID

from sdnist.gui.constants import (
    REPORT_DIR_PREFIX, ARCHIVE_DIR_PREFIX)

from sdnist.gui.pages.page import AbstractPage
from sdnist.gui.pages import Page
from sdnist.gui.pages.dashboard.stats_panel import \
    StatsPanel

from sdnist.gui.panels import \
    Header, ToolBar, MenuBar, StatusBar
from sdnist.gui.panels.toolbar import (
    OPEN_METADATA_BTN, CREATE_METADATA_BTN,
    SAVE_METADATA_BTN, CREATE_REPORT_BTN,
    CREATE_INDEX_BTN, CREATE_ARCHIVE_BTN,
    CREATE_METAREPORT_BTN, CREATE_REPORTS_BTN
)
# from sdnist.gui.panels.toolbar import \
#     METADATA_BTN, REPORT_BTN, INDEX_BTN, \
#     ARCHIVE_BTN, METAREPORT_BTN
from sdnist.gui.panels.menubar import \
    LOAD_DATA, SETTINGS, TARGET_DATA, NUMERICAL_RESULT
from sdnist.gui.panels import \
    LoadDeidData, SettingsPanel
from sdnist.gui.panels.simple import \
    PartInfoLinePanel

from sdnist.gui.windows.filetree import PathType
from sdnist.gui.windows.metadata import MetaDataForm
from sdnist.gui.windows import \
    MetaReportFilter, MetaReportInfo
from sdnist.gui.windows import DeidCSV
from sdnist.gui.windows import DirectoryInfo
from sdnist.gui.windows.handler import (
    WindowHandler, METADATA_FORM)

from sdnist.gui.config import load_cfg, save_cfg
from sdnist.gui.strs import *

from sdnist.index import index
from sdnist.archive import archive

from sdnist.report.__main__ import setup, run
from sdnist.report.helpers import ProgressStatus

from sdnist.gui.colors import path_type_colors
from sdnist.strs import *

from sdnist.load import DEFAULT_DATASET
import sdnist.gui.utils as u


progress = None


class Dashboard(AbstractPage):
    def __init__(self,
                 manager: pggui.UIManager,
                 deid_data_root: str):
        super().__init__(manager, Path(deid_data_root))

        # Get the window resolution from manager
        self.w, self.h = manager.window_resolution

        self.header_height = int(self.h * 0.05)  # 7% of window height
        self.default_header_height = 30
        self.header_height = max(self.header_height,
                                 self.default_header_height)
        self.header = None
        self.toolbar = None
        self.menubar = None
        self.statusbar = None
        self.path_header = None

        self.m_area_x = 0
        # header 1 is toolbar
        # header 2 is menubar
        # main area starts after two header bars
        self.m_area_y = self.header_height * 2
        self.m_area_w = self.w
        # total area height is for main area is whole height
        # minus the three headers: toolbar, menubar and statusbar
        self.m_area_h = self.h - self.header_height * 3
        self.filetree_rect = pg.Rect(
            0,
            self.m_area_y,
            int(self.w * 0.25),
            self.m_area_h
        )

        self.window_rect = pg.Rect(
            self.filetree_rect.right,
            self.filetree_rect.top,
            self.w - self.filetree_rect.right,
            self.m_area_h
        )

        self.win_handler = None

        # Create form window
        self.metaform = None

        # Create csv window
        self.csv_window = None

        # Create directory information window
        self.dir_window = None

        # Create stats window
        self.stats = None

        # Create meta report filter window
        self.mreport_filter = None

        # Panel to select deid data directory
        self.load_data = None
        self.selected_path: Optional[Path] = None
        self.report_pool = []
        self.settings = load_cfg()

        self.progress = ProgressStatus()
        self.completed_reports = 0
        self.last_progress = 0

    def create(self):
        self.win_handler = WindowHandler(
            manager=self.manager,
            root_directory=str(self.data),
            top=self.m_area_y,
            left=self.filetree_rect,
            right=self.window_rect
        )

        header_w = 190
        header_rect = pg.Rect(0, 0, header_w, self.header_height)

        self.header = Header(
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
        menubar_rect = pg.Rect(0, 0,
                               self.w, self.header_height)
        self.menubar = MenuBar(menubar_rect, self.manager, starting_height=1)

        path_header_rect = pg.Rect(
            0, self.header_height, int(self.w * 0.55), self.header_height
        )

        self.path_header = PartInfoLinePanel(
            parts=['Path: ', str(u.short_path(self.data))],
            part1_size=0.2,
            part2_size=0.8,
            colors=['#0e4f3f', "#253a66"],
            parts_align=['center', 'left'],
            bold_head=True,
            rect=path_header_rect,
            manager=self.manager
        )

        toolbar_rect = pg.Rect(path_header_rect.w, self.header_height,
                               self.w * 0.45, self.header_height)
        self.toolbar = ToolBar(toolbar_rect, self.manager)

        statusbar_rect = pg.Rect(0, self.h - self.header_height,
                                 self.w, self.header_height)
        self.statusbar = StatusBar(statusbar_rect, self.manager)

        # SET CALLBACKS
        menubar_cb ={
            LOAD_DATA: self.load_deid_callback,
            TARGET_DATA: self.target_data_callback,
        }
        self.menubar.set_callbacks(menubar_cb)

    def draw(self, screen: pg.Surface):
        pass

    def update(self):
        if self.progress is None:
            return
        if self.progress.has_updates():
            if self.statusbar.reports_progress is not None:
                self.statusbar.reports_progress.update_progress(self.progress)
        if self.progress.get_current_progress() \
                != self.progress.get_last_progress():
            self.statusbar.update_progress(self.progress)
            new_reports_created = len(self.progress.get_completed_reports())
            if new_reports_created > self.completed_reports:
                self.completed_reports = new_reports_created
                self.win_handler.update_filetree()
            self.progress.set_last_progress(
                self.progress.get_current_progress())

    def handle_event(self, event: pg.event.Event):
        if self.load_data:
            self.load_data.handle_event(event)

        if self.statusbar.reports_progress is not None:
            self.statusbar.handle_event(event)

        if self.menubar:
            self.menubar.handle_event(event)

        self.win_handler.handle(event)
        prev_selected = self.selected_path
        self.selected_path = self.win_handler.selected_path

        selected_path_type, selected_path_status = \
            self.win_handler.filetree.compute_selected_file_type()

        if prev_selected != self.selected_path:
            self.toolbar.update_buttons(selected_path_type, selected_path_status)
            self.toolbar.update_callbacks(self.get_toolbar_callbacks())
            self.update_path_header(self.selected_path, selected_path_type)

        if self.toolbar and SAVE_METADATA_BTN in self.toolbar.buttons:
            if not self.is_metadata_valid():
                self.toolbar.buttons[SAVE_METADATA_BTN].disable()
                self.toolbar.buttons[CREATE_REPORT_BTN].disable()
            else:
                self.toolbar.buttons[SAVE_METADATA_BTN].enable()


    def get_toolbar_callbacks(self):
        callbacks = dict()
        callbacks[OPEN_METADATA_BTN] = self.open_metadata_callback
        callbacks[CREATE_METADATA_BTN] = self.create_metadata_callback
        callbacks[SAVE_METADATA_BTN] = self.save_metadata_callback
        callbacks[CREATE_REPORT_BTN] = self.report_callback
        callbacks[CREATE_REPORTS_BTN] = self.report_callback
        callbacks[CREATE_ARCHIVE_BTN] = self.archive_callback
        callbacks[CREATE_METAREPORT_BTN] = self.metareport_callback
        callbacks[CREATE_INDEX_BTN] = self.index_callback

        return callbacks

    def next_page(self):
        return Page.DASHBOARD

    def next_page_data(self):
        pass

    def create_metadata_callback(self):
        if self.selected_path is None:
            print('No path selected')
            return
        if self.selected_path.suffix != '.csv':
            print('Selected path is not a csv file')
            return
        # metaform path
        mf_path = Path(self.selected_path.parent,
                          self.selected_path.stem + '.json')
        if not mf_path.exists():
            with open(mf_path, 'w') as f:
                json.dump({}, f)
        self.open_metadata_callback()

    def save_metadata_callback(self):
        if self.win_handler.current_window != METADATA_FORM:
            return False
        metaform = self.win_handler.windows[METADATA_FORM]
        metaform.save_data()
        if (self.toolbar and
                CREATE_REPORT_BTN in self.toolbar.buttons):
            self.toolbar.buttons[CREATE_REPORT_BTN].enable()

        # File Tree Window
        self.win_handler.update_filetree()

    def is_metadata_valid(self):
        if self.win_handler.current_window != METADATA_FORM:
            return False
        meta_form = self.win_handler.windows[METADATA_FORM]
        is_valid = meta_form.validate_form()
        return is_valid

    def open_metadata_callback(self):
        if self.selected_path is None:
            print('No path selected')
            return
        if self.selected_path.suffix != '.csv':
            print('Selected path is not a csv file')
            return
        # metaform path
        mf_path = Path(self.selected_path.parent,
                          self.selected_path.stem + '.json')
        if not mf_path.exists():
            print('Metadata file does not exist', mf_path)
            return
        self.win_handler.select_path(mf_path)

    def report_callback(self):
        if self.selected_path is None:
            return
        x = Path()
        csv_files = []
        s_path = Path(self.selected_path)
        if s_path.is_dir():
            # exclude directories that start with SDNIST_DER_
            all_files = list(glob.iglob(str(s_path) + f'/**/*.csv',
                                        recursive=True))

            files = filter(lambda x: (
                REPORT_DIR_PREFIX not in str(x) and
                ARCHIVE_DIR_PREFIX not in str(x)), all_files)

            csv_files = [str(f) for f in files]
        elif s_path.suffix == '.csv':
            csv_files = [str(s_path)]
        BaseManager.register('ProgressStatus', ProgressStatus)
        manager = BaseManager()
        manager.start()
        self.progress = manager.ProgressStatus()

        inputs = setup(csv_files)
        inputs = [(
            self.progress,
            i[SYNTHETIC_FILEPATH],
            i[OUTPUT_DIRECTORY],
            i[DATASET_NAME],
            Path(DEFAULT_DATASET),
            i[LABELS_DICT],
            False,
            False,
            self.settings[NUMERICAL_METRIC_RESULTS]
            )
            for i in inputs
        ]

        reports = []
        self.completed_reports = 0
        for i in inputs:
            str_path = str(i[2])
            self.progress.add_report(str_path)
            reports.append(str_path)

        self.statusbar.add_progress(reports)
        pool_size = len(inputs) if len(inputs) < 5 else 5
        pool = Pool(pool_size)
        # res = pool.starmap(run, inputs)
        # self.left_panel = SidePanel(0, self.header_height,
        #                             self.manager, str(self.data))
        for i in inputs:
            self.report_pool.append(pool.apply_async(run, (*i,)))

        # for input in inputs:
        #     print(input)
        #     run(*input)

    def index_callback(self):
        if self.selected_path is None:
            return
        idx_df = index(str(self.selected_path))
        out_path = Path(self.selected_path, 'index.csv')
        idx_df.to_csv(out_path)
        self.win_handler.update_filetree()

    def archive_callback(self):
        if self.selected_path is None:
            return
        archive(str(self.selected_path))
        self.win_handler.update_filetree()

    def metareport_callback(self):
        self.win_handler.create_metareport_filter()

    def load_deid_callback(self):
        if self.load_data is None:
            load_data_rect = pg.Rect(0, 0,
                                     self.w // 1.5,
                                     self.h // 2)
            self.load_data = LoadDeidData(rect=load_data_rect,
                                          manager=self.manager,
                                          data=self.data,
                                          done_button_visible=True,
                                          done_button_callback=self.update_deid_data_path)

    def target_data_callback(self):
        self.win_handler.create_target_data()

    def update_deid_data_path(self, save_path=True, new_path: str=None):
        if save_path:
            if new_path and Path(new_path).exists():
                self.data = Path(new_path)
            self.win_handler.create_filetree(str(self.data))
        if self.load_data:
            self.load_data.destroy()
            self.load_data = None


    def update_path_header(self, selected_path: Path,
                           selected_path_type: PathType):

        if self.selected_path is None:
            return

        if self.path_header is None:
            return

        self.adjust_path_header()
        # hpd: header parts data
        hpd = path_type_colors[selected_path_type]
        parts_text = [hpd[NAME], str(u.short_path(selected_path))]
        back_colors = [hpd[PART_1][BACK_COLOR], hpd[PART_2][BACK_COLOR]]
        text_colors = [hpd[PART_1][TEXT_COLOR], hpd[PART_2][TEXT_COLOR]]

        self.path_header.update_parts(parts_text, back_colors, text_colors)

        if selected_path_type in [PathType.REPORT, PathType.METAREPORT]:
            self.adjust_path_header(True)

    def adjust_path_header(self, full_width: bool = False):
        if full_width:
            self.path_header.rect.w = self.w
            self.path_header.rebuild()
            self.toolbar.panel.relative_rect.w = 0
            self.toolbar.panel.rebuild()
        else:
            self.path_header.rect.w = int(self.w * 0.55)
            self.path_header.rebuild()
            self.toolbar.panel.relative_rect.w = int(self.w * 0.45)
            self.toolbar.panel.rebuild()


