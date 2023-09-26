from typing import Optional

import pygame as pg
import pygame_gui as pggui
from pygame_gui.elements.ui_panel import UIPanel
from pygame_gui.elements.ui_label import UILabel
from pathlib import Path
from multiprocessing import Pool

from sdnist.gui.pages.page import AbstractPage
from sdnist.gui.pages import Page
from sdnist.gui.panels import Header, Toolbar
from sdnist.gui.panels.toolbar import \
    METADATA_BTN, REPORT_BTN, INDEX_BTN, \
    ARCHIVE_BTN, METAREPORT_BTN

from sdnist.gui.pages.dashboard.sidepanel import SidePanel
from sdnist.gui.pages.dashboard.metadata import MetaDataForm
from sdnist.gui.pages.dashboard.stats_panel import StatsPanel

from sdnist.index import index
from sdnist.archive import archive

from sdnist.report.__main__ import setup, run
from sdnist.strs import *
from sdnist.load import DEFAULT_DATASET

from sdnist.gui.config import load_cfg

progress = 0


class Dashboard(AbstractPage):
    def __init__(self, manager: pggui.UIManager, deid_data_root: str):
        super().__init__(manager, Path(deid_data_root))

        # Get the window resolution from manager
        self.w, self.h = manager.window_resolution

        self.header_height = int(self.h * 0.05)  # 5% of window height

        self.header = None
        self.toolbar = None
        self.left_panel = None

        # Create form window
        self.metaform = None

        # Create stats window
        self.stats = None

        self.selected_path: Optional[Path] = None
        self.report_pool = []
        self.settings = load_cfg()

    def create(self):
        header_rect = pg.Rect(0, 0, self.w // 2, self.header_height)

        self.header = Header(header_rect,self.manager)

        toolbar_rect = pg.Rect(self.w // 2, 0,
                               self.w // 2, self.header_height)
        self.toolbar = Toolbar(toolbar_rect, self.manager)

        # Left Side Panel
        self.left_panel = SidePanel(0, self.header_height,
                                    self.manager,
                                    self.data)

    def draw(self, screen: pg.Surface):
        pass

    def handle_event(self, event: pg.event.Event):
        if self.metaform:
            self.metaform.handle_event(event)
        if self.left_panel.selected is None \
           or self.left_panel.selected[0] == str(self.selected_path):
            return

        self.selected_path = Path(self.left_panel.selected[0])

        path_type = 'dir'
        if self.selected_path.is_file() and self.selected_path.suffix == '.csv':
            path_type = 'csv'
        elif self.selected_path.is_file() and self.selected_path.suffix == '.json':
            path_type = 'json'

        # metaform_csv = '' if self.metaform is None else self.metaform.file

        if path_type in ['json', 'csv'] and self.metaform is None:
            self.metaform = MetaDataForm(
                pg.Rect(self.left_panel.window_rect.right,
                        self.left_panel.window_rect.top,
                        self.w - self.left_panel.window_rect.right,
                        self.h - self.left_panel.window_rect.top),
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
            self.left_panel = SidePanel(0, self.header_height,
                                        self.manager, str(self.data))

    def update_progress(self, result):
        global progress
        progress += 1
        self.left_panel = SidePanel(0, self.header_height,
                                    self.manager, str(self.data))

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
            False
            )
            for i in inputs
        ]
        pool = Pool(5)
        # res = pool.starmap(run, inputs)
        # self.left_panel = SidePanel(0, self.header_height,
        #                             self.manager, str(self.data))
        for i in inputs:
            self.report_pool.append(pool.apply_async(run, (*i,),
                                                     callback=self.update_progress))
        # for input in inputs:
        #     print(input)
        #     run(**input)
        #     self.left_panel = SidePanel(0, self.header_height,
        #                                 self.manager, str(self.data))

    def index_callback(self):
        if self.selected_path is None:
            return

        idx_df = index(str(self.selected_path))
        out_path = Path(self.selected_path, 'index.csv')
        idx_df.to_csv(out_path)
        self.left_panel = SidePanel(0, self.header_height,
                                    self.manager, str(self.data))

    def archive_callback(self):
        if self.selected_path is None:
            return
        archive(str(self.selected_path))
        self.left_panel = SidePanel(0, self.header_height,
                                    self.manager, str(self.data))

    def metareport_callback(self):
        if self.selected_path is None:
            return

# import os
# from multiprocessing import Pool
# import time
#
#
# # Function to be mapped
# def f(args):
#     x, y = args
#     time.sleep(1)
#     print(f"Task {os.getpid()} completed")
#     return x * y
#
#
# # Callback function to update progress
# def update_progress(result):
#     global completed_tasks
#     completed_tasks += 1
#     print(f"Progress: {completed_tasks / total_tasks * 100}%")
#
#
# def main():
#     global completed_tasks, total_tasks
#     completed_tasks = 0
#     total_tasks = 10
#     args = [(i, i) for i in range(total_tasks)]
#
#     with Pool() as pool:
#         results = [pool.apply_async(f, (arg,), callback=update_progress) for arg in args]
#         pool.close()
#         pool.join()
#
#     print("All tasks completed.")
#
# if __name__ == '__main__':
#     main()
#
#
