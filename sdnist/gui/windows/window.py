from abc import ABC, abstractmethod
import pygame as pg
import pygame_gui as pggui


class AbstractWindow(ABC):
    @abstractmethod
    def __init__(self, rect: pg.Rect,
                 manager: pggui.UIManager,
                 data: any = None):
        self.w, self.h = manager.window_resolution
        self.manager = manager
        self.data = data
        self.rect = rect

    @abstractmethod
    def _create(self):
        pass

    @abstractmethod
    def destroy(self):
        pass

    @abstractmethod
    def handle_event(self, event: pg.event.Event):
        pass
