from typing import Callable
import pygame as pg
import pygame_gui as pggui
from pygame_gui.elements.ui_panel import UIPanel
from pygame_gui.elements.ui_label import UILabel

from sdnist.gui.panels.panel import AbstractPanel
from sdnist.gui.elements import UICallbackButton

METADATA_BTN = 'Metadata'
REPORT_BTN = 'Report'
INDEX_BTN = 'Index'
ARCHIVE_BTN = 'Archive'
METAREPORT_BTN = 'Metareport'

toolbar_btns = [METADATA_BTN,
                REPORT_BTN,
                INDEX_BTN,
                ARCHIVE_BTN,
                METAREPORT_BTN]


class Toolbar(AbstractPanel):
    def __init__(self, rect, manager):
        super().__init__(rect, manager)
        self.panel = None
        self.btns = dict()

        self._create()

    def set_callback(self, btn_name: str,
                     callback: Callable):
        if btn_name not in self.btns:
            raise ValueError(f'Invalid button name: {btn_name}')
        btn = self.btns[btn_name]
        btn.callback = callback

    def _create(self):
        self.panel = UIPanel(self.rect,
                             starting_height=0,
                             manager=self.manager)
        def empty():
            return

        net_width = 0

        for btn_name in toolbar_btns[::-1]:
            btn_rect = pg.Rect((0, 0), (120, 30))
            btn_rect.right = -1 * net_width
            btn = UICallbackButton(relative_rect=btn_rect,
                                   callback=empty,
                                   text=btn_name,
                                   container=self.panel,
                                   parent_element=self.panel,
                                   manager=self.manager,
                                   anchors={'right': 'right',
                                            'centery': 'centery'})
            net_width += btn.relative_rect.width
            self.btns[btn_name] = btn

    def destroy(self):
        if self.panel is not None:
            self.panel.kill()
            self.panel = None
        self.btns.clear()

    def handle_event(self, event: pg.event.Event):
        pass
