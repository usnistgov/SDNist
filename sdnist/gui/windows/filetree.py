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

from sdnist.gui.elements import FileButton, DirectoryButton
from sdnist.gui.constants import REPORT_DIR_PREFIX
from sdnist.gui.windows.window import AbstractWindow


class FileTree(AbstractWindow):
    def __init__(self,
                 rect: pg.Rect,
                 manager: pggui.UIManager,
                 directory: str):
        super().__init__(rect, manager)
        self.directory = Path(directory)
        self.w, self.h = rect.w, rect.h
        self.font = pg.font.Font(None, 24)  # Use default font, size 24
        self.dir_expansion = dict()
        self.buttons = dict()
        self.selected = None
        self._create()

    def _create(self):
        self.scroll_rect = pg.Rect(0, 0,
                                   self.w,
                                   self.h - 20)

        self.scroll = UIScrollingContainer(relative_rect=self.scroll_rect,
                                           starting_height=2,
                                           manager=self.manager,
                                           container=self.window,
                                           anchors={'left': 'left',
                                                    'right': 'right',
                                                    'top': 'top',
                                                    'bottom': 'bottom'})
        self._draw_files_tree()

    def destroy(self):
        self.scroll.kill()

    def handle_event(self, event: pg.event.Event):
        pass

    def _draw_files_tree(self):
        self.files_ui = dict()
        self.buttons = dict()

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
            if str(root) in self.dir_expansion:
                expansion = self.dir_expansion[str(root)]
            else:
                self.dir_expansion[str(root)] = True

            text = f'{root.name}'

            # root button
            btn_x, btn_y = 10 * level, i * 30
            btn_h = 30
            # print(btn_x, btn_y, self.rect.h)
            btn_w = get_button_width(text)
            btn_w += btn_h + DirectoryButton.PAD_X
            file_btn_rect = pg.Rect(btn_x,
                                    btn_y,
                                    btn_w, btn_h)

            # print(f'{"-"*(level + 1)}>{root.name} {(btn_x, btn_y)} '
            #       f'{(btn_w)}')

            root_btn = DirectoryButton(relative_rect=file_btn_rect,
                                       starting_height=3,
                                       text=text,
                                       expanded=expansion,
                                       selection_callback=partial(callback, str(root)),
                                       expansion_callback=partial(self.handle_dir_expand, str(root)),
                                       manager=self.manager,
                                       container=self.scroll,
                                       anchors={'left': 'left'},
                                       object_id=ObjectID(class_id='@filetree_button',
                                                          object_id='#filetree_directory_button'))

            self.buttons[str(root)] = root_btn
            if expansion:
                for f in root.iterdir():
                    if f.is_file() and f.suffix in ['.csv', '.json']:
                        # lvl_d[k] = dict()
                        json_file_btn_id = '#filetree_jsonfile_button'
                        csv_file_btn_id = '#filetree_csvfile_button'

                        i += 1
                        text = f.name
                        btn_x, btn_y = 10 * (level + 1), i * 30
                        btn_w = get_button_width(text)
                        file_btn_rect = pg.Rect(btn_x,
                                                btn_y,
                                                btn_w, 30)
                        file_type = f.suffix[1:]
                        btn_id = json_file_btn_id if file_type == 'json' else csv_file_btn_id
                        obj_id = ObjectID(class_id='@filetree_button',
                                          object_id=btn_id)

                        # print(f'{"-" * (level + 1)*2}-@>{f.name} {(btn_x, btn_y)}'
                        #       f'{(btn_w)}')

                        file_btn = FileButton(relative_rect=file_btn_rect,
                                              starting_height=3,
                                              text=text,
                                              callback=None,
                                              manager=self.manager,
                                              container=self.scroll,
                                              anchors={'left': 'left'},
                                              object_id=obj_id)
                        file_btn.callback = partial(callback, str(f), file_btn)
                        self.buttons[str(f)] = file_btn
                    elif f.is_dir() and not f.name.startswith(REPORT_DIR_PREFIX):

                        lvl_d, last_i, child_level = draw_subtree(f, level + 1, i + 1)
                        i = last_i
                # i += 1
            return lvl_d, i, child_level

        self.files_ui, final_y, max_level = draw_subtree(self.directory, 0, 0)

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
        # print('Total btns: ', len(self.btns))
        focus_set = set(list(self.buttons.values()) + [self.scroll])
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

            for bname, b in self.buttons.items():
                b.kill()
            self._draw_files_tree()
