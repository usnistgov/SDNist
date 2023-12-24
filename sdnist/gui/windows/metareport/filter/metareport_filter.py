from typing import Callable
import pandas as pd
from pathlib import Path
import pygame as pg
import pygame_gui as pggui

from pygame_gui.core.object_id import ObjectID
from pygame_gui.elements.ui_panel import UIPanel

from sdnist.gui.windows.window import AbstractWindow
from sdnist.gui.windows.metareport.filter.inclusion_panel \
    import InclusionFilters
from sdnist.gui.windows.metareport.filter.exclusion_panel \
    import ExclusionFilters
from sdnist.gui.windows.metareport.filter.header import \
    MetaReportFilterHeader
from sdnist.gui.panels.dftable.filterdata import \
    FilterData
from sdnist.gui.panels.dftable import DFTable

from sdnist.gui.windows.metadata.labels import *

from sdnist.metareport.__main__ import run, setup


class MetaReportFilter(AbstractWindow):
    def __init__(self,
                 create_metareport_callback: Callable,
                 index_path: str,
                 *args, **kwargs):
        self.title = 'Metareport Filters'
        kwargs['window_display_title'] = self.title
        kwargs['resizable'] = True
        kwargs['draggable'] = False
        kwargs['object_id'] = ObjectID(
            class_id='@no_title_window',
            object_id='#metareport_filter_window')

        self.orig_rect = kwargs['rect']
        self.header_h = 40

        # new_rect = pg.Rect(self.orig_rect.x, self.orig_rect.y,
        #                    self.orig_rect.w,
        #                    self.orig_rect.h * 0.6 - self.title_h)
        # kwargs['rect'] = new_rect
        super().__init__(*args, **kwargs)
        self.create_metareport_callback = create_metareport_callback
        self.index_path = Path(index_path)
        self.index = pd.read_csv(self.index_path)
        if 'Unnamed: 0' in self.index.columns.to_list():
            self.index.index = self.index['Unnamed: 0'].values
            self.index = self.index.drop(columns=['Unnamed: 0'])
        self.header = None
        self.inc_panel = None
        self.exc_panel = None

        self.filter_data = FilterData(data=self.index, path=self.index_path)
        self.idx_tbl = None

        self.default_enabled_features = [
            TEAM,
            LIBRARY_NAME,
            ALGORITHM_NAME,
            FEATURE_SET_NAME,
            TARGET_DATASET,
            EPSILON,
            FEATURES_LIST,
            FEATURE_SPACE_SIZE,
            REPORT_PATH
        ]
        self._create()

    def _create(self):
        header_rect = pg.Rect(0, 0,
                              self.rect.w, self.header_h)
        self.header = MetaReportFilterHeader(
            generate_metareport_callback=self.generate_metareport,
            text='Metareport Filters',
            rect=header_rect,
            manager=self.manager,
            parent_window=self.window,
            container=self.window
        )
        inc_y = header_rect.h
        inc_h = exc_h = (self.rect.h - inc_y) * 0.3
        exc_y = inc_y + inc_h
        inc_rect = pg.Rect((0, inc_y),
                           (self.rect.w, inc_h))
        exc_rect = pg.Rect((0, exc_y),
                           (self.rect.w, exc_h))

        self.inc_panel = InclusionFilters(filter_data=self.filter_data,
                                          rect=inc_rect,
                                          manager=self.manager,
                                          container=self.window,
                                          on_update_callback=None)
        self.exc_panel = ExclusionFilters(filter_data=self.filter_data,
                                          rect=exc_rect,
                                          manager=self.manager,
                                          container=self.window,
                                          on_update_callback=None)

        idx_x = 0
        idx_y = self.exc_panel.rect.y + self.exc_panel.rect.h - 20

        idx_h = (self.rect.h - header_rect.h) * 0.4
        idx_rect = pg.Rect((idx_x, idx_y),
                           (self.rect.w, idx_h))

        self.idx_tbl = DFTable(rect=idx_rect,
                               manager=self.manager,
                               container=self.window,
                               filter_data=self.filter_data)
        self.inc_panel.on_update_callback = self.idx_tbl.update_data
        self.exc_panel.on_update_callback = self.idx_tbl.update_data

    def destroy(self):
        super().destroy()

        self.inc_panel.destroy()
        self.inc_panel = None
        self.exc_panel.destroy()
        self.exc_panel = None

    def handle_event(self, event):
        pass

    def generate_metareport(self):
        reports_dir = self.index_path.parent

        # get filtered report paths from idx_table
        filtered_df = self.idx_tbl.get_filtered_dataframe()
        reports_path = filtered_df[REPORT_PATH] \
            .apply(lambda x: Path(x)).tolist()

        self.create_metareport_callback(reports_dir=reports_dir,
                                        reports_path=reports_path)



