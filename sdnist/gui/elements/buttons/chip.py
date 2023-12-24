from typing import Optional, Callable

import pygame_gui as pggui
import pygame as pg

from pygame_gui.elements.ui_button import UIButton
from pygame_gui.elements.ui_panel import UIPanel
from pygame_gui.core.object_id import ObjectID

from sdnist.gui.elements.buttons.button import \
    UICallbackButton


class ChipButton(UIButton):
    def __init__(self,
                 full_text: Optional[str],
                 button_callback: Optional[Callable] = None,
                 cancel_callback: Optional[Callable] = None,
                 display_text: Optional[str] = '',
                 *args, **kwargs):
        kwargs['object_id'] = ObjectID(class_id='@chip_button',
                                       object_id='#chip_button')
        kwargs['tool_tip_text'] = full_text
        self.full_text = full_text
        self.display_text = display_text

        if len(display_text) == 0:
            self.display_text = self.full_text

        kwargs['text'] = self.display_text
        super().__init__(*args, **kwargs)

        self.manager = kwargs.get('manager', None)
        self.container = kwargs.get('container', None)
        self.button_callback = button_callback
        self.cancel_callback = cancel_callback
        self.cancel_button = None
        self.mask_panel = None

        self._create()

    def update(self, time_delta: float):
        super().update(time_delta)
        # check hover
        # if self.hovered and self.mask_panel:
        #     self.mask_panel.background_colour = self.colours['hovered_bg']
        # else:
        #     self.mask_panel.background_colour = self.colours['normal_bg']
        # self.mask_panel.rebuild()

    def kill(self):
        super().kill()
        if self.cancel_button:
            self.cancel_button.kill()
            self.cancel_button = None

        if self.mask_panel:
            self.mask_panel.kill()
            self.mask_panel = None

    def _create(self):
        c_btn_w = self.rect.h - 5
        c_btn_x = self.relative_rect.x + \
            self.relative_rect.w - c_btn_w - 5
        c_btn_y = self.rect.y

        m_btn_x = c_btn_x - 6
        m_btn_w = c_btn_w
        m_btn_h = c_btn_w - 6
        m_btn_rect = pg.Rect(m_btn_x, 0,
                             m_btn_w, m_btn_h)
        # self.mask_panel = UIPanel(
        #     relative_rect=m_btn_rect,
        #     manager=self.manager,
        #     container=self.container,
        #     anchors={'left': 'left',
        #              'centery': 'centery'},
        # )
        # self.mask_panel.background_colour = self.colours['normal_bg']
        # self.mask_panel.border_width = 0
        # self.mask_panel.shadow_width = 0
        # self.mask_panel.rebuild()
        c_btn_x = (self.relative_rect.x + self.relative_rect.w
                   - c_btn_w - 3)
        c_btn_rect = pg.Rect(c_btn_x, 0,
                             c_btn_w, c_btn_w)
        self.cancel_button = UICallbackButton(
            callback=self.cancel_callback,
            starting_height=self.starting_height + 1,
            relative_rect=c_btn_rect,
            text='X',
            manager=self.manager,
            container=self.container,
            anchors={'left': 'left',
                     'centery': 'centery'},
            object_id=ObjectID(class_id='@icon_button',
                               object_id='#cancel_icon_button')
        )
        self.text_horiz_alignment = 'left'
        self.rebuild()

        self.cancel_button.rebuild()

    def process_event(self, event):
        response = super().process_event(event)
        if event.type == pg.USEREVENT:
            if event.user_type == pggui.UI_BUTTON_PRESSED \
                    and event.ui_element == self:
                if self.button_callback:
                    self.button_callback()
        return response
