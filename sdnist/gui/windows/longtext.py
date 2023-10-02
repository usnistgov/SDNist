from pathlib import Path
from typing import Optional, Callable
import pygame as pg
import pygame_gui as pggui

from pygame_gui.elements.ui_window import UIWindow
from pygame_gui.elements.ui_text_entry_box import UITextEntryBox

from sdnist.gui.elements.textentrybox import CustomTextEntryBox


class LongTextWindow:
    def __init__(self, rect: pg.Rect,
                 manager: pggui.UIManager,
                 text_change_callback: Optional[Callable] = None,
                 container: Optional[any] = None,
                 initial_text: str = '',
                 data: any = None):
        self.w, self.h = manager.window_resolution
        self.manager = manager
        self.data = data
        self.rect = rect
        self.container = container
        self.text_change_callback = text_change_callback
        self.panel = None
        self.text_in = None
        self.text = initial_text
        self._create()

    def _create(self):
        self.window = UIWindow(rect=self.rect,
                               manager=self.manager,
                               window_display_title=self.data,
                               draggable=False,
                               resizable=True)

        self.text_rect = pg.Rect((0, 0),
                                 (self.rect.w, self.rect.h * 0.5))
        self.text_in = CustomTextEntryBox(
                                   text_changed_callback=self.text_change_callback,
                                   placeholder_text='',
                                   relative_rect=self.text_rect,
                                   manager=self.manager,
                                   container=self.window)
        self.text_in.set_text(self.text)
        # self.text.set_minimum_dimensions((self.rect.w, self.rect.h * 0.5))

    def destroy(self):
        self.window.kill()
        self.text_in.kill()
