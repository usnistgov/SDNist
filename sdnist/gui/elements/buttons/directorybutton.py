from typing import Callable, Optional

import pygame as pg
import pygame_gui as pggui

from pygame_gui.elements.ui_button import UIButton
from pygame_gui.core import ObjectID

from sdnist.gui.elements.buttons.button import UICallbackButton

from sdnist.gui.helper import PathType

# Custom button class
class DirectoryButton(UIButton):
    PAD_X = 0
    def __init__(self,
                 selection_callback: Optional[Callable],
                 expansion_callback: Optional[Callable],
                 expanded: Optional[bool] = True,
                 back_button_color: str = '#000000',
                 *args, **kwargs):
        self.orig_rect = None
        if 'relative_rect' in kwargs:
            # Free space on left for the expand button.
            # For this decrease width of the actual button
            rr = kwargs['relative_rect']
            expand_btn_w = rr.h
            self.orig_rect = kwargs['relative_rect']
            kwargs['relative_rect'] = pg.Rect((rr.x + expand_btn_w + self.PAD_X + 5, rr.y),
                                              (rr.w - expand_btn_w - self.PAD_X - 5, rr.h))

        super().__init__(*args, **kwargs)

        self.selection_callback = selection_callback
        self.expansion_callback = expansion_callback
        self.back_button_color = back_button_color
        self.expanded = expanded
        self.expanded_text = '[-]' if self.expanded else '[+]'
        self.expand_btn_rect = pg.Rect(self.orig_rect.x, self.orig_rect.y,
                                       self.rect.h, self.rect.h)
        self.back_btn_rect = pg.Rect((self.orig_rect.x + self.expand_btn_rect.w, self.orig_rect.y),
                                     (40,
                                      self.orig_rect.h))
        self.expand_btn = None
        self.back_btn = None

        self._create()

    def _create(self):
        self.expand_btn = UICallbackButton(
            callback=self.expansion_callback,
            text=self.expanded_text,
            relative_rect=self.expand_btn_rect,
            manager=self.ui_manager,
            container=self.ui_container,
            anchors={'left': 'left',},
            object_id=ObjectID(class_id='@filetree_button',
                               object_id='#directory_expand_button')
        )
        self.expand_btn.text_horiz_alignment_padding = 0
        self.expand_btn.text_vert_alignment_padding = 0
        self.expand_btn.rebuild()

        obj_id = ObjectID(class_id='@filetree_button',
                          object_id='#directory_back_button')

        self.back_btn = UICallbackButton(
            callback=self.selection_callback,
            text='DIR',
            relative_rect=self.back_btn_rect,
            manager=self.ui_manager,
            container=self.ui_container,
            anchors={'left': 'left',},
            object_id=obj_id
        )
        self.back_btn.colours['normal_bg'] = pg.Color(self.back_button_color)
        self.back_btn.rebuild()

    def kill(self):
        super().kill()
        if self.expand_btn:
            self.expand_btn.kill()
            self.expand_btn = None

        if self.back_btn:
            self.back_btn.kill()
            self.back_btn = None

    def process_event(self, event):
        response = super().process_event(event)
        if event.type == pg.USEREVENT:
            if event.user_type == pggui.UI_BUTTON_PRESSED \
                    and event.ui_element == self:
                if self.selection_callback:
                    self.selection_callback(self)
                if self.is_selected:
                    self.unselect()
                else:
                    self.select()
        return response