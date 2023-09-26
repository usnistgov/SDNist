from typing import Optional
from abc import ABC, abstractmethod
import pygame as pg
import pygame_gui as pggui


class AbstractPanel(ABC):
    @abstractmethod
    def __init__(self, rect: pg.Rect,
                 manager: pggui.UIManager,
                 container: Optional[any] = None,
                 data: any = None):
        self.w, self.h = manager.window_resolution
        self.manager = manager
        self.data = data
        self.rect = rect
        self.container = container

    @abstractmethod
    def _create(self):
        pass

    @abstractmethod
    def destroy(self):
        pass

    @abstractmethod
    def handle_event(self, event: pg.event.Event):
        pass
