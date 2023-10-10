from typing import Optional
import pygame_gui as pggui
import pygame as pg
from functools import partial

from pygame_gui.elements.ui_window import UIWindow
from pygame_gui.elements.ui_button import UIButton
from pygame_gui.elements.ui_label import UILabel
from pygame_gui.elements.ui_panel import UIPanel
from pygame_gui.elements.ui_text_entry_line import UITextEntryLine
from pygame_gui.elements.ui_selection_list import UISelectionList

from sdnist.gui.elements.textline import CustomUITextEntryLine

from sdnist.gui.elements.button import UICallbackButton
from sdnist.gui.elements.selection import CallbackSelectionList
from sdnist.gui.elements import CustomUIPanel
from sdnist.gui.panels import AbstractPanel
from sdnist.gui.windows.metadata.labels import LabelType as LabelT


class MetadataFormField(AbstractPanel):
    def __init__(self,
                 rect: pg.Rect,
                 manager: pggui.UIManager,
                 container: any,
                 label_name: str,
                 label_value: Optional[str],
                 label_type: LabelT,
                 is_editable: bool = False,
                 is_required: bool = False,
                 options: Optional[list] = None):
        super().__init__(rect, manager, container=container)
        self.label_name = label_name
        self.label_value = label_value \
            if label_value else ''
        self.text_in = None
        self.label_type = label_type
        self.is_editable = is_editable
        self.is_required = is_required
        self.options = options
        self.is_dropdown = True if self.label_type in \
                                   [LabelT.DROPDOWN, LabelT.MULTI_DROPDOWN] \
                                else False
        self.multiselect = True if self.label_type == LabelT.MULTI_DROPDOWN \
            else False

        self.input_rect = None
        self.inp_btn = None
        self.panel = None
        self.dropdown = None
        self.selected_val = None
        self.on_change = None
        # assign a callback to this variable
        self.on_selected_val_change = None
        self._create()

    def _create(self):
        # create panel
        self.panel = CustomUIPanel(
                             callback=partial(self.test_panel_callback),
                             relative_rect=self.rect,
                             container=self.container,
                             starting_height=0,
                             manager=self.manager,
                             anchors={'left': 'left',
                                      'top': 'top'})
        self.panel.on_hovered()
        lbl_w = self.rect.w * 0.3
        lbl_rect = pg.Rect((0, 0), (lbl_w, self.rect.h))
        label = UILabel(relative_rect=lbl_rect,
                        container=self.panel,
                        parent_element=self.panel,
                        text=self.label_name.capitalize(),
                        manager=self.manager,
                        anchors={'left': 'left',
                                 'top': 'top'})
        # input width
        inp_w = self.rect.w * 0.7
        if self.label_type in [LabelT.STRING, LabelT.INT, LabelT.FLOAT]:
            self.input_rect = pg.Rect((lbl_rect.right, 0), (inp_w, self.rect.h))

            self.text_in = CustomUITextEntryLine(on_click=None,
                                                 on_change=self.on_change,
                                                 editable=self.is_editable,
                                                 relative_rect=self.input_rect ,
                                                 container=self.panel,
                                                 parent_element=self.panel,
                                                 manager=self.manager,
                                                 anchors={'left': 'left',
                                                           'top': 'top'},
                                                initial_text=self.label_value)
        elif self.label_type in [LabelT.DROPDOWN, LabelT.MULTI_DROPDOWN]:
            # dropdown input width
            d_in_w = inp_w * 0.9
            d_in_btn_w = inp_w * 0.1

            if self.label_value and self.label_value in self.options:
                self.selected_val = self.label_value

            self.input_rect  = pg.Rect((lbl_rect.right, 0), (d_in_w, self.rect.h))
            self.text_in = CustomUITextEntryLine(on_click=None,
                                                 on_change=self.on_change,
                                                 editable=self.is_editable,
                                                 relative_rect=self.input_rect,
                                                 container=self.panel,
                                                 parent_element=self.panel,
                                                 manager=self.manager,
                                                 anchors={'left': 'left',
                                                           'top': 'top'},
                                                 initial_text=self.label_value)

            inp_btn_rect = pg.Rect((self.input_rect .right, 0),
                                   (d_in_btn_w, self.rect.h))

            self.inp_btn = UICallbackButton(
                               callback=None,
                               relative_rect=inp_btn_rect,
                               container=self.panel,
                               parent_element=self.panel,
                               manager=self.manager,
                               text='+',
                               anchors={'left': 'left',
                                        'top': 'top'})
        elif self.label_type in [LabelT.LONG_STRING]:
            self.input_rect = pg.Rect((lbl_rect.right, 0), (inp_w, self.rect.h))

            self.text_in = CustomUITextEntryLine(on_click=None,
                                                 on_change=self.on_change,
                                                 relative_rect=self.input_rect ,
                                                 container=self.panel,
                                                 parent_element=self.panel,
                                                 manager=self.manager,
                                                 anchors={'left': 'left',
                                                           'top': 'top'},
                                                 initial_text=self.label_value)

    def test_panel_callback(self):
        print(self.label_name, 'panel hovered')

    def destroy(self):
        pass

    def handle_event(self, event: pg.event.Event):
        pass

    def create_selection_list(self):
        ir = self.input_rect
        dr_h = len(self.options) * self.rect.h

        dr_h = dr_h if dr_h < self.container.rect.h * 0.3 \
            else self.container.rect.h * 0.3
        if self.rect.y > self.container.rect.h * 0.6:
            dr = pg.Rect((ir.x + self.rect.x,
                          self.rect.y - dr_h),
                         (ir.w, dr_h))
        else:
            dr = pg.Rect((ir.x + self.rect.x,
                          self.rect.y + ir.h),
                         (ir.w, dr_h))

        if self.selected_val and self.multiselect:
            default_val = self.selected_val.split(', ')
        else:
            default_val = self.selected_val
        self.dropdown = CallbackSelectionList(
                                        callback=self.set_value,
                                        starting_height=1,
                                        relative_rect=dr,
                                        container=self.container,
                                        parent_element=self.container,
                                        manager=self.manager,
                                        item_list=self.options,
                                        allow_multi_select=self.multiselect,
                                        anchors={'left': 'left',
                                                 'top': 'top'},
                                        default_selection=default_val)
        if self.inp_btn:
            self.inp_btn.set_text('-')
        print('created')

    def destroy_selection_list(self):
        if self.dropdown:
            self.dropdown.kill()
            self.dropdown = None
            if self.inp_btn:
                self.inp_btn.set_text('+')
            print('destroyed')

    def set_value(self, value: any):
        if self.multiselect:
            value = ', '.join(value)

        prev_selected = self.selected_val
        self.selected_val = value
        if prev_selected != self.selected_val:
            if self.on_selected_val_change:
                self.on_selected_val_change(self.selected_val)
        self.text_in.set_text(value)

        if not self.multiselect:
            self.destroy_selection_list()
