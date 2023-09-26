import pygame_gui as pggui
import pygame as pg

from pygame_gui.elements.ui_button import UIButton


class UICallbackButton(UIButton):
    def __init__(self, callback, can_toggle: bool = False,
                 *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.callback = callback
        self.can_toggle = can_toggle

    def process_event(self, event):
        response = super().process_event(event)
        if event.type == pg.USEREVENT:
            if event.user_type == pggui.UI_BUTTON_PRESSED \
                    and event.ui_element == self:
                self.callback()
                if self.can_toggle:
                    if self.is_selected:
                        self.unselect()
                    else:
                        self.select()
        return response
