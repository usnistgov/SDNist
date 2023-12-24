from pathlib import Path
import pandas as pd
import pygame as pg
import pygame_gui as pggui

from pygame_gui.core import ObjectID

from pygame_gui.elements.ui_panel import UIPanel
from sdnist.gui.windows.window import AbstractWindow
from sdnist.gui.panels.buttonsgroup import ButtonsGroupPanel

from sdnist.gui.panels.dftable import DFTable
from sdnist.gui.panels.simple.banner import BannerPanel
from sdnist.gui.panels.headers import WindowHeader
from sdnist.gui.windows.csv.deidinfo import DeidInfoPanel

from sdnist.gui.panels.dftable.filterdata import FilterData
from sdnist.gui.strs import *
import sdnist.gui.utils as u
from sdnist.gui.constants import window_header_h

class DeidCSV(AbstractWindow):
    def __init__(self,
                 csv_path: str,
                 title: str = 'Deid CSV File',
                 *args,
                 **kwargs):

        self.title = title
        kwargs['window_display_title'] = self.title
        kwargs['resizable'] = True
        kwargs['draggable'] = False
        super().__init__(*args, **kwargs)

        self.csv_path = csv_path
        self.header_h = window_header_h
        self.data = pd.read_csv(self.csv_path)
        self.features = self.data.columns.to_list()

        self.filter_data = FilterData(data=self.data,
                                      path=Path(self.csv_path))
        self.options_panel_rect = pg.Rect(
            0, self.header_h, self.rect.width, 30
        )
        view_panel_y = self.header_h + self.options_panel_rect.height
        view_panel_h = self.rect.height - view_panel_y
        self.view_panel_rect = pg.Rect(
            0, view_panel_y,
            self.rect.width, view_panel_h
        )

        self.header = None
        self.options = None
        self.info_panel = None
        self.data_panel = None

        self._create()

    def _create(self):

        header_rect = pg.Rect(0, 0, self.rect.w, self.header_h)
        self.header = WindowHeader(
            title=self.title,
            rect=header_rect,
            manager=self.manager,
            container=self.window,
        )

        self.options = ButtonsGroupPanel(
            on_select_callback=self.on_select_btn_grp,
            rect=self.options_panel_rect,
            manager=self.manager,
            container=self.window,
            object_id=ObjectID(class_id='@header_panel',
                               object_id='#button_group_panel')
        )
        self.options.on_select_button(INFORMATION)

    def on_select_btn_grp(self, btn_name: str):
        if btn_name == INFORMATION:
            if self.data_panel:
                self.data_panel.destroy()
                self.data_panel = None
            self.info_panel = DeidInfoPanel(
                file_path=Path(self.csv_path),
                data=self.data,
                rect=self.view_panel_rect,
                manager=self.manager,
                container=self.window,
            )
        elif btn_name == DATA:
            if self.info_panel:
                self.info_panel.destroy()
                self.info_panel = None
            self.data_panel = DFTable(
                rect=self.view_panel_rect,
                manager=self.manager,
                filter_data=self.filter_data,
                container=self.window
            )

    def handle_event(self, event: pg.event.Event):
        pass



