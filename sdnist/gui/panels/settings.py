import os

import pygame as pg
import pygame_gui as pggui
from pygame_gui.elements import UIPanel
from pygame_gui.elements.ui_label import UILabel
from pygame_gui.elements.ui_button import UIButton
from pygame_gui.elements.ui_window import UIWindow
from pygame_gui.elements.ui_text_entry_line import UITextEntryLine
from pygame_gui.elements.ui_horizontal_slider import UIHorizontalSlider

from sdnist.gui.panels.panel import AbstractPanel
from sdnist.gui.elements import \
    UICallbackButton, CustomUITextEntryLine
import sdnist.gui.strs as strs

setting_options = [
    strs.TEAM_NAME,
    strs.MAX_PROCESSES,
    strs.NUMERICAL_METRIC_RESULTS
]


class SettingsPanel(AbstractPanel):
    def __init__(self,
                 done_button_visible=False,
                 done_button_callback=None,
                 *args,
                 **kwargs):
        super().__init__(*args, **kwargs)

        self.settings = {k: v
                         for k, v in self.data.items()
                         if k in setting_options}

        self.max_cpu = max(1, os.cpu_count()-3)

        if strs.MAX_PROCESSES not in self.settings:
            self.settings[strs.MAX_PROCESSES] = max(1, self.max_cpu)
        if strs.NUMERICAL_METRIC_RESULTS not in self.settings:
            self.settings[strs.NUMERICAL_METRIC_RESULTS] = False

        self.base = None
        self.done_button_visible = done_button_visible
        self.done_button_callback = done_button_callback
        self.done_window = None
        self.team_name_label = None
        self.team_name = None
        self.max_processes_label = None
        self.max_processes = None
        self.max_processes_value_lbl = None
        self.numerical_metric_results_label = None
        self.numerical_metric_results = None
        self._create()

    def _create(self):
        if self.container is None:
            window_rect = pg.Rect(self.rect.w//2, self.rect.h//2,
                                  self.rect.w, self.rect.h)
            self.base = UIWindow(rect=window_rect,
                                 manager=self.manager,
                                 window_display_title=
                                 'Settings',
                                 draggable=True,
                                 resizable=True)
            super().destroy()
        else:
            self.base = self.panel

        start_x = int(self.rect.w * 0.05)
        start_y = int(self.rect.h * 0.08)
        option_h = int(self.rect.h * 0.05)
        option_w = int(self.rect.w * 0.5)
        # add team name setting
        team_name_rect = pg.Rect((start_x, start_y),
                                 (option_w, option_h))
        lbl_left_margin = 30
        lbl_w = int(self.rect.w * 0.4)

        # TEAM Name
        self.team_name_label = UILabel(
            relative_rect=team_name_rect,
            container=self.base,
            parent_element=self.base,
            text='Team Name',
            manager=self.manager)
        team_name_rect.left = team_name_rect.w + lbl_left_margin
        team_name_rect.w = lbl_w
        self.team_name = CustomUITextEntryLine(
            editable=False,
            relative_rect=team_name_rect,
            container=self.base,
            parent_element=self.base,
            manager=self.manager,
            anchors={'top': 'top',
                     'left': 'left'})

        if strs.TEAM_NAME in self.settings \
            and self.settings[strs.TEAM_NAME] is not None \
            and self.settings[strs.TEAM_NAME] != '':
            self.team_name.set_text(self.settings[strs.TEAM_NAME])

        # MAX Processes
        max_processes_rect_x = start_x
        max_processes_rect_y = team_name_rect.y + start_y
        max_processes_rect = pg.Rect((max_processes_rect_x,
                                      max_processes_rect_y),
                                      (option_w, option_h))
        self.max_processes_label = UILabel(
            relative_rect=max_processes_rect,
            container=self.base,
            parent_element=self.base,
            text='Max Processes',
            manager=self.manager,
            anchors={'top': 'top',
                     'left': 'left'})

        max_processes_rect.left = max_processes_rect.w + lbl_left_margin
        max_processes_rect.w = lbl_w
        # use UIHorizontalSlider for max processes

        self.max_processes = UIHorizontalSlider(
            relative_rect=max_processes_rect,
            container=self.base,
            parent_element=self.base,
            manager=self.manager,
            anchors={'top': 'top',
                     'left': 'left'},
            start_value=self.max_cpu,
            value_range=(1, self.max_cpu)
        )

        if strs.MAX_PROCESSES in self.settings \
            and self.settings[strs.MAX_PROCESSES] is not None \
            and str(self.settings[strs.MAX_PROCESSES]).isnumeric():
            self.max_processes.set_current_value(int(self.settings[strs.MAX_PROCESSES]))

        max_processes_value_rect = pg.Rect((max_processes_rect.x +
                                            max_processes_rect.w + 10,
                                            max_processes_rect.y),
                                            (option_w, option_h))

        self.max_processes_value_lbl = UILabel(
            relative_rect=max_processes_value_rect,
            container=self.base,
            parent_element=self.base,
            text=f"{str(self.max_processes.get_current_value())}/{self.max_cpu}",
            manager=self.manager,
        )

        # Numerical metric results setting
        numerical_metric_results_rect_x = start_x
        numerical_metric_results_rect_y = max_processes_rect.y + start_y
        numerical_metric_results_rect = pg.Rect((numerical_metric_results_rect_x,
                                                 numerical_metric_results_rect_y),
                                                 (option_w, option_h))

        self.numerical_metric_results_label = UILabel(
            relative_rect=numerical_metric_results_rect,
            container=self.base,
            parent_element=self.base,
            text='Report Only Numerical Metric Results',
            manager=self.manager,
            anchors={'top': 'top',
                     'left': 'left'})

        numerical_metric_results_rect.left = numerical_metric_results_rect.w + lbl_left_margin
        numerical_metric_results_rect.w = lbl_w
        self.numerical_metric_results = UIButton(
            relative_rect=numerical_metric_results_rect,
            container=self.base,
            parent_element=self.base,
            manager=self.manager,
            anchors={'top': 'top',
                     'left': 'left'},
            text='No'
        )

        if strs.NUMERICAL_METRIC_RESULTS in self.settings \
           and self.settings[strs.NUMERICAL_METRIC_RESULTS] is not None:
            self.numerical_metric_results.set_text(
                'Yes' if self.settings[strs.NUMERICAL_METRIC_RESULTS]
                else 'No'
            )

        if self.done_button_visible:
            done_btn_w = 200
            done_btn_h = 50
            done_btn_x = int(self.rect.w * 0.5) - done_btn_w//2
            done_btn_y = self.rect.h - 100
            button_rect = pg.Rect((done_btn_x, done_btn_y),
                                  (done_btn_w, done_btn_h))
            self.done_button = UICallbackButton(
                                        callback=self.done_button_callback,
                                        relative_rect=button_rect,
                                        container=self.base,
                                        parent_element=self.base,
                                        text='SAVE',
                                        manager=self.manager,
                                        anchors={'top': 'top',
                                                 'left': 'left'})

    def destroy(self):
        super().destroy()
        if isinstance(self.base, UIWindow):
            self.base.kill()
            self.base = None

    def handle_event(self, event: pg.event.Event):
        if event.type == pg.USEREVENT:
            if event.user_type == pggui.UI_WINDOW_CLOSE:
                if event.ui_element == self.base:
                    if self.done_button_callback:
                        self.done_button_callback(save_settings=False)
            if event.user_type == pggui.UI_HORIZONTAL_SLIDER_MOVED:
                if event.ui_element == self.max_processes:
                    self.settings[strs.MAX_PROCESSES] = \
                        int(self.max_processes.get_current_value())
                    self.max_processes_value_lbl.set_text(
                        f"{str(self.max_processes.get_current_value())}/{self.max_cpu}")

            # also check if right and left button of the slider is pressed.
            elif event.user_type == pggui.UI_BUTTON_PRESSED:
                if event.ui_element == self.max_processes.left_button:
                    self.settings[strs.MAX_PROCESSES] = \
                        int(self.max_processes.get_current_value())
                    self.max_processes_value_lbl.set_text(
                        f"{str(self.max_processes.get_current_value())}/{self.max_cpu}")
                elif event.ui_element == self.max_processes.right_button:
                    self.settings[strs.MAX_PROCESSES] = \
                        int(self.max_processes.get_current_value())
                    self.max_processes_value_lbl.set_text(
                        f"{str(self.max_processes.get_current_value())}/{self.max_cpu}")
                elif event.ui_element == self.numerical_metric_results:
                    self.settings[strs.NUMERICAL_METRIC_RESULTS] = \
                        not self.settings[strs.NUMERICAL_METRIC_RESULTS]
                    self.numerical_metric_results.set_text(
                        'Yes' if self.settings[strs.NUMERICAL_METRIC_RESULTS] else 'No')
