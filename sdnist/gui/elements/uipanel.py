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
                self.callback(hovered=True)
                self.border_width = 1
                self.border_colour = pg.Color('white')
                self.rebuild()
            else:
                self.hovered = False
                self.callback(hovered=False)
                self.border_width = 0
                self.rebuild()

        return processed
