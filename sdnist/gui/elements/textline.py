import pygame_gui as pggui
import pygame as pg


class CustomUITextEntryLine(pggui.elements.UITextEntryLine):
    def __init__(self, *args, on_click=None, on_change=None,
                 editable=True,
                 text_end_visible=False,
                 **kwargs):
        super().__init__(*args, **kwargs)
        self.on_click = on_click
        self.on_change = on_change
        self.editable = editable
        self.text_end_visible = text_end_visible
        if self.text_end_visible:
            self.set_text_end_visible()

    def update(self, time_delta):
        super().update(time_delta)

    def process_event(self, event):
        processed = False
        if event.type == pg.MOUSEBUTTONDOWN \
                and self.rect.collidepoint(event.pos) \
                and self.on_click:
            processed = super().process_event(event)
            if self.on_click:
                self.on_click()
        elif event.type in [pg.KEYDOWN, pg.KEYUP, pg.TEXTINPUT] and \
                self.editable:
            processed = super().process_event(event)
            if self.on_change:
                self.on_change()
        elif event.type in [pg.MOUSEBUTTONDOWN,
                            pg.MOUSEMOTION, pg.MOUSEBUTTONUP]:
            processed = super().process_event(event)
        return processed

    def set_text(self, text: str):
        if self.text_end_visible:
            self.set_text_end_visible()
        super().set_text(text)

    def set_text_end_visible(self):
        self.cursor_has_moved_recently = True
        super().set_text(str(self.get_text()))


