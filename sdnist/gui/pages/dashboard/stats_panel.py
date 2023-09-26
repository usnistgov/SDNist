from typing import Optional
from pathlib import Path
import json

import pygame as pg
import pygame_gui as pggui
from pygame_gui.elements.ui_window import UIWindow
from pygame_gui.elements.ui_button import UIButton
from pygame_gui.elements.ui_label import UILabel
from pygame_gui.elements.ui_text_entry_line import UITextEntryLine

from sdnist.gui.panels import AbstractPanel
from sdnist.gui.elements import UICallbackButton


class StatsPanel(AbstractPanel):
    def __init__(self, rect: pg.Rect,
                 manager: pggui.UIManager,
                 csv_file: str,
                 copy_from_csv_file: Optional[str] = None):
        super().__init__(rect, manager)
        self.csv_file = csv_file
        self.copy_from_csv_file = copy_from_csv_file
        self.window = None
        self._create()

    def _create(self):
        self.window = UIWindow(rect=self.rect,
                               manager=self.manager,
                               window_display_title=
                               "" + \
                               self.csv_file ,
                               draggable=False,
                               resizable=True)

    def destroy(self):
        self.window.kill()
        self.window = None

    def handle_event(self, event: pg.event.Event):
        pass