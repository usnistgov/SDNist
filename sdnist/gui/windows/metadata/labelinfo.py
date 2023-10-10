from pathlib import Path
from typing import Optional, Callable
import pygame as pg
import pygame_gui as pggui

from pygame_gui.elements.ui_window import UIWindow
from pygame_gui.elements.ui_panel import UIPanel
from pygame_gui.elements.ui_text_box import UITextBox
from pygame_gui.elements.ui_text_entry_box import UITextEntryBox

from sdnist.gui.elements.textentrybox import CustomTextEntryBox
from sdnist.gui.panels import AbstractPanel
from sdnist.gui.windows.metadata.labels import LabelType


class LabelInfoPanel(AbstractPanel):
    def __init__(self,
                 rect: pg.Rect,
                 manager: pggui.UIManager,
                 label_name: str,
                 label_type: LabelType,
                 label_description: str,
                 text_change_callback: Optional[Callable] = None,
                 container: Optional[any] = None,
                 initial_text: str = '',
                 data: any = None):
        super().__init__(rect, manager, container, data)
        self.text_change_callback = text_change_callback
        self.panel = None
        self.text_in = None
        self.text = initial_text
        self.label_name = label_name
        self.label_type = label_type
        self.label_description = label_description
        self.title_height = 30
        self._create()

    def _create(self):
        self.panel = UIPanel(relative_rect=self.rect,
                             manager=self.manager,
                             container=self.container,
                             starting_height=10)
        self._create_title()
        if self.label_type == LabelType.LONG_STRING:
            self._create_text_in_box()
        else:
            self._create_text_box()
        self._create_description_title()
        self._create_label_description_text()
        # self.text.set_minimum_dimensions((self.rect.w, self.rect.h * 0.5))

    def _create_title(self):
        self.title_rect = pg.Rect((0, 0),
                                  (self.rect.w, self.title_height))
        title_text = f'{self.label_name}'
        self.title = UITextBox(html_text=title_text,
                               relative_rect=self.title_rect,
                               manager=self.manager,
                               container=self.panel)
        self.title.scroll_bar_width = 0
        self.title.rebuild()

    def _create_text_in_box(self):
        self.text_rect = pg.Rect((0, self.title_height),
                                 (self.rect.w, self.rect.h * 0.4))
        self.text_in = CustomTextEntryBox(
                                   text_changed_callback=self.text_change_callback,
                                   placeholder_text='',
                                   relative_rect=self.text_rect,
                                   manager=self.manager,
                                   container=self.panel)
        self.text_in.set_text(self.text)

    def _create_text_box(self):
        self.text_rect = pg.Rect((0, self.title_height),
                                 (self.rect.w, self.rect.h * 0.2))
        self.text_in = CustomTextEntryBox(
                                   placeholder_text='',
                                   relative_rect=self.text_rect,
                                   editable=False,
                                   manager=self.manager,
                                   container=self.panel)
        self.text_in.set_text(self.text)

    def _create_description_title(self):
        self.desc_title_rect = pg.Rect(0,
                                       self.text_rect.y + self.text_rect.h,
                                       self.rect.w, self.title_height)
        title_text = f'Field Description'
        self.desc_title = UITextBox(html_text=title_text,
                                    relative_rect=self.desc_title_rect,
                                    manager=self.manager,
                                    container=self.panel)
        self.desc_title.scroll_bar_width = 0
        self.desc_title.rebuild()

    def _create_label_description_text(self):
        self.desc_text_rect = pg.Rect((0,
                                       self.desc_title_rect.y +
                                       self.desc_title_rect.h),
                                       (self.rect.w, self.rect.h * 0.5))
        self.desc_text = CustomTextEntryBox(
                                   placeholder_text='',
                                   relative_rect=self.desc_text_rect,
                                   editable=False,
                                   manager=self.manager,
                                   container=self.panel,
                                   anchors={'left': 'left',
                                            'top': 'top'})
        self.desc_text.set_text(self.label_description)

    def destroy(self):
        self.panel.kill()
        self.text_in.kill()

    def handle_event(self, event: pg.event.Event):
        pass
