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
from sdnist.gui.panels.sdnist import SdnistPanel
from sdnist.gui.panels.headers.header import Header

from sdnist.report.helpers import \
    team_uid, is_valid_team_uid, is_valid_email
import sdnist.gui.strs as strs
from sdnist.gui.colors import main_theme_color


class ChooseTeamPanel(AbstractPanel):
    def __init__(self,
                 sdnist_cfg: dict,
                 *args,
                 **kwargs):
        super().__init__(*args, **kwargs)
        self.sdnist_cfg = sdnist_cfg
        self._create()
        self.property_h = 60

        info_title_rect = pg.Rect(
            0, 0,
            self.rect.w, 40
        )
        self.info_title = Header(
            text='Choose a team name and click "Next" to continue.',
            rect=info_title_rect,
            manager=self.manager,
            container=self.panel,
            text_size='medium'
        )
        self.info_title.panel.background_colour = pg.Color(main_theme_color)
        self.info_title.rebuild()

        y_position = info_title_rect.bottom + self.property_h // 2
        self.team_label, self.team_entry, _, _ = self.create_line(
            strs.TEAM_NAME,
            'Team Name:', y_position, optional=False,
            placeholder_text='Enter a team name')

        y_position += self.property_h  # Adjust the vertical space as needed
        self.id_label, self.id_entry, self.button, _ = self.create_line(
            strs.TEAM_UNIQUE_IDENTIFIER, 'Team Unique Identifier:', y_position,
            button_text='Generate', optional=False,
            placeholder_text='')

        y_position += self.property_h  # Adjust the vertical space as needed
        self.email_label, self.email_entry, _, self.email_option_lbl = self.create_line(
            strs.TEAM_CONTACT_EMAIL,'Team Contact Email:', y_position, optional=True,
            placeholder_text='Enter an email address')

    def _create(self):
        pad_y = 60

    def create_line(self, label_name: strs,
                    label_text: strs,
                    y_position: int,
                    button_text=None,
                    optional=False,
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
                        object_id=ObjectID(class_id='@header_label',
                                           object_id='#choose_team_panel_label'))
        opt_label = None
        if optional:
            opt_label = UILabel(relative_rect=pg.Rect((lbl_x + lbl_width + txt_width, y_position),
                                                      (btn_width, lbl_height)),
                                text=' (Optional)',
                                manager=self.manager,
                                container=self.panel,
                                object_id=ObjectID(class_id='@header_label',
                                                   object_id='#choose_team_panel_label'))
        text = ''

        if label_name == strs.TEAM_UNIQUE_IDENTIFIER:
            text = team_uid()

        text_entry = UITextEntryLine(
            relative_rect=pg.Rect((lbl_x + lbl_width, y_position),
                                  (txt_width, lbl_height)),
            manager=self.manager,
            container=self.panel,
            placeholder_text=placeholder_text,
            initial_text=text,
            object_id=ObjectID(
                class_id='@custom_text_entry_line',
                object_id='#custom_text_entry_line'
            )
        )


        return label, text_entry, None, opt_label

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
            entry.border_width = 0 if is_valid else 1
            entry.border_colour = pg.Color('white' if is_valid else 'red')
            invalid_text = f'Invalid Value: {text}' \
                if len(text) else 'Empty value not allowed'
            entry.placeholder_text = entry.placeholder_text \
                if is_valid else invalid_text
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
