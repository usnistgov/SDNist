from typing import Optional, Tuple, List, Dict
from pathlib import Path
import json
from functools import partial
import pandas as pd
from itertools import chain

import pygame as pg
import pygame_gui as pggui

from pygame_gui.core import ObjectID
from pygame_gui.elements.ui_window import UIWindow
from pygame_gui.elements.ui_scrolling_container import UIScrollingContainer
from pygame_gui.elements.ui_button import UIButton
from pygame_gui.elements.ui_label import UILabel
from pygame_gui.elements.ui_text_entry_line import UITextEntryLine

from sdnist.index import feature_space_size
from sdnist.gui.target import TargetData
from sdnist.gui.elements.textline import CustomUITextEntryLine

from sdnist.gui.panels.headers import Header
from sdnist.gui.panels.headers import WindowHeader

from sdnist.gui.elements import UICallbackButton
from sdnist.gui.windows.window import AbstractWindow
from sdnist.gui.windows.metadata.labels import *
from sdnist.gui.windows.metadata.formfield import \
    MetadataFormField
from sdnist.gui.panels.longtextinput import \
    LongTextInputPanel
from sdnist.gui.panels.longtext import \
    LongTextPanel
from sdnist.gui.windows.metadata.labels import \
    LabelType as LabelT

from sdnist.gui.windows.metadata.labelinfo import \
    LabelInfoPanel

from sdnist.gui.windows.metadata.featureset import \
    feature_set
from sdnist.index.deid_id import \
    deid_data_hash
import sdnist.gui.strs as strs
from sdnist.gui.constants import *
from sdnist.gui.res import \
    load_library_names, \
    load_algorithm_names, \
    get_index_definition


class MetaDataForm(AbstractWindow):
    def __init__(self, rect: pg.Rect,
                 manager: pggui.UIManager,
                 settings: dict,
                 file_path: str,
                 copy_from_file: Optional[str] = None,
                 *args, **kwargs):
        self.title = 'Deid File Metadata Form'
        kwargs['window_display_title'] = self.title
        kwargs['resizable'] = True
        kwargs['draggable'] = False
        super().__init__(rect, manager, *args, **kwargs)
        self.settings = settings
        self.test_data_btn = None
        self.labels = dict()
        self._file = file_path
        self.json_file = self._file
        self.csv_file = self._file
        self.labels_data = None

        self._copy_from_csv_file = copy_from_file
        if Path(self._file).suffix == '.json':
            self.csv_file = self._file.replace('json', 'csv')
            self.deid_data = pd.read_csv(self.csv_file)
        elif Path(self._file).suffix == '.csv':
            self.json_file = self._file.replace('csv', 'json')
        if Path(self.json_file).exists():
            with open(self.json_file, 'r') as f:
                self.labels_data = json.load(f)
                if strs.LABELS in self.labels_data:
                    self.labels_data = self.labels_data[strs.LABELS]

        self.deid_df = pd.read_csv(self.csv_file)
        self.deid_df = self.deid_df.loc[:,
                                        ~self.deid_df.columns
                                        .str.startswith('Unnamed')]
        fset_name, fset = feature_set(self.deid_df)
        fset_str = ', '.join(fset)

        self.libraries = load_library_names()
        self.algorithms = load_algorithm_names()
        self.lbl_desc = get_index_definition()

        self.algorithm_types = list(set(chain([v[0] for k, v in self.algorithms.items()])))
        self.privacy_categories = list(set(chain([v[1] for k, v in self.algorithms.items()])))

        self.target = TargetData(DATA_ROOT_PATH)
        self.target_name = self.target.deduce_target_data(self.csv_file)
        self.feature_space = ''
        if self.target_name:
            t_df, t_sch, d_dict = self.target.get(self.target_name,
                                                  self.deid_df.columns.tolist())
            self.feature_space = feature_space_size(t_df, d_dict)
            self.feature_space = f'{self.feature_space}  ({self.feature_space:.1e})'
        # Metadata form definition
        # [label name, label value, label input type, editable,
        # is_required, options]
        self.form_dfn = {
            BASE_LABELS: {
                strs.TEAM_UNIQUE_IDENTIFIER: [strs.TEAM_UNIQUE_IDENTIFIER, self.settings[strs.TEAM_UNIQUE_IDENTIFIER], LabelT.STRING, False, True, None],
                TEAM: [TEAM, self.settings[strs.TEAM_NAME], LabelT.STRING, False, True, None],
                DEID_DATA_ID: [DEID_DATA_ID, deid_data_hash(self.csv_file), LabelT.STRING, False, True, None],
                FEATURE_SET_NAME: [FEATURE_SET_NAME, fset_name, LabelT.STRING, False, True, None],
                FEATURES_LIST: [FEATURES_LIST, fset_str, LabelT.STRING, False, True, None],
                FEATURE_SPACE_SIZE: [FEATURE_SPACE_SIZE, self.feature_space, LabelT.STRING, False, True, None],
            },
            REQUIRED_LABELS: {
                TARGET_DATASET: [TARGET_DATASET, self.target_name, LabelT.DROPDOWN,
                                 False, True, target_datasets],
                LIBRARY_NAME: [LIBRARY_NAME, None, LabelT.DROPDOWN, True, True,
                               list(self.libraries.keys())],
                LIBRARY_VERSION: [LIBRARY_VERSION, None, LabelT.STRING, True, True, None],
                LIBRARY_LINK: [LIBRARY_LINK, None, LabelT.STRING, True, True, None],
                ALGORITHM_NAME: [ALGORITHM_NAME, None, LabelT.DROPDOWN, True, True,
                                 list(self.algorithms.keys())],
                VARIANT_LABEL: [VARIANT_LABEL, None, LabelT.STRING, True, True, None],
                SUBMISSION_NUMBER: [SUBMISSION_NUMBER, None, LabelT.INT, True, True, None],
            },
            OPTIONAL_LABELS: {
                EPSILON: [EPSILON, None, LabelT.FLOAT, True, False, None],
                DELTA: [DELTA, None, LabelT.FLOAT, True, False, None],
                QUASI_IDENTIFIERS_SUBSET: [QUASI_IDENTIFIERS_SUBSET,
                                           None, LabelT.MULTI_DROPDOWN, True, False, fset],
                VARIANT_LABEL_DETAIL: [VARIANT_LABEL_DETAIL,
                                       None, LabelT.LONG_STRING, True, False, None],
                PRIVACY_LABEL_DETAIL: [PRIVACY_LABEL_DETAIL,
                                       None, LabelT.LONG_STRING, True, False, None],
                ALGORITHM_TYPE: [ALGORITHM_TYPE,
                                 None, LabelT.DROPDOWN, True, False, self.algorithm_types],
                PRIVACY_CATEGORY: [PRIVACY_CATEGORY,
                                   None, LabelT.DROPDOWN, True, False, self.privacy_categories],
                RESEARCH_PAPERS: [RESEARCH_PAPERS,
                                  None, LabelT.LONG_STRING, True, False, None],
            }
        }

        if self.labels_data:
            for lbl_name, lbl_data in self.form_dfn[BASE_LABELS].items():
                if lbl_name in self.labels_data:
                    lbl_data[1] = str(self.labels_data[lbl_name])
            for lbl_name, lbl_data in self.form_dfn[REQUIRED_LABELS].items():
                if lbl_name in self.labels_data:
                    lbl_data[1] = str(self.labels_data[lbl_name])
            for lbl_name, lbl_data in self.form_dfn[OPTIONAL_LABELS].items():
                if lbl_name in self.labels_data:
                    lbl_data[1] = str(self.labels_data[lbl_name])

        self.header_h = window_header_h
        self.header = None

        self.form_w = self.rect.w * 0.65
        self.info_w = self.rect.w * 0.35
        self.form_elems = dict()
        self.form_elem_id = dict()
        self.active_dropdown_lbl = None
        self.active_longtext_lbl = None
        self.active_longtext = None
        self.active_label_info_lbl = None
        self.active_label_info = None

        self.label_info_panels = dict()
        self.label_validation = dict()
        self._create()

        if not self.labels_data or 'labels' not in self.labels_data:
            self.save_data()

    @property
    def file(self) -> str:
        return self._file

    @file.setter
    def file(self, value: str):
        self._file = value
        self._update()

    def _create(self):
        file_path = Path(__file__).parent
        test_meta_path = Path(file_path, '..', '..', 'test_metadata.json')
        partial_load_testdata = partial(self.load_test_data,
                                        test_meta_path)

        self.labels = dict()
        self.headers = dict()
        # label category 1
        pad_x = self.rect.w * 0.01
        pad_y = self.rect.h * 0.01

        form_head_h = self.header_h
        lbl_w = self.form_w * 0.95
        lbl_h = self.rect.h * 0.038

        lbl_in_w = self.rect.w * 0.3
        lbl_in_h = self.rect.h * 0.05

        header_rect = pg.Rect(0, 0, self.rect.w, self.header_h)
        self.header = WindowHeader(
            title=self.title,
            rect=header_rect,
            manager=self.manager,
            container=self.window
        )

        scroll_pad = 20
        category_w = self.form_w - 20
        self.form_scroll_rect = pg.Rect((0, self.header_h),
                                       (self.form_w,
                                        self.rect.h - scroll_pad))
        self.form_scroll = UIScrollingContainer(relative_rect=self.form_scroll_rect,
                                                manager=self.manager,
                                                container=self.window,
                                                starting_height=1,
                                                anchors={'left': 'left',
                                                         'top': 'top'})
        last_rect = pg.Rect(0, 0, 0, 0)
        i = 0  # count form section header
        j = 0  # count form field
        for lbl_category, lbl_input in self.form_dfn.items():
            lc_rect = pg.Rect((0,
                               i * (form_head_h + pad_y) + j * (lbl_h + pad_y)),
                              (category_w, form_head_h))
            cat_header = Header(
                text=lbl_category.capitalize(),
                text_anchors={'left': 'left',
                              'centery': 'centery'},
                rect=lc_rect,
                container=self.form_scroll,
                parent_element=self.form_scroll,
                manager=self.manager,
                object_id=ObjectID(
                    class_id='@header_panel',
                    object_id='#info_header_panel'
                )
            )
            self.headers[lbl_category] = cat_header
            i += 1
            for lbl_title, lbl in lbl_input.items():
                rect = pg.Rect((pad_x, j * (lbl_h + pad_y) + i * (form_head_h + pad_y)),
                               (lbl_w, lbl_h))
                callback = partial(self.show_label_info,
                                      lbl_title)
                validate_callback = partial(self.validate_field,
                                            lbl_category)
                ff = MetadataFormField(rect,
                                       self.manager,
                                       self.form_scroll,
                                       callback,
                                       validate_callback,
                                       *lbl)
                if lbl[2] == LabelT.LONG_STRING:
                    text_change = partial(self.on_textline_update, lbl_title)
                    ff.on_change = text_change

                if ff.text_in:
                    part_callback = partial(self._on_textline_clicked,
                                            lbl_title)
                    ff.text_in.on_click = part_callback
                if ff.inp_btn:
                    handle_dropdown = partial(self.handle_dropdown,
                                              label_name=lbl_title)
                    ff.inp_btn.callback = handle_dropdown
                j += 1

                if lbl_title not in self.form_elems:
                    self.form_elems[lbl_title] = ff
                    self.form_elem_id[ff] = lbl_title

                last_rect = rect
        # set on selected change on target dataset
        self.form_elems[TARGET_DATASET].on_selected_val_change = self.update_feature_space

        all_fields = [self.form_elems[lbl_title].get_all_elements()
                      for lbl_title in self.form_elems.keys()]
        all_fields += [h.get_elements()
                       for h in self.headers.values()]
        # flatten all_fields
        all_fields = list(chain(*all_fields))
        all_fields = set(all_fields + [self.form_scroll])
        # Update from scroll dimensions
        # self.form_scroll.border_width = 4
        # self.form_scroll.border_colour = pg.Color('white')
        # self.form_scroll.rebuild()
        self.form_scroll.set_scrollable_area_dimensions(
            (category_w, last_rect.y + last_rect.h + 20)
        )
        if self.form_scroll.vert_scroll_bar:
            self.form_scroll.vert_scroll_bar.set_focus_set(all_fields)
        #
        # if self.form_scroll.horiz_scroll_bar:
        #     self.form_scroll.horiz_scroll_bar.set_focus_set(all_fields)

    def _update(self):
        self.window.set_display_title(
            "Deid File Metadata Form: " +
            str(Path(*Path(self._file).parts[-4:]))
        )
        if Path(self._file).suffix == '.csv':
            json_file = Path(self._file).parent.joinpath(Path(self._file)
                                                         .name.split('.')[0]
                                                         + '.json')
            if json_file.exists():
                self.load_test_data(str(json_file))
            else:
                for lbl_title, lbl_input in self.labels.items():
                    lbl_input[1].set_text(str(''))
        elif Path(self.file).suffix == '.json':
            with open(self._file, 'r') as f:
                meta = json.load(f)
            if strs.LABELS in meta:
                meta = meta[strs.LABELS]

            for lbl_title, lbl_input in self.labels.items():
                if lbl_title in meta:
                    lbl_str = str(meta[lbl_title]) if lbl_title in meta else ''
                    lbl_input[1].set_text(lbl_str)

    def destroy(self):

        if self.window:
            self.window.kill()
            self.window = None

        if self.test_data_btn:
            self.test_data_btn.kill()
            self.test_data_btn = None

        if self.active_label_info:
            self.active_label_info.destroy()
            self.active_label_info = None
            self.active_label_info_lbl = None

        for lbl, elem in self.form_elems.items():
            elem.destroy()

        self.form_elems.clear()

    def handle_event(self, event: pg.event.Event):
        pass

    def _on_textline_clicked(self, label_name: str):
        if self.active_dropdown_lbl != label_name:
            if self.active_longtext:
                self.active_longtext.destroy()
                self.active_longtext = None
            self.active_longtext_lbl = None
        if self.active_dropdown_lbl != label_name:
            if self.active_dropdown_lbl in self.form_elems:
                elem = self.form_elems[self.active_dropdown_lbl]
                elem.destroy_selection_list()
            self.active_dropdown_lbl = None

        lbl_elem = self.form_elems[label_name]
        if lbl_elem.is_dropdown:
            self.handle_dropdown(label_name)
        elif lbl_elem.label_type == LabelT.LONG_STRING:
            self.handle_longtext(label_name)

    def handle_dropdown(self, label_name: str):
        # check if assumed active dropdown has not
        # become inactive aLabelTer user selected an
        # item from the dropdown
        for lbl, elem in self.form_elems.items():
            if elem.dropdown is None \
                    and self.active_dropdown_lbl == lbl:
                self.active_dropdown_lbl = None

        # If the dropdown is active and the clicked
        # dropdown is the same as the active dropdown
        # then deactivate the dropdown
        if self.active_dropdown_lbl and \
                self.active_dropdown_lbl == label_name:
            self.active_dropdown_lbl = None
            elem = self.form_elems[label_name]
            elem.destroy_selection_list()
        # Else make the dropdown active and destroyed
        # any other open dropdown
        else:
            for lbl, elem in self.form_elems.items():
                if lbl != label_name:
                    if elem.dropdown:
                        self.active_dropdown_lbl = None
                        elem.destroy_selection_list()
                elif elem.is_dropdown:
                    elem.create_selection_list()
                    self.active_dropdown_lbl = label_name

    def handle_longtext(self, label_name: str):
        elem = self.form_elems[label_name]
        if elem.label_type != LabelT.LONG_STRING:
            if self.active_longtext:
                self.active_longtext.destroy()
                self.active_longtext = None
            self.active_longtext_lbl = None

        if self.active_longtext_lbl == label_name:
            return
        else:
            if self.active_longtext:
                self.active_longtext.destroy()
                self.active_longtext = None
            lt_rect = pg.Rect((self.form_w, self.header_h),
                              (self.rect.w - self.form_w, self.rect.h))
            text_callback = partial(self.on_longtext_update, label_name)
            elem = self.form_elems[label_name]
            self.active_longtext = LongTextInputPanel(lt_rect,
                                                      self.manager,
                                                      text_change_callback=text_callback,
                                                      container=self.window,
                                                      initial_text=elem.text_in.get_text(),
                                                      data=label_name)

            self.active_longtext_lbl = label_name

    def load_test_data(self, data_path: str):

        with open(data_path, 'r') as f:
            test_meta = json.load(f)

        test_meta = test_meta[strs.LABELS]

        for lbl_title, lbl_input in self.labels.items():
            if lbl_title in test_meta:
                lbl_input[1].set_text(str(test_meta[lbl_title]))

    def save_data(self):
        meta = dict()
        meta[strs.LABELS] = dict()
        for lbl_title, lbl_input in self.form_elems.items():
            meta[strs.LABELS][lbl_title] = lbl_input.text_in.get_text()

        with open(self.json_file, 'w') as f:
            json.dump(meta, f, indent=4)

    def update_feature_space(self, target_name: str):
        self.target_name = target_name
        if self.target_name:
            t_df, t_sch, d_dict = self.target.get(self.target_name,
                                                  self.deid_df.columns.tolist())
            self.feature_space = feature_space_size(t_df, d_dict)
            self.feature_space = f'{self.feature_space}  ' \
                                 f'({self.feature_space:.1e})'
            self.form_elems[FEATURE_SPACE_SIZE].text_in.set_text(self.feature_space)

    def on_longtext_update(self, label_name: str):
        elem = self.form_elems[label_name]
        if self.active_longtext_lbl == label_name:
            elem.text_in.set_text(self.active_longtext.text_in.get_text())

    def on_textline_update(self, label_name: str):
        elem = self.form_elems[label_name]
        if self.active_longtext_lbl == label_name and \
                self.active_longtext:
            self.active_longtext.text_in.set_text(elem.text_in.get_text())

    def show_label_info(self, label_name: str, hovered: bool = False):
        if hovered:
            if label_name != self.active_label_info_lbl:
                if self.active_label_info_lbl:
                    self.form_elems[self.active_label_info_lbl].panel.unset_hovered()
                if self.active_label_info:
                    self.active_label_info.panel.hide()
                    self.active_label_info = None
                    self.active_label_info_lbl = None
                is_valid = self.label_validation[label_name]
                self.form_elems[label_name].panel.set_hovered(valid=is_valid)
                if label_name in self.label_info_panels:
                    self.active_label_info = self.label_info_panels[label_name]
                    self.active_label_info.panel.show()
                    self.active_label_info_lbl = label_name
                else:
                    lt_rect = pg.Rect((self.form_w, self.header_h),
                                      (self.rect.w - self.form_w, self.rect.h))
                    elem = self.form_elems[label_name]
                    desc = '\n'.join(self.lbl_desc.get(label_name, []))
                    self.active_label_info = LabelInfoPanel(lt_rect,
                                                            self.manager,
                                                            label_name,
                                                            elem.label_type,
                                                            desc,
                                                            container=self.window,
                                                            initial_text=elem.text_in.get_text(),
                                                            data=label_name)
                    self.label_info_panels[label_name] = self.active_label_info
                self.active_label_info_lbl = label_name

    def validate_field(self, label_category: str,
                      label_name: str, label_value: str) -> bool:
        is_valid = False
        if label_category in [BASE_LABELS, REQUIRED_LABELS]:
            if label_value and len(label_value):
                is_valid = True
        else:
            is_valid = True

        self.label_validation[label_name] = is_valid
        return is_valid

    def validate_form(self):
        for lbl_title, lbl_input in self.form_elems.items():
            if lbl_title in self.label_validation:
                if not self.label_validation[lbl_title]:
                    return False
        return True