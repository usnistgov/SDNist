from typing import Optional, Callable
from enum import Enum

import pandas as pd
import pygame as pg
import uuid
import pygame_gui as pggui
from functools import partial
from itertools import chain

from pygame_gui.elements.ui_panel import UIPanel
from pygame_gui.elements.ui_label import UILabel
from pygame_gui.elements.ui_scrolling_container import \
    UIScrollingContainer
from pygame_gui.core.object_id import ObjectID

from sdnist.gui.panels import \
    AbstractPanel, Header
from sdnist.gui.elements import \
    UICallbackButton
from sdnist.gui.groups import \
    ButtonGroup

from sdnist.gui.windows.metareport.filter.feature_filter import \
    FeatureFilter
from sdnist.gui.windows.metareport.filter.filterset import \
    FilterSet
from sdnist.gui.panels.dftable.filterdata import \
    FilterData, FSetType


class FiltersPanel(AbstractPanel):
    def __init__(self,
                 filter_data: FilterData,
                 filter_type: FSetType,
                 header_text: str = "Filters",
                 on_update_callback: Optional[Callable] = None,
                 *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.filter_data = filter_data

        self.filter_type = filter_type
        self.header_text = header_text
        self.on_update_callback = on_update_callback
        self.pad_x = 0
        self.pad_y = 0
        self.title_w = self.rect.w
        self.title_h = 40

        self.header_h = self.title_h
        self.add_btn_h = 30  # add filter button height
        self.scroll_h = self.rect.h - \
            self.header_h - 3 * self.pad_y
        self.header_w = 150 - 2 * self.pad_x
        self.scroll_w = self.rect.w - 2 * self.pad_x
        self.add_btn_w = 100
        # filter set
        self.fset_btn_w = 50
        self.fset_union_lbl_w = 30
        self.fset_btn_h = self.add_btn_h

        self.title_panel = None
        self.header = None
        self.scroll = None
        self.add_fset_btn = None
        self.add_filter_btn = None
        self.filter_sets_elems = []
        self.filter_set_scrolls = dict()
        self.filter_set_group = None
        self.filter_sets_lbls = []
        self.union_lbls = []

        self.filter_set_number = 0
        self.filters = dict()

    def _create(self):
        title_rect = pg.Rect((0, 0),
                            (self.title_w, self.title_h))
        obj_name = f'{self.filter_type.name.lower()}_title_panel'
        self.title_panel = UIPanel(
            relative_rect=title_rect,
            manager=self.manager,
            container=self.panel,
            starting_height=0,
            anchors={'top': 'top',
                     'left': 'left'},
            object_id=ObjectID(
                class_id=f'@filter_title_panel',
                object_id=f'#{obj_name}'
            )
        )

        head_rect = pg.Rect((0, self.pad_y),
                            (self.header_w, self.header_h))
        self.header = Header(
            text=self.header_text,
            rect=head_rect,
            manager=self.manager,
            container=self.panel,
            anchors={'top': 'top',
                     'left': 'left'},
            object_id=ObjectID(
                    class_id=f'@filter_title_panel',
                    object_id=f'#{obj_name}')
        )

        self.create_filterset_btns()

    def destroy(self):
        super().destroy()
        self.destroy_filterset_buttons()
        if self.header:
            self.header.kill()
            self.header = None
        for scroll in self.filter_set_scrolls.values():
            scroll.destroy()
        self.filter_set_scrolls = dict()

    def destroy_filterset_buttons(self):
        if self.add_fset_btn:
            self.add_fset_btn.kill()
            self.add_fset_btn = None

        if self.add_filter_btn:
            self.add_filter_btn.kill()
            self.add_filter_btn = None

        for elem in self.filter_sets_elems:
            elem.kill()
        self.filter_sets_elems = []

        for elem in self.union_lbls:
            elem.kill()
        self.filter_sets_lbls = []

    def handle_event(self, event: pg.event.Event):
        pass

    def create_filterset_btns(self):
        self.destroy_filterset_buttons()
        self.filter_set_number += 1
        fset_name = self.filter_data.filterset_name(
            self.filter_type, self.filter_set_number
        )
        self.filters[fset_name] = dict()

        start_x = self.header.title_x + self.header_w + self.pad_x

        self.filter_set_group = ButtonGroup()

        # create filterset buttons
        for i, fset_name in enumerate(self.filters.keys()):
            fset_x = start_x + self.fset_btn_w * i
            fset_x = fset_x + self.fset_union_lbl_w * i

            # create button to select filter set
            fset_rect = pg.Rect((fset_x, 0),
                                (self.fset_btn_w, self.fset_btn_h))
            select_filter_set = partial(self.select_feature_set,
                                        fset_name)
            fset_btn = UICallbackButton(
                callback=select_filter_set,
                can_toggle=False,
                relative_rect=fset_rect,
                text=fset_name,
                manager=self.manager,
                container=self.title_panel,
                anchors={'centery': 'centery',
                         'left': 'left'},
            )

            # create container for the filterset. This container
            # will hold the feature filters
            if fset_name not in self.filter_set_scrolls:
                fset_scroll_y = self.header_h + 2 * self.pad_y
                fset_scroll_rect = pg.Rect(0, fset_scroll_y,
                                           self.scroll_w, self.scroll_h)
                on_update_callback = partial(self.on_update_filter_callback,
                                             fset_name)
                fset_scroll = FilterSet(filterset_name=fset_name,
                                        filter_data=self.filter_data,
                                        rect=fset_scroll_rect,
                                        manager=self.manager,
                                        container=self.panel,
                                        parent_window=self.container,
                                        on_update_callback=on_update_callback)
                self.filter_set_scrolls[fset_name] = fset_scroll

            self.filter_sets_elems.append(fset_btn)
            self.filter_set_group.add(fset_btn)
            self.select_feature_set(fset_name)

            if i < len(self.filters) - 1:
                union_lbl_x = fset_x + self.fset_btn_w
                union_lbl_rect = pg.Rect((union_lbl_x, 0),
                                         (self.fset_union_lbl_w,
                                          self.fset_btn_h))
                union_lbl = UILabel(
                    relative_rect=union_lbl_rect,
                    text='OR',
                    manager=self.manager,
                    container=self.title_panel,
                    anchors={'centery': 'centery',
                             'left': 'left'},
                )
                union_lbl.text_horiz_alignment = 'center'
                union_lbl.rebuild()
                self.union_lbls.append(union_lbl)

        # create buttons to add filterset and filters
        fset_btn_x = self.filter_sets_elems[-1].relative_rect.x + \
            self.filter_sets_elems[-1].relative_rect.w
        add_fset_btn_rect = pg.Rect((fset_btn_x, 0),
                                    (-1, self.add_btn_h))
        self.add_fset_btn = UICallbackButton(
            callback=self.create_filterset_btns,
            relative_rect=add_fset_btn_rect,
            text='Add Filter Set',
            manager=self.manager,
            container=self.title_panel,
            anchors={'centery': 'centery',
                     'left': 'left'},
        )

        add_btn_x = add_fset_btn_rect.x + \
            self.add_fset_btn.relative_rect.w

        add_btn_rect = pg.Rect((add_btn_x, 0),
                               (-1, self.add_btn_h))
        add_feature_filter = partial(self.add_feature_filter)
        self.add_filter_btn = UICallbackButton(
            callback=add_feature_filter,
            relative_rect=add_btn_rect,
            text='Add Filter',
            manager=self.manager,
            container=self.title_panel,
            anchors={'centery': 'centery',
                     'left': 'left'},
        )

    def select_feature_set(self, filter_set_name: str):
        if self.filter_set_group:
            self.filter_set_group.select(filter_set_name)
            for k, scroll in self.filter_set_scrolls.items():
                if k == filter_set_name:
                    scroll.show()
                else:
                    scroll.hide()

    def add_feature_filter(self,
                           filter_id: str = None,
                           filter_data: dict = None):
        filter_set_name = self.filter_set_group.selected
        if filter_set_name not in self.filter_set_scrolls:
            return

        self.filter_set_scrolls[filter_set_name].add_feature_filter(
            filter_id=filter_id,
            filter_data=filter_data
        )

    def on_update_filter_callback(self, filter_set_name: str, filter_id: str, filter_data: dict):
        self.filter_data.update(filter_set_name, filter_id, filter_data)
        if self.on_update_callback:
            self.on_update_callback()
