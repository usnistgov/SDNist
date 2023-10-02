import pygame_gui as pggui
import pygame as pg

from pygame_gui.elements.ui_text_entry_box import UITextEntryBox


class CustomTextEntryBox(UITextEntryBox):
    def __init__(self, text_changed_callback, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.text_changed_callback = text_changed_callback
        self.previous_text = self.get_text()

    def update(self, time_delta):
        super().update(time_delta)
        current_text = self.get_text()
        if current_text != self.previous_text:
            self.text_changed_callback()
            self.previous_text = current_text
