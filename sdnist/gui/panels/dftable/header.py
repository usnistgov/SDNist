from typing import List
import pygame as pg

from pygame_gui.core.object_id import ObjectID
from pygame_gui.elements.ui_window import UIWindow

from sdnist.gui.panels.header import Header
from sdnist.gui.elements import LabelDropDown


class DFTableHeader(Header):
    def __init__(self,
                 all_features: List[str],
                 enabled_features: List[str],
                 parent_window: UIWindow,
                 *args, **kwargs):
        text_anchors = kwargs.get('text_anchors', None)
        kwargs['object_id'] = \
            ObjectID(class_id='@header_panel',
                     object_id='#dftable_header')
        if text_anchors is None:
            kwargs['text_anchors'] = {
                'centery': 'centery',
                'left': 'left'
            }
        super().__init__(*args, **kwargs)
        self.all_features = all_features
        self.enabled_features = enabled_features
        self.parent_window = UIWindow

        # all features dropdown
        self.all_feat_dd = None

    def _create(self):
        super()._create()

        all_feats_rect = pg.Rect(
            0, 0,
            200,
            self.h * 0.8
        )

        # self.all_feat_dd = LabelDropDown(
        #     on_change_callback=None,
        #     rect=all_feats_rect,
        #     manager=self.manager,
        #     container=self.panel,
        #     parent_window=self.parent_window,
        #     options_list=self.all_features,
        #     starting_option=self.enabled_features
        # )
