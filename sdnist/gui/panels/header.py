import pygame as pg
import pygame_gui as pggui
from pygame_gui.elements.ui_panel import UIPanel
from pygame_gui.elements.ui_label import UILabel

from sdnist.gui.panels.panel import AbstractPanel


class Header(AbstractPanel):
    def __init__(self, rect, manager):
        super().__init__(rect, manager)
        self.header_panel = None
        self.header_text = None
        self._create()

    def _create(self):
        self.header_panel = UIPanel(self.rect,
                                    starting_height=0,
                                    manager=self.manager)

        # Header Text using pygame_gui
        self.header_text = UILabel(relative_rect=pg.Rect((0, 0),
                                                         (100, 50)),
                                    container=self.header_panel,
                                    parent_element=self.header_panel,
                                    text='DASHBOARD',
                                    manager=self.manager,
                                    anchors={'centery': 'centery',
                                             'centerx': 'centerx'})

    def destroy(self):
        if self.header_panel is not None:
            self.header_panel.kill()
            self.header_panel = None
        if self.header_text is not None:
            self.header_text.kill()
            self.header_text = None

    def handle_event(self, event: pg.event.Event):
        pass