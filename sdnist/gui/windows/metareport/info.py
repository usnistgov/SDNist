import pygame as pg
import pygame_gui as pggui

from sdnist.gui.windows.window import AbstractWindow


class MetaReportInfo(AbstractWindow):

    def __init__(self,
                 rect: pg.Rect,
                 manager: pggui.UIManager,
                 directory: str,
                 *args, **kwargs):
        self.title = 'Meta Report Info'
        kwargs['window_display_title'] = self.title
        kwargs['resizable'] = True
        kwargs['draggable'] = False
        super().__init__(rect, manager, *args, **kwargs)

        self.directory = directory

        self._create()

    def _create(self):
        pass

    def destroy(self):
        pass

    def handle_event(self, event: pg.event.Event):
        pass
