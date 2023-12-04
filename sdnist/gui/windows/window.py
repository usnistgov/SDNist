from abc import ABC, abstractmethod
import pygame as pg
import pygame_gui as pggui

from pygame_gui.elements.ui_window import UIWindow

class PlainWindow:
    def __init__(self,
                 rect: pg.Rect,
                 manager: pggui.UIManager,
                 on_top: bool = False,
                 *args, **kwargs):
        self.w, self.h = manager.window_resolution
        self.x, self.y = manager.root_container.rect.topleft
        self.manager = manager
        self.rect = rect
        self.on_top = on_top
        self.window = UIWindow(rect=self.rect,
                               manager=self.manager,
                               *args, **kwargs)

    def destroy(self):
        self.window.kill()
        self.window = None

    def handle_event(self, event: pg.event.Event):
        pass


class AbstractWindow(ABC):
    @abstractmethod
    def __init__(self,
                 rect: pg.Rect,
                 manager: pggui.UIManager,
                 data: any = None,
                 on_top: bool = False,
                 *args, **kwargs):
        self.w, self.h = manager.window_resolution
        self.x, self.y = manager.root_container.rect.topleft
        self.manager = manager
        self.data = data
        self.rect = rect
        self.on_top = on_top
        self.window = UIWindow(rect=self.rect,
                               manager=self.manager,
                               *args, **kwargs)

    @abstractmethod
    def _create(self):
        pass

    def destroy(self):
        self.window.kill()
        self.window = None

    def handle_event(self, event: pg.event.Event):
        if (self.on_top and
                not self.manager.ui_window_stack.is_window_at_top(self.window)):
            self.manager.ui_window_stack.move_window_to_front(self.window)
