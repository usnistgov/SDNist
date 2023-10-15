from abc import ABC, abstractmethod
import pygame as pg
import pygame_gui as pggui


class AbstractPage(ABC):

    @abstractmethod
    def __init__(self, manager: pggui.UIManager, data: any = None):
        self.manager = manager
        self.data = data
        self.w, self.h = self.manager.window_resolution

    @abstractmethod
    def draw(self, screen: pg.Surface):
        """Draws the graphical elements on the screen."""
        pass

    @abstractmethod
    def handle_event(self, event: pg.event.Event):
        """Handles the events for this page."""
        pass

    @abstractmethod
    def update(self):
        """Updates the page."""
        pass

    @abstractmethod
    def next_page(self):
        """Returns the next page to be displayed."""
        pass

    @abstractmethod
    def next_page_data(self):
        """Returns data to be passed to the next page."""
        pass
