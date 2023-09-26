import pygame as pg
import pygame_gui as pggui
import json

from pygame_gui.elements.ui_window import UIWindow


from sdnist.gui.pages import Page
from sdnist.gui.pages.page import AbstractPage
from sdnist.gui.panels import SettingsPanel
from sdnist.gui.pages.home.choose_team import \
    ChooseTeamPanel
from sdnist.gui.pages.home.choose_deid import \
    ChooseDeidPathPanel
from sdnist.gui.elements import UICallbackButton

from sdnist.gui.config import cfg_path

import sdnist.gui.strs as strs


class Home(AbstractPage):
    def __init__(self, manager: pggui.UIManager,
                 enable: bool = True):
        super().__init__(manager)
        self.enabled = enable
        self.load_button = None

        self.manager = manager

        self.window = None
        self.file_dialog = None
        self.picked_path = None

        self.current_panel = None
        self.choose_team = None
        self.choose_settings = None
        self.choose_deid_path = None

        self.sdnist_cfg = dict()
        with open(cfg_path, 'r') as f:
            self.sdnist_cfg = json.load(f)

        self.picked_path = None

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
        self.w_w, self.w_h = int(self.w * 0.8), int(self.h * 0.8)
        left, top = (self.w - self.w_w)//2, (self.h - self.w_h)//2
        self.window_rect = pg.Rect(left, top,
                                   self.w_w,
                                   self.w_h)
        self.window = UIWindow(rect=self.window_rect,
                               manager=self.manager,
                               window_display_title="Setup",
                               draggable=False,
                               resizable=False)

        callback = None
        if len(self.sdnist_cfg[strs.TEAM_NAME]) == 0:
            # Create choose a team name
            choose_team_rect = pg.Rect(0, 0,
                                       self.w_w, self.w_h * 0.8)
            self.choose_team = ChooseTeamPanel(choose_team_rect,
                                               self.manager,
                                               container=self.window)

            self.current_panel = self.choose_team
            callback = self.save_team_name
        else:
            # Create choose deid path
            choose_load_path_rect = pg.Rect(0, 0,
                                            self.w_w, self.w_h * 0.8)
            self.choose_deid_path = ChooseDeidPathPanel(choose_load_path_rect,
                                                        self.manager,
                                                        container=self.window)
            self.current_panel = self.choose_deid_path
            callback = self.save_deid_path

        next_btn_rect = pg.Rect(self.w_w * 0.8, self.w_h * 0.8,
                                self.w_w * 0.1, self.w_h * 0.08)

        self.next_button = UICallbackButton(callback=callback,
                                            relative_rect=next_btn_rect,
                                            text="Next",
                                            manager=self.manager,
                                            container=self.window)

    def destroy(self):
        self.window.kill()
        self.window = None

    def draw(self, screen: pg.Surface):
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

    def save_team_name(self):
        if self.choose_team is None:
            return

        team_name = self.choose_team.text_entry.get_text()

        if len(team_name) == 0:
            return

        self.sdnist_cfg[strs.TEAM_NAME] = team_name
        self.next_button.callback = self.save_settings
        self.choose_team.destroy()

        choose_settings_rect = pg.Rect(0, 0,
                                       self.w_w, self.w_h * 0.8)
        self.choose_settings = SettingsPanel(choose_settings_rect,
                                             self.manager,
                                             data={strs.TEAM_NAME: team_name},
                                             container=self.window)
        self.current_panel = self.choose_settings

    def save_settings(self):
        self.sdnist_cfg.update(self.choose_settings.settings)
        self.next_button.callback = self.save_deid_path
        self.choose_settings.destroy()
        self.choose_settings = None

        choose_load_path_rect = pg.Rect(0, 0,
                                        self.w_w, self.w_h * 0.8)
        self.choose_deid_path = ChooseDeidPathPanel(choose_load_path_rect,
                                                    self.manager,
                                                    container=self.window)
        self.current_panel = self.choose_deid_path
        with open(cfg_path, 'w') as f:
            json.dump(self.sdnist_cfg, f, indent=4)

    def save_deid_path(self):
        if self.choose_deid_path.picked_path:
            self.picked_path = self.choose_deid_path.picked_path
            self.choose_deid_path.destroy()
            self.choose_deid_path = None


