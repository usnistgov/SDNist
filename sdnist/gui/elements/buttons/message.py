from typing import Callable, Optional

import pygame as pg
import pygame_gui as pggui

from pygame_gui.elements.ui_button import UIButton
from pygame_gui.elements.ui_label import UILabel
from pygame_gui.elements.ui_panel import UIPanel
from pygame_gui.core import ObjectID

from sdnist.gui.elements.buttons.button import UICallbackButton

from sdnist.gui.helper import PathType

# Custom button class
class MessageButton(UICallbackButton):
    def __init__(self,
                 *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.expanded = False
        self.expanded_text = '[-]' if self.expanded else '[+]'

        self.lbl_panel = None
        self.label = None

        self.messages = 0

        self._create()

    def _create(self):
        lbl_rect = pg.Rect((self.rect.x + self.rect.w // 1.5, 0),
                           (self.rect.w - self.rect.w // 2.5,
                            self.rect.h - 5))
        self.lbl_panel = UIPanel(
            relative_rect=lbl_rect,
            manager=self.ui_manager,
            container=self.ui_container,
            anchors={'left': 'left',
                     'top': 'top'},
            object_id=ObjectID(class_id='@from_field_panel',
                               object_id='#notification_panel')
        )
        lbl_rect.x = 0
        lbl_rect.w = -1
        lbl_rect.h = -1
        self.label = UILabel(
            text=str(self.messages),
            relative_rect=lbl_rect,
            manager=self.ui_manager,
            container=self.lbl_panel,
            parent_element=self.lbl_panel,
            anchors={'centerx': 'centerx',
                     'centery': 'centery'},
            object_id=ObjectID(class_id='@sdnist_version_label',
                               object_id='#notification_label')
        )

        self.show_messages_indicator()

    def show_messages_indicator(self):
        if self.messages > 0:
            self.label.show()
            self.lbl_panel.show()
        else:
            self.label.hide()
            self.lbl_panel.hide()

    def update_messages(self, messages):
        if messages != self.messages:
            self.messages = messages
            self.show_messages_indicator()
            self.label.set_text(str(self.messages))
            self.label.rebuild()
            self.lbl_panel.rebuild()

    def kill(self):
        super().kill()
        self.label.kill()
        self.lbl_panel.kill()

