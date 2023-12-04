import os
from pathlib import Path
from typing import List

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


class PartInfoLinePanel(AbstractPanel):
    def __init__(self,
                 parts: List[str],
                 part1_size: float = 0.25,
                 part2_size: float = 0.25,
                 colors: List[str] = None,
                 parts_align: List[str] = None,
                 bold_head: bool = False,
                 *args,
                 **kwargs):
        super().__init__(*args, **kwargs)
        self.parts_text = parts
        self.total_parts = len(self.parts_text)
        if (self.total_parts == 2 and part1_size == 0.25 and
            part2_size == 0.25):
            part1_size = 0.5
            part2_size = 0.5
        self.part1_w = int(self.rect.w * part1_size)
        self.part2_w = int(self.rect.w * part2_size)
        self.colors = colors
        self.other_parts_w = (self.rect.w - self.part1_w - self.part2_w)
        self.parts_align = parts_align
        self.bold_head = bold_head
        if self.parts_align is None:
            self.parts_align = ['left'] * self.total_parts

        if self.total_parts == 2:
            self.other_parts_w = 0
        else:
            self.other_parts_w = self.other_parts_w \
                                     // (len(self.parts_text) - 2)

        self.parts_lbls = dict()
        self._create()

    def _create(self):
        if self.colors is None:
            colors = ["#0e4f3f", "#14633c", "#0e4f3f", "#14633c", "#0e4f3f", "#14633c",
                      "#0e4f3f", "#14633c", "#0e4f3f", "#14633c"]
        else:
            colors = self.colors
        parts = [('part1', self.parts_text[0], self.part1_w, colors[0], self.parts_align[0]),
                 ('part2', self.parts_text[1], self.part2_w, colors[1], self.parts_align[1])]
        parts += [('part' + str(i), p, self.other_parts_w, colors[i+2], self.parts_align[i+2])
                    for i, p in enumerate(self.parts_text[2:])]
        start_w = 0

        for i, p in enumerate(parts):
            name = p[0]
            text = p[1]
            w = p[2]
            color = p[3]
            p_rect = pg.Rect((start_w, 0),
                             (w, self.rect.h))
            align = p[4]

            if i == 0 and self.bold_head:
                obj_id = "#info_part_label_bold"
            else:
                obj_id = "#info_part_label"
            p_lbl = UILabel(
                relative_rect=p_rect,
                container=self.panel,
                parent_element=self.panel,
                text=text,
                manager=self.manager,
                anchors={'top': 'top',
                         'left': 'left'},
                object_id=ObjectID(
                    class_id='@header_label',
                    object_id=obj_id)
            )

            p_lbl.bg_colour = pg.Color(color)
            p_lbl.rebuild()
            p_lbl.text_horiz_alignment = align
            self.parts_lbls[text] = p_lbl
            start_w += w

    def destroy(self):
        super().destroy()
        for p in self.parts_lbls.values():
            p.kill()
        self.parts_lbls = dict()

    def update_parts(self, parts: List[str], colors: List[str], text_colors: List[str]):
        for i, p in enumerate(self.parts_lbls.values()):
            p.set_text(parts[i])
            p.bg_colour = pg.Color(colors[i])
            p.text_colour = pg.Color(text_colors[i])
            p.rebuild()

    def handle_event(self, event: pg.event.Event):
        pass

    def rebuild(self):
        self.panel.rect.w = self.rect.w
        super().rebuild()
        last_p = list(self.parts_lbls.values())[-1]
        last_p.rect.w = self.rect.w - last_p.rect.x
        last_p.rebuild()