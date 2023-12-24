from typing import Optional, Callable

import pygame as pg
import pygame_gui as pggui

from pygame_gui.core import ObjectID
from pygame_gui.core import UIElement
from pygame_gui.elements.ui_window import UIWindow
from pygame_gui.elements.ui_label import UILabel

from sdnist.gui.elements.buttons.button import UICallbackButton
from sdnist.gui.elements.selection import CallbackSelectionList


class LabelDropDown:
    def __init__(self,
                 on_change_callback: Optional[Callable],
                 rect: pg.Rect,
                 manager: pggui.UIManager,
                 container: any,
                 parent_window: UIWindow,
                 options_list: list,
                 starting_option: str,
                 *args, **kwargs):
        self.on_change_callback = on_change_callback
        self.rect = rect
        self.manager = manager
        self.container = container
        self.parent_window = parent_window
        self.options_list = options_list
        self.starting_option = starting_option
        self.lbl_btn = None
        self.dd: Optional[CallbackSelectionList] = None

        self._create()

    def get_elements(self):
        elems = [
            self.lbl_btn
        ]
        return elems

    def _create(self):
        lbl_btn_rect = pg.Rect((self.rect.x, self.rect.y),
                               (self.rect.w, self.rect.h))
        self.lbl_btn = UICallbackButton(
            callback=self.toggle_dropdown,
            relative_rect=lbl_btn_rect,
            text=self.starting_option,
            manager=self.manager,
            container=self.container,
            object_id=ObjectID(
                class_id='@toolbar_button',
                object_id='#metareport_filter_dropdown_button')
        )
        lbl_w = 20
        lbl_x = lbl_btn_rect.x + lbl_btn_rect.w - lbl_w
        lbl_y = lbl_btn_rect.y

        lbl_rect = pg.Rect((lbl_x, lbl_y),
                           (lbl_w, self.rect.h))

        self.lbl = UILabel(
            relative_rect=lbl_rect,
            text='+',
            manager=self.manager,
            container=self.container,
            anchors={'left': 'left',
                     'top': 'top'},
            object_id=ObjectID(
                class_id='@option_label',
                object_id='#metareport_filter_expand_label')
        )
        self.lbl.text_horiz_alignment = 'center'

    def destroy(self):
        self.close_dropdown()
        self.lbl_btn.kill()
        self.lbl.kill()

    def toggle_dropdown(self):
        if self.dd:
            self.close_dropdown()
        else:
            self.create_dropdown()

    def close_dropdown(self):
        if self.dd:
            self.dd.kill()
            self.dd = None
            self.lbl.set_text('+')

    def create_dropdown(self):
        dd_x = self.container.rect.x - self.parent_window.rect.x \
            + self.rect.x
        dd_y = self.container.rect.y - self.parent_window.rect.y \
            + self.rect.h

        dd_rect = pg.Rect((dd_x,
                           dd_y),
                          (self.rect.w,
                           150))

        self.dd = CallbackSelectionList(
            callback=self.update_selected_value,
            starting_height=4,
            relative_rect=dd_rect,
            item_list=self.options_list,
            manager=self.manager,
            container=self.parent_window,
            anchors={'left': 'left',
                     'top': 'top'},
            default_selection=self.starting_option
        )
        self.lbl.set_text('-')

    def update_selected_value(self, new_value):
        if new_value is None or new_value == self.starting_option:
            return

        self.lbl_btn.set_text(new_value)
        self.starting_option = new_value
        self.close_dropdown()
        if self.on_change_callback:
            self.on_change_callback(new_value)
