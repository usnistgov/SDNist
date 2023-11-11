from pathlib import Path
import pygame as pg
import pygame_gui as pggui

from pygame_gui.windows import \
    UIFileDialog
from pygame_gui.elements.ui_panel import UIPanel
from pygame_gui.elements.ui_button import UIButton
from pygame_gui.elements.ui_window import UIWindow
from pygame_gui.elements.ui_label import UILabel
from pygame_gui.elements.ui_text_entry_line import \
    UITextEntryLine

from sdnist.gui.panels.panel import AbstractPanel
from sdnist.gui.elements.textline import CustomUITextEntryLine
from sdnist.gui.elements.buttons import UICallbackButton

from sdnist.gui.windows import DoneWindow

# title = 'Load De-identified Data Directory'


class LoadDeidData(AbstractPanel):
    def __init__(self,
                 done_button_visible=False,
                 done_button_callback=None,
                 *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.gui_data_path = Path(Path.cwd(), 'gui_data')
        self.label = None
        self.path_text = None
        self.load_button = None
        self.base = None
        self.done_button_visible = done_button_visible
        self.done_button_callback = done_button_callback
        self.done_window = None

        self.file_dialog = None
        self.picked_path = None
        if self.data and Path(self.data).exists():
            self.picked_path = Path(self.data)
        self._create()

    def _create(self):
        if self.container is None:
            window_rect = pg.Rect(self.rect.w//2, self.rect.h//2,
                                  self.rect.w, self.rect.h)
            self.base = UIWindow(rect=window_rect,
                                 manager=self.manager,
                                 window_display_title=
                                 'Load De-identified Data Directory',
                                 draggable=True,
                                 resizable=True)
            super().destroy()
        else:
            self.base = self.panel

        # create UILabel with text Select Directory Containing
        # De-identified Data csv files
        label_h = int(self.rect.h * 0.3)
        label_rect = pg.Rect((0, label_h), (-1, 50))
        self.label = UILabel(relative_rect=label_rect,
                             container=self.base,
                             parent_element=self.base,
                             text='Select a directory that contains '
                                   'de-identified data csv files',
                             manager=self.manager,
                             anchors={'centerx': 'centerx',
                                      'top': 'top'})

        # Create UITextEntryLine for user to enter path
        # under the path_text element
        text_w = int(self.rect.w * 0.6)
        load_btn_w = 200

        text_x = (self.rect.w - text_w - load_btn_w - 2*10)//2 + 10
        text_rect = pg.Rect((text_x, label_h + 50), (text_w, 50))
        init_text = str(self.picked_path) if self.picked_path else ''

        self.path_text = CustomUITextEntryLine(on_click=None,
                                             relative_rect=text_rect,
                                             container=self.base,
                                             parent_element=self.base,
                                             manager=self.manager,
                                             anchors={'left': 'left',
                                                      'top': 'top'},
                                             initial_text=init_text,
                                             text_end_visible=True)
        # Create UIButton for user to load data
        # next to the text entry line
        load_btn_x = text_w + text_x + 10
        button_rect = pg.Rect((load_btn_x, label_h + 50), (load_btn_w, 50))
        self.load_button = UIButton(relative_rect=button_rect,
                                    container=self.base,
                                    parent_element=self.base,
                                    text='Select Directory',
                                    manager=self.manager,
                                    anchors={'top': 'top',
                                             'left': 'left'})

        if self.done_button_visible:
            done_btn_w = 200
            done_btn_h = 50
            done_btn_x = int(self.rect.w * 0.5) - done_btn_w//2
            done_btn_y = self.rect.h - 100

            button_rect = pg.Rect((done_btn_x, done_btn_y),
                                  (done_btn_w, done_btn_h))
            self.done_button = UICallbackButton(
                                        callback=self.done_button_callback,
                                        relative_rect=button_rect,
                                        container=self.base,
                                        parent_element=self.base,
                                        text='DONE',
                                        manager=self.manager,
                                        anchors={'top': 'top',
                                                 'left': 'left'})

    def destroy(self):
        super().destroy()
        if isinstance(self.base, UIWindow):
            self.base.kill()
            self.base = None
        if self.label:
            self.label.kill()
            self.label = None
        if self.path_text:
            self.path_text.kill()
            self.path_text = None
        if self.load_button:
            self.load_button.kill()
            self.load_button = None

    def handle_event(self, event: pg.event.Event):
        if event.type == pg.USEREVENT:
            if event.user_type == pggui.UI_WINDOW_CLOSE:
                if event.ui_element == self.base:
                    if self.done_button_callback:
                        self.done_button_callback(save_path=False)
            if event.user_type == pggui.UI_BUTTON_PRESSED:
                if event.ui_element == self.load_button:
                    # Create a file dialog
                    self.file_dialog = UIFileDialog(rect=pg.Rect(200, 150, 400, 300),
                                                    manager=self.manager,
                                                    window_title="Select Directory with Died Data",
                                                    initial_file_path=str(self.gui_data_path),
                                                    allow_picking_directories=True,
                                                    allow_existing_files_only=False,
                                                    allowed_suffixes={".csv", ".json"})
                    self.load_button.disable()
            elif event.user_type == pggui.UI_WINDOW_CLOSE:
                # When file dialog is closed or cancelled
                if isinstance(event.ui_element, UIFileDialog):
                    self.load_button.enable()
            # if picked path is wrong show error message on UIFileDialog
        elif event.type == pggui.UI_FILE_DIALOG_PATH_PICKED:
            self.picked_path = event.text
            if self._check_picked_path():
                self.file_dialog.kill()
                self.file_dialog = None
                if self.path_text:
                    self.path_text.set_text(self.picked_path)
                self.load_button.enable()
            else:
                # TODO: FIX THIS. UIFileDialog does not show error message and close
                # TODO: after emitting UI_FILE_DIALOG_PATH_PICKED event
                self.picked_path = None
                self.file_dialog.error_message = "Please select a valid directory or file"
                self.load_button.enable()

    def _check_picked_path(self) -> bool:
        path = Path(self.picked_path)
        if not path.exists():
            return False

        if path.is_dir():
            # check recursively if there is any csv file using glob
            csv_files = list(path.glob('**/*.csv'))
            if len(csv_files) > 0:
                return True
        elif path.is_file():
            if path.suffix == '.csv':
                return True
        return False
