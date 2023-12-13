from typing import List, Callable
from itertools import chain
from functools import partial
import pygame as pg
from pathlib import Path
import pygame_gui as pggui

from pygame_gui.core import ObjectID
from pygame_gui.elements.ui_panel import UIPanel
from pygame_gui.elements.ui_progress_bar import UIProgressBar
from pygame_gui.elements.ui_label import UILabel
from pygame_gui.elements.ui_scrolling_container import \
    UIScrollingContainer

from sdnist.gui.windows.window import AbstractWindow
from sdnist.gui.panels.panel import AbstractPanel
from sdnist.gui.elements import CustomUITextEntryLine
from sdnist.gui.windows.progress.message import MessagePanel

from sdnist.report.helpers import \
    ProgressStatus, ProgressLabels

from sdnist.gui.colors import back_color, report_clr

class ReportsProgressPanel(AbstractWindow):
    def __init__(self,
                 progress_callback: Callable,
                 reports_list: List[str],
                 *args, **kwargs):
        # if 'object_id' not in kwargs:
        #     kwargs['object_id'] = ObjectID(
        #         class_id="@messages_window",
        #         object_id="#messages_window"
        #     )
        super().__init__(*args, **kwargs)
        self.window.background_colour = pg.Color(back_color)
        self.window.shape = 'rounded_rectangle'
        self.window.shape_corner_radius = 20
        self.window.shadow_width = 1
        self.window.rebuild()
        self.base = self.window
        self.reports_list = reports_list
        self.progress_callback = progress_callback
        self.messages = []
        self.messages_idx = dict()
        self.build_messages()

        self.elem_w = int(self.rect.w - 20)
        self.net_height = 0
        self.scroll = None
        self.expand_prog_btn = None
        self.progress_text = None

        self.not_started_reports: List[str] = []
        self.started_reports: List[str] = []
        self.finished_reports: List[str] = []

        self.prog_elems = dict()
        self.message_panels = dict()
        self._create()

    def _create(self):
        scroll_rect = pg.Rect((0, 0),
                              (self.rect.w, self.rect.h))
        self.scroll = UIScrollingContainer(relative_rect=scroll_rect,
                                           manager=self.manager,
                                           container=self.window,
                                           anchors={
                                               'left': 'left',
                                               'right': 'right',
                                               'top': 'top',
                                               'bottom': 'bottom'
                                           },
                                           object_id=ObjectID(
                                               class_id="@messages_vert_scroll",
                                               object_id="#message_vert_scroll"
                                           ))

        self.create_messages()

    def build_messages(self):
        self.messages = [(Path(rep_f), 'NOT STARTED', 0)
                         for rep_f in self.reports_list]

        self.messages_idx = {
            m[0]: i for i, m in enumerate(self.messages)
        }

    def update_messages(self, new_reports: List[str]):
        self.reports_list = new_reports
        self.destroy_messages()
        self.build_messages()
        self.create_messages()

    def create_messages(self):
        pad_x = 10
        pad_y = 10
        subsection_h = 30

        file_panel_h = 3 * subsection_h + 4 * pad_y
        panel_w = self.elem_w - 2 * pad_x
        self.net_height = pad_y
        for i, (rep_f, status, progress) in enumerate(self.messages):
            panel_x = pad_x
            panel_rect = pg.Rect((panel_x, self.net_height),
                                 (panel_w, file_panel_h))
            close_callback = partial(
                self.close_message, rep_f
            )
            open_callback = partial(
                self.open_message,rep_f
            )
            message_panel = MessagePanel(
                open_callback=open_callback,
                close_callback=close_callback,
                path_type='report',
                path=rep_f,
                rect=panel_rect,
                manager=self.manager,
                container=self.scroll,
                subsection_height=subsection_h,
                pad_x=pad_x,
                pad_y=pad_y,
                progress=progress
            )
            message_panel.msg_label.set_text(status)

            self.message_panels[rep_f] = message_panel
            self.prog_elems[rep_f] = message_panel.get_all_elements()
            self.net_height += panel_rect.h + pad_y

        all_elems = set(chain(*self.prog_elems.values()))
        all_elems.add(self.scroll)
        self.scroll.set_scrollable_area_dimensions(
            (self.elem_w, self.net_height)
        )
        if self.scroll.vert_scroll_bar:
            self.scroll.vert_scroll_bar.set_focus_set(all_elems)

    def destroy(self):
        print('DESTROY REPORT PROGRESS')
        super().destroy()
        if self.scroll is not None:
            self.scroll.kill()
            self.scroll = None
            self.prog_elems = dict()
            for m in self.message_panels.values():
                m.destroy()

    def destroy_messages(self):
        for m in self.message_panels.values():
            m.destroy()
        self.message_panels.clear()
        self.messages_idx.clear()
        self.messages_idx = {
            m[0]: i for i, m in enumerate(self.messages)
        }

    def handle_event(self, event: pg.event.Event):
        super().handle_event(event)

    def open_message(self, path: Path):
        msg_idx = self.messages_idx[path]
        del self.messages[msg_idx]
        self.destroy_messages()
        self.create_messages()
        self.progress_callback(path, True)

    def close_message(self, path: Path):
        msg_idx = self.messages_idx[path]
        del self.messages[msg_idx]
        self.destroy_messages()
        self.create_messages()
        self.progress_callback(path)

    def update_progress(self, progress: ProgressStatus):
        updates = progress.get_updates()
        for rep_f, prog_lbl, prog_percent in updates:
            rep_f = Path(rep_f)
            if rep_f not in self.prog_elems.keys():
                continue
            msg_idx = self.messages_idx[rep_f]
            msg_panel = self.message_panels[rep_f]

            if msg_panel.progress_bar:
                msg_panel.progress_bar.set_current_progress(prog_percent)
            prefix = 'Finished' if prog_lbl != ProgressLabels.STARTED \
                else ''
            msg = f'{prefix} {prog_lbl.name}'

            new_msg = (rep_f, msg, prog_percent)
            self.messages[msg_idx] = new_msg
            if msg_panel.msg_label:
                msg_panel.msg_label.set_text(msg)

