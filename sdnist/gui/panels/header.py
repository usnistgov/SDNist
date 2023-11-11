from typing import Dict, Optional
import pygame as pg
import pygame_gui as pggui

from pygame_gui.core.object_id import ObjectID
from pygame_gui.elements.ui_panel import UIPanel
from pygame_gui.elements.ui_label import UILabel

from sdnist.gui.panels.panel import AbstractPanel


class Header(AbstractPanel):
    def __init__(self,
                 text: str = "HEADER",
                 text_anchors: Dict[str, str] = None,
                 text_object_id: Optional[ObjectID] = None,
                 *args, **kwargs):
        kwargs['starting_height'] = 0
        super().__init__(*args, **kwargs)
        if not text_anchors:
            text_anchors = {'centery': 'centery',
                            'centerx': 'centerx'}
        self.text_anchors = text_anchors
        if not text_object_id:
            text_object_id = ObjectID(class_id='@header_label',
                                      object_id='#header_label')
        self.text_object_id = text_object_id
        self.title_x = 10
        self.header_text = text
        self._create()

    def _create(self):
        # Header Text using pygame_gui
        self.header_text = UILabel(relative_rect=pg.Rect((self.title_x, 0),
                                                         (-1, 50)),
                                   container=self.panel,
                                   parent_element=self.panel,
                                   text=self.header_text,
                                   manager=self.manager,
                                   anchors=self.text_anchors,
                                   object_id=self.text_object_id)

    def destroy(self):
        super().destroy()
        if self.header_text is not None:
            self.header_text = None

    def handle_event(self, event: pg.event.Event):
        pass
