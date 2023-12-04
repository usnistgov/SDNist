from typing import Callable
import pygame as pg
import pygame_gui as pggui
from pathlib import Path
import webbrowser

from sdnist.gui.windows.window import AbstractWindow

from sdnist.gui.panels.simple.banner import BannerPanel
from sdnist.gui.panels.simple.infoline import InfoLinePanel
from sdnist.gui.panels.headers import CallbackHeader
from sdnist.gui.panels.headers import WindowHeader
import sdnist.gui.utils as u
from sdnist.gui.constants import window_header_h

class ReportInfo(AbstractWindow):
    def __init__(self,
                 delete_callback: Callable,
                 report_path: str,
                 rect: pg.Rect,
                 manager: pggui.UIManager,
                 *args,
                 **kwargs):

        self.title = 'SDNIST Data Evaluation Report'
        kwargs['window_display_title'] = self.title
        kwargs['resizable'] = True
        kwargs['draggable'] = False
        super().__init__(rect, manager, *args, **kwargs)

        self.delete_callback = delete_callback
        self.report_path = report_path

        self.header_h = window_header_h

        self.header = None
        self.path_banner = None
        self._create()

    def _create(self):
        short_path = u.short_path(Path(self.report_path))
        option_h = 50
        header_rect = pg.Rect(0, 0, self.rect.w, self.header_h)
        self.header = WindowHeader(
            title=self.title,
            enable_delete_button=True,
            delete_callback=self.delete_path,
            delete_button_text='Delete Report',
            delete_button_width=120,
            rect=header_rect,
            manager=self.manager,
            container=self.window
        )

        open_report_rect = pg.Rect(
            0, self.header_h,
            self.rect.w, option_h
        )

        self.open_rect = CallbackHeader(
            callback=self.open_report,
            rect=open_report_rect,
            manager=self.manager,
            container=self.window,
            text='Open Report',
        )


    def handle_event(self, event: pg.event.Event):
        pass

    def open_report(self):
        html_path = Path(self.report_path, 'report.html')
        out_path = f'file://{html_path}'
        webbrowser.open(out_path, new=True)

    def delete_path(self):
        self.delete_callback(self.report_path)



