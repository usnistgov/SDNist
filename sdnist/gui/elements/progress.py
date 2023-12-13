from typing import Callable

from pygame_gui.elements.ui_progress_bar import UIProgressBar

class CustomUIProgress(UIProgressBar):
    def __init__(self, on_finish: Callable, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.on_finish = on_finish

    def update(self, time_delta: float):
        super().update(time_delta)
        if self.progress_percentage == 1:
            if self.on_finish:
                self.on_finish()

