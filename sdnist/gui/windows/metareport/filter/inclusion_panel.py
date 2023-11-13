from typing import Optional

import pandas as pd
import pygame as pg
import pygame_gui as pggui

from sdnist.gui.panels import AbstractPanel
from sdnist.gui.windows.metareport.filter.filters_panel \
    import FiltersPanel

from sdnist.gui.panels.dftable.filterdata import \
    FSetType


class InclusionFilters(FiltersPanel):
    def __init__(self,
                 *args, **kwargs):
        super().__init__(header_text="Inclusion Filters",
                         filter_type=FSetType.Inclusion_Filter,
                         *args, **kwargs)
        self._create()

    def _create(self):
        super()._create()

    def destroy(self):
        super().destroy()

    def handle_event(self, event: pg.event.Event):
        pass
