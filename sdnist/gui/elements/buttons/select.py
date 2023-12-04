from typing import Optional, Callable

import pygame_gui as pggui
import pygame as pg

from pygame_gui.elements.ui_button import UIButton


class UISelectButton(UIButton):
    def __init__(self,
                 selection_callback: Optional[Callable] = None,
                 can_toggle: Optional[bool] = False,
                 *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.selection_callback = selection_callback
        self.can_toggle = can_toggle


    def process_event(self, event):
        response = super().process_event(event)
        if event.type == pg.USEREVENT:
            if event.user_type == pggui.UI_BUTTON_PRESSED \
                    and event.ui_element == self:
                if self.selection_callback:
                    self.selection_callback()
                if self.is_selected:
                    self.unselect()
                else:
                    self.select()
        return response
