import pygame as pg
import pygame_gui as pggui

from sdnist.gui.panels.panel import AbstractPanel

from pygame_gui.elements.ui_panel import UIPanel
from pygame_gui.elements.ui_label import UILabel
from pygame_gui.elements.ui_text_entry_line import \
    UITextEntryLine


class ChooseTeamPanel(AbstractPanel):
    def __init__(self, rect: pg.Rect,
                 manager: pggui.UIManager,
                 container: any):
        super().__init__(rect, manager, container=container)
        self.panel = None
        self.label = None
        self.text_entry = None
        self._create()

    def _create(self):
        # create panel
        if self.container is None:
            self.panel = UIPanel(self.rect,
                                 starting_height=1,
                                 manager=self.manager)
        else:
            self.panel = UIPanel(self.rect,
                                 starting_height=1,
                                 manager=self.manager,
                                 container=self.container)

        # create UILabel with text Choose a Team Name
        label_h = int(self.rect.h * 0.3)
        label_rect = pg.Rect((0, label_h), (-1, 50))
        self.label = UILabel(relative_rect=label_rect,
                             container=self.panel,
                             parent_element=self.panel,
                             text='Choose a Team Name',
                             manager=self.manager,
                             anchors={'centerx': 'centerx',
                                      'top': 'top'})

        # create UITextEntryLine for user to enter team name
        text_w = int(self.rect.w * 0.4)
        text_rect = pg.Rect((0, label_h + 50), (text_w, 50))
        self.text_entry = UITextEntryLine(relative_rect=text_rect,
                                          container=self.panel,
                                          parent_element=self.panel,
                                          manager=self.manager,
                                          anchors={'top': 'top',
                                                   'centerx': 'centerx'})

    def destroy(self):
        self.panel.kill()
        self.panel = None
        self.label.kill()
        self.label = None
        self.text_entry.kill()
        self.text_entry = None

    def handle_event(self, event: pg.event.Event):
        pass

