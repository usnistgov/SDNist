import uuid
from typing import Optional
from itertools import chain
from functools import partial

import pandas as pd

import pygame_gui as pggui
import pygame as pg

from pygame_gui.elements.ui_panel import UIPanel
from pygame_gui.elements.ui_window import UIWindow

from pygame_gui.elements.ui_scrolling_container import \
    UIScrollingContainer

from sdnist.gui.windows.metareport.filter.feature_filter import \
    FeatureFilter
from sdnist.gui.panels.dftable.filterdata import \
    FilterData


class FilterSet:
    def __init__(self,
                 filterset_name: str,
                 filter_data: FilterData,
                 rect: pg.Rect,
                 manager: pggui.UIManager,
                 container: Optional[UIPanel] = None,
                 parent_window: Optional[UIWindow] = None,
                 on_update_callback: Optional[callable] = None,
                 *args, **kwargs):
        self.filterset_name = filterset_name
        self.filter_data = filter_data
        self.rect = rect
        self.manager = manager
        self.container = container
        self.parent_window = parent_window
        self.on_update_callback = on_update_callback

        self.feature_filters = dict()

        self.scroll = None

    def _create(self):
        scroll_rect = pg.Rect(0, self.rect.y,
                              self.rect.w, self.rect.h - 20)
        self.scroll = UIScrollingContainer(
            relative_rect=scroll_rect,
            manager=self.manager,
            container=self.container,
            starting_height=1,

        )
        filters = self.filter_data.get_filters(self.filterset_name)
        for uid, f_filter_d in filters.items():
            self.add_feature_filter(uid, filter_data=f_filter_d)

    def destroy(self):
        if self.scroll:
            self.scroll.kill()
            self.scroll = None
        if self.feature_filters:
            for ff in self.feature_filters.values():
                ff.destroy()
        self.feature_filters = dict()

    def show(self):
        self.destroy()
        self._create()

    def hide(self):
        self.destroy()

    def add_feature_filter(self,
                           filter_id: str = None,
                           filter_data: dict = None):
        if filter_id is None:
            filter_id = uuid.uuid4().hex
        if filter_data is None:
            filter_data = dict()

        ff_w = self.rect.w - 20
        ff_x = 0
        ff_y = (len(self.feature_filters)) * 40

        ff_rect = pg.Rect((ff_x, ff_y),
                          (ff_w, 40))
        remove_ff_callback = partial(self.delete_feature_filter,
                                     filter_id)
        on_update_callback = partial(self.on_update_filter_callback,
                                     filter_id=filter_id)

        ff = FeatureFilter(on_update_filter_callback=on_update_callback,
                           uid=filter_id,
                           index=self.filter_data.data,
                           feature_filters=filter_data,
                           parent_window=self.parent_window,
                           delete_filter_callback=remove_ff_callback,
                           rect=ff_rect,
                           manager=self.manager,
                           container=self.scroll,
                           anchors={'top': 'top',
                                    'left': 'left'},
                           object_id=pggui.core.ObjectID(
                             class_id='@feature_filter_panel',
                             object_id=f'#feature_filter_panel'
                           ))

        self.feature_filters[filter_id] = ff

        self.scroll.set_scrollable_area_dimensions((
            self.rect.w - 20, ff.rect.y + ff.rect.h
        ))

        f_filters = self.feature_filters.values()
        focus_set = list(chain(*[ff.get_elements() for ff in f_filters]))
        focus_set = set(focus_set + [self.scroll])
        if self.scroll.vert_scroll_bar:
            self.scroll.vert_scroll_bar.set_focus_set(focus_set)

        self.on_update_filter_callback(filter_id)

    def delete_feature_filter(self, filter_id: str):
        if filter_id in self.feature_filters:
            ff = self.feature_filters[filter_id]
            ff.destroy()
            del self.feature_filters[filter_id]

        self.filter_data.remove(self.filterset_name, filter_id)
        self.on_update_filter_callback(filter_id)

        # update filters y positions
        for i, (k, v) in enumerate(self.feature_filters.items()):
            v.rect.y = i * 40
            v.rebuild()

        f_filters = list(self.feature_filters.values())
        if len(f_filters) == 0:
            scroll_h = self.rect.h - 20
        else:
            l_ff = f_filters[-1]
            scroll_h = l_ff.rect.y + l_ff.rect.h

        self.scroll.set_scrollable_area_dimensions((
            self.rect.w - 20, scroll_h
        ))

        focus_set = list(chain(*[ff.get_elements() for ff in f_filters]))
        focus_set = set(focus_set + [self.scroll])
        if self.scroll.vert_scroll_bar:
            self.scroll.vert_scroll_bar.set_focus_set(focus_set)

    def on_update_filter_callback(self, filter_id: str):
        ff = self.feature_filters.get(filter_id, None)
        f_data = ff.get_data() if ff else dict()
        if self.on_update_callback:
            self.on_update_callback(filter_id, f_data)

