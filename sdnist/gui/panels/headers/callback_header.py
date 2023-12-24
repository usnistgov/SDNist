from typing import (
    List, Optional, Callable, Dict)
import pygame as pg

from pygame_gui.core.object_id import ObjectID
from pygame_gui.elements.ui_window import UIWindow
from pygame_gui.elements.ui_label import UILabel

from sdnist.gui.panels.panel import AbstractPanel
from sdnist.gui.panels.headers.header import Header
from sdnist.gui.elements import UICallbackButton


class CallbackHeader(AbstractPanel):
    def __init__(self,
                 callback: Optional[Callable] = None,
                 has_title: bool = False,
                 title: str = '',
                 text: str = "HEADER",
                 text_anchors: Dict[str, str] = None,
                 text_object_id: Optional[ObjectID] = None,
                 *args, **kwargs):
        kwargs['object_id'] = \
            ObjectID(class_id='@header_panel',
                     object_id='#metareport_filter_header')
        super().__init__(*args, **kwargs)
        if not text_anchors:
            text_anchors = {'centery': 'centery',
                            'centerx': 'centerx'}
        self.text_anchors = text_anchors
        if not text_object_id:
            text_object_id = ObjectID(class_id='@header_label',
                                      object_id='#header_label')
        self.text_object_id = text_object_id
        self.callback = callback
        self.has_title = has_title
        self.title_text = title
        self.text = text

        self.title = None
        self.title_rect = pg.Rect(
            (10, 0),
            (self.rect.w * 0.25, self.rect.h * 0.95)
        )

        self.callback_button = None
        self.button_rect = pg.Rect(
            (10, 0),
            (200, self.rect.h * 0.95)
        )
        self._create()

    def _create(self):
        btn_anchors = {
            'centery': 'centery',
            'left': 'left'
        }
        if self.has_title:
            self.title = UILabel(
                relative_rect=self.title_rect,
                container=self.panel,
                parent_element=self.panel,
                text=self.title_text,
                manager=self.manager,
                anchors={
                    'left': 'left',
                    'centery': 'centery'
                },
            )
            btn_anchors = {
                'centery': 'centery',
                'left': 'left'
            }
            self.button_rect = pg.Rect(
                (self.title_rect.w + 10, 0),
                (-1, self.rect.h * 0.95)
            )

        self.callback_button = UICallbackButton(
            callback=self.callback,
            text=self.text,
            relative_rect=self.button_rect,
            manager=self.manager,
            container=self.panel,
            anchors=btn_anchors,
            object_id=ObjectID(
                class_id='@chip_button',
                object_id='#callback_header_button'
            )
        )

    def destroy(self):
        super().destroy()
        if self.callback_button is not None:
            self.callback_button.kill()
            self.callback_button = None

    def handle_event(self, event: pg.event.Event):
        pass

    def get_elements(self):
        return [self.callback_button, self.panel]



