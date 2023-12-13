from typing import Callable
import pygame as pg
import pygame_gui as pggui

from sdnist.gui.windows.window import AbstractWindow
from sdnist.gui.panels.headers import WindowHeader

from sdnist.gui.constants import window_header_h

class ArchiveInfo(AbstractWindow):
    def __init__(self,
                 delete_callback: Callable,
                 archive_directory: str,
                 rect: pg.Rect,
                 manager: pggui.UIManager,
                 *args,
                 **kwargs):

        self.title = 'SDNIST Evaluation Archive'
        kwargs['window_display_title'] = self.title
        kwargs['resizable'] = True
        kwargs['draggable'] = False
        super().__init__(rect, manager, *args, **kwargs)

        self.delete_callback = delete_callback
        self.header_h = window_header_h
        self.archive_directory = archive_directory

        self.header = None
        self._create()

    def _create(self):
        option_h = 50
        header_rect = pg.Rect(0, 0, self.rect.w, self.header_h)
        self.header = WindowHeader(
            title=self.title,
            enable_delete_button=True,
            delete_callback=self.delete_path,
            delete_button_text='Delete Archive',
            delete_button_width=160,
            rect=header_rect,
            manager=self.manager,
            container=self.window
        )

    def handle_event(self, event: pg.event.Event):
        pass

    def delete_path(self):
        self.delete_callback(self.archive_directory)


