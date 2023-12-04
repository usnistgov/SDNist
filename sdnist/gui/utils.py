import pygame as pg
import pygame_gui as pggui
from pygame_gui.elements.ui_button import UIButton
from pathlib import Path

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

def short_path(path: Path, max_front: int = 2, max_back: int = 2):
    parts = list(path.parts)
    if len(parts) > 6:
        part_front = parts[:max_front]
        part_back = parts[-max_back:]
        parts = part_front + ['.../'] + part_back
    return Path(*parts)