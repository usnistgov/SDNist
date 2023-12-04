from typing import List
import pygame as pg
import pygame_gui as pggui

from pygame_gui.core import ObjectID
from pygame_gui.elements.ui_panel import UIPanel
from pygame_gui.elements.ui_progress_bar import UIProgressBar
from pygame_gui.elements.ui_label import UILabel

from sdnist.gui.panels.panel import AbstractPanel
from sdnist.gui.windows.progress.reports_progress import \
    ReportsProgressPanel
from sdnist.gui.elements import UICallbackButton

from sdnist.gui.colors import main_theme_color
from sdnist.report.helpers import ProgressStatus
from sdnist.version import __version__

class SdnistPanel(AbstractPanel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._create()

    def _create(self):
        logo_panel_rect = pg.Rect(
            -1 * self.rect.w//2 + 130, 0,
            self.rect.width,
            self.rect.height
        )
        self.logo_panel = UIPanel(
            relative_rect=logo_panel_rect,
            manager=self.manager,
            container=self.panel,
            parent_element=self.panel,
            object_id=ObjectID(
                class_id='@window_header_panel',
                object_id='#sdnist_logo_panel'
            )
        )
        self.logo_panel.background_colour = pg.Color(main_theme_color)
        self.logo_panel.rebuild()

        main_lbl_rect = pg.Rect(
            0, 0, 250, self.rect.height
        )
        main_lbl_rect.left = -1 * main_lbl_rect.w - 30
        self.main_lbl = UILabel(
            relative_rect=main_lbl_rect,
            text='SDNIST',
            manager=self.manager,
            container=self.logo_panel,
            parent_element=self.logo_panel,
            anchors={'right': 'right',
                     'centery': 'centery'},
            object_id=ObjectID(
                class_id='@sdnist_label',
                object_id='#sdnist_label'
            )
        )

        version_rect = pg.Rect(
            logo_panel_rect.right + 5,
            self.rect.height//2, 120, self.rect.height // 2
        )

        self.version_panel = UIPanel(
            relative_rect=version_rect,
            manager=self.manager,
            container=self.panel,
            parent_element=self.panel,
            object_id=ObjectID(
                class_id='@window_header_panel',
                object_id='#sdnist_version_panel'
            )
        )
        self.version_panel.background_colour = pg.Color(main_theme_color)
        self.version_panel.rebuild()

        version_lbl_rect = pg.Rect(
            0, 0, version_rect.w, version_rect.h
        )
        self.version_lbl = UILabel(
            relative_rect=version_lbl_rect,
            text=f'v{__version__}',
            manager=self.manager,
            container=self.version_panel,
            parent_element=self.version_panel,
            anchors={'centerx': 'centerx',
                     'centery': 'centery'},
            object_id=ObjectID(
                class_id='@sdnist_label',
                object_id='#sdnist_version_label'
            )
        )


        # self.main_lbl.bg_colour = pg.Color(main_theme_color)
        # self.main_lbl.rebuild()

    def destroy(self):
        super().destroy()

    def handle_event(self, event: pg.event.Event):
        pass

    def rebuild(self):
        super().rebuild()
