import pygame as pg
import pygame_gui as pggui
import json

from pygame_gui.core import ObjectID
from pygame_gui.elements.ui_window import UIWindow

from sdnist.gui.panels.sdnist import SdnistPanel
from sdnist.gui.pages import Page
from sdnist.gui.pages.page import AbstractPage
from sdnist.gui.panels import SettingsPanel
from sdnist.gui.panels.headers import WindowHeader
from sdnist.gui.pages.home.choose_team import \
    ChooseTeamPanel
from sdnist.gui.panels import \
    LoadDeidData
from sdnist.gui.elements import UICallbackButton
from sdnist.gui.constants import window_header_h

from sdnist.gui.config import \
    load_cfg, save_cfg

import sdnist.gui.strs as strs
from sdnist.gui.colors import (
    main_theme_color, back_color)


class Home(AbstractPage):
    def __init__(self,
                 manager: pggui.UIManager,
                 enable: bool = True):
        super().__init__(manager)
        self.enabled = enable
        self.load_button = None

        self.manager = manager
        self.header_h = window_header_h
        self.pad_y = 30
        self.sdnist_h = 100

        self.window = None
        self.header = None
        self.file_dialog = None
        self.picked_path = None

        self.w_w, self.w_h = int(self.w * 0.8), int(self.h * 0.8)
        self.panel_h = self.w_h * 0.45
        self.current_panel = None
        self.choose_team = None
        self.choose_settings = None
        self.choose_deid_path = None

        self.sdnist_cfg = load_cfg()

        self.picked_path = None
        self.back_color = pg.Color(back_color)
        if self.enabled:
            self._create()

    def enable(self):
        self.enabled = True
        self._create()

    def disable(self):
        self.enabled = False
        self.load_button.kill()
        self.load_button = None

    def _create(self):

        left, top = (self.w - self.w_w)//2, (self.h - self.w_h)//2 - 50
        title = "Onboarding"
        self.window_rect = pg.Rect(left, top,
                                   self.w_w,
                                   self.w_h)
        self.window = UIWindow(rect=self.window_rect,
                               manager=self.manager,
                               draggable=False,
                               resizable=False)
        self.window.background_colour = self.back_color
        self.window.rebuild()
        header_rect = pg.Rect(0, 0, self.w_w, self.header_h)
        self.header = WindowHeader(
            title=title,
            rect=header_rect,
            manager=self.manager,
            container=self.window,
            header_at_center=True
        )
        self.header.panel.background_colour = pg.Color("#1e1e1f")
        self.header.rebuild()

        y_pos = self.header_h + self.pad_y
        sdnist_rect = pg.Rect(
            0, y_pos, self.w_w, self.sdnist_h
        )
        self.sdnist_panel = SdnistPanel(
            rect=sdnist_rect,
            manager=self.manager,
            container=self.window
        )
        self.sdnist_panel.panel.background_colour = self.back_color
        self.sdnist_panel.rebuild()

        y_pos = sdnist_rect.bottom + self.pad_y
        callback = None
        if not (len(self.sdnist_cfg[strs.TEAM_UNIQUE_IDENTIFIER]) and
                len(self.sdnist_cfg[strs.TEAM_NAME])):
            # Create choose a team name
            choose_team_rect = pg.Rect(0, y_pos,
                                       self.w_w, self.panel_h)
            self.choose_team = ChooseTeamPanel(sdnist_cfg=self.sdnist_cfg,
                                               rect=choose_team_rect,
                                               manager=self.manager,
                                               container=self.window)
            self.choose_team.panel.background_colour = self.back_color
            self.choose_team.rebuild()

            self.current_panel = self.choose_team
            callback = self.save_team_info
        else:
            if self.header.title:
                self.header.title.set_text("Load Deid Data")

            # Create choose deid path
            choose_load_path_rect = pg.Rect(0, y_pos,
                                            self.w_w, self.panel_h)
            self.choose_deid_path = LoadDeidData(rect=choose_load_path_rect,
                                                 manager=self.manager,
                                                 container=self.window)
            self.choose_deid_path.panel.background_colour = self.back_color
            self.choose_deid_path.panel.rebuild()
            self.current_panel = self.choose_deid_path
            callback = self.save_deid_path

        next_btn_rect = pg.Rect(self.w_w * 0.8, self.w_h * 0.8,
                                self.w_w * 0.4, self.w_h * 0.08)

        self.next_button = UICallbackButton(callback=callback,
                                            relative_rect=next_btn_rect,
                                            text="Next",
                                            manager=self.manager,
                                            container=self.window,
                                            object_id=ObjectID(
                                                class_id='@chip_button',
                                                object_id='#next_button'
                                            ))

    def destroy(self):
        self.window.kill()
        self.window = None

    def draw(self, screen: pg.Surface):
        pass

    def update(self):
        pass

    def handle_event(self, event: pg.event.Event):
        if self.current_panel:
            self.current_panel.handle_event(event)

    def next_page(self):
        if self.picked_path is not None:
            return Page.DASHBOARD
        else:
            return Page.HOME

    def next_page_data(self):
        return self.picked_path

    def save_team_info(self):
        if self.choose_team is None \
                or not self.choose_team.can_save():
            return
        team_info = self.choose_team.get_team_info()

        self.sdnist_cfg = {**self.sdnist_cfg, **team_info}
        save_cfg(self.sdnist_cfg)

        self.next_button.callback = self.save_settings
        self.choose_team.destroy()
        y_pos = self.sdnist_panel.rect.bottom + self.pad_y
        choose_settings_rect = pg.Rect(0, y_pos,
                                       self.w_w, self.panel_h)
        self.choose_settings = SettingsPanel(rect=choose_settings_rect,
                                             manager=self.manager,
                                             data={strs.TEAM_NAME: self.sdnist_cfg[strs.TEAM_NAME]},
                                             container=self.window)
        self.choose_settings.panel.background_colour = self.back_color
        self.choose_settings.rebuild()
        self.current_panel = self.choose_settings

    def save_settings(self):
        self.sdnist_cfg.update(self.choose_settings.get_settings())
        self.next_button.callback = self.save_deid_path
        self.choose_settings.destroy()
        self.choose_settings = None
        y_pos = self.sdnist_panel.rect.bottom + self.pad_y
        choose_load_path_rect = pg.Rect(0, y_pos,
                                        self.w_w, self.panel_h)
        self.choose_deid_path = LoadDeidData(rect=choose_load_path_rect,
                                             manager=self.manager,
                                             container=self.window)
        self.choose_deid_path.panel.background_colour = self.back_color
        self.choose_deid_path.panel.rebuild()

        self.current_panel = self.choose_deid_path
        save_cfg(self.sdnist_cfg)

    def save_deid_path(self):
        if self.choose_deid_path.picked_path:
            self.picked_path = self.choose_deid_path.picked_path
            self.choose_deid_path.destroy()
            self.choose_deid_path = None
        else:
            if self.choose_deid_path:
                self.choose_deid_path.set_invalid_path()

