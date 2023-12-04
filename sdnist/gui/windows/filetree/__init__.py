from typing import Optional, Tuple, Dict, List
from enum import Enum
from pathlib import Path
from functools import partial
from itertools import chain

import pygame_gui as pggui
import pygame as pg

from pygame_gui.elements.ui_panel import UIPanel
from pygame_gui.elements.ui_window import UIWindow
from pygame_gui.elements.ui_button import UIButton
from pygame_gui.elements.ui_scrolling_container \
    import UIScrollingContainer
from pygame_gui.core import ObjectID

from sdnist.gui.elements import (
    FileButton,
    DirectoryButton,
    FlagButton
)
from sdnist.gui.constants import (
    REPORT_DIR_PREFIX,
    METAREPORT_DIR_PREFIX,
    ARCHIVE_DIR_PREFIX
)
from sdnist.gui.windows.window import (
    AbstractWindow
)
from sdnist.gui.windows.filetree.filehelp import (
    count_path_types)
from sdnist.gui.panels.headers import (
    WindowHeader
)

from sdnist.gui.colors import path_type_colors
from sdnist.gui.helper import PathType
from sdnist.gui.strs import *
from sdnist.gui.constants import window_header_h

class FileTree(AbstractWindow):
    def __init__(self,
                 rect: pg.Rect,
                 manager: pggui.UIManager,
                 directory: str,
                 selected_path: Optional[Path] = None):
        super().__init__(rect, manager)
        self.directory = Path(directory)
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

    def _draw_files_tree(self):
        self.files_ui = dict()
        self.buttons = dict()
        test = True

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

        def draw_subtree(root: Path, level: int,
                         start_y_idx: int):
            # print(root)
            lvl_str = ' ' * level
            lvl_d = dict()
            child_level = level
            i = start_y_idx

            expansion = True
            path_type = self.compute_filetype(root)[0]
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
                path_type = self.compute_filetype(f)[0]
                if path_type in [PathType.REPORTS, PathType.METAREPORTS, PathType.ARCHIVES]:
                    return [path_type, 0]
                elif path_type in [PathType.DEID_DATA_DIR]:
                    return [path_type, 1]
                elif path_type in [PathType.CSV]:
                    return [path_type, 2]
                elif path_type in [PathType.JSON]:
                    return [path_type, 3]
                elif path_type in [PathType.INDEX]:
                    return [path_type, 4]
                return [path_type, 0]

            self.buttons[str(root.absolute())] = root_btn
            if expansion:
                f_list: List[List] = [[f] + get_file_sort_codes(f)
                          for f in root.iterdir()]
                f_list.sort(key=lambda x: x[2])
                for f, path_type, _ in f_list:
                    if f.is_file() and f.suffix in ['.csv', '.json']:
                        path_color = path_type_colors[path_type][PART_1][BACK_COLOR]
                        i += 1
                        text = f.name
                        f_btn_x = btn_x + 30
                        f_btn_y = i * 30
                        btn_w = get_button_width(text) + 60
                        file_btn_rect = pg.Rect(f_btn_x,
                                                f_btn_y,
                                                btn_w, 30)
                        file_type = f.suffix[1:]


                        # print(f'{"-" * (level + 1)*2}-@>{f.name} {(btn_x, btn_y)}'
                        #       f'{(btn_w)}')
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
                        self.buttons[str(f.absolute())] = file_btn
                    elif f.is_dir():
                        lvl_d, last_i, child_level = draw_subtree(f, level + 1, i + 1)
                        i = last_i
                # i += 1
            return lvl_d, i, child_level

        self.files_ui, final_y, max_level = draw_subtree(
            self.directory, 0, 0
        )

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
            self._draw_files_tree()


    def compute_selected_file_type(self) -> \
        Optional[Tuple[PathType, Dict]]:
        if not self.selected:
            return None

        path = Path(self.selected[0])
        path_type, path_status = self.compute_filetype(path)
        self.selected_path_type = path_type

        return self.selected_path_type, path_status

    @staticmethod
    def compute_filetype(path: Path) -> \
        Optional[Tuple[PathType, Dict]]:

        path_status = dict()
        path_type = None
        if path.is_file():
            if path.suffix == '.csv' and 'index' not in path.name:
                path_type = PathType.CSV
                metadata_path = Path(str(path).replace('.csv', '.json'))
                path_status[METADATA] = metadata_path.exists()
            elif path.suffix == '.json':
                path_type = PathType.JSON
            elif path.suffix == '.csv' and 'index' in path.name:
                path_type = PathType.INDEX
        elif path.is_dir():
            if REPORT_DIR_PREFIX in str(path):
                path_type = PathType.REPORT
            elif METAREPORT_DIR_PREFIX in str(path):
                path_type = PathType.METAREPORT
            elif ARCHIVE_DIR_PREFIX in str(path):
                path_type = PathType.ARCHIVE
            elif METAREPORTS.lower() in str(path):
                path_type = PathType.METAREPORTS
            elif REPORTS.lower() in str(path):
                path_type = PathType.REPORTS
            elif ARCHIVES in str(path):
                path_type = PathType.ARCHIVES
            else:
                path_type = PathType.DEID_DATA_DIR
                path_type_counts = count_path_types(path)
                counts = path_type_counts
                index_path = Path(path, 'index.csv')
                path_status[INDEX_FILES] = index_path.exists()
                path_status[DEID_CSV_FILES] = counts[DEID_CSV_FILES] > 0
                path_status[REPORTS] = counts[REPORTS] > 0

        return path_type, path_status

