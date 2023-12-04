from typing import Callable
import pygame_gui as pggui
import pygame as pg

from pygame_gui.elements.ui_panel import UIPanel


class CustomUIPanel(UIPanel):
    def __init__(self, callback: Callable,  *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.hovered = False
        self.callback = callback
        self.last_mouse_pos = (-100, -100)

    def process_event(self, event):
        processed = super().process_event(event)

        if event.type in [pg.MOUSEMOTION]:
            self.last_mouse_pos = event.pos
            if self.rect.collidepoint(event.pos):
                self.hovered = True
                self.callback(self.hovered)
            else:
                self.hovered = False
                self.callback(self.hovered)

        return processed

    def set_hovered(self, valid: bool):
        if not valid:
            color = pg.Color('#781f1f')
        else:
            color = pg.Color('#206327')
        self.hovered = True
        self.background_colour = color
        self.rebuild()

    def unset_hovered(self):
        self.hovered = False
        self.background_colour = pg.Color('#2b3136')
        self.rebuild()
