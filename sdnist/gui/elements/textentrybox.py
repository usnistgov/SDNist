from typing import Optional, Callable
import pygame_gui as pggui
import pygame as pg

from pygame_gui.core import ObjectID
from pygame_gui.elements.ui_text_entry_box import UITextEntryBox


class CustomTextEntryBox(UITextEntryBox):
    def __init__(self,
                 text_changed_callback: Optional[Callable] = None,
                 editable: bool = True,
                 *args, **kwargs):
        if 'object_id' not in kwargs:
            kwargs['object_id'] = ObjectID(
                class_id="@custom_text_entry_box",
                object_id="#custom_text_entry_box"
            )
        super().__init__(*args, **kwargs)
        self.text_changed_callback = text_changed_callback
        self.editable = editable
        self.previous_text = self.get_text()

    def update(self, time_delta):
        super().update(time_delta)
        current_text = self.get_text()
        if current_text != self.previous_text:
            if self.text_changed_callback:
                self.text_changed_callback()
            self.previous_text = current_text

    def process_event(self, event: pg.Event) -> bool:
        processed = False
        if event.type in [pg.KEYDOWN, pg.KEYUP, pg.TEXTINPUT] and \
                self.editable:
            processed = super().process_event(event)
            if self.text_changed_callback:
                self.text_changed_callback()
        elif event.type in [pg.MOUSEBUTTONDOWN,
                            pg.MOUSEMOTION, pg.MOUSEBUTTONUP]:
            processed = super().process_event(event)

        return processed

