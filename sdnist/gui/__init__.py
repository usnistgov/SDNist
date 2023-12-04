import os
from pathlib import Path

import pygame
import pygame_gui
from pygame_gui.windows import UIFileDialog
from pygame_gui.elements.ui_button import \
    UIButton

from sdnist.version import __version__
from sdnist.gui.colors import themes, \
    THM_WATER_POKEMON, THM_POKEMON_TGC

from sdnist.gui.pages import Page
from sdnist.gui.pages.home import Home
from sdnist.gui.pages.dashboard import Dashboard

from sdnist.gui.colors import main_theme_color


def create_page(page: Page, manager: pygame_gui.UIManager, data: any = None):
    if page == Page.HOME:
        return Home(manager)
    elif page == Page.DASHBOARD:
        return Dashboard(manager, data)
    else:
        raise ValueError("Invalid page")


def sdnist_gui():
    pygame.init()
    # Get all the displays available on the system
    # First is the main display and the rest are secondary displays
    displays = pygame.display.get_desktop_sizes()

    # If there are more than one display, use the second display
    if len(displays) > 1:
        disp_idx = 2
    else:
        disp_idx = 0

    screen_width = displays[disp_idx][0]
    screen_height = displays[disp_idx][1]
    width = screen_width
    height = screen_height
    dim = (width, height)

    gui_pkg_path = Path(__file__).parent
    theme_path = Path(gui_pkg_path, 'theme.json')

    pygame.display.set_caption("SDNIST-" + __version__)

    screen = pygame.display.set_mode(dim, pygame.RESIZABLE,
                                     display=disp_idx)
    # pygame.display.toggle_fullscreen()
    # pygame.display.set_mode(dim)
    screen.fill('white')

    manager = pygame_gui.UIManager(dim, str(theme_path))
    # Create a button

    clock = pygame.time.Clock()
    FPS = 60

    # test_data_path = Path(Path(gui_pkg_path, '..', '..',
    #                            'gui_data', 'in_data', 'data1', 'anonos_sdk_Anonos'))
    test_data_path = Path(Path(Path.cwd(),
                               'gui_data', 'in_data'))
    # test_data_path = Path(Path(gui_pkg_path, '..', '..',
    #                            'gui_data', 'in_data'))
    current_page = Page.DASHBOARD
    home_enabled = True if current_page == Page.HOME else False
    pages = {
        Page.HOME: Home(manager, enable=home_enabled),
        Page.DASHBOARD: Dashboard(manager, str(test_data_path))
    }

    if current_page == Page.DASHBOARD:
        pages[current_page].create()

    is_running = True
    while is_running:
        time_delta = clock.tick(FPS) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                is_running = False
            elif event.type == pygame.VIDEORESIZE:
                if (width, height) != (event.w, event.h):
                    width, height = event.w, event.h
                    dim = (width, height)
                    screen = pygame.display.set_mode((width, height), pygame.RESIZABLE)
                    manager = pygame_gui.UIManager(dim, str(theme_path))
                    pages = {
                        Page.HOME: Home(manager, enable=home_enabled),
                        Page.DASHBOARD: Dashboard(manager, str(test_data_path))
                    }
                    if current_page == Page.DASHBOARD:
                        pages[current_page].create()

            pages[current_page].handle_event(event)
            manager.process_events(event)

        next_page = pages[current_page].next_page()
        if next_page != current_page:
            pages[current_page].destroy()
            pages[next_page] = create_page(next_page,
                                           manager,
                                           pages[current_page].next_page_data())
            if next_page == Page.DASHBOARD:
                pages[next_page].create()
            current_page = next_page
        manager.update(time_delta)
        pages[current_page].draw(screen)
        pages[current_page].update()
        screen.fill(main_theme_color)
        manager.draw_ui(screen)
        pygame.display.update()
    pygame.quit()
