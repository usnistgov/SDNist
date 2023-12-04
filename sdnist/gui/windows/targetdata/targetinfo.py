import os
from pathlib import Path
from functools import partial

import pandas as pd
import pygame as pg
import pygame_gui as pggui

from pygame_gui.elements.ui_scrolling_container import (
    UIScrollingContainer)
from sdnist.gui.panels.panel import AbstractPanel
from sdnist.gui.panels.headers import Header
from sdnist.gui.panels.headers import CallbackHeader
from sdnist.gui.panels.simple import InfoLinePanel
from sdnist.gui.panels.simple import PartInfoLinePanel

from sdnist.gui.elements import \
    UICallbackButton, CustomUITextEntryLine
import sdnist.gui.strs as strs

from sdnist.report.dataset.target import TargetLoader
from sdnist.load import TestDatasetName

NUM_RECORDS = "Number of records"
NUM_FEATURES = "Number of features"
NUM_PUMAS = "Number of PUMAs"
EXTRA_INFO = 'extra_info'
DATA_PATH = 'data_path'

MASSACHUSETTS_2019 = "Massachusetts 2019 ACS EXCERPT"
TEXAS_2019 = "Texas 2019 ACS EXCERPT"
NATIONAL_2019 = "National 2019 ACS EXCERPT"

class TargetInfoPanel(AbstractPanel):
    def __init__(self,
                 target_loader: TargetLoader,
                 select_target_callback: callable,
                 *args,
                 **kwargs):
        super().__init__(*args, **kwargs)
        self.target_loader = target_loader
        self.select_target_callback = select_target_callback
        self.scroll = None

        self.info = self.get_target_info()

        self._create()

    def _create(self):
        start_x = 0
        start_y = 0
        option_h = int(self.rect.h * 0.05)

        scroll_rect = pg.Rect(
            (0, 0),
            (self.rect.w, self.rect.h)
        )
        self.scroll = UIScrollingContainer(
            relative_rect=scroll_rect,
            manager=self.manager,
            container=self.panel,
            starting_height=1
        )
        all_elems = []
        for d_name, d_info in self.info.items():
            h_rect = pg.Rect((start_x, start_y),
                             (self.rect.w, option_h))
            callback = partial(self.view_data,
                               d_info[EXTRA_INFO][DATA_PATH])
            h_panel = CallbackHeader(
                callback=callback,
                has_title=True,
                title=d_name,
                text="Show Data",
                rect=h_rect,
                container=self.scroll,
                parent_element=self.scroll,
                manager=self.manager,
                text_anchors={'centery': 'centery',
                'left': 'left'},
            )
            all_elems.extend(h_panel.get_elements())
            start_y += option_h
            for lk, lv in d_info.items():
                if lk in [EXTRA_INFO]:
                    continue
                line_rect = pg.Rect((start_x, start_y),
                                    (self.rect.w, option_h))
                line_panel = InfoLinePanel(
                    head_text=lk,
                    tail_text=lv,
                    rect=line_rect,
                    container=self.scroll,
                    parent_element=self.scroll,
                    manager=self.manager,
                )
                all_elems.extend(line_panel.get_elements())
                start_y += option_h

        self.scroll.set_scrollable_area_dimensions(
            (self.rect.w, start_y)
        )
        all_elems.append(self.scroll)
        if self.scroll.vert_scroll_bar:
            self.scroll.vert_scroll_bar.set_focus_set(
                set(all_elems)
            )

    def destroy(self):
        super().destroy()

    def handle_event(self, event: pg.event.Event):
        pass

    def get_target_info(self):
        info = dict()
        ma_d, ma_dp, _ = self.target_loader.load_dataset(TestDatasetName.ma2019)
        tx_d, tx_dp, _ = self.target_loader.load_dataset(TestDatasetName.tx2019)
        na_d, na_dp, _ = self.target_loader.load_dataset(TestDatasetName.national2019)

        for d in [(MASSACHUSETTS_2019, ma_d, ma_dp),
                  (TEXAS_2019, tx_d, tx_dp),
                  (NATIONAL_2019, na_d, na_dp)]:
            info[d[0]] = dict()
            info[d[0]][NUM_RECORDS] = str(d[1].shape[0])
            info[d[0]][NUM_FEATURES] = str(d[1].shape[1])
            info[d[0]][NUM_PUMAS] = str(len(d[1]['PUMA'].unique().tolist()))
            info[d[0]][EXTRA_INFO] = dict()
            info[d[0]][EXTRA_INFO][DATA_PATH] = f'{d[2]}.csv'
        return info

    def view_data(self, file_path: Path):
        self.select_target_callback(file_path)
