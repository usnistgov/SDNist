from typing import Optional
import pygame as pg
import pygame_gui as pggui

from pygame_gui.elements.ui_window import UIWindow
from pygame_gui.elements.ui_panel import UIPanel

from sdnist.gui.elements import UICallbackButton


class DoneWindow:
    def __init__(self,
                 rect: pg.Rect,
                 manager: pggui.UIManager,
                 title: str = '',
                 container: Optional[any] = None,
                 data: any = None,
                 done_button_visible=False,
                 done_button_callback=None):
        self.w, self.h = manager.window_resolution
        self.manager = manager
        self.data = data
        self.rect = rect
        self.container = container
        self.base = None
        self.done_button = None
        self.done_button_visible = done_button_visible
        self.done_button_callback = done_button_callback
        print('init')
        self._create()

    def _create(self):
        print('MAIN CREATE')
        if self.container is None:
            print('CONTAINER IS NONE')
            self.base = UIWindow(rect=self.rect,
                                 manager=self.manager,
                                 window_display_title=self.data,
                                 draggable=False,
                                 resizable=False)
        else:
            self.panel = UIPanel(self.rect,
                                 starting_height=1,
                                 manager=self.manager,
                                 container=self.container)



