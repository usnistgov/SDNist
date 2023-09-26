from typing import Dict
from pathlib import Path
from functools import partial

import pygame_gui as pggui
import pygame as pg
from pygame_gui.elements.ui_panel import UIPanel
from pygame_gui.elements.ui_window import UIWindow
from pygame_gui.elements.ui_button import UIButton
from pygame_gui.elements.ui_scrolling_container \
    import UIScrollingContainer
from pygame_gui.core import ObjectID

from sdnist.gui.constants import REPORT_DIR_PREFIX


# Custom button class
class FileTreeButton(UIButton):
    def __init__(self, callback, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.callback = callback

    def process_event(self, event):
        response = super().process_event(event)
        if event.type == pg.USEREVENT:
            if event.user_type == pggui.UI_BUTTON_PRESSED \
                    and event.ui_element == self:
                self.callback(self)
                if self.is_selected:
                    self.unselect()
                else:
                    self.select()
        return response


class SidePanel:
    def __init__(self, left: int, top: int,
                 manager: pggui.UIManager,
                 directory: str):
        self.manager = manager
        self.directory = Path(directory)
        self.w, self.h = self.manager.window_resolution
        self.left, self.top = left, top

        self.window_rect = pg.Rect(0, self.top,
                                   int(self.w * 0.2),
                                   self.h - self.top)

        self.window = UIWindow(rect=self.window_rect,
                               manager=manager,
                               window_display_title="Files",
                               draggable=False,
                               resizable=True)
        self.panel_rect = pg.Rect(0, 0,
                                  int(self.w * 0.2),
                                  self.h - self.top)

        self.panel = UIPanel(relative_rect=self.panel_rect,
                             starting_height=1,
                             manager=manager,
                             container=self.window)

        self.scroll_rect = pg.Rect(0, 0,
                                  int(self.w * 0.2),
                                  self.h - self.top - 20)
        self.scroll = UIScrollingContainer(relative_rect=self.scroll_rect,
                                           starting_height=2,
                                           manager=manager,
                                           container=self.panel,
                                           anchors={'left': 'left',
                                                     'right': 'right',
                                                     'top': 'top',
                                                     'bottom': 'bottom'})

        # self.files = self._create_files_tree()
        self._draw_files_tree()

        self.selected = None

    def _draw_files_tree(self):
        self.files_ui = dict()

        def callback(file: str, btn_ref: FileTreeButton):
            if Path(file).exists():
                if self.selected:
                    self.selected[1].unselect()
                self.selected = (file, btn_ref)
        self.btns = []

        def draw_subtree(root: Path, level: int, start_y_idx: int):
            lvl_str = ' ' * level
            lvl_d = dict()
            child_level = level
            i = start_y_idx

            # root button
            btn_x, btn_y = 10 * level, i * 30
            file_btn_rect = pg.Rect(btn_x,
                                    btn_y,
                                    -1, 30)

            root_btn = FileTreeButton(relative_rect=file_btn_rect,
                                      starting_height=3,
                                      text=root.name,
                                      callback=partial(callback, str(root)),
                                      manager=self.manager,
                                      container=self.scroll,
                                      anchors={'left': 'left'},
                                      object_id=ObjectID(class_id='@file_tree_button',
                                                         object_id='#directory_button'))
            self.btns.append(root_btn)
            for f in root.iterdir():
                if f.is_file() and f.suffix in ['.csv', '.json']:
                    # lvl_d[k] = dict()
                    json_file_btn_id = '#json_file_button'
                    csv_file_btn_id = '#csv_file_button'

                    i += 1
                    btn_x, btn_y = 10 * (level + 1), i * 30
                    file_btn_rect = pg.Rect(btn_x,
                                            btn_y,
                                            -1, 30)
                    file_type = f.suffix[1:]
                    btn_id = json_file_btn_id if file_type == 'json' else csv_file_btn_id
                    obj_id = ObjectID(class_id='@file_tree_button',
                                      object_id=btn_id)
                    file_btn = FileTreeButton(relative_rect=file_btn_rect,
                                              starting_height=3,
                                              text=f.name,
                                              callback=partial(callback, str(f)),
                                              manager=self.manager,
                                              container=self.scroll,
                                              anchors={'left': 'left'},
                                              object_id=obj_id)
                    self.btns.append(file_btn)
                elif f.is_dir() and not f.name.startswith(REPORT_DIR_PREFIX):
                    lvl_d, last_i, child_level = draw_subtree(f, level + 1, i + 1)
                    i = last_i
                # i += 1
            return lvl_d, i, child_level

        self.files_ui, final_y, max_level = draw_subtree(self.directory, 0, 0)

        # final y is index of file button
        # final x is actual max width of file button
        surface_y = final_y * 30 + 30
        max_btn_w = max([btn.relative_rect.width for btn in self.btns])
        surface_x = max_btn_w + max_level * 30
        # print('MAX BTN W', max_btn_w, 'MAX LVL: ', max_level)
        self.scroll.set_scrollable_area_dimensions((surface_x,
                                                    surface_y))
        self.panel.set_minimum_dimensions((100, 100))
        # print('Total btns: ', len(self.btns))
        focus_set = set(self.btns + [self.scroll])
        if self.scroll.vert_scroll_bar:
            # self.scroll.vert_scroll_bar.set_scroll_from_start_percentage(0.5)
            self.scroll.vert_scroll_bar.set_focus_set(focus_set)

        if self.scroll.horiz_scroll_bar:
            self.scroll.horiz_scroll_bar.set_focus_set(focus_set)

