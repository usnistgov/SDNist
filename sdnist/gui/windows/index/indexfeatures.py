import os
from pathlib import Path

import pandas as pd
import pygame as pg
import pygame_gui as pggui

from pygame_gui.elements.ui_scrolling_container import (
    UIScrollingContainer)
from sdnist.gui.panels.panel import AbstractPanel
from sdnist.gui.panels.simple import InfoLinePanel
from sdnist.gui.panels.simple import PartInfoLinePanel

from sdnist.gui.elements import \
    UICallbackButton, CustomUITextEntryLine
import sdnist.gui.strs as strs


class IndexFeaturesPanel(AbstractPanel):
    def __init__(self,
                 file_path: Path,
                 data: pd.DataFrame,
                 *args,
                 **kwargs):
        super().__init__(*args, **kwargs)
        self.data = data
        self.data_path = file_path
        self.scroll = None

        self.n_rows = self.data.shape[0]
        self.features = self.data.columns.to_list()
        if 'Unnamed: 0' in self.features:
            self.data = self.data.drop(columns=['Unnamed: 0'])
        if 'index' in self.features:
            self.data = self.data.drop(columns=['index'])
        self.features = self.data.columns.to_list()
        self.n_features = self.data.shape[1]
        self._create()

    def _create(self):
        start_x = 0
        start_y = 0
        option_h = int(self.rect.h * 0.05)
        elem_w = int(self.rect.w - 20)

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

        labels_map = {
            "Number of Deid Files": str(self.n_rows),
            "Number of Index Properties": str(self.n_features)
        }
        all_elems = []
        for lk, lv in labels_map.items():
            line_rect = pg.Rect((start_x, start_y),
                                (elem_w, option_h))
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

        features_map = dict()
        for f in self.features:
            name = f
            unique_values = len(self.data[f].unique().tolist())
            has_N = 'N' in self.data[f].unique().tolist()
            dtype = str(self.data[f].dtype)
            features_map[f] = (name, unique_values)

        feature_head_rect = pg.Rect(
            (0, start_y),
            (elem_w, option_h)
        )
        feature_head = PartInfoLinePanel(
            parts=['FEATURE NAME','NUM OF UNIQUE VALUES'],
            rect=feature_head_rect,
            container=self.scroll,
            parent_element=self.scroll,
            manager=self.manager,
        )
        all_elems.extend(feature_head.parts_lbls.values())
        start_y += option_h
        for f in self.features:
            f_rect = pg.Rect(
                (0, start_y),
                (elem_w, option_h)
            )
            f_elem = PartInfoLinePanel(
                parts=[f, str(features_map[f][1])],
                rect=f_rect,
                container=self.scroll,
                parent_element=self.scroll,
                manager=self.manager,
            )
            all_elems.extend(f_elem.parts_lbls.values())
            start_y += option_h

        self.scroll.set_scrollable_area_dimensions(
            (elem_w, start_y)
        )

        if self.scroll.vert_scroll_bar:
            self.scroll.vert_scroll_bar.set_focus_set(
                set(all_elems)
            )

    def destroy(self):
        super().destroy()

    def handle_event(self, event: pg.event.Event):
        pass