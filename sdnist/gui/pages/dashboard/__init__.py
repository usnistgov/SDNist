from typing import Optional

import pygame as pg
import pygame_gui as pggui
from pygame_gui.elements.ui_panel import UIPanel
from pygame_gui.elements.ui_label import UILabel
from pathlib import Path
from multiprocessing import Pool

from sdnist.gui.pages.page import AbstractPage
from sdnist.gui.pages import Page
from sdnist.gui.panels import \
    Header, ToolBar, MenuBar, StatusBar
from sdnist.gui.panels.toolbar import \
    METADATA_BTN, REPORT_BTN, INDEX_BTN, \
    ARCHIVE_BTN, METAREPORT_BTN
from sdnist.gui.panels.menubar import \
    LOAD_DATA, SETTINGS
from sdnist.gui.panels import \
    LoadDeidData, SettingsPanel

from sdnist.gui.windows.filetree import FileTree
from sdnist.gui.windows.metadata import MetaDataForm
from sdnist.gui.pages.dashboard.stats_panel import \
    StatsPanel

from sdnist.index import index
from sdnist.archive import archive

from sdnist.report.__main__ import setup, run
from sdnist.strs import *
from sdnist.gui.strs import *
from sdnist.load import DEFAULT_DATASET

from sdnist.gui.config import load_cfg, save_cfg


progress = 0


class Dashboard(AbstractPage):
    def __init__(self, manager: pggui.UIManager, deid_data_root: str):
        super().__init__(manager, Path(deid_data_root))

        # Get the window resolution from manager
        self.w, self.h = manager.window_resolution

        self.header_height = int(self.h * 0.05)  # 5% of window height
        self.default_header_height = 30
        self.header_height = max(self.header_height,
                                 self.default_header_height)
        self.header = None
        self.toolbar = None
        self.menubar = None
        self.statusbar = None

        self.m_area_x = 0
        # header 1 is toolbar
        # header 2 is menubar
        # main area starts after two header bars
        self.m_area_y = self.header_height * 2
        self.m_area_w = self.w
        # total area height is for main area is whole height
        # minus the three headers: toolbar, menubar and statusbar
        self.m_area_h = self.h - self.header_height * 3
        self.filetree_rect = pg.Rect(0, self.m_area_y,
                                     self.w,
                                     self.m_area_h)
        self.filetree = None

        # Create form window
        self.metaform = None

        # Create stats window
        self.stats = None

        # Panel to select deid data directory
        self.load_data = None
        self.selected_path: Optional[Path] = None
        self.report_pool = []
        self.settings = load_cfg()
        self.settings_window = None

    def create(self):
        header_rect = pg.Rect(0, 0, self.w // 2, self.header_height)

        self.header = Header(header_rect, self.manager)

        toolbar_rect = pg.Rect(self.w // 2, 0,
                               self.w // 2, self.header_height)
        self.toolbar = ToolBar(toolbar_rect, self.manager)
        menubar_rect = pg.Rect(0, self.header_height,
                               self.w, self.header_height)
        self.menubar = MenuBar(menubar_rect, self.manager)
        statusbar_rect = pg.Rect(0, self.h - self.header_height,
                                 self.w, self.header_height)
        self.statusbar = StatusBar(statusbar_rect, self.manager)
        # Left Side Panel
        self.filetree = FileTree(self.filetree_rect,
                                 self.manager,
                                 str(self.data))

        # SET CALLBACKS
        self.menubar.set_callback(LOAD_DATA, self.load_deid_callback)
        self.menubar.set_callback(SETTINGS, self.settings_callback)

    def draw(self, screen: pg.Surface):
        pass

    def handle_event(self, event: pg.event.Event):
        if self.load_data:
            self.load_data.handle_event(event)
        if self.settings_window:
            self.settings_window.handle_event(event)
        if self.metaform:
            self.metaform.handle_event(event)
        if self.filetree.selected is None \
           or self.filetree.selected[0] == str(self.selected_path):
            return

        if str(self.selected_path) == self.filetree.selected[0]:
            return
        self.selected_path = Path(self.filetree.selected[0])

        if self.metaform:
            self.metaform.destroy()
        path_type = 'dir'
        if self.selected_path.is_file() and self.selected_path.suffix == '.csv':
            path_type = 'csv'
        elif self.selected_path.is_file() and self.selected_path.suffix == '.json':
            path_type = 'json'

        # metaform_csv = '' if self.metaform is None else self.metaform.file

        if path_type in ['json', 'csv']:
            self.metaform = MetaDataForm(
                pg.Rect(self.filetree.window_rect.right,
                        self.filetree.window_rect.top,
                        self.w - self.filetree.window_rect.right,
                        self.m_area_h),
                self.manager,
                settings=self.settings,
                file_path=str(self.selected_path),
            )

            self.toolbar.set_callback(METADATA_BTN, self.metadata_callback)

        if path_type in ['json', 'csv']:
            self.metaform.file = str(self.selected_path)
            self.toolbar.set_callback(METADATA_BTN, self.metadata_callback)

        if path_type in ['dir', 'csv']:
            self.toolbar.set_callback(REPORT_BTN, self.report_callback)

        if path_type in ['dir']:
            self.toolbar.set_callback(INDEX_BTN, self.index_callback)
            self.toolbar.set_callback(ARCHIVE_BTN, self.archive_callback)
            self.toolbar.set_callback(METAREPORT_BTN, self.metareport_callback)

    def next_page(self):
        return Page.DASHBOARD

    def next_page_data(self):
        pass

    def metadata_callback(self):
        if self.metaform:
            self.metaform.save_data()
            # File Tree Window
            self.filetree = FileTree(self.filetree_rect,
                                     self.manager,
                                     str(self.data))

    def update_progress(self, result):
        global progress
        progress += 1

        # FileTreeWindow
        self.filetree = FileTree(self.filetree_rect,
                                 self.manager,
                                 str(self.data))

    def report_callback(self):
        if self.selected_path is None:
            return
        x = Path()
        csv_files = []
        s_path = Path(self.selected_path)
        if s_path.is_dir():
            files = list(s_path.glob('**/*.csv'))
            csv_files = [str(f) for f in files]
        elif s_path.suffix == '.csv':
            csv_files = [str(s_path)]

        inputs = setup(csv_files)
        inputs = [(
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
        # pool = Pool(5)
        # res = pool.starmap(run, inputs)
        # self.left_panel = SidePanel(0, self.header_height,
        #                             self.manager, str(self.data))
        # for i in inputs:
        #     self.report_pool.append(pool.apply_async(run, (*i,),
        #                                              callback=self.update_progress))
        for input in inputs:
            print(input)
            run(*input)
            # self.left_panel = SidePanel(0, self.header_height,
            #                             self.manager, str(self.data))

    def index_callback(self):
        if self.selected_path is None:
            return

        idx_df = index(str(self.selected_path))
        out_path = Path(self.selected_path, 'index.csv')
        idx_df.to_csv(out_path)
        self.filetree = FileTree(self.filetree_rect,
                                 self.manager,
                                 str(self.data))

    def archive_callback(self):
        if self.selected_path is None:
            return
        archive(str(self.selected_path))
        self.filetree = FileTree(self.filetree_rect,
                                 self.manager,
                                 str(self.data))

    def metareport_callback(self):
        if self.selected_path is None:
            return

    def load_deid_callback(self):
        if self.load_data is None:
            load_data_rect = pg.Rect(0, 0,
                                     self.w // 2,
                                     self.h // 2)
            self.load_data = LoadDeidData(load_data_rect,
                                          self.manager,
                                          data=self.data,
                                          done_button_visible=True,
                                          done_button_callback=self.update_deid_data_path)

    def settings_callback(self):
        if self.settings_window is None:
            settings_rect = pg.Rect(0, 0,
                                    self.w // 2,
                                    self.h // 2)
            self.settings_window = SettingsPanel(settings_rect,
                                                 self.manager,
                                                 data=self.settings,
                                                 done_button_visible=True,
                                                 done_button_callback=self.update_settings)

    def update_deid_data_path(self, save_path=True):
        if self.load_data.picked_path and \
                str(self.data) != self.load_data.picked_path:
            if save_path:
                self.data = Path(self.load_data.picked_path)
                self.filetree = FileTree(self.filetree_rect,
                                         self.manager,
                                         str(self.data))
            self.load_data.destroy()
            self.load_data = None

    def update_settings(self, save_settings=True):
        if save_settings:
            self.settings.update(self.settings_window.settings)
        self.settings_window.destroy()
        self.settings_window = None
        save_cfg(self.settings)


