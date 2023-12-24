from typing import List, Callable
import pygame as pg
import pygame_gui as pggui
from pathlib import Path

from pygame_gui.core import ObjectID
from pygame_gui.elements.ui_panel import UIPanel
from pygame_gui.elements.ui_progress_bar import UIProgressBar
from pygame_gui.elements.ui_label import UILabel

from sdnist.gui.panels.panel import AbstractPanel
from sdnist.gui.windows.progress.reports_progress import \
    ReportsProgressPanel
from sdnist.gui.elements import MessageButton

from sdnist.report.helpers.progress_status import (
    ProgressStatus, ProgressType)


class StatusBar(AbstractPanel):
    def __init__(self, path_open_callback: Callable,
                 *args, **kwargs):
        if 'object_id' not in kwargs:
            kwargs['object_id'] = ObjectID(
                class_id='@menubar_panel',
                object_id='#menubar_panel'
            )
        super().__init__(*args, **kwargs)
        self.path_open_callback = path_open_callback
        self.elem_h = self.rect.h * 0.7
        self.right_margin = 30
        self.progress_bar = None
        self.message_btn = None
        self.progress_text = None
        self.reports_progress = None


        self.report_names: List[str] = []

        self._create()

    def _create(self):
        expand_btn_w = 70
        expand_btn_rect = pg.Rect((0, 0),
                                 (expand_btn_w, self.elem_h))
        expand_btn_rect.right = -1 * self.right_margin
        self.message_btn = MessageButton(
            callback=self.toggle_view_reports_progress,
            relative_rect=expand_btn_rect,
            container=self.panel,
            parent_element=self.panel,
            manager=self.manager,
            can_toggle=True,
            text='+',
            anchors={'right': 'right',
                     'centery': 'centery'},
            object_id=ObjectID(
                class_id='@chip_button',
                object_id='#expand_message_button'
            )
        )
        self.create_report_progress()

    def destroy(self):
        super().destroy()
        self.destroy_progress()
        self.destroy_report_progress()

    def handle_event(self, event: pg.event.Event):
        self.reports_progress.handle_event(event)

    def add_progress(self, report_names: List, progress_type: ProgressType):
        self.destroy_progress()

        self.reports_progress.update_messages(report_names)
        self.report_names = report_names
        self.message_btn.update_messages(len(report_names))

        progress_rect = pg.Rect(0, 0,
                                self.rect.w * 0.2,
                                self.elem_h)

        net_width = self.message_btn.rect.w + self.right_margin + 15
        progress_rect.right = -1 * net_width
        self.progress_bar = UIProgressBar(relative_rect=progress_rect,
                                          manager=self.manager,
                                          container=self.panel,
                                          visible=1,
                                          anchors={'right': 'right',
                                                   'centery': 'centery'})

        text_rect = pg.Rect(0, 0,
                            200,
                            self.elem_h)
        net_width += progress_rect.w
        text_rect.right = -1 * net_width
        text = f'{progress_type.name} Done: 0/{len(self.report_names)}'
        self.progress_text = UILabel(relative_rect=text_rect,
                                     text=text,
                                     manager=self.manager,
                                     container=self.panel,
                                     anchors={'right': 'right',
                                              'centery': 'centery'})

    def create_report_progress(self):
        rep_prog_w = self.w * 0.4
        rep_prog_h = self.h * 0.4
        rep_prog_x = self.w - rep_prog_w
        rep_prog_y = self.h - rep_prog_h - self.rect.h

        rep_prog_rect = pg.Rect(rep_prog_x, rep_prog_y,
                                rep_prog_w, rep_prog_h)

        self.reports_progress = ReportsProgressPanel(
            progress_callback=self.progress_callback,
            on_top=True,
            rect=rep_prog_rect,
            manager=self.manager,
            reports_list=self.report_names
        )
        self.reports_progress.window.hide()

    def destroy_progress(self):
        print('destroy progress')
        if self.progress_bar is not None:
            self.progress_bar.kill()
            self.progress_bar = None
        if self.progress_text is not None:
            self.progress_text.kill()
            self.progress_text = None

    def destroy_report_progress(self):
        if self.reports_progress is not None:
            self.reports_progress.destroy()
            self.reports_progress = None

    def update_progress(self, progress: ProgressStatus):
        if self.progress_bar is not None:
            percent = progress.get_progress_percent()
            self.progress_bar.set_current_progress(percent)
        progress_type = progress.get_progress_type().name
        if self.progress_text is not None:
            text = f'{progress_type} Done: {len(progress.get_completed_items())}' \
                          f'/{len(self.report_names)}'
            self.progress_text.set_text(text)

    def toggle_view_reports_progress(self):
        if not (self.reports_progress
                and self.reports_progress.window):
            self.create_report_progress()

        if self.reports_progress.window.visible:
            self.reports_progress.window.hide()
        else:
            self.reports_progress.window.show()

    def progress_callback(self, path: Path, is_open: bool = False):
        if self.reports_progress:
            messages = len(self.reports_progress.messages)
            self.message_btn.update_messages(messages)
        if is_open:
            self.toggle_view_reports_progress()
            self.path_open_callback(path)

