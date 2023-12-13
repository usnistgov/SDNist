from typing import Optional, Callable
import pygame_gui as pggui
import pygame as pg
from pathlib import Path
from functools import partial

from pygame_gui.core import ObjectID
from pygame_gui.elements.ui_window import UIWindow
from pygame_gui.elements.ui_button import UIButton
from pygame_gui.elements.ui_progress_bar import UIProgressBar
from pygame_gui.elements.ui_label import UILabel
from pygame_gui.elements.ui_panel import UIPanel
from pygame_gui.elements.ui_text_entry_line import UITextEntryLine
from pygame_gui.elements.ui_selection_list import UISelectionList

from sdnist.gui.elements.textline import CustomUITextEntryLine

from sdnist.gui.elements.buttons import UICallbackButton
from sdnist.gui.elements.progress import CustomUIProgress
from sdnist.gui.elements.selection import CallbackSelectionList
from sdnist.gui.elements import CustomUIPanel
from sdnist.gui.panels import AbstractPanel
from sdnist.gui.windows.metadata.labels import LabelType as LabelT

from sdnist.gui.colors import report_clr

class MessagePanel(AbstractPanel):
    def __init__(self,
                 open_callback: Callable,
                 close_callback: Callable,
                 path_type: str,
                 path: Path,
                 subsection_height: int = 30,
                 pad_x: int = 10,
                 pad_y: int = 10,
                 progress: float = 0,
                 *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.panel.border_width = 0
        self.panel.shape = 'rounded_rectangle'
        self.panel.shape_corner_radius = 15
        self.panel.border_colour = pg.Color(report_clr)
        self.panel.rebuild()
        self.open_callback = open_callback
        self.close_callback = close_callback
        self.path_type = path_type
        self.path = path
        self.progress = progress

        self.pad_x = pad_x
        self.pad_y = pad_y

        self.text_h = subsection_height
        self.progress_h = subsection_height
        self.msg_h = subsection_height
        self.btn_h = subsection_height

        self.text_path = None
        self.progress_bar = None
        self.msg_label = None
        self.open_btn = None
        self.close_btn = None

        self._create()

    def _create(self):
        lbl_w = self.rect.w - 2 * self.pad_x

        text_rect = pg.Rect((self.pad_x, self.pad_y),
                            (lbl_w, self.text_h))
        self.text_path = CustomUITextEntryLine(
            relative_rect=text_rect,
            initial_text=self.path.name,
            manager=self.manager,
            container=self.panel,
            anchors={'left': 'left',
                     'top': 'top'},
            text_end_visible=True,
            editable=False
        )

        msg_y = text_rect.y + text_rect.h + self.pad_y

        msg_rect = pg.Rect((self.pad_x, msg_y),
                           (lbl_w, self.msg_h))
        msg_text = f'NOT STARTED'
        self.msg_label = UILabel(relative_rect=msg_rect,
                                 text=msg_text,
                                 manager=self.manager,
                                 container=self.panel,
                                 anchors={'left': 'left',
                                          'top': 'top'})

        progress_y = msg_y + self.msg_h + self.pad_y

        progress_rect = pg.Rect((self.pad_x, progress_y),
                                (lbl_w, self.progress_h))

        if self.progress < 100:
            self.progress_bar = CustomUIProgress(
                on_finish=self.on_finish,
                relative_rect=progress_rect,
                manager=self.manager,
                container=self.panel,
                visible=1,
                anchors={'left': 'left',
                       'top': 'top'}
            )
            self.progress_bar.set_current_progress(self.progress)
        else:
            self.create_buttons()

    def get_all_elements(self):
        elems = [
            self.panel,
            self.text_path,
            self.progress_bar,
            self.msg_label,
            self.open_btn,
            self.close_btn
        ]

        elems = [e for e in elems if e is not None]

        return elems

    def destroy(self):
        super().destroy()
        if self.text_path is not None:
            self.text_path.kill()
            self.text_path = None
        if self.progress_bar is not None:
            self.progress_bar.kill()
            self.progress_bar = None
        if self.msg_label is not None:
            self.msg_label.kill()
            self.msg_label = None


    def handle_event(self, event: pg.event.Event):
        pass

    def on_finish(self):
        if self.progress_bar:
            self.progress_bar.kill()
            self.progress_bar = None
            self.create_buttons()

    def create_buttons(self):
        btn_y = self.msg_label.relative_rect.y + self.msg_h + self.pad_y
        close_btn_x = self.pad_x
        btn_w = self.rect.w * 0.15

        close_btn_rect = pg.Rect((close_btn_x, btn_y),
                                (btn_w, self.btn_h))
        close_btn_rect.left = -1 * (close_btn_x + btn_w)
        self.close_btn = UICallbackButton(
            relative_rect=close_btn_rect,
            text='CLOSE',
            manager=self.manager,
            container=self.panel,
            anchors={'right': 'right',
                     'top': 'top'},
            callback=self.close_callback,
            object_id=ObjectID(
                class_id="@chip_button",
                object_id="#message_close_button"
            )
        )

        open_btn_x = close_btn_x + btn_w + self.pad_x
        open_btn_rect = pg.Rect((open_btn_x, btn_y),
                                 (btn_w, self.btn_h))
        open_btn_rect.left = -1 * (btn_w * 2 + self.pad_x * 2)
        self.open_btn = UICallbackButton(
            relative_rect=open_btn_rect,
            text='OPEN',
            manager=self.manager,
            container=self.panel,
            anchors={'right': 'right',
                     'top': 'top'},
            callback=self.open_callback,
            object_id=ObjectID(
                class_id="@chip_button",
                object_id="#message_open_button"
            )
        )



