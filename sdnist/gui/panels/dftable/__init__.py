import math
from typing import List
import pandas as pd
import pygame as pg
import pygame_gui as pggui
from pathlib import Path
from functools import partial

from pygame_gui.core import ObjectID

from pygame_gui.elements.ui_scrolling_container import \
    UIScrollingContainer
from pygame_gui.elements.ui_label import UILabel
from pygame_gui.elements.ui_panel import UIPanel
from pygame_gui.elements.ui_tool_tip import UITooltip

from sdnist.gui.panels.panel import AbstractPanel

from sdnist.gui.panels.dftable.header import DFTableHeader
from sdnist.gui.elements.buttons import UICallbackButton
from sdnist.gui.elements.scroll_container import CustomScrollingContainer

from sdnist.gui.windows.metadata.labels import *
from sdnist.gui.panels.dftable.filterdata import FilterData, INDEX

class DFTable(AbstractPanel):
    def __init__(self,
                 rect: pg.Rect,
                 manager: pggui.UIManager,
                 filter_data: FilterData,
                 *args, **kwargs):

        if 'object_id' not in kwargs:
            kwargs['object_id'] = ObjectID(
                class_id='@dftable_panel',
                object_id='#dftable_panel'
            )
        super().__init__(rect, manager, *args, **kwargs)

        self.filter_data = filter_data
        self.file_path = self.filter_data.path
        self.title = str(Path(*Path(self.file_path).parts[-2:]))
        self.orig_data = self.filter_data.data
        self.features = self.orig_data.columns.to_list()
        self.disp_data = self.orig_data[self.features]
        self.view_data = None


        # header panel
        self.header_h = 40
        self.header = None
        # scrolling container
        self.scroll = None

        # panel
        self.df_panel_w = self.rect.w - 20
        self.df_panel_h = self.rect.h - self.header_h - 20
        self.df_panel = None

        self.max_view_rows = 20
        self.max_view_cols = 7

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
            enabled_features=self.features,
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
            object_id=ObjectID(
                object_id="@dftable_scroll_container",
                class_id="#dftable_scroll_container"
            )
        )

        self.df_panel = UIPanel(
            relative_rect=pg.Rect(0,
                                  self.header_h,
                                  self.df_panel_w,
                                  self.df_panel_h),
            manager=self.manager,
            container=self.panel,
            starting_height=2,
            object_id=ObjectID(
                class_id='@dftable_panel',
                object_id='#dftable_panel'
            )
        )
        self.update_view_data(0, 0)

    def update_data(self):
        self.disp_data = self.filter_data.apply_filters()
        self.disp_data = self.disp_data.reset_index(drop=True)
        self.disp_data = self.disp_data[self.features]
        cols = self.disp_data.columns.tolist()
        if len(self.disp_data) < self.max_view_rows:
            self.view_data = self.disp_data
        else:
            self.view_data = self.disp_data.head(self.max_view_rows)

        new_cols = cols[0:self.max_view_cols]

        self.view_data = self.view_data[new_cols]
        self._create_cells()

    def update_view_data(self,
                         vert_scroll_pos,
                         horiz_scroll_pos):
        vsp = vert_scroll_pos
        hsp = horiz_scroll_pos

        s_max = self.scroll.scroll_slider_max_h()

        start_h = ((len(self.disp_data) * self.v_btn_h)
                   - self.df_panel.rect.h + self.v_btn_h) * (vsp / s_max)
        start_row_idx = math.ceil(start_h / self.v_btn_h)

        if start_row_idx < len(self.disp_data) - self.max_view_rows:
            self.view_data = self.disp_data.loc[
                start_row_idx:start_row_idx + self.max_view_rows
            ]
        elif start_row_idx >= len(self.disp_data):
            self.view_data = self.disp_data.tail(self.max_view_rows)
        else:
            self.view_data = self.disp_data.loc[start_row_idx:]

        self.view_data = self.disp_data[self.disp_data.index.isin(self.view_data.index.tolist())]
        s_max = self.scroll.scroll_slider_max_w()
        cols = self.features
        start_w = (len(cols) * self.v_btn_w) * (hsp / s_max)
        start_col_idx = int(start_w / self.v_btn_w) + 1

        if start_col_idx > len(cols) - 1:
            start_col_idx = len(cols) - 1

        if start_col_idx < len(cols):
            new_cols = cols[start_col_idx:start_col_idx + self.max_view_cols]
        else:
            new_cols = cols

        new_cols = [INDEX] + new_cols
        self.view_data = self.view_data[new_cols]
        import time
        start = time.time()
        self._create_cells()
        end = time.time()
        print('TIME TO CREATE CELLS: ', end - start)

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

        slider_size_area = 5000
        total_data = len(self.disp_data)
        if self.v_btn_h * total_data < self.rect.h:
            slider_size_area = self.v_btn_h * total_data
        elif self.rect.h < self.v_btn_h * total_data < 8000:
            slider_size_area = self.v_btn_h * total_data
        else:
            slider_size_area = 8000

        self.scroll.set_scrollable_area_dimensions((
            self.f_btn_w * len(self.features),
            slider_size_area
        ))

        if self.view_data is None:
            self.view_data = self.disp_data.head(self.max_view_rows)
        start_x = self.scroll.relative_rect.x
        start_y = 0

        for i, f in enumerate(self.view_data.columns.tolist()):
            btn_x = start_x + self.f_btn_w * i
            btn_y = start_y
            btn_rect = pg.Rect(btn_x, btn_y,
                               self.f_btn_w,
                               self.f_btn_h)
            sort_callback = partial(self.sort_feature, f)
            btn = UICallbackButton(
                relative_rect=btn_rect,
                text=f,
                manager=self.manager,
                container=self.df_panel,
                callback=sort_callback,
                tool_tip_text=f,
                object_id=ObjectID(
                    class_id='@dftable_feature_button',
                    object_id='#dftable_feature_button'
                )
            )

            self.feature_buttons[f] = btn
            focus_set.add(btn)
        # last_f_btn = self.feature_buttons[self.enabled_features[-1]]
        def empty():
            return None

        # Add index values
        for i, idx in enumerate(self.view_data[INDEX].values.tolist()):
            val = idx
            btn_x = start_x
            btn_y = start_y + self.f_btn_h + self.v_btn_h * i
            # btn_rect = pg.Rect(btn.rect.x, btn.rect.y + 30 * (i + 1),
            #                    btn_width, 30)
            btn_rect = pg.Rect(btn_x,
                               btn_y,
                               self.v_btn_w, self.v_btn_h)
            cell_obj_id = ObjectID(
                class_id="@dftable_feature_button",
                object_id="#dftable_index_cell_button"
            )
            btn = UICallbackButton(
                relative_rect=btn_rect,
                text=str(val)[:20],
                manager=self.manager,
                container=self.df_panel,
                callback=empty,
                tool_tip_text=str(val),
                object_id=cell_obj_id
            )

            focus_set.add(btn)
            self.cells.append(btn)

        f_view_data = self.view_data[self.view_data.columns[1:]]
        start_x = start_x + self.v_btn_w
        start_y = 0
        # Add Feature Values

        for i, (_, row) in enumerate(f_view_data.iterrows()):
            for j, f in enumerate(f_view_data.columns.to_list()):

                val = row[f]
                btn_x = start_x + self.v_btn_w * j
                btn_y = start_y + self.f_btn_h + self.v_btn_h * i

                btn_rect = pg.Rect(btn_x,
                                   btn_y,
                                   self.v_btn_w, self.v_btn_h)

                cell_obj_id = ObjectID(
                    class_id="@dftable_feature_button",
                    object_id="#dftable_cell_odd_button"
                )
                if j % 2 == 0:
                    cell_obj_id = ObjectID(
                        class_id="@dftable_feature_button",
                        object_id="#dftable_cell_even_button"
                    )

                btn = UICallbackButton(
                relative_rect=btn_rect,
                text=str(val[:20]),
                manager=self.manager,
                container=self.df_panel,
                callback=empty,
                tool_tip_text=str(val),
                object_id=cell_obj_id
                )

                focus_set.add(btn)
                self.cells.append(btn)
                # self.feature_buttons[f] = btn
        focus_set.add(self.df_panel)
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
