import pygame as pg
import pygame_gui as pggui

from sdnist.gui.panels.panel import AbstractPanel


class TargetDataPanel(AbstractPanel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._create()

    def _create(self):
        pass

    def destroy(self):
        pass

    def handle_event(self, event: pg.event.Event):
        pass
