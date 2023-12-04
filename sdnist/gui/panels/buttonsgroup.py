from typing import Callable
import pygame as pg
from functools import partial

import pygame_gui as pggui
from pygame_gui.elements.ui_panel import UIPanel
from pygame_gui.elements.ui_label import UILabel

from sdnist.gui.panels.panel import AbstractPanel
from sdnist.gui.elements import UICallbackButton
from sdnist.gui.groups import ButtonGroup

from sdnist.gui.strs import *

class ButtonsGroupPanel(AbstractPanel):
    def __init__(self,
                 on_select_callback,
                 *args, **kwargs):
        kwargs['starting_height'] = 2
        super().__init__(*args, **kwargs)
        self.on_select_callback = on_select_callback
        self.button_names = [INFORMATION, DATA]
        self.buttons = dict()
        self.btn_grp = None
        self._create()

    def set_callback(self, btn_name: str,
                     callback: Callable):
        if btn_name not in self.buttons:
            raise ValueError(f'Invalid button name: {btn_name}')
        btn = self.buttons[btn_name]
        btn.callback = callback

    def _create(self):
        def empty():
            return

        net_width = 0
        btn_width = 120
        all_btn_width = btn_width * len(self.button_names)
        start_x = (self.rect.w - all_btn_width) // 2
        for btn_name in self.button_names:
            x = start_x + net_width
            btn_rect = pg.Rect((x, 0), (120, 30))
            callback = partial(self.on_select_button, btn_name)
            btn = UICallbackButton(relative_rect=btn_rect,
                                   callback=callback,
                                   text=btn_name,
                                   container=self.panel,
                                   parent_element=self.panel,
                                   manager=self.manager,
                                   anchors={'left': 'left',
                                            'centery': 'centery'})
            net_width += btn.relative_rect.width
            self.buttons[btn_name] = btn
        self.btn_grp = ButtonGroup(list(self.buttons.values()))
        self.on_select_button(INFORMATION)

    def destroy(self):
        super().destroy()
        self.buttons.clear()

    def handle_event(self, event: pg.event.Event):
        pass

    def select_button(self, btn_name: str):
        if not self.btn_grp:
            return
        self.btn_grp.select(btn_name)

    def on_select_button(self, btn_name: str):
        if not self.btn_grp:
            return
        self.select_button(btn_name)
        self.on_select_callback(btn_name)

