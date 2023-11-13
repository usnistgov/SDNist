import pygame as pg
import pygame_gui as pggui
from pygame_gui.elements.ui_button import UIButton


def get_text_width(text: str, manager: pggui.UIManager) -> int:
    rect = pg.Rect(0, 0, -1, 40)
    btn = UIButton(relative_rect=rect,
                   text=text,
                   manager=manager,
                   visible=0)
    w = btn.rect.w
    btn.kill()
    btn = None
    return w
