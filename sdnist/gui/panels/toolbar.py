from typing import Callable, Dict
import pygame as pg
import pygame_gui as pggui

from pygame_gui.core import ObjectID
from pygame_gui.elements.ui_panel import UIPanel
from pygame_gui.elements.ui_label import UILabel

from sdnist.gui.windows.filetree.filehelp import IS_BUSY
from sdnist.gui.panels.panel import AbstractPanel
from sdnist.gui.elements import UICallbackButton

from sdnist.gui.helper import PathType
from sdnist.gui.handlers.window import METAREPORT_FILTER

from sdnist.gui.strs import *

OPEN_METADATA_BTN = 'Open MetaData'
CREATE_METADATA_BTN = 'Create MetaData'
SAVE_METADATA_BTN = 'Save MetaData'
CREATE_REPORT_BTN = 'Create Report'
CREATE_REPORTS_BTN = 'Create Reports'
CREATE_INDEX_BTN = 'Create Index'
CREATE_ARCHIVE_BTN = 'Create Archive'
CREATE_METAREPORT_BTN = 'Create Metareport'


class ToolBar(AbstractPanel):
    def __init__(self, *args, **kwargs):
        kwargs['starting_height'] = 0
        kwargs['object_id'] = ObjectID(class_id='@toolbar_panel',
                                       object_id='#toolbar_panel')
        super().__init__(*args, **kwargs)
        self.button_names = []
        self.button_enabled = []
        self.buttons = dict()
        self.last_clicked_name = None
        self._create()

    def set_callback(self, btn_name: str,
                     callback: Callable):
        def wrapper():
            self.last_clicked_name = btn_name
            return callback()

        if btn_name not in self.buttons:
            return
        btn = self.buttons[btn_name]
        btn.callback = wrapper

    def _create(self):
        self.create_buttons()

    def destroy(self):
        super().destroy()
        self.destroy_buttons()

    def destroy_buttons(self):
        for bn, b in self.buttons.items():
            b.kill()
            self.buttons[bn] = None
        self.buttons.clear()

    def create_buttons(self):
        def empty():
            return
        net_width = 0

        for btn_name in self.button_names[::-1]:
            btn_enabled = self.button_enabled[self.button_names.index(btn_name)]
            btn_rect = pg.Rect((0, 0), (170, self.rect.h * 0.95))
            btn_rect.right = -1 * net_width
            btn = UICallbackButton(relative_rect=btn_rect,
                                   callback=empty,
                                   text=btn_name,
                                   container=self.panel,
                                   parent_element=self.panel,
                                   manager=self.manager,
                                   anchors={'right': 'right',
                                            'centery': 'centery'},
                                   object_id=ObjectID(
                                        class_id="@toolbar_button",
                                        object_id="#toolbar_ready_button"
                                   ))
            if not btn_enabled:
                btn.disable()

            net_width += btn.relative_rect.width
            self.buttons[btn_name] = btn

    def handle_event(self, event: pg.event.Event):
        pass

    def update_buttons(self, path_type: PathType, path_status: Dict):
        self.destroy_buttons()
        self.button_names = []
        self.button_enabled = []
        is_metareport_filter_open = path_status.get(METAREPORT_FILTER, False)
        has_non_num_reports = path_status.get(NUMERICAL_METRIC_RESULTS, False)

        if path_type == PathType.CSV:
            if METADATA in path_status:
                if path_status[METADATA]:
                    self.button_names.append(OPEN_METADATA_BTN)
                    self.button_enabled.append(True)
                else:
                    self.button_names.append(CREATE_METADATA_BTN)
                    self.button_enabled.append(True)
                self.button_names.append(CREATE_REPORT_BTN)
                self.button_enabled.append(True)
            else:
                self.button_names = [CREATE_METADATA_BTN,
                                     CREATE_REPORT_BTN]
                self.button_enabled = [True, True]
        elif path_type == PathType.JSON:
            self.button_names = [CREATE_REPORT_BTN, SAVE_METADATA_BTN]
            self.button_enabled = [True, True]
        elif path_type == PathType.DEID_DATA_DIR:
            create_index = False
            create_report = False
            deid_count = path_status.get(DEID_CSV_FILES, 0)
            reports_count = path_status.get(REPORTS, 0)
            index_count = path_status.get(INDEX_FILES, 0)
            metadata_count = path_status.get(META_DATA_FILES, 0)

            deid_exist = deid_count > 0
            reports_exist = reports_count > 0
            index_exist = index_count > 0
            deid_without_metadata = metadata_count < deid_count

            create_report =(
                deid_exist
                and deid_count >= metadata_count
                and (deid_count > 1
                     or (deid_count == 1
                         and not deid_without_metadata)
                     )
                )

            if reports_exist and not index_exist:
                create_index = True
            if deid_without_metadata:
                self.button_names.append(CREATE_METADATA_BTN)
                self.button_enabled.append(True)
            if create_index:
                self.button_names.append(CREATE_INDEX_BTN)
                self.button_enabled.append(True)
            elif index_exist:
                self.button_names.extend([CREATE_ARCHIVE_BTN])
                self.button_enabled.append(True)
                if has_non_num_reports and not is_metareport_filter_open:
                    self.button_names.append(CREATE_METAREPORT_BTN)
                    self.button_enabled.append(True)
            if create_report:
                self.button_names.append(CREATE_REPORTS_BTN)
                self.button_enabled.append(True)
        elif path_type == PathType.INDEX:
            self.button_names = [CREATE_ARCHIVE_BTN]
            self.button_enabled = [True]
            has_non_num_reports = path_status.get(NUMERICAL_METRIC_RESULTS, False)
            if has_non_num_reports and not is_metareport_filter_open:
                self.button_names.append(CREATE_METAREPORT_BTN)
                self.button_enabled.append(True)

        if IS_BUSY in path_status:
            if CREATE_REPORT_BTN in self.button_names:
                idx = self.button_names.index(CREATE_REPORT_BTN)
                self.button_enabled[idx] = not path_status[IS_BUSY]
            if CREATE_REPORTS_BTN in self.button_names:
                idx = self.button_names.index(CREATE_REPORTS_BTN)
                self.button_enabled[idx] = not path_status[IS_BUSY]
        self.create_buttons()

    def update_callbacks(self, callbacks: Dict[str, Callable]):
        for bn in self.button_names:
            cb = callbacks[bn]
            self.buttons[bn].callback = cb
