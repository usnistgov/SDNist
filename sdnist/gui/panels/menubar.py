from typing import Callable
import pygame as pg
import pygame_gui as pggui
from pygame_gui.elements.ui_panel import UIPanel
from pygame_gui.elements.ui_label import UILabel

from sdnist.gui.panels.panel import AbstractPanel
from sdnist.gui.elements import UICallbackButton

LOAD_DATA = 'Load Data'
TARGET_DATA = 'Target Data'
SETTINGS = 'Settings'

menubar_btns = [
    LOAD_DATA,
    TARGET_DATA,
    SETTINGS
]


class MenuBar(AbstractPanel):
    def __init__(self, rect, manager, data=None):
        super().__init__(rect, manager, data)
        self.panel = None
        self.buttons = dict()
        self._create()

    def set_callback(self, btn_name: str,
                     callback: Callable):
        if btn_name not in self.buttons:
            raise ValueError(f'Invalid button name: {btn_name}')
        btn = self.buttons[btn_name]
        btn.callback = callback

    def _create(self):
        self.panel = UIPanel(self.rect,
                             starting_height=0,
                             manager=self.manager)
        def empty():
            return

        net_width = 0
        for i, btn_name in enumerate(menubar_btns):
            btn_rect = pg.Rect((0, 0), (120, 30))
            btn_rect.left = net_width
            print('LEFT', btn_rect.left)
            btn = UICallbackButton(relative_rect=btn_rect,
                                   callback=empty,
                                   text=btn_name,
                                   container=self.panel,
                                   parent_element=self.panel,
                                   manager=self.manager,
                                   anchors={'left': 'left',
                                            'centery': 'centery'})
            net_width += btn.relative_rect.width
            print('NET WIDTH', net_width)
            self.buttons[btn_name] = btn

    def destroy(self):
        if self.panel is not None:
            self.panel.kill()
            self.panel = None
        self.buttons.clear()

    def handle_event(self, event: pg.event.Event):
        pass
