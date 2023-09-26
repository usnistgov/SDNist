import pygame_gui as pggui
import pygame as pg

from pygame_gui.elements.ui_selection_list import UISelectionList


class CallbackSelectionList(UISelectionList):
    def __init__(self, callback, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.callback = callback

    def process_event(self, event):
        # Let the base class handle its usual event processing
        response = super().process_event(event)

        # If this event was a new selection, call our callback
        if event.type == pg.USEREVENT and event.ui_element == self:
            if event.user_type == pggui.UI_SELECTION_LIST_NEW_SELECTION \
               or event.user_type == pggui.UI_SELECTION_LIST_DROPPED_SELECTION:
                if self.allow_multi_select:
                    self.callback(self.get_multi_selection())
                else:
                    self.callback(self.get_single_selection())

        return response
