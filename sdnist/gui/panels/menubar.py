from typing import Callable, Dict
import pygame as pg
import pygame_gui as pggui
from pygame_gui.elements.ui_panel import UIPanel
from pygame_gui.elements.ui_label import UILabel
from pygame_gui.core.object_id import ObjectID

from sdnist.gui.panels.panel import AbstractPanel
from sdnist.gui.elements import UICallbackButton

from sdnist.gui.strs import *
from sdnist.gui.config import load_cfg, save_cfg

LOAD_DATA = 'Load Data'
TARGET_DATA = 'Target Data'
SETTINGS = 'Settings'
NUMERICAL_RESULT = 'Numerical Results'
menubar_left_btns = [

]

menubar_rigth_btns = [
    LOAD_DATA,
    TARGET_DATA,
    SETTINGS,
    NUMERICAL_RESULT
]

class MenuBar(AbstractPanel):
    def __init__(self, *args, **kwargs):
        if 'starting_height' not in kwargs:
            kwargs['starting_height'] = 0
        kwargs['object_id'] = ObjectID(
            class_id='@menubar_panel',
            object_id='#menubar_panel')
        super().__init__(*args, **kwargs)
        self.buttons = dict()
        self.settings = load_cfg()
        self.numerical_result_callback = None
        self.numerical_results = self.settings.get(NUMERICAL_METRIC_RESULTS,
                                                   False)

        self.settings_window = None
        self._create()

    def set_callbacks(self, callbacks: Dict[str, Callable]):
        for btn_name, callback in callbacks.items():
            if btn_name not in self.buttons:
                raise ValueError(f'Invalid button name: {btn_name}')
            if btn_name == NUMERICAL_RESULT:
                self.numerical_result_callback = callback
                btn = self.buttons[btn_name]
                btn.callback = self.toggle_numerical_result
            else:
                btn = self.buttons[btn_name]
                btn.callback = callback

    def _create(self):
        def empty():
            return

        net_width = 0
        for i, btn_name in enumerate(menubar_rigth_btns[::-1]):
            btn = self.create_right_button(btn_name, net_width)
            net_width += btn.rect.w
            if btn_name == NUMERICAL_RESULT:
                btn.callback = self.toggle_numerical_result
            self.buttons[btn_name] = btn

    def create_right_button(self, btn_name, net_width):
        def empty():
            return

        btn_text = btn_name
        btn_tool_tip = btn_name
        obj_id = ObjectID(
            class_id="@menubar_button",
            object_id="#menubar_left_button",
        )
        btn_w = 140
        if btn_name == NUMERICAL_RESULT:
            btn_tool_tip = ('Create reports with only numerical results. '
                            'This only generates csv and json files.')
            btn_w = 250
            if self.numerical_results:
                btn_text = NUMERICAL_RESULT + ' : ON'
                obj_id = ObjectID(
                    class_id="@menubar_button",
                    object_id="#menubar_right_button",
                )
            else:
                btn_text = NUMERICAL_RESULT + ' : OFF'
                obj_id = ObjectID(
                    class_id="@menubar_button",
                    object_id="#menubar_right_off_button",
                )

        btn_rect = pg.Rect((0, 0), (btn_w, 40))
        net_width += btn_w
        btn_rect.left = -1 * net_width

        btn = UICallbackButton(relative_rect=btn_rect,
                               callback=empty,
                               text=btn_text,
                               container=self.panel,
                               parent_element=self.panel,
                               manager=self.manager,
                               anchors={'right': 'right',
                                        'centery': 'centery'},
                               tool_tip_text=btn_tool_tip,
                               object_id=obj_id)
        net_width = 0
        return btn
    def destroy(self):
        super().destroy()
        for btn in self.buttons.values():
            btn.kill()
        self.buttons.clear()

    def handle_event(self, event: pg.event.Event):
        if self.settings_window:
            self.settings_window.handle_event(event)

    def toggle_numerical_result(self):
        self.settings[NUMERICAL_METRIC_RESULTS] = \
            not self.settings[NUMERICAL_METRIC_RESULTS]

        save_cfg(self.settings)
        self.update_numerical_results()

    def update_numerical_results(self):
        btn = self.buttons[NUMERICAL_RESULT]
        btn.kill()
        self.numerical_results = self.settings[NUMERICAL_METRIC_RESULTS]
        btn = self.create_right_button(NUMERICAL_RESULT, 0)
        btn.callback = self.toggle_numerical_result
        self.buttons[NUMERICAL_RESULT] = btn

        if self.numerical_result_callback:
            self.numerical_result_callback()

    def update_settings(self):
        self.settings = load_cfg()
        self.update_numerical_results()
