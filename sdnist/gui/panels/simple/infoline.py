import os
from pathlib import Path

import pandas as pd
import pygame as pg
import pygame_gui as pggui

from pygame_gui.core import ObjectID
from pygame_gui.elements import UIPanel
from pygame_gui.elements.ui_label import UILabel
from pygame_gui.elements.ui_button import UIButton
from pygame_gui.elements.ui_window import UIWindow
from pygame_gui.elements.ui_text_entry_line import UITextEntryLine
from pygame_gui.elements.ui_horizontal_slider import UIHorizontalSlider

from sdnist.gui.panels.panel import AbstractPanel
from sdnist.gui.elements import \
    UICallbackButton, CustomUITextEntryLine
import sdnist.gui.strs as strs

setting_options = [
    strs.TEAM_NAME,
    strs.MAX_PROCESSES,
    strs.NUMERICAL_METRIC_RESULTS
]


class InfoLinePanel(AbstractPanel):
    def __init__(self,
                 head_text: str = 'Head',
                 tail_text: str = 'Tail',
                 head_size: float = 0.2,
                 *args,
                 **kwargs):
        super().__init__(*args, **kwargs)
        self.head_text = head_text
        self.tail_text = tail_text
        self.head_w = int(self.rect.w * head_size)
        self.tail_w = int(self.rect.w * (1 - head_size))

        self.head_lbl = None
        self.tail_lbl = None
        self._create()

    def _create(self):
        head_lbl_rect = pg.Rect((0, 0),
                           (self.head_w, self.rect.h))
        self.head_lbl = UILabel(
            relative_rect=head_lbl_rect,
            container=self.panel,
            parent_element=self.panel,
            text=self.head_text,
            manager=self.manager,
            anchors={'top': 'top',
                     'left': 'left'},
            object_id=ObjectID(
                class_id='@header_label',
                object_id='#info_head_label'
            )
        )

        tail_lbl_rect = pg.Rect((self.head_w, 0),
                             (self.tail_w, self.rect.h))
        self.tail_lbl = UILabel(
            relative_rect=tail_lbl_rect,
            container=self.panel,
            parent_element=self.panel,
            text=self.tail_text,
            manager=self.manager,
            anchors={'top': 'top',
                     'left': 'left'},
            object_id=ObjectID(
                class_id='@header_label',
                object_id='#info_tail_label'
            )
        )

    def destroy(self):
        super().destroy()

        if self.head_lbl:
            self.head_lbl.kill()
            self.head_lbl = None
        if self.tail_lbl:
            self.tail_lbl.kill()
            self.tail_lbl = None

    def handle_event(self, event: pg.event.Event):
        pass

    def get_elements(self):
        return [self.head_lbl, self.tail_lbl]