from typing import Optional, Tuple, List, Dict
from pathlib import Path
import json
from functools import partial
import hashlib
import pandas as pd
from itertools import chain

import pygame as pg
import pygame_gui as pggui
from pygame_gui.elements.ui_window import UIWindow
from pygame_gui.elements.ui_button import UIButton
from pygame_gui.elements.ui_label import UILabel
from pygame_gui.elements.ui_text_entry_line import UITextEntryLine

from sdnist.gui.elements.textline import CustomUITextEntryLine
from sdnist.gui.panels import AbstractPanel
from sdnist.gui.elements import UICallbackButton
from sdnist.gui.pages.dashboard.metadata.labels import *
from sdnist.gui.pages.dashboard.metadata.formfield import \
    MetadataFormField
import sdnist.gui.strs as strs
from sdnist.gui.constants import *
from sdnist.gui.config import \
    load_algorithm_names, \
    load_library_names


def labels_hash(deid_data_path: str) -> str:
    with open(deid_data_path, 'r') as f:
        data_lines = f.readlines()
    data_str = ''
    for l in data_lines:
        data_str += l
    hasher = hashlib.sha1()
    hasher.update(data_str.encode('utf-8'))
    return hasher.hexdigest()


featureset_dict = {
    strs.ALL_FEATURES: all_features,
    strs.SIMPLE_FEATURES: simple_features,
    strs.DEMOGRAPHIC_FOCUSED: demographic_focused,
    strs.DETAILED_INDUSTRY_FOCUSED: detailed_industry_focused,
    strs.FAMILY_FOCUSED: family_focused,
    strs.INDUSTRY_FOCUSED: industry_focused,
    strs.SMALL_CATEGORICAL: small_categorical,
    strs.TINY_CATEGORICAL: tiny_categorical
}


def featureset(deid_data: pd.DataFrame) -> Tuple[str, List[str]]:
    # check for unnamed columns
    dd = deid_data
    dd = dd.loc[:, ~dd.columns.str.startswith('Unnamed')]

    d_cols = set(dd.columns.tolist())

    for fs_name, fs in featureset_dict.items():
        if d_cols == set(fs):
            return fs_name, sorted(fs)

    t_cols = len(d_cols)
    return f'custom-features-{t_cols}', sorted(list(d_cols))


def feature_space_size(target_df: pd.DataFrame, data_dict: Dict):
    size = 1

    for col in target_df.columns:
        if col in ['PINCP', 'POVPIP', 'WGTP', 'PWGTP', 'AGEP']:
            size = size * 100
        elif col in ['SEX', 'MSP', 'HISP', 'RAC1P', 'HOUSING_TYPE', 'OWN_RENT',
                     'INDP_CAT', 'EDU', 'PINCP_DECILE', 'DVET', 'DREM', 'DPHY', 'DEYE',
                     'DEAR']:
            size = size * len(data_dict[col]['values'])
        elif col in ['PUMA', 'DENSITY']:
            size = size * len(target_df['PUMA'].unique())
        elif col in ['NOC', 'NPF', 'INDP']:
            size = size * len(target_df[col].unique())
    return size


def deduce_target_dataset(deid_data_path: str) -> Optional[str]:
    checks = {
        "ma2019": {
            "in": ['_ma_', '-ma-', 'ma2019'],
            "starts_with": ['ma_', 'ma-'],
            "ends_with": ['_ma', '-ma']
        },
        "tx2019": {
            "in": ['_tx_', '-tx-', 'tx2019'],
            "starts_with": ['tx_', 'tx-'],
            "ends_with": ['_tx', '-tx']
        },
        "national2019": {
            "in": ['_na_', '-na-', 'na2019', '_national_', '-national-', 'national2019'],
            "starts_with": ['na_', 'na-', 'national_', 'national-'],
            "ends_with": ['_na', '-na', '_national', '-national']
        }
    }

    for k, v in checks.items():
        for i in v['in']:
            if i in deid_data_path:
                return k
        for i in v['starts_with']:
            if deid_data_path.startswith(i):
                return k
        for i in v['ends_with']:
            if deid_data_path.endswith(i):
                return k
    return None


class MetaDataForm(AbstractPanel):
    def __init__(self, rect: pg.Rect,
                 manager: pggui.UIManager,
                 settings: dict,
                 file_path: str,
                 copy_from_file: Optional[str] = None):
        super().__init__(rect, manager)
        self.settings = settings
        self.window = None
        self.test_data_btn = None
        self.labels = dict()
        self._file = file_path
        self._csv_file = self._file

        self._copy_from_csv_file = copy_from_file
        if Path(self._file).suffix == '.json':
            self.csv_file = self._file.replace('.json', '.csv')
            self.deid_data = pd.read_csv(self.csv_file)

        fset_name, fset = featureset(self.deid_data)
        fset_str = ', '.join(fset)
        self.libraries = load_library_names()
        self.algorithms = load_algorithm_names()
        self.algorithm_types = list(set(chain([v[0] for k, v in self.algorithms.items()])))
        self.privacy_categories = list(set(chain([v[1] for k, v in self.algorithms.items()])))
        # Metadata form definition
        # [label name, label value, label input type, editable,
        # options, is_required
        self.form_dfn = {
            "base fields": {
                TEAM: [TEAM, self.settings[strs.TEAM_NAME], "string", False, True, None],
                DEID_DATA_ID: [DEID_DATA_ID, labels_hash(self._csv_file), "string", False, True, None],
                FEATURE_SET_NAME: [FEATURE_SET_NAME, fset_name, "string", False, True, None],
                FEATURES_LIST: [FEATURES_LIST, fset_str, "string", False, True, None],
                FEATURE_SPACE_SIZE: [FEATURE_SPACE_SIZE, '', "string", False, True, None]
            },
            "required fields": {
                TARGET_DATASET: [TARGET_DATASET, deduce_target_dataset(self._csv_file), "dropdown",
                 True, True, target_datasets],
                LIBRARY_NAME: [LIBRARY_NAME, None, "dropdown", True, True,
                 list(self.libraries.keys())],
                ALGORITHM_NAME: [ALGORITHM_NAME, None, "dropdown", True, True,
                 list(self.algorithms.keys())],
                VARIANT_LABEL: [VARIANT_LABEL, None, "string", True, True, None],
                SUBMISSION_NUMBER: [SUBMISSION_NUMBER, None, "int", True, True, None],
            },
            "optional fields": {
                EPSILON: [EPSILON, None, "float", True, False, None],
                DELTA: [DELTA, None, "float", True, False, None],
                QUASI_IDENTIFIERS_SUBSET: [QUASI_IDENTIFIERS_SUBSET,
                                           None, "multi-dropdown", True, False, fset],
                VARIANT_LABEL_DETAIL: [VARIANT_LABEL_DETAIL,
                                       None, 'long-string', True, False, None],
                PRIVACY_LABEL_DETAIL: [PRIVACY_LABEL_DETAIL,
                                       None, 'long-string', True, False, None],
                ALGORITHM_TYPE: [ALGORITHM_TYPE,
                                 None, 'dropdown', True, False, self.algorithm_types],
                PRIVACY_CATEGORY: [PRIVACY_CATEGORY,
                                   None, 'dropdown', True, False, self.privacy_categories],
                RESEARCH_PAPERS: [RESEARCH_PAPERS,
                                  None, 'long-string', True, False, None],
            }
        }

        self.form_elems = dict()
        self.form_elem_id = dict()
        self.active_dropdown_lbl = None
        self._create()

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
        self.window = UIWindow(rect=self.rect,
                               manager=self.manager,
                               window_display_title=
                               "Deid File Metadata Form: " +
                               str(Path(*Path(self._file).parts[-4:])),
                               draggable=False,
                               resizable=True)

        test_btn_rect = pg.Rect((0, 0), (200, 30))
        test_btn_rect.topright = (0, 0)
        self.test_data_btn = UICallbackButton(relative_rect=test_btn_rect,
                                              callback=partial_load_testdata,
                                              text='Load Test Metadata',
                                              container=self.window,
                                              parent_element=self.window,
                                              manager=self.manager,
                                              anchors={'right': 'right',
                                                       'top': 'top'})
        self.labels = dict()

        # label category 1
        pad_x = self.rect.w * 0.05
        pad_y = self.rect.h * 0.01

        lbl_w = self.rect.w * 0.6
        lbl_h = self.rect.h * 0.033

        lbl_in_w = self.rect.w * 0.3
        lbl_in_h = self.rect.h * 0.05
        i = 0
        for lbl_category, lbl_input in self.form_dfn.items():
            lc_rect = pg.Rect((pad_x, pad_y + i * (lbl_h + pad_y)),
                              (lbl_w, lbl_h))
            lc_label = UILabel(relative_rect=lc_rect,
                               container=self.window,
                               parent_element=self.window,
                               text=lbl_category.capitalize(),
                               manager=self.manager,
                               anchors={'left': 'left',
                                        'top': 'top'})
            i += 1
            for lbl_title, lbl in lbl_input.items():
                rect = pg.Rect((pad_x, pad_y + i * (lbl_h + pad_y)),
                               (lbl_w, lbl_h))
                ff = MetadataFormField(rect,
                                       self.manager,
                                       self.window,
                                       *lbl)
                if ff.text_in:
                    part_callback = partial(self._on_textline_clicked,
                                            lbl_title)
                    ff.text_in.on_click = part_callback
                if ff.inp_btn:
                    handle_dropdown = partial(self.handle_dropdown,
                                              label_name=lbl_title)
                    ff.inp_btn.callback = handle_dropdown
                i += 1

                if lbl_title not in self.form_elems:
                    self.form_elems[lbl_title] = ff
                    self.form_elem_id[ff] = lbl_title

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
            if 'labels' in meta:
                meta = meta['labels']

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

        for lbl, lbl_input in self.labels.values():
            lbl.kill()
            lbl_input.kill()

    def handle_event(self, event: pg.event.Event):
        # if event.type == pg.USEREVENT:
        #     if event.ui_element in self.form_elem_id.keys():
        #         print('found')
        pass

    def _on_textline_clicked(self, label_name: str):
        self.handle_dropdown(label_name)

    def handle_dropdown(self, label_name: str):
        # check if assumed active dropdown has not
        # become inactive after user selected an
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
            print('ACTIVE')
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

    def load_test_data(self, data_path: str):

        with open(data_path, 'r') as f:
            test_meta = json.load(f)

        test_meta = test_meta['labels']

        for lbl_title, lbl_input in self.labels.items():
            if lbl_title in test_meta:
                lbl_input[1].set_text(str(test_meta[lbl_title]))

    def save_data(self):
        file_name = Path(self.file).name
        json_file = Path(self.file).parent.joinpath(file_name.split('.')[0] + '.json')

        meta = dict()
        meta['labels'] = dict()
        for lbl_title, lbl_input in self.labels.items():
            meta['labels'][lbl_title] = lbl_input[1].get_text()

        with open(json_file, 'w') as f:
            json.dump(meta, f, indent=4)

