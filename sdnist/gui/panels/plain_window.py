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

