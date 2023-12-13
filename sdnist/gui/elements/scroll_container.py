from typing import Callable, Optional, Tuple, Union

import pygame
from pygame.event import Event
from pygame.math import Vector2

from pygame_gui.elements.ui_scrolling_container import UIScrollingContainer


class CustomScrollingContainer(UIScrollingContainer):
    def __init__(self,
                 scroll_callback: Callable,
                 *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.scroll_callback = scroll_callback
        self.max_h = self.scrolling_bottom
        self.max_w = self.scrolling_right
        self.vert_scroll_pos = 0
        self.horiz_scroll_pos = 0
        self.vert_height = 0


    def set_scrollable_area_dimensions(self, dimensions: Union[Vector2,
                                                               Tuple[int, int],
                                                               Tuple[float, float]]):
        super().set_scrollable_area_dimensions(dimensions)
        self.max_w = dimensions[0]
        self.max_h = dimensions[1]

    def scroll_slider_max_h(self):
        if self.vert_scroll_bar:
            return self.vert_scroll_bar.rect.h \
                   - self.vert_scroll_bar.sliding_button.rect.h - 6
        return 1

    def scroll_slider_max_w(self):
        if self.horiz_scroll_bar:
            return self.horiz_scroll_bar.rect.w \
                   - self.horiz_scroll_bar.sliding_button.rect.w - 6
        return 1

    def update(self, time_delta: float):
        super().update(time_delta)
        exec_callback = False
        if self.horiz_scroll_bar and self.horiz_scroll_bar.has_moved_recently:
            exec_callback = True
            self.horiz_scroll_pos = self.horiz_scroll_bar.sliding_button.relative_rect.x
        if self.vert_scroll_bar and self.vert_scroll_bar.has_moved_recently:
            exec_callback = True
            self.vert_scroll_pos = self.vert_scroll_bar.sliding_button.relative_rect.y

        if exec_callback and self.scroll_callback:
            self.scroll_callback(self.vert_scroll_pos, self.horiz_scroll_pos)

    # def process_event(self, event: Event) -> bool:
    #     res = super().process_event(event)
    #     # self.scroll_left = self.horiz_scroll_bar.has_moved_recently
    #     # Check for scroll event
    #     # print(self.scrolling_right, self.scrolling_bottom)
    #
    #     return res
