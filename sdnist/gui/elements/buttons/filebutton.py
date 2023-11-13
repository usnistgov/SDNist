import pygame as pg
import pygame_gui as pggui

from pygame_gui.elements.ui_button import UIButton

from sdnist.gui.elements.buttons.button \
    import UICallbackButton


# Custom button class
class FileButton(UICallbackButton):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.orig_rect = self.rect.copy()



