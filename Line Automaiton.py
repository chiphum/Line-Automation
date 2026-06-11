import pygame
import sys

# ----------------------------
# Configuration
# ----------------------------
SCREEN_WIDTH = 1600
SCREEN_HEIGHT = 980
FPS = 60

NUM_PITCHES_MAIN = 8
NUM_PITCHES_BLUE = 8
NUM_PITCHES_YELLOW = 8
SPLIT_PITCH = NUM_PITCHES_MAIN

TAKT_TIME_MAIN = 1.2
INITIAL_YELLOW_BRANCH_SPEED_FACTOR = 0.25
INITIAL_BLUE_BRANCH_SPEED_FACTOR = 0.75
MAX_VEHICLES = 40

BG_COLOR = (245, 247, 250)
TEXT_COLOR = (50, 60, 70)
TITLE_COLOR = (36, 52, 71)
LINE_COLOR = (210, 214, 220)
LINE_BORDER = (130, 140, 150)
ACCENT_GREEN = (76, 175, 80)
ACCENT_BLUE = (52, 120, 189)
BUTTON_BLUE = (52, 120, 189)
BUTTON_BLUE_HOVER = (72, 140, 209)
BUTTON_TEXT = (255, 255, 255)
PANEL_BG = (232, 237, 243)
PANEL_BORDER = (190, 198, 208)

VEHICLE_BLUE = (47, 99, 163)
VEHICLE_YELLOW = (232, 193, 33)
VEHICLE_WINDOW = (180, 210, 235)
WHEEL_COLOR = (45, 45, 45)
RAIL_COLOR = (180, 185, 192)
SPLIT_LINE_BLUE = (120, 150, 210)
SPLIT_LINE_YELLOW = (220, 190, 80)

# ----------------------------
# Header / UI layout
# ----------------------------
HEADER_TOP = 16
HEADER_HEIGHT = 130
TITLE_X = 40
TITLE_Y = 20
TAKT_X = 40
TAKT_Y = 68

CONTROL_PANEL_X = 40
CONTROL_PANEL_Y = 110
CONTROL_PANEL_W = 730
CONTROL_PANEL_H = 92

# ----------------------------
# Diagram layout
# ----------------------------
DIAGRAM_LEFT = 70
DIAGRAM_RIGHT = SCREEN_WIDTH - 40
BRANCH_START_OFFSET_X = 75

BLUE_BRANCH_TOP = 180
MAIN_TOP = 430
YELLOW_BRANCH_TOP = 720

PITCH_HEIGHT = 88
MIN_PITCH_WIDTH = 62
MAX_PITCH_WIDTH = 86
MIN_PITCH_GAP = 4
MAX_PITCH_GAP = 10

YELLOW_BRANCH_MIN_SPACING = 1.0
BLUE_BRANCH_MIN_SPACING = 1.0

SPEED_STEP = 0.05
MIN_SPEED_FACTOR = 0.05
MAX_SPEED_FACTOR = 2.00

# ----------------------------
# Dynamic fit-to-screen layout
# ----------------------------
def compute_layout():
    total_width = DIAGRAM_RIGHT - DIAGRAM_LEFT

    step_guess = int((total_width - BRANCH_START_OFFSET_X) / (NUM_PITCHES_MAIN + NUM_PITCHES_BLUE))

    pitch_gap = max(MIN_PITCH_GAP, min(MAX_PITCH_GAP, int(step_guess * 0.10)))
    pitch_width = step_guess - pitch_gap
    pitch_width = max(MIN_PITCH_WIDTH, min(MAX_PITCH_WIDTH, pitch_width))
    pitch_gap = max(MIN_PITCH_GAP, min(MAX_PITCH_GAP, pitch_gap))

    step = pitch_width + pitch_gap

    main_total_w = NUM_PITCHES_MAIN * step - pitch_gap
    branch_total_w = NUM_PITCHES_BLUE * step - pitch_gap

    # Left-align main line with control panel
    main_left = CONTROL_PANEL_X

    branch_start_x = int(main_left + main_total_w + BRANCH_START_OFFSET_X)

    # Safety clamp so branch end stays on-screen
    branch_end = branch_start_x + branch_total_w
    overflow = branch_end - DIAGRAM_RIGHT
    if overflow > 0:
        main_left -= int(overflow)
        branch_start_x -= int(overflow)

    return {
        "pitch_width": int(pitch_width),
        "pitch_gap": int(pitch_gap),
        "pitch_step": int(step),
        "main_left": int(main_left),
        "branch_start_x": int(branch_start_x),
    }

LAYOUT = compute_layout()

# ----------------------------
# Vehicle model
# ----------------------------
class Vehicle:
    def __init__(self, vehicle_id):
        self.vehicle_id = vehicle_id
        self.color = VEHICLE_YELLOW if vehicle_id % 4 == 0 else VEHICLE_BLUE
        self.route = "main"
        self.main_pitch_float = 1.0
        self.branch_pitch_float = None

    def is_yellow(self):
        return self.color == VEHICLE_YELLOW

    def is_blue(self):
        return self.color == VEHICLE_BLUE

    def update_main(self, delta_pitch):
        if self.main_pitch_float is not None:
            self.main_pitch_float += delta_pitch

    def is_on_screen(self):
        if self.route == "main" and self.main_pitch_float is not None:
            return self.main_pitch_float <= NUM_PITCHES_MAIN + 0.8
        if self.route == "blue_branch" and self.branch_pitch_float is not None:
            return self.branch_pitch_float <= NUM_PITCHES_BLUE + 0.8
        if self.route == "yellow_branch" and self.branch_pitch_float is not None:
            return self.branch_pitch_float <= NUM_PITCHES_YELLOW + 0.8
        return False

# ----------------------------
# Geometry helpers
# ----------------------------
def pitch_width():
    return LAYOUT["pitch_width"]

def pitch_gap():
    return LAYOUT["pitch_gap"]

def pitch_step():
    return LAYOUT["pitch_step"]

def main_left():
    return LAYOUT["main_left"]

def branch_start_x():
    return LAYOUT["branch_start_x"]

def main_pitch_rect(pitch_num):
    x = main_left() + (pitch_num - 1) * pitch_step()
    y = MAIN_TOP
    return pygame.Rect(int(x), int(y), pitch_width(), PITCH_HEIGHT)

def split_origin():
    rect = main_pitch_rect(SPLIT_PITCH)
    x = rect.x + rect.width
    y = rect.y + rect.height / 2
    return x, y

def branch_pitch_rect(branch_name, pitch_num):
    x = branch_start_x() + (pitch_num - 1) * pitch_step()
    y = BLUE_BRANCH_TOP if branch_name == "blue_branch" else YELLOW_BRANCH_TOP
    return pygame.Rect(int(x), int(y), pitch_width(), PITCH_HEIGHT)

def interpolate_position(rect_a, rect_b, frac):
    x = rect_a.x + (rect_b.x - rect_a.x) * frac
    y = rect_a.y + (rect_b.y - rect_a.y) * frac
    return x, y

def get_vehicle_xy(route, pitch_float):
    if route == "main":
        if pitch_float <= 1:
            rect = main_pitch_rect(1)
            return rect.x + pitch_width() * 0.12, rect.y + PITCH_HEIGHT * 0.42
        if pitch_float >= NUM_PITCHES_MAIN:
            rect = main_pitch_rect(NUM_PITCHES_MAIN)
            return rect.x + pitch_width() * 0.12, rect.y + PITCH_HEIGHT * 0.42
        base = int(pitch_float)
        frac = pitch_float - base
        rect_a = main_pitch_rect(base)
        rect_b = main_pitch_rect(base + 1)
        x, y = interpolate_position(rect_a, rect_b, frac)
        return x + pitch_width() * 0.12, y + PITCH_HEIGHT * 0.42

    if route == "blue_branch":
        if pitch_float <= 1:
            rect = branch_pitch_rect("blue_branch", 1)
            return rect.x + pitch_width() * 0.12, rect.y + PITCH_HEIGHT * 0.42
        if pitch_float >= NUM_PITCHES_BLUE:
            rect = branch_pitch_rect("blue_branch", NUM_PITCHES_BLUE)
            return rect.x + pitch_width() * 0.12, rect.y + PITCH_HEIGHT * 0.42
        base = int(pitch_float)
        frac = pitch_float - base
        rect_a = branch_pitch_rect("blue_branch", base)
        rect_b = branch_pitch_rect("blue_branch", base + 1)
        x, y = interpolate_position(rect_a, rect_b, frac)
        return x + pitch_width() * 0.12, y + PITCH_HEIGHT * 0.42

    if route == "yellow_branch":
        if pitch_float <= 1:
            rect = branch_pitch_rect("yellow_branch", 1)
            return rect.x + pitch_width() * 0.12, rect.y + PITCH_HEIGHT * 0.42
        if pitch_float >= NUM_PITCHES_YELLOW:
            rect = branch_pitch_rect("yellow_branch", NUM_PITCHES_YELLOW)
            return rect.x + pitch_width() * 0.12, rect.y + PITCH_HEIGHT * 0.42
        base = int(pitch_float)
        frac = pitch_float - base
        rect_a = branch_pitch_rect("yellow_branch", base)
        rect_b = branch_pitch_rect("yellow_branch", base + 1)
        x, y = interpolate_position(rect_a, rect_b, frac)
        return x + pitch_width() * 0.12, y + PITCH_HEIGHT * 0.42

    return 0, 0

# ----------------------------
# Drawing helpers
# ----------------------------
def draw_text(surface, text, font, color, x, y, center=False):
    rendered = font.render(text, True, color)
    rect = rendered.get_rect()
    if center:
        rect.center = (x, y)
    else:
        rect.topleft = (x, y)
    surface.blit(rendered, rect)

def draw_pitch(surface, font, pitch_num, rect, prefix):
    pygame.draw.rect(surface, LINE_COLOR, rect, border_radius=8)
    pygame.draw.rect(surface, LINE_BORDER, rect, width=2, border_radius=8)

    label = font.render(f"{prefix}{pitch_num}", True, TEXT_COLOR)
    label_rect = label.get_rect(center=(rect.centerx, rect.bottom + 15))
    surface.blit(label, label_rect)

def draw_vehicle(surface, x, y, scale, body_color):
    body_w = int(min(62, pitch_width() * 0.78) * scale)
    body_h = int(22 * scale)
    cabin_w = int(min(28, pitch_width() * 0.34) * scale)
    cabin_h = int(16 * scale)
    wheel_d = int(11 * scale)

    body_rect = pygame.Rect(int(x), int(y), body_w, body_h)
    pygame.draw.rect(surface, body_color, body_rect, border_radius=8)

    cabin_rect = pygame.Rect(int(x + body_w * 0.28), int(y - 13 * scale), cabin_w, cabin_h)
    pygame.draw.rect(surface, VEHICLE_WINDOW, cabin_rect, border_radius=6)
    pygame.draw.rect(surface, body_color, cabin_rect, width=2, border_radius=6)

    pygame.draw.circle(surface, WHEEL_COLOR, (int(x + body_w * 0.20), int(y + 22 * scale)), wheel_d // 2)
    pygame.draw.circle(surface, WHEEL_COLOR, (int(x + body_w * 0.78), int(y + 22 * scale)), wheel_d // 2)

def draw_button(surface, rect, font, text, mouse_pos):
    is_hovered = rect.collidepoint(mouse_pos)
    color = BUTTON_BLUE_HOVER if is_hovered else BUTTON_BLUE
    pygame.draw.rect(surface, color, rect, border_radius=8)
    pygame.draw.rect(surface, ACCENT_BLUE, rect, width=2, border_radius=8)
    draw_text(surface, text, font, BUTTON_TEXT, rect.centerx, rect.centery, center=True)

def draw_branch_connector(surface, branch_name, color):
    split_x, split_y = split_origin()
    rect = branch_pitch_rect(branch_name, 1)
    branch_center_y = rect.y + rect.height / 2

    elbow_x = split_x + 5
    end_x = rect.x - 4

    points = [
        (int(split_x), int(split_y)),
        (int(elbow_x), int(split_y)),
        (int(end_x), int(branch_center_y)),
        (int(rect.x), int(branch_center_y)),
    ]
    pygame.draw.lines(surface, color, False, points, 4)

def draw_main_line(surface, label_font):
    first_rect = main_pitch_rect(1)
    last_rect = main_pitch_rect(NUM_PITCHES_MAIN)

    label_rect = pygame.Rect(first_rect.x, first_rect.y - 70, last_rect.right - first_rect.x, 30)
    pygame.draw.rect(surface, ACCENT_GREEN, label_rect, border_radius=4)
    draw_text(surface, "Main Line", label_font, (255, 255, 255), label_rect.centerx, label_rect.centery, center=True)

    rail_y = first_rect.y + PITCH_HEIGHT / 2 - 7
    rail_rect = pygame.Rect(first_rect.x, int(rail_y), last_rect.right - first_rect.x, 14)
    pygame.draw.rect(surface, RAIL_COLOR, rail_rect, border_radius=3)

    for i in range(1, NUM_PITCHES_MAIN + 1):
        draw_pitch(surface, label_font, i, main_pitch_rect(i), "P")

def draw_branch_line(surface, label_font, branch_name, label, prefix):
    last_pitch = NUM_PITCHES_BLUE if branch_name == "blue_branch" else NUM_PITCHES_YELLOW
    rect1 = branch_pitch_rect(branch_name, 1)
    rect_last = branch_pitch_rect(branch_name, last_pitch)

    label_rect = pygame.Rect(rect1.x, rect1.y - 55, rect_last.right - rect1.x, 30)
    pygame.draw.rect(surface, ACCENT_GREEN, label_rect, border_radius=4)
    draw_text(surface, label, label_font, (255, 255, 255), label_rect.centerx, label_rect.centery, center=True)

    rail_y = rect1.y + PITCH_HEIGHT / 2 - 7
    rail_rect = pygame.Rect(rect1.x, int(rail_y), rect_last.right - rect1.x, 14)
    pygame.draw.rect(surface, RAIL_COLOR, rail_rect, border_radius=3)

    for i in range(1, last_pitch + 1):
        draw_pitch(surface, label_font, i, branch_pitch_rect(branch_name, i), prefix)

def draw_header_controls(surface, fonts, buttons, blue_speed_factor, yellow_speed_factor):
    _, subtitle_font, _, _, button_font = fonts
    mouse_pos = pygame.mouse.get_pos()

    panel_rect = pygame.Rect(CONTROL_PANEL_X, CONTROL_PANEL_Y, CONTROL_PANEL_W, CONTROL_PANEL_H)
    pygame.draw.rect(surface, PANEL_BG, panel_rect, border_radius=12)
    pygame.draw.rect(surface, PANEL_BORDER, panel_rect, width=2, border_radius=12)

    draw_text(surface, "Blue Speed", subtitle_font, TITLE_COLOR, CONTROL_PANEL_X + 24, CONTROL_PANEL_Y + 14)
    draw_text(surface, f"{blue_speed_factor:.2f}x", subtitle_font, TEXT_COLOR, CONTROL_PANEL_X + 24, CONTROL_PANEL_Y + 46)

    draw_button(surface, buttons["blue_minus"], button_font, "-", mouse_pos)
    draw_button(surface, buttons["blue_plus"], button_font, "+", mouse_pos)

    draw_text(surface, "Yellow Speed", subtitle_font, TITLE_COLOR, CONTROL_PANEL_X + 250, CONTROL_PANEL_Y + 14)
    draw_text(surface, f"{yellow_speed_factor:.2f}x", subtitle_font, TEXT_COLOR, CONTROL_PANEL_X + 250, CONTROL_PANEL_Y + 46)

    draw_button(surface, buttons["yellow_minus"], button_font, "-", mouse_pos)
    draw_button(surface, buttons["yellow_plus"], button_font, "+", mouse_pos)

    draw_text(surface, "System", subtitle_font, TITLE_COLOR, CONTROL_PANEL_X + 500, CONTROL_PANEL_Y + 14)
    draw_button(surface, buttons["reset"], button_font, "Reset", mouse_pos)

def draw_scene(surface, fonts, vehicles, takt_display, buttons, blue_speed_factor, yellow_speed_factor):
    surface.fill(BG_COLOR)

    title_font, subtitle_font, label_font, small_font, button_font = fonts

    draw_text(surface, "Main Line Splits into Horizontal Blue and Yellow Branch Lines", title_font, TITLE_COLOR, TITLE_X, TITLE_Y)
    draw_text(surface, f"Takt: {takt_display}", subtitle_font, TEXT_COLOR, TAKT_X, TAKT_Y)

    draw_header_controls(surface, fonts, buttons, blue_speed_factor, yellow_speed_factor)

    draw_main_line(surface, label_font)
    draw_branch_line(surface, label_font, "blue_branch", "Blue Branch Line", "B")
    draw_branch_line(surface, label_font, "yellow_branch", "Yellow Branch Line", "Y")

    draw_branch_connector(surface, "blue_branch", SPLIT_LINE_BLUE)
    draw_branch_connector(surface, "yellow_branch", SPLIT_LINE_YELLOW)

    for vehicle in vehicles:
        if vehicle.route == "main" and vehicle.main_pitch_float is not None:
            x, y = get_vehicle_xy("main", vehicle.main_pitch_float)
            draw_vehicle(surface, x, y, 1.0, vehicle.color)
        elif vehicle.route == "blue_branch" and vehicle.branch_pitch_float is not None:
            x, y = get_vehicle_xy("blue_branch", vehicle.branch_pitch_float)
            draw_vehicle(surface, x, y, 1.0, vehicle.color)
        elif vehicle.route == "yellow_branch" and vehicle.branch_pitch_float is not None:
            x, y = get_vehicle_xy("yellow_branch", vehicle.branch_pitch_float)
            draw_vehicle(surface, x, y, 1.0, vehicle.color)

    draw_text(
        surface,
        "Header moved above the diagram so the main line can shift left and the branch lines can fit inside the right edge.",
        subtitle_font,
        ACCENT_BLUE,
        SCREEN_WIDTH // 2,
        945,
        center=True
    )

# ----------------------------
# Simulation helpers
# ----------------------------
def update_branch_line(branch_vehicles, speed_factor, min_spacing, delta_pitch_main):
    branch_speed = delta_pitch_main * speed_factor
    branch_vehicles.sort(key=lambda v: v.branch_pitch_float, reverse=True)

    for i, vehicle in enumerate(branch_vehicles):
        if i == 0:
            vehicle.branch_pitch_float += branch_speed
        else:
            vehicle_ahead = branch_vehicles[i - 1]
            target_position = vehicle_ahead.branch_pitch_float - min_spacing
            proposed_position = vehicle.branch_pitch_float + branch_speed
            vehicle.branch_pitch_float = min(proposed_position, target_position)

def try_split_branch(vehicles, color_check, target_route, min_spacing):
    branch_vehicles = [v for v in vehicles if v.route == target_route and v.branch_pitch_float is not None]
    last_branch_position = min([v.branch_pitch_float for v in branch_vehicles], default=None)

    candidates = [
        v for v in vehicles
        if v.route == "main"
        and color_check(v)
        and v.main_pitch_float is not None
        and v.main_pitch_float >= SPLIT_PITCH
    ]
    candidates.sort(key=lambda v: v.vehicle_id)

    for vehicle in candidates:
        can_enter = False
        if last_branch_position is None:
            can_enter = True
        elif last_branch_position >= 1.0 + min_spacing:
            can_enter = True

        if can_enter:
            vehicle.route = target_route
            vehicle.branch_pitch_float = 1.0
            vehicle.main_pitch_float = None
            branch_vehicles.append(vehicle)
            last_branch_position = 1.0
        else:
            vehicle.main_pitch_float = SPLIT_PITCH

def reset_simulation():
    vehicles = [Vehicle(1)]
    next_vehicle_id = 2
    elapsed_since_takt = 0.0
    current_takt = 1
    return vehicles, next_vehicle_id, elapsed_since_takt, current_takt

def clamp(value, min_value, max_value):
    return max(min_value, min(max_value, value))

# ----------------------------
# Main loop
# ----------------------------
def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Vehicle Production Line Split Layout")
    clock = pygame.time.Clock()

    title_font = pygame.font.SysFont("arial", 32, bold=True)
    subtitle_font = pygame.font.SysFont("arial", 22)
    label_font = pygame.font.SysFont("arial", 20, bold=True)
    small_font = pygame.font.SysFont("arial", 16)
    button_font = pygame.font.SysFont("arial", 22, bold=True)

    fonts = (title_font, subtitle_font, label_font, small_font, button_font)

    buttons = {
        "blue_minus": pygame.Rect(CONTROL_PANEL_X + 120, CONTROL_PANEL_Y + 36, 44, 34),
        "blue_plus": pygame.Rect(CONTROL_PANEL_X + 172, CONTROL_PANEL_Y + 36, 44, 34),
        "yellow_minus": pygame.Rect(CONTROL_PANEL_X + 380, CONTROL_PANEL_Y + 36, 44, 34),
        "yellow_plus": pygame.Rect(CONTROL_PANEL_X + 432, CONTROL_PANEL_Y + 36, 44, 34),
        "reset": pygame.Rect(CONTROL_PANEL_X + 580, CONTROL_PANEL_Y + 34, 100, 38),
    }

    blue_branch_speed_factor = INITIAL_BLUE_BRANCH_SPEED_FACTOR
    yellow_branch_speed_factor = INITIAL_YELLOW_BRANCH_SPEED_FACTOR

    vehicles, next_vehicle_id, elapsed_since_takt, current_takt = reset_simulation()

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0
        elapsed_since_takt += dt

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if buttons["reset"].collidepoint(event.pos):
                    vehicles, next_vehicle_id, elapsed_since_takt, current_takt = reset_simulation()
                    blue_branch_speed_factor = INITIAL_BLUE_BRANCH_SPEED_FACTOR
                    yellow_branch_speed_factor = INITIAL_YELLOW_BRANCH_SPEED_FACTOR
                elif buttons["blue_minus"].collidepoint(event.pos):
                    blue_branch_speed_factor = clamp(blue_branch_speed_factor - SPEED_STEP, MIN_SPEED_FACTOR, MAX_SPEED_FACTOR)
                elif buttons["blue_plus"].collidepoint(event.pos):
                    blue_branch_speed_factor = clamp(blue_branch_speed_factor + SPEED_STEP, MIN_SPEED_FACTOR, MAX_SPEED_FACTOR)
                elif buttons["yellow_minus"].collidepoint(event.pos):
                    yellow_branch_speed_factor = clamp(yellow_branch_speed_factor - SPEED_STEP, MIN_SPEED_FACTOR, MAX_SPEED_FACTOR)
                elif buttons["yellow_plus"].collidepoint(event.pos):
                    yellow_branch_speed_factor = clamp(yellow_branch_speed_factor + SPEED_STEP, MIN_SPEED_FACTOR, MAX_SPEED_FACTOR)

        delta_pitch_main = dt / TAKT_TIME_MAIN

        for vehicle in vehicles:
            if vehicle.route == "main":
                vehicle.update_main(delta_pitch_main)

        try_split_branch(
            vehicles,
            color_check=lambda v: v.is_blue(),
            target_route="blue_branch",
            min_spacing=BLUE_BRANCH_MIN_SPACING
        )
        try_split_branch(
            vehicles,
            color_check=lambda v: v.is_yellow(),
            target_route="yellow_branch",
            min_spacing=YELLOW_BRANCH_MIN_SPACING
        )

        blue_branch_vehicles = [v for v in vehicles if v.route == "blue_branch" and v.branch_pitch_float is not None]
        yellow_branch_vehicles = [v for v in vehicles if v.route == "yellow_branch" and v.branch_pitch_float is not None]

        update_branch_line(
            blue_branch_vehicles,
            speed_factor=blue_branch_speed_factor,
            min_spacing=BLUE_BRANCH_MIN_SPACING,
            delta_pitch_main=delta_pitch_main
        )
        update_branch_line(
            yellow_branch_vehicles,
            speed_factor=yellow_branch_speed_factor,
            min_spacing=YELLOW_BRANCH_MIN_SPACING,
            delta_pitch_main=delta_pitch_main
        )

        if elapsed_since_takt >= TAKT_TIME_MAIN:
            elapsed_since_takt -= TAKT_TIME_MAIN
            current_takt += 1
            if next_vehicle_id <= MAX_VEHICLES:
                vehicles.append(Vehicle(next_vehicle_id))
                next_vehicle_id += 1

        vehicles = [v for v in vehicles if v.is_on_screen()]

        draw_scene(
            screen,
            fonts,
            vehicles,
            current_takt,
            buttons,
            blue_branch_speed_factor,
            yellow_branch_speed_factor
        )
        pygame.display.flip()

    pygame.quit()
    sys.exit()

# Entry point

if __name__ == "__main__":
    main()