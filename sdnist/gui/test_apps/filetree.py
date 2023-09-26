import pygame
import pygame_gui

pygame.init()

# Dimensions
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
WHITE = (255, 255, 255)

screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))

manager = pygame_gui.UIManager((WINDOW_WIDTH, WINDOW_HEIGHT), 'theme.json')

# UIWindow as side panel
side_panel = pygame_gui.elements.UIWindow(
    rect=pygame.Rect((0, 0), (200, 600)),
    manager=manager,
    window_display_title="Files",
    object_id="#side_panel"
)

# Dummy data for file tree
file_tree = {
    "Folder A": {
        "File A1.txt": None,
        "File A2.txt": None,
        "Folder A-sub": {
            "File A-sub1.txt": None
        }
    },
    "Folder B": {
        "File B1.txt": None
    }
}

# To simplify, we'll create the file tree using buttons. Clicking a folder button will expand/collapse its content.
buttons = []

y_position = 0
for folder, content in file_tree.items():
    btn = pygame_gui.elements.UIButton(
        relative_rect=pygame.Rect((10, y_position), (180, 30)),
        text=folder,
        manager=manager,
        container=side_panel
    )
    y_position += 35
    buttons.append(btn)

# Main loop
running = True
while running:
    time_delta = pygame.time.Clock().tick(60) / 1000.0
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.USEREVENT:
            if event.user_type == pygame_gui.UI_BUTTON_PRESSED:
                # Handle folder expand/collapse here
                pass

        manager.process_events(event)

    manager.update(time_delta)
    screen.fill(WHITE)
    manager.draw_ui(screen)
    pygame.display.update()

pygame.quit()
