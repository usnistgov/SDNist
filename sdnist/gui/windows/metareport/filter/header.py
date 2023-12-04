from typing import List, Optional, Callable
import pygame as pg

from pygame_gui.core.object_id import ObjectID
from pygame_gui.elements.ui_window import UIWindow

from sdnist.gui.panels.headers import Header
from sdnist.gui.elements import UICallbackButton


class MetaReportFilterHeader(Header):
    def __init__(self,
                 parent_window: UIWindow,
                 generate_metadata_callback: Optional[Callable] = None,
                 *args, **kwargs):
        self.parent_window = parent_window
        self.generate_metadata_callback = generate_metadata_callback

        text_anchors = kwargs.get('text_anchors', None)
        kwargs['object_id'] = \
            ObjectID(class_id='@header_panel',
                     object_id='#metareport_filter_header')
        if text_anchors is None:
            kwargs['text_anchors'] = {
                'centery': 'centery',
                'left': 'left'
            }
        super().__init__(*args, **kwargs)

        # all features dropdown
        self.all_feat_dd = None

        # button the generated metadata by passing
        # in the metadata filters
        self.gen_metadata_btn = None

    def _create(self):
        super()._create()

        gen_btn_rect = pg.Rect((0, 0),
                               (200, self.rect.h * 0.95))
        gen_btn_rect.x = -1 * gen_btn_rect.w
        self.generate_metadata = UICallbackButton(
            callback=self.generate_metadata_callback,
            text='GENERATE METAREPORT',
            relative_rect=gen_btn_rect,
            manager=self.manager,
            container=self.panel,
            anchors={
                'centery': 'centery',
                'right': 'right'
            },
            object_id=ObjectID(
                class_id='@generate_button',
                object_id='#generate_metareport_button'
            )
        )



