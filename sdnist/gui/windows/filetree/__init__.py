import shutil
from typing import Optional, Tuple, Dict, List
from enum import Enum
from pathlib import Path
from functools import partial
from itertools import chain
import os

import pandas as pd
import pygame_gui as pggui
import pygame as pg

from pygame_gui.elements.ui_button import UIButton
from pygame_gui.elements.ui_scrolling_container \
    import UIScrollingContainer
from pygame_gui.core import ObjectID

from sdnist.gui.windows.filetree.filehelp import (
    get_path_types
)

from sdnist.gui.elements import (
    DirectoryButton,
    FlagButton
)

from sdnist.gui.windows.window import (
    AbstractWindow
)

from sdnist.gui.panels.headers import (
    WindowHeader
)

from sdnist.gui.colors import path_type_colors
from sdnist.gui.helper import PathType
from sdnist.gui.strs import *
from sdnist.gui.constants import window_header_h

from sdnist.gui.handlers.files import FilesTreeHandler
from sdnist.report.helpers import ProgressStatus
from sdnist.report.dataset.target import TargetLoader

class FileTree(AbstractWindow):
    def __init__(self,
                 target_loader: TargetLoader,
                 rect: pg.Rect,
                 manager: pggui.UIManager,
                 directory: str,
                 selected_path: Optional[Path] = None):
        super().__init__(rect, manager)
        self.target_loader = target_loader
        self.directory = Path(directory)
        self.ft_handler = FilesTreeHandler(
            root=self.directory,
            target_loader=self.target_loader
        )
        self.w, self.h = rect.w, rect.h
        self.header_h = window_header_h
        self.font = pg.font.Font(None, 24)
        self.dir_expansion = dict()
        self.buttons = dict()

        if selected_path:
            self.selected = (str(selected_path), None)
        else:
            self.selected = None
        self.selected_path_type = None
        self.selected_path_status = None
        self._create()

    def _create(self):
        header_rect = pg.Rect(0, 0, self.w, self.header_h)
        self.header = WindowHeader(
            title='Files',
            rect=header_rect,
            manager=self.manager,
            container=self.window,
            object_id=ObjectID(
                class_id='@window_header_panel',
                object_id='#main_header_panel'
            )
        )
        self.scroll_rect = pg.Rect(0, self.header_h,
                                   self.w,
                                   self.h - self.header_h)

        self.scroll = UIScrollingContainer(
            relative_rect=self.scroll_rect,
            starting_height=2,
            manager=self.manager,
            container=self.window,
            anchors={
                'left': 'left',
                'right': 'right',
                'top': 'top',
                'bottom': 'bottom'
            }
        )
        self.update_tree()


    def destroy(self):
        self.scroll.kill()

    def handle_event(self, event: pg.event.Event):
        pass

    def update_tree(self):
        if self.selected is None:
            self.selected = (str(self.directory), None)

        for b in self.buttons.values():
            b.kill()
        self.buttons.clear()
        self._draw_files_tree()

        sel_dir = self.selected[0]

        btn = self.buttons[str(sel_dir)]
        self.selected = (self.selected[0], btn)
        btn.select()

    def _draw_files_tree(self, is_expansion=False):
        self.files_ui = dict()
        self.buttons = dict()
        test = True

        def is_directory_empty(directory_path):
            with os.scandir(directory_path) as scan:
                return next(scan, None) is None

        def callback(path: str, btn_ref: UIButton):
            if Path(path).exists():
                if self.selected:
                    self.selected[1].unselect()
                self.selected = (path, btn_ref)

        def get_button_width(text: str):
            btn = UIButton(relative_rect=pg.Rect(0, 0, -1, 0),
                            text=text,
                            manager=self.manager,
                            visible=False)
            w = btn.rect.w
            btn.kill()
            btn = None
            return w

        def draw_subtree(root: Path,
                         level: int,
                         start_y_idx: int):
            # print(root)
            lvl_str = ' ' * level
            lvl_d = dict()
            child_level = level
            i = start_y_idx

            if is_directory_empty(root):
                if self.selected and str(root) == self.selected[0]:
                    self.selected = (str(root.parent), None)
                shutil.rmtree(root)
                return lvl_d, i - 1, child_level - 1

            expansion = True
            path_type = get_path_types(root,
                                       file_handler=self.ft_handler)[0]
            if str(root) in self.dir_expansion:
                expansion = self.dir_expansion[str(root)]
            elif path_type in [PathType.REPORTS,
                               PathType.METAREPORTS,
                               PathType.ARCHIVES,
                               PathType.REPORT,
                               PathType.METAREPORT,
                               PathType.ARCHIVE]:
                expansion = False
                self.dir_expansion[str(root)] = expansion
            else:
                self.dir_expansion[str(root)] = True

            if not is_expansion and self.selected:
                selected_path = str(self.selected[0])
                if (str(root) in selected_path
                        and str(root) != selected_path):
                    expansion = True
                    self.dir_expansion[str(root)] = expansion

            text = f'{root.name}'

            # root button
            btn_x, btn_y = 25 * level, i * 30
            btn_h = 30
            # print(btn_x, btn_y, self.rect.h)
            btn_w = get_button_width(text) + 15
            btn_w += btn_h + DirectoryButton.PAD_X
            root_btn_rect = pg.Rect(btn_x,
                                    btn_y,
                                    btn_w, btn_h)

            # print(f'{"-"*(level + 1)}>{root.name} {(btn_x, btn_y)} '
            #       f'{(btn_w)}')

            path_color = path_type_colors[path_type][PART_1][BACK_COLOR]
            root_btn = DirectoryButton(
                relative_rect=root_btn_rect,
                starting_height=3,
                text=text,
                expanded=expansion,
                selection_callback=partial(callback, str(root)),
                expansion_callback=partial(self.handle_dir_expand, str(root)),
                back_button_color=path_color,
                manager=self.manager,
                container=self.scroll,
                anchors={'left': 'left'},
                object_id=ObjectID(
                    class_id='@filetree_button',
                    object_id='#filetree_directory_button'
                ),
                tool_tip_text=text
            )

            def get_file_sort_codes(f: Path):
                path_type = get_path_types(path=f,
                                           file_handler=self.ft_handler)[0]
                if path_type in [PathType.REPORTS, PathType.METAREPORTS, PathType.ARCHIVES]:
                    return [path_type, 0]
                elif path_type in [PathType.DEID_DATA_DIR]:
                    return [path_type, 1]
                elif path_type in [PathType.DEID_CSV]:
                    return [path_type, 2]
                elif path_type in [PathType.DEID_JSON]:
                    return [path_type, 3]
                elif path_type in [PathType.INDEX]:
                    return [path_type, 4]
                elif path_type in [PathType.CSV]:
                    return [path_type, 5]
                elif path_type in [PathType.JSON]:
                    return [path_type, 6]
                return [path_type, 0]

            self.buttons[str(root.absolute())] = root_btn

            if expansion:
                f_list: List[List] = [[f] + get_file_sort_codes(f)
                          for f in root.iterdir()]
                f_list.sort(key=lambda x: x[2])
                for f, path_type, _ in f_list:
                    if f.is_file() and f.suffix in ['.csv', '.json']:
                        is_csv = f.suffix == '.csv'
                        is_deid_csv = path_type == PathType.DEID_CSV
                        is_index = 'index' in f.name
                        is_deid_json = path_type == PathType.DEID_JSON

                        path_color = path_type_colors[path_type][PART_1][BACK_COLOR]
                        i += 1
                        text = f.name
                        f_btn_x = btn_x + 30
                        f_btn_y = i * 30
                        btn_w = get_button_width(text) + 60
                        file_btn_rect = pg.Rect(f_btn_x,
                                                f_btn_y,
                                                btn_w, 30)

                        file_btn = FlagButton(
                            file_path=f,
                            callback=None,
                            back_button_color=path_color,
                            relative_rect=file_btn_rect,
                            starting_height=3,
                            text=text,
                            manager=self.manager,
                            container=self.scroll,
                            anchors={'left': 'left'}
                        )
                        file_btn.callback = partial(callback, str(f), file_btn)
                        if not is_csv and not is_deid_json:
                            file_btn.disable()
                        if is_csv and not is_index and not is_deid_csv:
                            # file_btn.back_btn.colours['normal_bg'] = pg.Color("#24272b")
                            # file_btn.front_btn.colours['normal_bg'] = pg.Color('red')
                            file_btn.rebuild()
                        self.buttons[str(f.absolute())] = file_btn

                    elif f.is_dir():
                        lvl_d, last_i, child_level = draw_subtree(f, level + 1, i + 1)
                        i = last_i
                # i += 1
            return lvl_d, i, child_level

        self.files_ui, final_y, max_level = draw_subtree(
            self.directory, 0, 0
        )

        if is_expansion and self.selected:
            sel_path = str(self.selected[0])
            if sel_path in self.buttons:
                btn = self.buttons[str(self.selected[0])]
                btn.select()
                self.selected = (sel_path, btn)

        # final y is index of file button
        # final x is actual max width of file button
        surface_y = final_y * 30 + 30
        max_btn_w = max([btn.orig_rect.w
                         for btn in self.buttons.values()])
        surface_x = max_btn_w + max_level * 30
        # print('MAX BTN W', max_btn_w, 'MAX LVL: ', max_level)
        self.scroll.set_scrollable_area_dimensions((surface_x,
                                                    surface_y))
        # self.panel.set_minimum_dimensions((100, 100))
        if test:
            buttons = [b.get_buttons()
                       if isinstance(b, FlagButton)
                       else [b]
                       for b in self.buttons.values()]
            buttons = list(chain(*buttons))
        else:
            buttons = list(self.buttons.values())
        focus_set = set(buttons + [self.scroll])
        if self.scroll.vert_scroll_bar:
            self.scroll.vert_scroll_bar.set_focus_set(focus_set)

        if self.scroll.horiz_scroll_bar:
            self.scroll.horiz_scroll_bar.set_focus_set(focus_set)

    def handle_dir_expand(self, dir_path: str):
        if dir_path in self.dir_expansion:
            if self.dir_expansion[dir_path]:
                self.dir_expansion[dir_path] = False
            else:
                self.dir_expansion[dir_path] = True

            for btn_name, b in self.buttons.items():
                b.kill()
            self._draw_files_tree(is_expansion=True)


    def compute_selected_file_type(self, progress: ProgressStatus) -> \
        Optional[Tuple[PathType, Dict]]:
        if not self.selected:
            return None

        path = Path(self.selected[0])
        path_type, path_status = get_path_types(path, progress,
                                                self.ft_handler)
        self.selected_path_type = path_type
        self.selected_path_status = path_status

        return self.selected_path_type, self.selected_path_status

