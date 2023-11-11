from abc import ABC, abstractmethod
import pygame as pg
import pygame_gui as pggui

from pygame_gui.elements.ui_window import UIWindow


class AbstractWindow(ABC):
    @abstractmethod
    def __init__(self, rect: pg.Rect,
                 manager: pggui.UIManager,
                 data: any = None,
                 *args, **kwargs):
        self.w, self.h = manager.window_resolution
        self.x, self.y = manager.root_container.rect.topleft
        self.manager = manager
        self.data = data
        self.rect = rect
        self.window = UIWindow(rect=self.rect,
                               manager=self.manager,
                               *args, **kwargs)

    @abstractmethod
    def _create(self):
        pass

    def destroy(self):
        self.window.kill()
        self.window = None

    @abstractmethod
    def handle_event(self, event: pg.event.Event):
        pass
