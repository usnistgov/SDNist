import glob
import json
from typing import Optional
import asyncio

import pygame as pg
import pygame_gui as pggui
from pathlib import Path

from sdnist.gui.constants import (
    REPORT_DIR_PREFIX, ARCHIVE_DIR_PREFIX)

from sdnist.gui.pages.page import AbstractPage
from sdnist.gui.pages import Page
from sdnist.gui.pages.dashboard.stats_panel import \
    StatsPanel

from sdnist.gui.panels.toolbar import (
    OPEN_METADATA_BTN, CREATE_METADATA_BTN,
    SAVE_METADATA_BTN, CREATE_REPORT_BTN,
    CREATE_INDEX_BTN, CREATE_ARCHIVE_BTN,
    CREATE_METAREPORT_BTN, CREATE_REPORTS_BTN
)

from sdnist.gui.panels.simple import \
    PartInfoLinePanel

from sdnist.gui.windows.filetree import PathType

from sdnist.gui.handlers.window import (
    WindowHandler,
    METADATA_FORM, METAREPORT_FILTER, DIRECTORY_INFO)

from sdnist.gui.config import load_cfg
from sdnist.gui.strs import *

from sdnist.archive import (
    create_archive_dir_path)

from sdnist.report.__main__ import setup, run
from sdnist.report.helpers.progress_status import (
    ProgressStatus, ProgressType, ProgressLabels)

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
        self.settings = load_cfg()

        self.completed_items = 0
        self.last_progress = 0
        self.frames = 0
        self.start_frame = False


    def create(self):
        self.win_handler = WindowHandler(
            manager=self.manager,
            root_directory=str(self.data),
            top=self.m_area_y,
            left=self.filetree_rect,
            right=self.window_rect
        )

        self.win_handler.create_header_logo()
        self.win_handler.create_menubar()
        self.win_handler.create_statusbar()

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

        self.win_handler.create_toolbar(path_header_rect,
                                        self.get_toolbar_callbacks())

    def draw(self, screen: pg.Surface):
        pass

    def update(self):
        if self.start_frame:
            self.frames += 1
        if self.frames > 200:
            self.win_handler.statusbar.destroy_progress()
            self.frames = 0
            self.start_frame = False

        prog = self.win_handler.process_handle.progress
        if prog is None or not prog.is_busy():
            return
        sb = self.win_handler.statusbar
        is_completed = prog.is_completed()
        item_path = None
        if prog.has_updates():
            updates = prog.get_updates()
            if sb.reports_progress is not None:
                sb.reports_progress.update_progress(updates)
            item_path, label, _, percent = updates[-1]
            is_report_created = any([True
                                     if lbl == ProgressLabels.CREATING_EVALUATION_REPORT
                                     else False
                                     for _, lbl, _, _ in updates])
            if is_report_created:
                self.win_handler.update_filetree()
                item_path = item_path if item_path else ''
                item_path = Path(item_path)
                self.win_handler.filetree.ft_handler.update_count(item_path)
                act_win = self.win_handler.current_window
                if act_win == DIRECTORY_INFO:
                    self.win_handler.create_deid_dir_info()
        if prog.get_current_progress() \
                != prog.get_last_progress():
            sb.update_progress(prog)
            prog.set_last_progress(
                prog.get_current_progress())
        if is_completed:
            item_path = item_path if item_path else ''
            item_path = Path(item_path)
            self.win_handler.filetree.ft_handler.update_count(item_path)
            self.win_handler.update_toolbar()
            self.win_handler.update_filetree()
            act_win = self.win_handler.current_window
            if act_win == METAREPORT_FILTER:
                win = self.win_handler.windows[METAREPORT_FILTER]
                win.header.generate_metareport_btn.enable()
            elif act_win == DIRECTORY_INFO:
                self.win_handler.create_deid_dir_info()
            self.start_frame = True

            # Schedule the delayed function call; this doesn't block


    def delayed_function_call(self):
        print('destroying')
        self.win_handler.statusbar.destroy_progress()
        # if self.loop:
        #     self.loop.stop()  # Stops the loop
        #     self.loop.close()  # Closes the loop
        #     self.loop = None

    def handle_event(self, event: pg.event.Event):
        if self.load_data:
            self.load_data.handle_event(event)

        self.win_handler.handle(event)
        prev_selected = self.selected_path
        self.selected_path = self.win_handler.selected_path

        selected_path_type, selected_path_status = \
            self.win_handler.filetree.compute_selected_file_type(
                self.win_handler.process_handle.progress
            )

        if prev_selected != self.selected_path:
            self.win_handler.toolbar.update_buttons(selected_path_type, selected_path_status)
            self.win_handler.toolbar.update_callbacks()
            self.update_path_header(self.selected_path, selected_path_type)

        if SAVE_METADATA_BTN in self.win_handler.toolbar.buttons:
            if not self.is_metadata_valid():
                self.win_handler.toolbar.buttons[SAVE_METADATA_BTN].disable()
                self.win_handler.toolbar.buttons[CREATE_REPORT_BTN].disable()
            else:
                self.win_handler.toolbar.buttons[SAVE_METADATA_BTN].enable()


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
        is_valid = (self.selected_path.is_file()
            and self.selected_path.suffix == '.csv')

        if not is_valid:
            print('Selected path is not a csv file or a directory')
            return

        if self.selected_path.is_dir():
            # exclude directories that start with SDNIST_DER_
            all_files = list(glob.iglob(str(self.selected_path) + f'/**/*.csv',
                                        recursive=True))

            files = filter(lambda x: (
                REPORT_DIR_PREFIX not in str(x) and
                ARCHIVE_DIR_PREFIX not in str(x)), all_files)

            csv_files = [str(f) for f in files]
            # get path to first json file with same name csv that doesn't exist
            metadata_no_exist = None
            for csv_file in csv_files:
                mf_path = Path(csv_file).with_suffix('.json')
                if not mf_path.exists():
                    metadata_no_exist = mf_path
                    break
            mf_path = metadata_no_exist
        else:
            # metaform path
            mf_path = Path(self.selected_path.parent,
                              self.selected_path.stem + '.json')
        if not mf_path.exists():
            with open(mf_path, 'w') as f:
                json.dump({}, f)
        self.selected_path = mf_path.with_suffix('.csv')
        self.open_metadata_callback()

    def save_metadata_callback(self):
        if self.win_handler.current_window != METADATA_FORM:
            return False
        metaform = self.win_handler.windows[METADATA_FORM]
        metaform.save_data()
        if CREATE_REPORT_BTN in self.win_handler.toolbar.buttons:
            self.win_handler.toolbar.buttons[CREATE_REPORT_BTN].enable()

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
        elif s_path.suffix == '.json':
            csv_files = [str(s_path.with_suffix('.csv'))]

        settings = load_cfg()
        inputs = setup(csv_files)
        inputs = [(
            i[SYNTHETIC_FILEPATH],
            i[OUTPUT_DIRECTORY],
            i[DATASET_NAME],
            Path(DEFAULT_DATASET),
            i[LABELS_DICT],
            False,
            False,
            settings[NUMERICAL_METRIC_RESULTS]
            )
            for i in inputs
        ]

        reports = []

        self.completed_items = 0
        for i in inputs:
            str_path = str(i[1])
            reports.append(str_path)


        self.win_handler.statusbar.add_progress(reports,
                                                ProgressType.REPORTS)
        self.win_handler.process_handle.reports(inputs)
        self.win_handler.update_toolbar()

    def index_callback(self):
        if self.selected_path is None:
            return

        out_path = Path(self.selected_path, 'index.csv')
        self.win_handler.statusbar.add_progress([str(out_path)],
                                                ProgressType.INDEX)
        self.win_handler.process_handle.index(str(self.selected_path))
        self.win_handler.update_toolbar()
        # self.win_handler.select_path(out_path)
        # self.win_handler.update_filetree()

    def archive_callback(self):
        if self.selected_path is None:
            return

        dir_path = Path(self.selected_path)
        if Path(self.selected_path).is_file():
            dir_path = Path(self.selected_path).parent
        archive_path = create_archive_dir_path(dir_path)
        self.win_handler.statusbar.add_progress([str(archive_path)],
                                                ProgressType.ARCHIVE)
        self.win_handler.process_handle.archive(dir_path, archive_path)
        self.win_handler.update_toolbar()
        # self.win_handler.select_path(archive_path)

    def metareport_callback(self):
        self.win_handler.create_metareport_filter()
        self.win_handler.update_toolbar()

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
            self.win_handler.toolbar.panel.relative_rect.w = 0
            self.win_handler.toolbar.panel.rebuild()
        else:
            self.path_header.rect.w = int(self.w * 0.55)
            self.path_header.rebuild()
            self.win_handler.toolbar.panel.relative_rect.w = int(self.w * 0.45)
            self.win_handler.toolbar.panel.rebuild()


