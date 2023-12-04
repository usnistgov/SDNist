import math
from typing import List
import pandas as pd
import pygame as pg
import pygame_gui as pggui
from pathlib import Path

from pygame_gui.elements.ui_scrolling_container import \
    UIScrollingContainer
from pygame_gui.elements.ui_label import UILabel
from pygame_gui.elements.ui_panel import UIPanel

from sdnist.gui.panels.panel import AbstractPanel
from sdnist.gui.panels.dftable.filterdata import FilterData
from sdnist.gui.panels.dftable.header import DFTableHeader
from sdnist.gui.elements.buttons import UICallbackButton
from sdnist.gui.elements.scroll_container import CustomScrollingContainer

from sdnist.gui.windows.metadata.labels import *


class DFTable(AbstractPanel):
    def __init__(self,
                 rect: pg.Rect,
                 manager: pggui.UIManager,
                 file_path: Path,
                 data: pd.DataFrame,
                 filter_data: FilterData,
                 enabled_features: List[str],
                 *args, **kwargs):
        self.title = str(Path(*Path(file_path).parts[-2:]))
        super().__init__(rect, manager, *args, **kwargs)

        self.filter_data = filter_data
        self.file_path = file_path
        self.orig_data = data
        if 'index' not in self.orig_data.columns.to_list():
            self.orig_data['index'] = self.orig_data.index
        self.disp_data = data[enabled_features]

        self.view_data = None
        self.enabled_features = enabled_features

        # header panel
        self.header_h = 40
        self.header = None
        # scrolling container
        self.scroll = None

        # panel
        self.df_panel_w = self.rect.w - 20
        self.df_panel_h = self.rect.h - self.header_h - 20
        self.df_panel = None

        # feature button
        self.f_btn_h = 40
        self.f_btn_w = self.df_panel_w // 7

        # value label
        self.v_btn_h = 30
        self.v_btn_w = self.f_btn_w

        self.feature_buttons = dict()
        self.cells = []
        self._create()

    def _create(self):
        header_rect = pg.Rect(0, 0,
                              self.rect.w, self.header_h)
        self.header = DFTableHeader(
            text=self.title,
            rect=header_rect,
            manager=self.manager,
            container=self.panel,
            all_features=self.filter_data.data.columns.tolist(),
            enabled_features=self.enabled_features,
            parent_window=self.container
        )

        scroll_rect = pg.Rect(0,
                              self.header_h,
                              self.rect.w,
                              self.rect.h - self.header_h)
        self.scroll = CustomScrollingContainer(
            scroll_callback=self.update_view_data,
            relative_rect=scroll_rect,
            manager=self.manager,
            container=self.panel,
            starting_height=1,
        )

        self.df_panel = UIPanel(
            relative_rect=pg.Rect(0,
                                  self.header_h,
                                  self.df_panel_w,
                                  self.df_panel_h),
            manager=self.manager,
            container=self.panel,
            starting_height=2)

        self._create_cells()

    def update_data(self):
        self.disp_data = self.filter_data.apply_filters()
        self.disp_data = self.disp_data.reset_index(drop=True)
        self.disp_data = self.disp_data[self.enabled_features]
        max_len = 10
        if len(self.disp_data) < max_len:
            self.view_data = self.disp_data
        else:
            self.view_data = self.disp_data.head(max_len)
        self._create_cells()

    def update_view_data(self, vert_scroll_pos, horiz_scroll_pos):
        vsp = vert_scroll_pos
        hsp = horiz_scroll_pos

        s_max = self.scroll.scroll_slider_max_h()
        start_h = ((len(self.disp_data) * self.v_btn_h)
                   - self.df_panel.rect.h + self.v_btn_h) * (vsp / s_max)
        start_row_idx = math.ceil(start_h / self.v_btn_h)

        if start_row_idx < len(self.disp_data) - 10:
            self.view_data = self.disp_data.loc[start_row_idx:start_row_idx + 10]
        elif start_row_idx >= len(self.disp_data):
            self.view_data = self.disp_data.tail(10)
        else:
            self.view_data = self.disp_data.loc[start_row_idx:]

        self.view_data = self.disp_data[self.disp_data.index.isin(self.view_data.index.tolist())]
        s_max = self.scroll.scroll_slider_max_w()
        cols = self.enabled_features
        start_w = ((len(cols) * self.v_btn_w) - self.panel.rect.w) * (hsp / s_max)
        start_col_idx = int(start_w / self.v_btn_w)

        if start_col_idx < len(cols) - 10:
            new_cols = cols[start_col_idx:start_col_idx+10]
        elif start_col_idx >= len(cols):
            new_cols = cols[-10:]
        else:
            new_cols = cols[start_col_idx:]
        self.view_data = self.view_data[new_cols]

        self._create_cells()

    def _create_cells(self):
        # print('CREATING CELLS')
        # self.disp_data = self.apply_filters()
        for f, btn in self.feature_buttons.items():
            btn.kill()
        self.feature_buttons = dict()
        for c in self.cells:
            c.kill()
        self.cells = []
        # Create feature buttons

        focus_set = set()

        self.scroll.set_scrollable_area_dimensions((
            self.f_btn_w * len(self.enabled_features),
            self.f_btn_h + self.v_btn_h * len(self.disp_data)
        ))

        if self.view_data is None:
            self.view_data = self.disp_data.head(10)

        for i, f in enumerate(self.view_data.columns.tolist()):
            btn_rect = pg.Rect(self.f_btn_w * i, 0,
                               self.f_btn_w, self.f_btn_h)
            btn = UICallbackButton(
                relative_rect=btn_rect,
                text=f,
                manager=self.manager,
                container=self.df_panel,
                callback=self.sort_feature,
                tool_tip_text=f
            )

            self.feature_buttons[f] = btn
            focus_set.add(btn)
        # last_f_btn = self.feature_buttons[self.enabled_features[-1]]

        # Add Feature Values
        for i, (_, row) in enumerate(self.view_data.iterrows()):
            for j, f in enumerate(self.view_data.columns.to_list()):
                val = row[f]
                # btn_rect = pg.Rect(btn.rect.x, btn.rect.y + 30 * (i + 1),
                #                    btn_width, 30)
                btn_rect = pg.Rect(self.v_btn_w * j,
                                   self.f_btn_h + self.v_btn_h * i,
                                   self.v_btn_w, self.v_btn_h)
                btn = UILabel(
                    relative_rect=btn_rect,
                    text=str(val)[:10],
                    manager=self.manager,
                    container=self.df_panel
                )
                focus_set.add(btn)
                self.cells.append(btn)
                # self.feature_buttons[f] = btn
        focus_set.add(self.scroll)

        if self.scroll.horiz_scroll_bar:
            self.scroll.horiz_scroll_bar.set_focus_set(focus_set)

        if self.scroll.vert_scroll_bar:
            self.scroll.vert_scroll_bar.set_focus_set(focus_set)


    def get_filtered_dataframe(self) -> pd.DataFrame:
        return self.disp_data

    def sort_feature(self, feature: str):
        pass

    def destroy(self):
        self.panel.kill()
        self.panel = None

    def handle_event(self, event: pg.event.Event):
        pass
