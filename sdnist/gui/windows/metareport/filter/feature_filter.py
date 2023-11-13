from typing import Optional, Callable
import pandas as pd
import pygame as pg
import pygame_gui as pggui

from pygame_gui.core.object_id import ObjectID
from pygame_gui.elements.ui_panel import UIPanel
from pygame_gui.elements.ui_scrolling_container import \
    UIScrollingContainer
from pygame_gui.elements.ui_drop_down_menu import \
    UIDropDownMenu

from sdnist.gui.panels import \
    AbstractPanel, Header
from sdnist.gui.elements import \
    UICallbackButton
from sdnist.gui.elements import \
    LabelDropDown, ChipsDropDown


class FeatureFilter(AbstractPanel):
    def __init__(self,
                 on_update_filter_callback: Optional[Callable],
                 uid: str,
                 index: pd.DataFrame,
                 feature_filters: Optional[dict] = None,
                 parent_window=None,
                 delete_filter_callback: Optional[Callable] = None,
                 *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.on_update_filter_callback = on_update_filter_callback
        self.uid = uid
        self.index = index
        self.feature_filters = feature_filters
        self.parent_window = parent_window
        self.delete_filter_callback = delete_filter_callback
        self.pad_x = 0
        self.pad_y = 0

        self.available_w = self.rect.w - 2 * self.pad_x
        self.available_h = self.rect.h - 2 * self.pad_y

        self.c_btn_w = self.available_h
        self.c_btn_h = self.available_h
        self.feature_dropdown_h = self.available_h
        self.feature_dropdown_w = self.available_w * 0.3
        self.feature_values_h = self.available_h
        self.feature_values_w = self.available_w * 0.6

        self.cancel_button = None
        self.feature_dropdown = None
        self.feature_values = None

        self.selected_feature = None
        self.selected_feature_values = []

        if len(self.feature_filters):
            self.selected_feature = list(self.feature_filters.keys())[0]
            self.selected_feature_values = \
                self.feature_filters[self.selected_feature]

        self._create()

    def get_elements(self):
        elems = [
            self.panel,
            self.cancel_button,
        ]
        elems = elems + self.feature_dropdown.get_elements()
        elems = elems + self.feature_values.get_elements()

        elems = [e for e in elems if e]
        return elems

    def get_data(self):
        if len(self.selected_feature_values) == 0:
            return dict()
        return {self.selected_feature: self.selected_feature_values}

    def _create(self):
        c_btn_x = self.pad_x
        c_btn_rect = pg.Rect((c_btn_x, 0),
                             (self.c_btn_h, self.c_btn_h))
        self.cancel_button = UICallbackButton(
            callback=self.delete_filter_callback,
            relative_rect=c_btn_rect,
            text='X',
            manager=self.manager,
            container=self.panel,
            anchors={'left': 'left',
                     'top': 'top'},
            object_id=ObjectID(class_id='@icon_button',
                               object_id='#remove_filter_button')
        )

        dropdown_rect = pg.Rect((self.c_btn_w, 0),
                                (self.feature_dropdown_w,
                                 self.feature_dropdown_h))
        if self.selected_feature is None:
            self.selected_feature = self.index.columns.tolist()[0]

        self.feature_dropdown = LabelDropDown(
            on_change_callback=self.on_feature_change,
            rect=dropdown_rect,
            manager=self.manager,
            container=self.panel,
            parent_window=self.parent_window,
            options_list=self.index.columns.tolist(),
            starting_option=self.selected_feature
        )

        values = self.index[self.selected_feature] \
            .unique().tolist()
        fv_x = self.c_btn_w + self.feature_dropdown_w
        values_rect = pg.Rect((fv_x, 0),
                              (self.feature_values_w,
                               self.feature_values_h))
        start_options = self.selected_feature_values

        self.feature_values = ChipsDropDown(
            on_selected_callback=self.on_feature_values_change,
            rect=values_rect,
            manager=self.manager,
            container=self.panel,
            parent_window=self.parent_window,
            options_list=values,
            starting_options=start_options
        )

    def destroy(self):
        super().destroy()
        elems = [self.feature_dropdown,
                 self.feature_values]
        for elem in elems:
            if elem is not None:
                elem.destroy()

    def rebuild(self):
        self.panel.set_relative_position((self.rect.x,
                                          self.rect.y))
        self.panel.rebuild()

    def handle_event(self, event: pg.event.Event):
        pass

    def add_filter(self):
        pass

    def on_feature_change(self, new_feature: str):
        values = self.index[new_feature].unique().tolist()
        self.feature_values.set_options(values)
        self.selected_feature = new_feature
        self.on_update_filter_callback()

    def on_feature_values_change(self, new_feature_values: str):
        self.selected_feature_values = new_feature_values
        self.on_update_filter_callback()

