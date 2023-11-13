from typing import List
from itertools import chain
import pygame as pg
import pygame_gui as pggui
from pygame_gui.elements.ui_panel import UIPanel
from pygame_gui.elements.ui_progress_bar import UIProgressBar
from pygame_gui.elements.ui_label import UILabel
from pygame_gui.elements.ui_scrolling_container import \
    UIScrollingContainer

from sdnist.gui.panels.panel import AbstractPanel
from sdnist.gui.elements import CustomUITextEntryLine

from sdnist.report.helpers import \
    ProgressStatus, ProgressLabels


class ReportsProgressPanel(AbstractPanel):
    def __init__(self, reports_list: List[str], *args, **kwargs):
        kwargs['starting_height'] = 1
        super().__init__(*args, **kwargs)
        self.reports_list = reports_list

        self.scroll = None
        self.expand_prog_btn = None
        self.progress_text = None

        self.not_started_reports: List[str] = []
        self.started_reports: List[str] = []
        self.finished_reports: List[str] = []

        self.prog_elems = dict()
        self._create()

    def _create(self):
        scroll_rect = pg.Rect((0, 0),
                              (self.rect.w, self.rect.h))
        self.scroll = UIScrollingContainer(relative_rect=scroll_rect,
                                           manager=self.manager,
                                           starting_height=2,
                                           container=self.panel,
                                           anchors={'left': 'left',
                                                    'top': 'top'})

        pad_x = 10
        pad_y = 10
        text_height = 30
        progress_height = 30
        msg_height = 30

        file_panel_h = text_height + progress_height \
            + msg_height + 4 * pad_y
        panel_w = self.rect.w - 2 * pad_x
        lbl_w = panel_w - 2 * pad_x
        net_height = 0
        for i, rep_f in enumerate(self.reports_list):
            panel_x = pad_x
            panel_y = pad_y + i * file_panel_h
            panel_rect = pg.Rect((panel_x, panel_y),
                                 (panel_w, file_panel_h))

            panel = UIPanel(relative_rect=panel_rect,
                            manager=self.manager,
                            container=self.scroll,
                            starting_height=3)

            text_rect = pg.Rect((pad_x, pad_y),
                                (lbl_w, text_height))
            text_file = CustomUITextEntryLine(
                relative_rect=text_rect,
                initial_text=rep_f,
                manager=self.manager,
                container=panel,
                anchors={'left': 'left',
                         'top': 'top'},
                text_end_visible=True,
                editable=False
            )

            progress_y = text_rect.y + text_rect.h + pad_y

            progress_rect = pg.Rect((pad_x, progress_y),
                                    (lbl_w, progress_height))

            progress_bar = UIProgressBar(relative_rect=progress_rect,
                                         manager=self.manager,
                                         container=panel,
                                         visible=1,
                                         anchors={'left': 'left',
                                                  'top': 'top'})

            msg_y = progress_y + progress_height + pad_y

            msg_rect = pg.Rect((pad_x, msg_y),
                               (lbl_w, msg_height))
            msg_text = f'NOT STARTED'
            msg_label = UILabel(relative_rect=msg_rect,
                                text=msg_text,
                                manager=self.manager,
                                container=panel,
                                anchors={'left': 'left',
                                         'top': 'top'})
            net_height += msg_rect.y + msg_rect.h + pad_y

            self.prog_elems[rep_f] = (panel, text_file, progress_bar, msg_label)

        all_elems = set(chain(*self.prog_elems.values()))
        self.scroll.set_scrollable_area_dimensions(
            (scroll_rect.w, net_height)
        )
        if self.scroll.vert_scroll_bar:
            self.scroll.vert_scroll_bar.set_focus_set(all_elems)

    def destroy(self):
        if self.scroll is not None:
            self.panel.kill()
            self.scroll.kill()
            self.panel = None
            self.scroll = None
            self.prog_elems = dict()

    def handle_event(self, event: pg.event.Event):
        pass

    def update_progress(self, progress: ProgressStatus):
        updates = progress.get_updates()
        for rep_f, prog_lbl, prog_percent in updates:
            if rep_f not in self.prog_elems.keys():
                continue
            _, _, progress_bar, msg_label = self.prog_elems[rep_f]
            progress_bar.set_current_progress(prog_percent)
            prefix = 'Finished' if prog_lbl != ProgressLabels.STARTED \
                else ''
            msg_label.set_text(f'{prefix} {prog_lbl.name}')
