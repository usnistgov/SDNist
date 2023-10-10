from pathlib import Path
from typing import Optional, Callable
import pygame as pg
import pygame_gui as pggui

from pygame_gui.elements.ui_window import UIWindow
from pygame_gui.elements.ui_panel import UIPanel
from pygame_gui.elements.ui_text_box import UITextBox
from pygame_gui.elements.ui_text_entry_box import UITextEntryBox

from sdnist.gui.elements.textentrybox import CustomTextEntryBox
from sdnist.gui.panels import AbstractPanel


class LongTextInputPanel(AbstractPanel):
    def __init__(self,
                 rect: pg.Rect,
                 manager: pggui.UIManager,
                 text_change_callback: Optional[Callable] = None,
                 container: Optional[any] = None,
                 initial_text: str = '',
                 data: any = None):
        super().__init__(rect, manager, container, data)
        self.text_change_callback = text_change_callback
        self.panel = None
        self.text_in = None
        self.text = initial_text
        self._create()

    def _create(self):
        self.panel = UIPanel(relative_rect=self.rect,
                             manager=self.manager,
                             container=self.container,
                             starting_height=10)
        title_height = 30
        self.title_rect = pg.Rect((0, 0),
                                  (self.rect.w, title_height))
        title_text = f'Input {self.data}'
        self.title = UITextBox(html_text=title_text,
                               relative_rect=self.title_rect,
                               manager=self.manager,
                               container=self.panel)
        self.title.scroll_bar_width = 0
        self.title.rebuild()
        self.text_rect = pg.Rect((0, title_height),
                                 (self.rect.w, self.rect.h * 0.4))
        self.text_in = CustomTextEntryBox(
                                   text_changed_callback=self.text_change_callback,
                                   placeholder_text='',
                                   relative_rect=self.text_rect,
                                   manager=self.manager,
                                   container=self.panel)
        self.text_in.set_text(self.text)
        # self.text.set_minimum_dimensions((self.rect.w, self.rect.h * 0.5))

    def destroy(self):
        self.panel.kill()
        self.text_in.kill()

    def handle_event(self, event: pg.event.Event):
        pass
