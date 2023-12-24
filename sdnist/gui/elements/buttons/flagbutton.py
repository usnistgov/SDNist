from typing import Optional, Callable
from pathlib import Path
import pygame_gui as pggui
import pygame as pg

from pygame_gui.elements.ui_button import UIButton
from pygame_gui.core import ObjectID

from sdnist.gui.elements.buttons.select import UISelectButton

class FlagButton:
    def __init__(self,
                 file_path: Path,
                 callback: Optional[Callable] = None,
                 back_button_color: str = '#000000',
                 **kwargs):
        self.orig_rect = kwargs['relative_rect']
        self.rect = kwargs['relative_rect']
        self.manager = kwargs['manager']
        self.container = kwargs['container']
        self._callback = callback
        self.file_path = file_path
        self.back_button_color = back_button_color
        self.text = kwargs['text']
        self.kwargs = kwargs

        self.back_w = 40
        self.back_btn = None
        self.front_btn = None
        self._create()

    @property
    def callback(self):
        return self._callback

    @callback.setter
    def callback(self, value):
        self._callback = value
        self.back_btn.selection_callback = value
        self.front_btn.selection_callback = value

    def unselect(self):
        if self.back_btn:
            self.back_btn.unselect()
        if self.front_btn:
            self.front_btn.unselect()

    def select(self):
        if self.back_btn:
            self.back_btn.select()
        if self.front_btn:
            self.front_btn.select()

    def disable(self):
        if self.back_btn:
            self.back_btn.disable()
        if self.front_btn:
            self.front_btn.disable()

    def enable(self):
        if self.back_btn:
            self.back_btn.enable()
        if self.front_btn:
            self.front_btn.enable()

    def rebuild(self):
        if self.back_btn:
            self.back_btn.rebuild()
        if self.front_btn:
            self.front_btn.rebuild()

    def _create(self):
        del self.kwargs['text']
        file_suffix = self.file_path.suffix
        file_type = ''
        obj_id = None

        if file_suffix == '.csv':
            file_type = 'CSV'
            self.back_w = 40
        elif file_suffix == '.json':
            file_type = 'JSON'
            self.back_w = 50

        self.back_btn_rect = pg.Rect(
            (self.rect.x, self.rect.y),
            (self.back_w + 15, self.rect.h)
        )
        self.kwargs['relative_rect'] = self.back_btn_rect
        self.back_btn = UISelectButton(
            selection_callback=self._callback,
            text=file_type,
            object_id=ObjectID(
                class_id='@filetree_button',
                object_id='#filetree_button'
            ),
            **self.kwargs,
        )
        self.back_btn.colours['normal_bg'] = pg.Color(self.back_button_color)
        self.back_btn.rebuild()

        self.front_btn_rect = pg.Rect(
            (self.rect.x + self.back_w, self.rect.y),
            (self.rect.w - self.back_w, self.rect.h)
        )
        self.kwargs['relative_rect'] = self.front_btn_rect
        self.front_btn = UISelectButton(
            text=self.text,
            tool_tip_text=self.text,
            object_id=ObjectID(
                class_id='@filetree_button',
                object_id='#filetree_button'
            ),
            **self.kwargs,
        )

    def get_buttons(self):
        return [self.back_btn, self.front_btn]

    def destroy(self):
        self.back_btn.kill()
        self.front_btn.kill()
        self.back_btn = None
        self.front_btn = None

    def kill(self):
        self.destroy()

