import pygame_gui as pggui
import pygame as pg


class CustomUITextEntryLine(pggui.elements.UITextEntryLine):
    def __init__(self, *args, on_click=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.on_click = on_click

    def update(self, time_delta):
        super().update(time_delta)

        # if self.focus and self.on_focus:
        #     self.on_focus()

    def process_event(self, event):
        processed = super().process_event(event)

        if event.type == pg.MOUSEBUTTONDOWN \
                and self.rect.collidepoint(event.pos) \
                and self.on_click:
            self.on_click()

        return processed
