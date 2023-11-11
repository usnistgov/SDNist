from typing import Dict
import pygame as pg
import pygame_gui as pggui

from sdnist.gui.panels.panel import AbstractPanel

from pygame_gui.elements.ui_panel import UIPanel
from pygame_gui.elements.ui_label import UILabel
from pygame_gui.elements.ui_text_entry_line import UITextEntryLine
from pygame_gui.elements.ui_button import UIButton
from pygame_gui.core import ObjectID

from sdnist.gui.elements import UICallbackButton

from sdnist.report.helpers import \
    team_uid, is_valid_team_uid, is_valid_email
import sdnist.gui.strs as strs


class ChooseTeamPanel(AbstractPanel):
    def __init__(self,
                 sdnist_cfg: dict,
                 rect: pg.Rect,
                 manager: pggui.UIManager,
                 container: any):
        super().__init__(rect, manager, container=container)
        self.sdnist_cfg = sdnist_cfg
        self.panel = self.create_panel()

        self.property_h = 80
        y_position = self.property_h * 2
        self.id_label, self.id_entry, self.button, _ = self.create_line(
            'Team Unique Identifier:', y_position,
            button_text='Generate', optional=False,
            placeholder_text='Paste existing team ID here or generate a new one')

        y_position += self.property_h  # Adjust the vertical space as needed
        self.team_label, self.team_entry, _, _ = self.create_line(
            'Team Name:', y_position, optional=False,
            placeholder_text='Enter team name')

        y_position += self.property_h  # Adjust the vertical space as needed
        self.email_label, self.email_entry, _, self.email_option_lbl = self.create_line(
            'Team Contact Email:', y_position, optional=True,
            placeholder_text='Enter email address')

    def _create(self):
        pass

    def create_panel(self):
        return UIPanel(self.rect, starting_height=1, manager=self.manager,
                       container=self.container if self.container else None)

    def create_line(self, label_text, y_position,
                    button_text=None, optional=False,
                    placeholder_text=''):
        placeholder_text = placeholder_text if placeholder_text else ''
        lbl_width = self.rect.w * 0.20
        txt_width = self.rect.w * 0.45
        btn_width = lbl_width//2

        lbl_height = 50
        lbl_x = self.rect.w//2 - (lbl_width + txt_width + btn_width)//2
        label = UILabel(relative_rect=pg.Rect((lbl_x, y_position),
                                              (lbl_width, lbl_height)),
                        text=label_text,
                        manager=self.manager,
                        container=self.panel,
                        object_id=ObjectID(class_id='@option_label',
                                           object_id='#choose_team_panel_lable'))
        opt_label = None
        if optional:
            opt_label = UILabel(relative_rect=pg.Rect((lbl_x + lbl_width + txt_width, y_position),
                                                      (btn_width, lbl_height)),
                                text=' (Optional)',
                                manager=self.manager,
                                container=self.panel,
                                object_id=ObjectID(class_id='@option_label',
                                                   object_id='#choose_team_panel_lable'))
        text_entry = UITextEntryLine(
            relative_rect=pg.Rect((lbl_x + lbl_width, y_position),
                                  (txt_width, lbl_height)),
            manager=self.manager,
            container=self.panel,
            placeholder_text=placeholder_text,
        )

        button = None
        if button_text:
            btn_x = lbl_x + lbl_width + txt_width
            button = UICallbackButton(
                             callback=self.generate_team_id,
                             relative_rect=pg.Rect((btn_x, y_position),
                                                   (btn_width, lbl_height)),
                             text=button_text,
                             manager=self.manager,
                             container=self.panel)

        return label, text_entry, button, opt_label

    def destroy(self):
        for element in [
            self.panel, self.id_label, self.id_entry, self.button,
            self.team_label, self.team_entry, self.email_label, self.email_entry
        ]:
            if element:
                element.kill()
                element = None

    def handle_event(self, event: pg.event.Event):
        pass  # Implement event handling as needed

    def can_save(self) -> bool:
        def validate_entry(entry, validation_function=None, empty_allowed=False):
            text = entry.get_text()
            is_valid = bool(text) and \
                (validation_function is None or validation_function(text))
            is_valid = True if not bool(text) and empty_allowed else is_valid
            entry.border_colour = pg.Color('white' if is_valid else 'red')
            entry.rebuild()
            return is_valid

        is_id = validate_entry(self.id_entry, is_valid_team_uid)
        is_name = validate_entry(self.team_entry)
        is_email = validate_entry(self.email_entry, is_valid_email, True)

        return all([is_id, is_name, is_email])

    def get_team_info(self) -> Dict[str, str]:
        team_id = self.id_entry.get_text()
        team_name = self.team_entry.get_text()
        email = self.email_entry.get_text()

        return {
            strs.TEAM_UNIQUE_IDENTIFIER: team_id,
            strs.TEAM_NAME: team_name,
            strs.TEAM_CONTACT_EMAIL: email
        }

    def generate_team_id(self):
        new_id = team_uid()
        self.id_entry.set_text(new_id)
        self.button.disable()
