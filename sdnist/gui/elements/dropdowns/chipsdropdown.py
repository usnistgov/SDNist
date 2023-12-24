from typing import Optional, List, Callable
from functools import partial
import pygame as pg
import pygame_gui as pggui

from pygame_gui.core import UIElement
from pygame_gui.elements.ui_window import UIWindow
from pygame_gui.elements.ui_label import UILabel
from pygame_gui.elements.ui_panel import UIPanel
from pygame_gui.core.object_id import ObjectID

from sdnist.gui.elements.buttons.button import UICallbackButton
from sdnist.gui.elements.buttons.chip import ChipButton

from sdnist.gui.elements.selection import CallbackSelectionList

from sdnist.gui.utils import get_text_width


class ChipsDropDown:
    def __init__(self,
                 on_selected_callback: Optional[Callable],
                 rect: pg.Rect,
                 manager: pggui.UIManager,
                 container: any,
                 parent_window: UIWindow,
                 options_list: list,
                 starting_options: List[str],
                 max_text_len: int = 20,
                 *args, **kwargs):
        self.on_selected_callback = on_selected_callback
        self.rect = rect
        self.manager = manager
        self.container = container
        self.parent_window = parent_window
        self.options_list = options_list
        self.starting_options = starting_options
        self.max_text_len = max_text_len

        self.expand_btn_w = 60
        self.more_items_lbl_w = 80
        self.chip_max_w = 200
        self.chip_min_w = 80

        self.pad_x = 3
        self.chips_panel = None
        self.more_items_label = None
        self.expand_btn = None
        self.chips = []
        self.dd: Optional[CallbackSelectionList] = None
        self.dd_visible = False
        self._create()

    def get_elements(self):
        elems = [
            self.chips_panel,
            self.more_items_label,
            self.expand_btn
        ]
        elems = elems + self.chips

        elems = [e for e in elems if e]
        return elems

    def set_options(self, new_options):
        self.options_list = new_options

        self.starting_options = []
        self.update_chips()
        self.close_dropdown()

    def _create(self):
        cp_w = self.rect.w - self.expand_btn_w - self.pad_x
        cp_rect = pg.Rect((self.rect.x, self.rect.y),
                          (cp_w, self.rect.h))
        self.chips_panel = UIPanel(
            relative_rect=cp_rect,
            starting_height=0,
            manager=self.manager,
            container=self.container,
            anchors={'left': 'left',
                     'top': 'top'},
            object_id=ObjectID(class_id='@chips_panel',
                               object_id='#chips_panel')
        )

        self.update_chips()

        exp_btn_x = cp_rect.right + self.pad_x
        exp_btn_y = self.chips_panel.rect.y + 100
        exp_btn_rect = pg.Rect((exp_btn_x, 0),
                               (self.expand_btn_w, self.rect.h))

        self.expand_btn = UICallbackButton(
            callback=self.toggle_dropdown,
            relative_rect=exp_btn_rect,
            text='+',
            manager=self.manager,
            container=self.container,
            object_id=ObjectID(
                class_id='@toolbar_button',
                object_id='#expand_button')
        )

    def destroy(self):
        self.close_dropdown()
        self.chips_panel.kill()
        self.expand_btn.kill()
        self.more_items_label.kill()
        for chip in self.chips:
            chip.kill()

    def toggle_dropdown(self):
        if self.dd:
            self.close_dropdown()
        else:
            self.create_dropdown()
            self.show_dropdown()

    def close_dropdown(self):
        if self.dd:
            self.dd.kill()
            self.dd = None
            self.expand_btn.set_text('+')
            self.dd_visible = False

    def show_dropdown(self):
        if self.dd:
            self.dd.show()
            self.dd_visible = True
            self.expand_btn.set_text('-')

    def create_dropdown(self):
        dd_x = self.container.rect.x - self.parent_window.rect.x \
               + self.rect.x
        dd_y = self.container.rect.y - self.parent_window.rect.y \
            + self.rect.h

        options_h = len(self.options_list) * 25
        dd_h = min(options_h, 200)
        dd_rect = pg.Rect((dd_x,
                           dd_y),
                          (self.rect.w,
                           dd_h))

        self.dd = CallbackSelectionList(
            callback=self.update_selected_value,
            starting_height=4,
            relative_rect=dd_rect,
            item_list=self.options_list,
            manager=self.manager,
            container=self.parent_window,
            parent_element=self.chips_panel,
            anchors={'left': 'left',
                     'top': 'top'},
            default_selection=self.starting_options,
            allow_multi_select=True,
            visible=0,
        )

    def update_selected_value(self, new_values):
        self.starting_options = new_values
        self.update_chips()
        self.on_selected_callback(new_values)

    def remove_chip(self, chip_text):
        if chip_text in self.starting_options:
            self.starting_options.remove(chip_text)
            prev_dd = self.dd
            self.create_dropdown()
            if self.dd_visible:
                self.show_dropdown()
                prev_dd.kill()
                prev_dd = None

            self.update_chips()
            self.on_selected_callback(self.starting_options)

    def update_chips(self):
        for chip in self.chips:
            chip.kill()
        if self.more_items_label:
            self.more_items_label.kill()
            self.more_items_label = None
        self.chips = []

        avail_w = self.chips_panel.rect.w \
            - self.more_items_lbl_w
        used_w = 0

        for i, opt in enumerate(self.starting_options):
            if len(self.chips):
                chip_x = self.chips[-1].relative_rect.x + self.chips[-1].rect.w
            else:
                chip_x = 0

            disp_opt = opt if len(opt) < self.max_text_len \
                else f'{opt[:self.max_text_len]}...'
            disp_opt += '    '
            chip_w = get_text_width(disp_opt, self.manager)
            chip_rect = pg.Rect((chip_x, 0),
                                (chip_w, self.chips_panel.rect.h))
            chip = ChipButton(
                cancel_callback=partial(self.remove_chip, opt),
                relative_rect=chip_rect,
                display_text=disp_opt,
                full_text=opt,
                manager=self.manager,
                container=self.chips_panel,
                anchors={'left': 'left',
                         'top': 'top'}
            )

            used_w += chip.rect.w
            if used_w > avail_w:
                chip.kill()
                break
            self.chips.append(chip)

        lbl_rect = pg.Rect((0, 0),
                           (self.more_items_lbl_w, self.rect.h))
        lbl_rect.x = -1 * lbl_rect.w

        more_items = len(self.starting_options) - len(self.chips)
        more_items_text = f'+{more_items}  ' if more_items else ''
        self.more_items_label = UILabel(
            relative_rect=lbl_rect,
            text=more_items_text,
            manager=self.manager,
            container=self.chips_panel,
            anchors={'right': 'right',
                     'top': 'top'}
        )
        self.more_items_label.text_horiz_alignment = 'right'
        self.more_items_label.rebuild()



