from typing import List
import pygame as pg
import pygame_gui as pggui
from pygame_gui.elements.ui_panel import UIPanel
from pygame_gui.elements.ui_progress_bar import UIProgressBar
from pygame_gui.elements.ui_label import UILabel

from sdnist.gui.panels.panel import AbstractPanel
from sdnist.gui.panels.reports_progress import \
    ReportsProgressPanel
from sdnist.gui.elements import UICallbackButton

from sdnist.report.helpers import ProgressStatus


class StatusBar(AbstractPanel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # height of any element in the
        # status bar
        self.elem_h = self.rect.h * 0.7
        self.progress_bar = None
        self.expand_prog_btn = None
        self.progress_text = None
        self.reports_progress = None

        self.report_names: List[str] = []

        self._create()

    def _create(self):
        pass

    def destroy(self):
        super().destroy()
        self.destroy_progress()

    def handle_event(self, event: pg.event.Event):
        pass

    def add_progress(self, report_names: List):
        # destroy previous progress bar if any
        self.destroy_progress()
        self.report_names = report_names
        # create new progress bar
        net_width = 0
        expand_btn_w = 50
        expand_btn_rect = pg.Rect((0, 0),
                                 (expand_btn_w, self.elem_h))
        expand_btn_rect.right = -1 * net_width
        self.expand_prog_btn = UICallbackButton(
            callback=self.toggle_view_reports_progress,
            relative_rect=expand_btn_rect,
            container=self.panel,
            parent_element=self.panel,
            manager=self.manager,
            can_toggle=True,
            text='+',
            anchors={'right': 'right',
                     'centery': 'centery'})

        progress_rect = pg.Rect(0, 0,
                                self.rect.w * 0.2,
                                self.elem_h)
        net_width += expand_btn_rect.w
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
        text = f'Reports Done: 0/{len(self.report_names)}'
        self.progress_text = UILabel(relative_rect=text_rect,
                                     text=text,
                                     manager=self.manager,
                                     container=self.panel,
                                     anchors={'right': 'right',
                                              'centery': 'centery'})
        rep_prog_w = self.w * 0.4
        rep_prog_h = self.h * 0.4
        rep_prog_x = self.w - rep_prog_w
        rep_prog_y = self.h - rep_prog_h - self.rect.h

        rep_prog_rect = pg.Rect(rep_prog_x, rep_prog_y,
                                rep_prog_w, rep_prog_h)
        self.reports_progress = ReportsProgressPanel(
            rect=rep_prog_rect,
            manager=self.manager,
            reports_list=self.report_names
        )
        self.reports_progress.panel.hide()

    def destroy_progress(self):
        if self.progress_bar is not None:
            self.progress_bar.kill()
            self.progress_bar = None
        if self.progress_text is not None:
            self.progress_text.kill()
            self.progress_text = None
        if self.expand_prog_btn is not None:
            self.expand_prog_btn.kill()
            self.expand_prog_btn = None
        if self.reports_progress is not None:
            self.reports_progress.destroy()
            self.reports_progress = None

    def update_progress(self, progress: ProgressStatus):
        if self.progress_bar is not None:
            percent = progress.get_progress_percent()
            self.progress_bar.set_current_progress(percent)
        if self.progress_text is not None:
            text = f'Reports Done: {len(progress.get_completed_reports())}' \
                          f'/{len(self.report_names)}'
            self.progress_text.set_text(text)

    def toggle_view_reports_progress(self):
        if self.reports_progress.panel.visible:
            self.reports_progress.panel.hide()
            self.expand_prog_btn.set_text('+')
        else:
            self.reports_progress.panel.show()
            self.expand_prog_btn.set_text('-')
