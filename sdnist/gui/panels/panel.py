from typing import Optional
from abc import ABC, abstractmethod
import pygame as pg
import pygame_gui as pggui

from pygame_gui.elements.ui_panel import UIPanel


class AbstractPanel(ABC):
    @abstractmethod
    def __init__(self,
                 rect: pg.Rect,
                 manager: pggui.UIManager,
                 container: Optional[any] = None,
                 data: any = None,
                 *args,
                 **kwargs):
        self.w, self.h = manager.window_resolution
        self.manager = manager
        self.data = data
        self.rect = rect
        self.container = container

        self.panel = UIPanel(
            relative_rect=self.rect,
            manager=self.manager,
            container=self.container,
            *args, **kwargs
        )


    @abstractmethod
    def _create(self):
        pass

    def destroy(self):
        if self.panel:
            self.panel.kill()
            self.panel = None

    def rebuild(self):
        self.panel.rebuild()

    @abstractmethod
    def handle_event(self, event: pg.event.Event):
        pass
