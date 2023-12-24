from pathlib import Path
from typing import Optional, Callable
import pygame as pg
import pygame_gui as pggui

from pygame_gui.core import ObjectID

from pygame_gui.elements.ui_window import UIWindow
from pygame_gui.elements.ui_panel import UIPanel
from pygame_gui.elements.ui_text_box import UITextBox
from pygame_gui.elements.ui_label import UILabel
from pygame_gui.elements.ui_text_entry_box import UITextEntryBox

from sdnist.gui.elements.textentrybox import CustomTextEntryBox
from sdnist.gui.panels import AbstractPanel


class BannerPanel(AbstractPanel):
    def __init__(self,
                 rect: pg.Rect,
                 manager: pggui.UIManager,
                 container: Optional[any] = None,
                 head_text: str = 'Head',
                 tail_text: str = 'Tail',
                 data: any = None):
        object_id = ObjectID(class_id='@header_panel',
                             object_id='#banner_panel')
        super().__init__(rect, manager, container,
                         data, object_id=object_id)
        self.text_in = None
        self.head_text = head_text
        self.tail_text = tail_text
        self.head_elem = None
        self.tail_elem = None
        self._create()

    def _create(self):
        head_w = int(self.rect.w * 0.2)
        head_rect = pg.Rect((0, 0),
                            (head_w, self.rect.h))
        head_lbl = f'{self.head_text}'
        self.head_elem = UILabel(text=head_lbl,
                               relative_rect=head_rect,
                               manager=self.manager,
                               container=self.panel,
                               parent_element=self.panel,
                                 object_id=ObjectID(
                                     class_id='@header_label',
                                     object_id='#banner_head_label')
                                 )
        self.head_elem.scroll_bar_width = 0
        self.head_elem.rebuild()
        tail_w = int(self.rect.w * 0.8)
        tail_rect = pg.Rect((head_w, 0),
                            (tail_w, self.rect.h))
        tail_lbl = f'{self.tail_text}'
        self.tail_elem = UILabel(text=tail_lbl,
                                 relative_rect=tail_rect,
                                 manager=self.manager,
                                 container=self.panel,
                                 parent_element=self.panel,
                                 object_id=ObjectID(
                                     class_id='@header_label',
                                     object_id='#banner_tail_label')
                                 )
        self.tail_elem.scroll_bar_width = 0
        self.tail_elem.rebuild()

    def destroy(self):
        self.head_elem.kill()
        self.tail_elem.kill()
        self.head_elem = None
        self.tail_elem = None
        super().destroy()

    def handle_event(self, event: pg.event.Event):
        super().handle_event(event)

