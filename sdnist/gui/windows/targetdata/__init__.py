from typing import Optional

import pandas as pd
import pygame as pg
import pygame_gui as pggui
from pathlib import Path

from pygame_gui.core import ObjectID
from sdnist.gui.windows.window import AbstractWindow
from sdnist.report.dataset import TargetLoader

from sdnist.gui.windows.window import AbstractWindow
from sdnist.gui.panels.buttonsgroup import ButtonsGroupPanel
from sdnist.gui.windows.targetdata.targetinfo import (
    TargetInfoPanel)

from sdnist.gui.panels.dftable import DFTable
from sdnist.gui.panels.simple.banner import BannerPanel
from sdnist.gui.windows.csv.deidinfo import DeidInfoPanel
from sdnist.gui.panels.headers import WindowHeader

from sdnist.gui.panels.dftable.filterdata import FilterData
from sdnist.gui.strs import *
import sdnist.gui.utils as u
from sdnist.gui.constants import window_header_h


class TargetDataWindow(AbstractWindow):
    def __init__(self,
                 target: TargetLoader,
                 rect: pg.Rect,
                 manager: pggui.UIManager,
                 *args,
                 **kwargs):

        self.title = 'Target Data'
        kwargs['window_display_title'] = self.title
        kwargs['resizable'] = True
        kwargs['draggable'] = False
        super().__init__(rect, manager, *args, **kwargs)

        self.target = target
        self.header_h = window_header_h
        self.header_rect = pg.Rect(0, 0,
                                   self.rect.w, self.header_h)

        self.options_panel_rect = pg.Rect(
            0, self.header_rect.bottom,
            self.rect.width, 30
        )
        self.banner_rect = pg.Rect(
            0, self.options_panel_rect.bottom,
            self.rect.width, 30
        )
        view_panel_y = self.banner_rect.bottom
        view_panel_h = self.rect.height - view_panel_y
        self.view_panel_rect = pg.Rect(
            0, view_panel_y,
            self.rect.width, view_panel_h
        )

        self.options = None
        self.info_panel = None
        self.data_panel = None

        self.selected_target_path: Optional[Path] = None
        self.selected_view = None
        self._create()

    def _create(self):
        self.header = WindowHeader(
            title=self.title,
            rect=self.header_rect,
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
        short_path = u.short_path(Path(self.target.root))
        self.path_banner = BannerPanel(
            rect=self.banner_rect,
            manager=self.manager,
            container=self.window,
            head_text="Target Data Root:",
            tail_text=str(short_path)
        )

    def on_select_btn_grp(self, btn_name: str):
        if self.selected_view == btn_name:
            return
        self.selected_view = btn_name
        if btn_name == INFORMATION:
            if self.data_panel:
                self.data_panel.destroy()
                self.data_panel = None
            self.info_panel = TargetInfoPanel(
                target_loader=self.target,
                select_target_callback=self.on_select_target_data,
                rect=self.view_panel_rect,
                manager=self.manager,
                container=self.window,
            )
        elif btn_name == DATA:
            if self.info_panel:
                self.info_panel.destroy()
                self.info_panel = None
            if self.selected_target_path:
                data = pd.read_csv(self.selected_target_path)
                self.data_panel = DFTable(
                    rect=self.view_panel_rect,
                    manager=self.manager,
                    container=self.window,
                    filter_data=FilterData(data=data, path=self.selected_target_path)
                )

    def on_select_target_data(self, target_path: Path):
        self.selected_target_path = target_path
        self.on_select_btn_grp(DATA)
        if self.options:
            self.options.select_button(DATA)

    def handle_event(self, event: pg.event.Event):
        pass




