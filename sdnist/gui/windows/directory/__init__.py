from typing import Dict
import pygame as pg
import pygame_gui as pggui
from pathlib import Path

from sdnist.gui.windows.window import AbstractWindow
from sdnist.gui.panels.simple.banner import BannerPanel
from sdnist.gui.panels.simple.infoline import InfoLinePanel
from sdnist.gui.panels.headers import WindowHeader

from sdnist.gui.constants import (
    REPORT_DIR_PREFIX,
    METAREPORT_DIR_PREFIX,
    ARCHIVE_DIR_PREFIX
)
import sdnist.gui.utils as u
from sdnist.gui.strs import *
from sdnist.gui.constants import window_header_h

class DirectoryInfo(AbstractWindow):
    def __init__(self,
                 directory_path: str,
                 counts: Dict[str, int],
                 rect: pg.Rect,
                 manager: pggui.UIManager,
                 *args,
                 **kwargs):

        self.title = 'Directory Summary'
        kwargs['window_display_title'] = self.title
        kwargs['resizable'] = True
        kwargs['draggable'] = False
        super().__init__(rect, manager, *args, **kwargs)

        self.directory_path = directory_path
        self.header_h = window_header_h
        self.deid_csv_files = counts[DEID_CSV_FILES]
        self.metadata_files = counts[META_DATA_FILES]
        self.archive_files = counts[ARCHIVE_FILES]
        self.reports = counts[REPORTS]
        self.metareports = counts[METAREPORTS]
        self.index_files = counts[INDEX_FILES]

        self.header = None
        self._create()

    def _create(self):
        option_h = 30
        header_rect = pg.Rect(0, 0, self.w, self.header_h)
        self.header = WindowHeader(
            title=self.title,
            rect=header_rect,
            manager=self.manager,
            container=self.window
        )
        counts_data = [
            (DEID_CSV_FILES, self.deid_csv_files),
            (META_DATA_FILES, self.metadata_files),
            (REPORTS, self.reports),
            (METAREPORTS, self.metareports),
            (INDEX_FILES, self.index_files),
            (ARCHIVE_FILES, self.archive_files),
        ]
        start_y = self.header_h
        for c_data in counts_data:
            head_text, tail_text = c_data[0], str(c_data[1])
            line_rect = pg.Rect((0, start_y),
                                (self.rect.w, option_h))
            line_panel = InfoLinePanel(
                head_text=head_text,
                tail_text=tail_text,
                rect=line_rect,
                container=self.window,
                parent_element=self.window,
                manager=self.manager,
            )
            start_y += option_h


    def handle_event(self, event: pg.event.Event):
        pass



