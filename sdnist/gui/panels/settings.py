import os

import pygame as pg
import pygame_gui as pggui

from pygame_gui.core import ObjectID
from pygame_gui.elements import UIPanel
from pygame_gui.elements.ui_label import UILabel
from pygame_gui.elements.ui_button import UIButton
from pygame_gui.elements.ui_window import UIWindow
from pygame_gui.elements.ui_text_entry_line import UITextEntryLine
from pygame_gui.elements.ui_horizontal_slider import UIHorizontalSlider

from sdnist.gui.panels.headers.header import Header
from sdnist.gui.panels.panel import AbstractPanel
from sdnist.gui.elements import \
    UICallbackButton, CustomUITextEntryLine
from sdnist.gui.panels.plain_window import PlainWindow
import sdnist.gui.strs as strs

from sdnist.gui.config import load_cfg, save_cfg
from sdnist.gui.colors import (
    main_theme_color, dark_grey, back_color)

setting_options = [
    strs.TEAM_NAME,
    strs.TEAM_CONTACT_EMAIL,
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
        settings = load_cfg()
        self.settings = {k: v
                         for k, v in settings.items()
                         if k in setting_options}

        self.max_cpu = max(1, os.cpu_count()-3)

        if strs.MAX_PROCESSES not in self.settings:
            self.settings[strs.MAX_PROCESSES] = max(1, self.max_cpu)
        if strs.NUMERICAL_METRIC_RESULTS not in self.settings:
            self.settings[strs.NUMERICAL_METRIC_RESULTS] = False

        self.base = None
        self.plain_window = None
        self.done_button_visible = done_button_visible
        self.done_button_callback = done_button_callback
        self.done_window = None
        self.team_name_label = None
        self.team_name = None
        self.team_email_label = None
        self.team_email = None
        self.max_processes_label = None
        self.max_processes = None
        self.max_processes_value_lbl = None
        self.numerical_metric_results_label = None
        self.numerical_metric_results = None
        self._create()

    def get_settings(self):
        if self.team_name:
            self.settings[strs.TEAM_NAME] = self.team_name.get_text()
        if self.team_email:
            self.settings[strs.TEAM_CONTACT_EMAIL] = self.team_email.get_text()
        if self.max_processes:
            self.settings[strs.MAX_PROCESSES] = \
                int(self.max_processes.get_current_value())
        if self.numerical_metric_results:
            self.settings[strs.NUMERICAL_METRIC_RESULTS] = \
                self.numerical_metric_results.text == 'ON'
        all_settings = load_cfg()
        all_settings.update(self.settings)
        return all_settings

    def save_settings(self):
        save_cfg(self.get_settings())

    def _create(self):
        if self.container is None:
            win_rect = pg.Rect(self.w // 2 - self.rect.w // 2,
                               self.h // 2 - self.rect.h // 2,
                               self.rect.w, self.rect.h)
            window_rect = pg.Rect(win_rect)
            self.plain_window = PlainWindow(rect=window_rect,
                                    manager=self.manager,
                                    window_display_title='Settings',
                                    draggable=True,
                                    resizable=True,
                                    on_top=True)
            self.base = self.plain_window.window
            self.base.background_colour = pg.Color(back_color)
            self.base.shape = 'rounded_rectangle'
            self.base.shape_corner_radius = 20
            self.base.shadow_width = 10
            self.base.rebuild()
            # destroy the default panel
            super().destroy()
            option_w = int(self.rect.w * 0.35)
            lbl_w = int(self.rect.w * 0.45)
            start_x = (self.rect.w - option_w - lbl_w) // 2
            start_y = 30
        else:
            self.base = self.panel
            option_w = int(self.rect.w * 0.3)
            lbl_w = int(self.rect.w * 0.4)

            info_title_rect = pg.Rect(
                0, 0,
                self.rect.w, 40
            )
            self.info_title = Header(
                text='Change default settings to your preference.',
                rect=info_title_rect,
                manager=self.manager,
                container=self.panel,
                text_size='medium'
            )

            self.info_title.panel.background_colour = pg.Color(main_theme_color)
            self.info_title.rebuild()

            start_x = (self.rect.w - option_w - lbl_w) // 2
            start_y = info_title_rect.bottom + 30

        lbl_obj_id = ObjectID(class_id='@header_label',
                              object_id='#choose_team_panel_label')


        option_h = 50
        pad_y = 5
        start_y += pad_y
        # add team name setting
        team_name_rect = pg.Rect((start_x, start_y),
                                 (option_w, option_h))
        lbl_left_margin = 30


        # TEAM Name
        self.team_name_label = UILabel(
            relative_rect=team_name_rect,
            container=self.base,
            parent_element=self.base,
            text='Team Name:',
            manager=self.manager,
            object_id=lbl_obj_id)

        team_name_rect.left = team_name_rect.right
        team_name_rect.w = lbl_w
        team_name_rect.y = team_name_rect.y + option_h * 0.05
        team_name_rect.h = option_h * 0.9

        self.team_name = CustomUITextEntryLine(
            editable=True,
            relative_rect=team_name_rect,
            container=self.base,
            parent_element=self.base,
            manager=self.manager,
            placeholder_text='Enter a team name',
            anchors={'top': 'top',
                     'left': 'left'})

        if strs.TEAM_NAME in self.settings \
            and self.settings[strs.TEAM_NAME] is not None \
            and self.settings[strs.TEAM_NAME] != '':
            self.team_name.set_text(self.settings[strs.TEAM_NAME])


        team_email_rect = pg.Rect((start_x,
                                   team_name_rect.bottom + pad_y),
                                  (option_w, option_h))
        self.team_email_label = UILabel(
            relative_rect=team_email_rect,
            container=self.base,
            parent_element=self.base,
            text='Team Email:',
            manager=self.manager,
            object_id=lbl_obj_id)

        team_email_rect.left = team_email_rect.right
        team_email_rect.w = lbl_w
        team_email_rect.y = team_email_rect.y + option_h * 0.05
        team_email_rect.h = option_h * 0.9

        self.team_email = CustomUITextEntryLine(
            editable=True,
            relative_rect=team_email_rect,
            container=self.base,
            parent_element=self.base,
            manager=self.manager,
            placeholder_text="Enter a team email",
            anchors={'top': 'top',
                     'left': 'left'})

        if strs.TEAM_CONTACT_EMAIL in self.settings \
            and self.settings[strs.TEAM_CONTACT_EMAIL] is not None:
            self.team_email.set_text(self.settings[strs.TEAM_CONTACT_EMAIL])

        # MAX Processes
        max_processes_rect_x = start_x
        max_processes_rect_y = team_email_rect.bottom + pad_y + option_h * 0.05
        max_processes_rect = pg.Rect((max_processes_rect_x,
                                      max_processes_rect_y),
                                      (option_w, option_h))
        self.max_processes_label = UILabel(
            relative_rect=max_processes_rect,
            container=self.base,
            parent_element=self.base,
            text='Max Processes:',
            manager=self.manager,
            anchors={'top': 'top',
                     'left': 'left'},
            object_id=lbl_obj_id)

        max_proc_input_rect = pg.Rect((max_processes_rect.right,
                                      max_processes_rect.y + option_h * 0.25),
                                      (lbl_w, option_h * 0.5))

        # use UIHorizontalSlider for max processes

        self.max_processes = UIHorizontalSlider(
            relative_rect=max_proc_input_rect,
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

        max_processes_value_rect = pg.Rect((max_proc_input_rect.x +
                                            max_proc_input_rect.w + 10,
                                            max_proc_input_rect.y),
                                            (option_w, option_h * 0.5))

        self.max_processes_value_lbl = UILabel(
            relative_rect=max_processes_value_rect,
            container=self.base,
            parent_element=self.base,
            text=f"{str(self.max_processes.get_current_value())}/{self.max_cpu}",
            manager=self.manager,
            object_id=lbl_obj_id
        )

        # Numerical metric results setting
        numerical_metric_results_rect_x = start_x
        numerical_metric_results_rect_y = max_processes_rect.bottom + pad_y
        numerical_metric_results_rect = pg.Rect((numerical_metric_results_rect_x,
                                                 numerical_metric_results_rect_y),
                                                 (option_w, option_h))

        self.numerical_metric_results_label = UILabel(
            relative_rect=numerical_metric_results_rect,
            container=self.base,
            parent_element=self.base,
            text='Report Only Numerical Metric Results:',
            manager=self.manager,
            anchors={'top': 'top',
                     'left': 'left'},
            object_id=lbl_obj_id)

        numerical_metric_results_rect.left = numerical_metric_results_rect.right
        numerical_metric_results_rect.w = lbl_w
        numerical_metric_results_rect.y = (
                numerical_metric_results_rect.y + option_h * 0.1)
        numerical_metric_results_rect.h = option_h * 0.9

        self.numerical_metric_results = UIButton(
            relative_rect=numerical_metric_results_rect,
            container=self.base,
            parent_element=self.base,
            manager=self.manager,
            anchors={'top': 'top',
                     'left': 'left'},
            text='OFF',
            object_id=ObjectID(
                class_id='@chip_button',
                object_id='#on_off_button'
            )
        )


        self.update_numeric_metric_results()

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
                                                 'left': 'left'},
                                        object_id=ObjectID(
                                            class_id='@chip_button',
                                            object_id='#on_off_button'
                                        ))
            self.done_button.text_horiz_alignment = 'center'
            self.done_button.rebuild()

    def destroy(self):
        super().destroy()
        if isinstance(self.base, UIWindow):
            self.base.kill()
            self.base = None

    def update_numeric_metric_results(self):
        is_on = False
        if strs.NUMERICAL_METRIC_RESULTS in self.settings \
           and self.settings[strs.NUMERICAL_METRIC_RESULTS] is not None:
            is_on = self.settings[strs.NUMERICAL_METRIC_RESULTS]
        self.numerical_metric_results.set_text(
            'ON' if is_on else 'OFF')
        color = pg.Color(main_theme_color) if is_on else pg.Color(dark_grey)

        self.numerical_metric_results.colours['normal_bg'] = pg.Color(color)
        self.numerical_metric_results.rebuild()

    def handle_event(self, event: pg.event.Event):
        if isinstance(self.base, UIWindow):
            if not self.manager.ui_window_stack.is_window_at_top(self.base):
                self.manager.ui_window_stack.move_window_to_front(self.base)

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
                    self.update_numeric_metric_results()
