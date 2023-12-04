from typing import (
    List, Optional, Callable, Dict)
import pygame as pg

from pygame_gui.core.object_id import ObjectID
from pygame_gui.elements.ui_window import UIWindow
from pygame_gui.elements.ui_label import UILabel

from sdnist.gui.panels.panel import AbstractPanel
from sdnist.gui.panels.headers.header import Header
from sdnist.gui.elements import UICallbackButton


class WindowHeader(AbstractPanel):
    def __init__(self,
                 title: str = '',
                 enable_delete_button: bool = False,
                 delete_callback: Optional[Callable] = None,
                 delete_button_text: str = 'Delete',
                 delete_button_width: int = 100,
                 other_buttons: List[str] = None,
                 other_buttons_callbacks: List[Callable] = None,
                 text_anchors: Dict[str, str] = None,
                 text_object_id: Optional[ObjectID] = None,
                 header_at_center: bool = False,
                 *args, **kwargs):
        if "object_id" not in kwargs:
            kwargs['object_id'] = \
                ObjectID(class_id='@window_header_panel',
                         object_id='#window_header_panel')
        super().__init__(*args, **kwargs)
        if not text_anchors:
            text_anchors = {'centery': 'centery',
                            'left': 'left'}
        self.text_anchors = text_anchors
        if not text_object_id:
            text_object_id = ObjectID(class_id='@header_label',
                                      object_id='#header_label')
        self.text_object_id = text_object_id
        self.enable_delete_button = enable_delete_button
        self.delete_callback = delete_callback
        self.delete_button_text = delete_button_text
        self.delete_button_width = delete_button_width
        self.other_buttons = other_buttons
        self.other_buttons_callbacks = other_buttons_callbacks

        self.title_text = title

        self.title = None
        self.header_at_center = header_at_center
        self.title_w = self.rect.w * 0.50
        self.title_text_align = 'left'
        if self.header_at_center:
            self.title_rect = pg.Rect(
                ((self.rect.w - self.title_w) // 2, 0),
                (self.title_w, self.rect.h)
            )
            self.title_text_align = 'center'
        else:
            self.title_rect = pg.Rect(
                (0, 0),
                (self.rect.w * 0.50, self.rect.h)
            )

        self.delete_button = None
        self.other_buttons = dict()

        self.button_rect = None
        self._create()

    def _create(self):

        self.title = UILabel(
            relative_rect=self.title_rect,
            container=self.panel,
            parent_element=self.panel,
            text=self.title_text,
            manager=self.manager,
            anchors=self.text_anchors,
            object_id=ObjectID(
                class_id='@header_label',
                object_id="#window_header_label"
            )
        )
        self.title.text_horiz_alignment = self.title_text_align
        self.title.rebuild()
        btn_anchors = {
            'centery': 'centery',
            'left': 'left'
        }
        self.button_rect = pg.Rect(
            (self.rect.w - self.delete_button_width - 15, 0),
            (self.delete_button_width, self.rect.h)
        )

        if self.enable_delete_button:
            self.delete_btn = UICallbackButton(
                callback=self.delete_callback,
                text=self.delete_button_text,
                relative_rect=self.button_rect,
                manager=self.manager,
                container=self.panel,
                parent_element=self.panel,
                anchors=btn_anchors,
                object_id=ObjectID(
                    class_id='@chip_button',
                    object_id='#delete_window_header_button'
                )
            )
            # self.delete_btn.rect.left = -1 * self.title.rect.w
            # self.delete_btn.rebuild()


    def destroy(self):
        super().destroy()
        if self.delete_button is not None:
            self.delete_button.kill()
            self.delete_button = None

    def handle_event(self, event: pg.event.Event):
        pass

    def get_elements(self):
        return [self.title, self.delete_button, self.panel]



