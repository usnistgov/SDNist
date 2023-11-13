from typing import Optional
from pygame_gui.elements.ui_button import UIButton


class ButtonGroup:
    def __init__(self, buttons: Optional[list[UIButton]] = None):
        buttons = [] if buttons is None else buttons
        self.buttons = {b.text: b for b in buttons}
        self.selected = None

    def add(self, button: UIButton, select: Optional[bool] = False):
        if button.text not in self.buttons:
            self.buttons[button.text] = button

        if select:
            self.select(button.text)

    def select(self, button):
        if button not in self.buttons:
            return
        if self.selected == button:
            self.buttons[button].select()
            return
        if self.selected:
            self.buttons[self.selected].unselect()
        self.selected = button
        self.buttons[button].select()
