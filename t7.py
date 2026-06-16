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
NUM_PITCHES_OUT = 8

SPLIT_PITCH = NUM_PITCHES_MAIN

TAKT_TIME_MAIN = 1.2
INITIAL_YELLOW_BRANCH_SPEED_FACTOR = 0.25
INITIAL_BLUE_BRANCH_SPEED_FACTOR = 0.75
MAX_VEHICLES = 200

DIAGRAM_SCALE = 0.50

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

HEADER_TOP = 16
HEADER_HEIGHT = 130
TITLE_X = 40
TITLE_Y = 20
TAKT_X = 40
TAKT_Y = 68

CONTROL_PANEL_X = 40
CONTROL_PANEL_Y = 110
CONTROL_PANEL_W = 780
CONTROL_PANEL_H = 92

MAIN_LABEL_OFFSET_Y = 60
BRANCH_LABEL_OFFSET_Y = 45
OUT_LABEL_OFFSET_Y = 60
LABEL_BLOCK_HEIGHT = 30

DIAGRAM_LEFT = 70
DIAGRAM_RIGHT = SCREEN_WIDTH - 40

BRANCH_START_OFFSET_X = int(24 * DIAGRAM_SCALE)
OUT_START_OFFSET_X = 120

BLUE_BRANCH_TOP = 260
MAIN_TOP = 470
YELLOW_BRANCH_TOP = 760
OUT_MAIN_TOP = 470

PITCH_HEIGHT = max(28, int(88 * DIAGRAM_SCALE))
MIN_PITCH_WIDTH = max(28, int(62 * DIAGRAM_SCALE))
MAX_PITCH_WIDTH = max(40, int(86 * DIAGRAM_SCALE))
MIN_PITCH_GAP = max(2, int(4 * DIAGRAM_SCALE))
MAX_PITCH_GAP = max(4, int(10 * DIAGRAM_SCALE))

YELLOW_BRANCH_MIN_SPACING = 1.0
BLUE_BRANCH_MIN_SPACING = 1.0
OUT_MAIN_MIN_SPACING = 1.0

SPEED_STEP = 0.05
MIN_SPEED_FACTOR = 0.05
MAX_SPEED_FACTOR = 2.00

SPLIT_TRAVEL_TIME = 0.99
MERGE_TRAVEL_TIME = 0.99


# ----------------------------
# Dynamic fit-to-screen layout
# ----------------------------
def compute_layout():
    total_width = DIAGRAM_RIGHT - DIAGRAM_LEFT

    merge_gap_x = 120
    usable_width = (
        total_width - BRANCH_START_OFFSET_X - OUT_START_OFFSET_X - merge_gap_x
    )
    total_pitch_count = NUM_PITCHES_MAIN + NUM_PITCHES_BLUE + NUM_PITCHES_OUT

    step_guess = int(usable_width / total_pitch_count)
    step_guess = max(step_guess, MIN_PITCH_WIDTH + MIN_PITCH_GAP)

    pitch_gap = max(MIN_PITCH_GAP, min(MAX_PITCH_GAP, int(step_guess * 0.10)))
    pitch_width = step_guess - pitch_gap
    pitch_width = max(MIN_PITCH_WIDTH, min(MAX_PITCH_WIDTH, pitch_width))
    pitch_gap = max(MIN_PITCH_GAP, min(MAX_PITCH_GAP, pitch_gap))

    step = pitch_width + pitch_gap

    main_total_w = NUM_PITCHES_MAIN * step - pitch_gap
    branch_total_w = NUM_PITCHES_BLUE * step - pitch_gap

    input_main_x = CONTROL_PANEL_X
    branch_start_x = input_main_x + main_total_w + BRANCH_START_OFFSET_X
    output_main_x = branch_start_x + branch_total_w + OUT_START_OFFSET_X

    return {
        "pitch_width": int(pitch_width),
        "pitch_gap": int(pitch_gap),
        "pitch_step": int(step),
        "input_main_x": int(input_main_x),
        "branch_start_x": int(branch_start_x),
        "output_main_x": int(output_main_x),
        "merge_gap_x": int(merge_gap_x),
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
        self.out_pitch_float = None

        self.split_target_route = None
        self.split_progress = 0.0

        self.merge_source_route = None
        self.merge_progress = 0.0
        self.merge_reserved = False

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
        if self.route == "out_main" and self.out_pitch_float is not None:
            return self.out_pitch_float <= NUM_PITCHES_OUT + 0.8
        if self.route == "splitting":
            return True
        if self.route == "merging":
            return True
        return False


# ----------------------------
# Geometry helpers
# ----------------------------
def pitch_width():
    return LAYOUT["pitch_width"]


def pitch_step():
    return LAYOUT["pitch_step"]


def input_main_x():
    return LAYOUT["input_main_x"]


def branch_start_x():
    return LAYOUT["branch_start_x"]


def output_main_x():
    return LAYOUT["output_main_x"]


def main_pitch_rect(pitch_num):
    x = input_main_x() + (pitch_num - 1) * pitch_step()
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


def output_main_pitch_rect(pitch_num):
    x = output_main_x() + (pitch_num - 1) * pitch_step()
    y = OUT_MAIN_TOP
    return pygame.Rect(int(x), int(y), pitch_width(), PITCH_HEIGHT)


def merge_target():
    rect = output_main_pitch_rect(1)
    return rect.x, rect.y + rect.height / 2


def interpolate_position(rect_a, rect_b, frac):
    x = rect_a.x + (rect_b.x - rect_a.x) * frac
    y = rect_a.y + (rect_b.y - rect_a.y) * frac
    return x, y


def get_split_path_points(target_route):
    split_x, split_y = split_origin()
    rect = branch_pitch_rect(target_route, 1)
    branch_center_y = rect.y + rect.height / 2

    elbow_x = split_x + 5
    end_x = rect.x - 4

    return [
        (float(split_x), float(split_y)),
        (float(elbow_x), float(split_y)),
        (float(end_x), float(branch_center_y)),
        (float(rect.x), float(branch_center_y)),
    ]


def get_merge_path_points(source_route):
    last_pitch = (
        NUM_PITCHES_BLUE if source_route == "blue_branch" else NUM_PITCHES_YELLOW
    )
    rect = branch_pitch_rect(source_route, last_pitch)
    start_x = rect.x + rect.width
    start_y = rect.y + rect.height / 2

    target_x, target_y = merge_target()
    elbow_x = start_x + LAYOUT["merge_gap_x"] // 2
    end_x = target_x - 4

    return [
        (float(start_x), float(start_y)),
        (float(elbow_x), float(start_y)),
        (float(end_x), float(target_y)),
        (float(target_x), float(target_y)),
    ]


def point_on_polyline(points, t):
    if len(points) < 2:
        return points[0] if points else (0.0, 0.0)

    segments = []
    total_len = 0.0

    for i in range(len(points) - 1):
        x1, y1 = points[i]
        x2, y2 = points[i + 1]
        seg_len = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
        segments.append((x1, y1, x2, y2, seg_len))
        total_len += seg_len

    if total_len == 0:
        return points[0]

    target_dist = max(0.0, min(1.0, t)) * total_len
    walked = 0.0

    for x1, y1, x2, y2, seg_len in segments:
        if walked + seg_len >= target_dist:
            local_t = 0.0 if seg_len == 0 else (target_dist - walked) / seg_len
            x = x1 + (x2 - x1) * local_t
            y = y1 + (y2 - y1) * local_t
            return x, y
        walked += seg_len

    return points[-1]


def get_vehicle_xy(route, pitch_float, aux_route=None, aux_progress=0.0):
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

    if route == "out_main":
        if pitch_float <= 1:
            rect = output_main_pitch_rect(1)
            return rect.x + pitch_width() * 0.12, rect.y + PITCH_HEIGHT * 0.42
        if pitch_float >= NUM_PITCHES_OUT:
            rect = output_main_pitch_rect(NUM_PITCHES_OUT)
            return rect.x + pitch_width() * 0.12, rect.y + PITCH_HEIGHT * 0.42
        base = int(pitch_float)
        frac = pitch_float - base
        rect_a = output_main_pitch_rect(base)
        rect_b = output_main_pitch_rect(base + 1)
        x, y = interpolate_position(rect_a, rect_b, frac)
        return x + pitch_width() * 0.12, y + PITCH_HEIGHT * 0.42

    if route == "splitting" and aux_route is not None:
        points = get_split_path_points(aux_route)
        x, y = point_on_polyline(points, aux_progress)
        return x, y - PITCH_HEIGHT * 0.08

    if route == "merging" and aux_route is not None:
        points = get_merge_path_points(aux_route)
        x, y = point_on_polyline(points, aux_progress)
        return x, y - PITCH_HEIGHT * 0.08

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
    pygame.draw.rect(surface, LINE_COLOR, rect, border_radius=6)
    pygame.draw.rect(surface, LINE_BORDER, rect, width=2, border_radius=6)

    label = font.render(f"{prefix}{pitch_num}", True, TEXT_COLOR)
    label_rect = label.get_rect(center=(rect.centerx, rect.bottom + 14))
    surface.blit(label, label_rect)


def draw_vehicle(surface, x, y, scale, body_color):
    body_w = int(min(62 * DIAGRAM_SCALE, pitch_width() * 0.78) * scale)
    body_h = int(22 * DIAGRAM_SCALE * scale)
    cabin_w = int(min(28 * DIAGRAM_SCALE, pitch_width() * 0.34) * scale)
    cabin_h = int(16 * DIAGRAM_SCALE * scale)
    wheel_d = max(4, int(11 * DIAGRAM_SCALE * scale))

    body_rect = pygame.Rect(int(x), int(y), body_w, body_h)
    pygame.draw.rect(
        surface, body_color, body_rect, border_radius=max(3, int(8 * DIAGRAM_SCALE))
    )

    cabin_rect = pygame.Rect(
        int(x + body_w * 0.28), int(y - 13 * DIAGRAM_SCALE * scale), cabin_w, cabin_h
    )
    pygame.draw.rect(
        surface,
        VEHICLE_WINDOW,
        cabin_rect,
        border_radius=max(2, int(6 * DIAGRAM_SCALE)),
    )
    pygame.draw.rect(
        surface,
        body_color,
        cabin_rect,
        width=1,
        border_radius=max(2, int(6 * DIAGRAM_SCALE)),
    )

    pygame.draw.circle(
        surface,
        WHEEL_COLOR,
        (int(x + body_w * 0.20), int(y + 22 * DIAGRAM_SCALE * scale)),
        wheel_d // 2,
    )
    pygame.draw.circle(
        surface,
        WHEEL_COLOR,
        (int(x + body_w * 0.78), int(y + 22 * DIAGRAM_SCALE * scale)),
        wheel_d // 2,
    )


def draw_button(surface, rect, font, text, mouse_pos):
    is_hovered = rect.collidepoint(mouse_pos)
    color = BUTTON_BLUE_HOVER if is_hovered else BUTTON_BLUE
    pygame.draw.rect(surface, color, rect, border_radius=8)
    pygame.draw.rect(surface, ACCENT_BLUE, rect, width=2, border_radius=8)
    draw_text(surface, text, font, BUTTON_TEXT, rect.centerx, rect.centery, center=True)


def draw_split_connector(surface, branch_name, color):
    points = get_split_path_points(branch_name)
    pygame.draw.lines(surface, color, False, [(int(x), int(y)) for x, y in points], 3)


def draw_merge_connector(surface, branch_name, color):
    points = get_merge_path_points(branch_name)
    pygame.draw.lines(surface, color, False, [(int(x), int(y)) for x, y in points], 3)


def draw_input_main_line(surface, label_font):
    first_rect = main_pitch_rect(1)
    last_rect = main_pitch_rect(NUM_PITCHES_MAIN)

    label_rect = pygame.Rect(
        first_rect.x,
        first_rect.y - MAIN_LABEL_OFFSET_Y,
        last_rect.right - first_rect.x,
        LABEL_BLOCK_HEIGHT,
    )
    pygame.draw.rect(surface, ACCENT_GREEN, label_rect, border_radius=4)
    draw_text(
        surface,
        "Input Main Line",
        label_font,
        (255, 255, 255),
        label_rect.centerx,
        label_rect.centery,
        center=True,
    )

    rail_y = first_rect.y + PITCH_HEIGHT / 2 - 5
    rail_rect = pygame.Rect(
        first_rect.x, int(rail_y), last_rect.right - first_rect.x, 10
    )
    pygame.draw.rect(surface, RAIL_COLOR, rail_rect, border_radius=3)

    for i in range(1, NUM_PITCHES_MAIN + 1):
        draw_pitch(surface, label_font, i, main_pitch_rect(i), "P")


def draw_branch_line(surface, label_font, branch_name, label, prefix):
    last_pitch = (
        NUM_PITCHES_BLUE if branch_name == "blue_branch" else NUM_PITCHES_YELLOW
    )
    rect1 = branch_pitch_rect(branch_name, 1)
    rect_last = branch_pitch_rect(branch_name, last_pitch)

    label_rect = pygame.Rect(
        rect1.x,
        rect1.y - BRANCH_LABEL_OFFSET_Y,
        rect_last.right - rect1.x,
        LABEL_BLOCK_HEIGHT,
    )
    pygame.draw.rect(surface, ACCENT_GREEN, label_rect, border_radius=4)
    draw_text(
        surface,
        label,
        label_font,
        (255, 255, 255),
        label_rect.centerx,
        label_rect.centery,
        center=True,
    )

    rail_y = rect1.y + PITCH_HEIGHT / 2 - 5
    rail_rect = pygame.Rect(rect1.x, int(rail_y), rect_last.right - rect1.x, 10)
    pygame.draw.rect(surface, RAIL_COLOR, rail_rect, border_radius=3)

    for i in range(1, last_pitch + 1):
        draw_pitch(surface, label_font, i, branch_pitch_rect(branch_name, i), prefix)


def draw_output_main_line(surface, label_font):
    first_rect = output_main_pitch_rect(1)
    last_rect = output_main_pitch_rect(NUM_PITCHES_OUT)

    label_rect = pygame.Rect(
        first_rect.x,
        first_rect.y - OUT_LABEL_OFFSET_Y,
        last_rect.right - first_rect.x,
        LABEL_BLOCK_HEIGHT,
    )
    pygame.draw.rect(surface, ACCENT_GREEN, label_rect, border_radius=4)
    draw_text(
        surface,
        "Output Main Line",
        label_font,
        (255, 255, 255),
        label_rect.centerx,
        label_rect.centery,
        center=True,
    )

    rail_y = first_rect.y + PITCH_HEIGHT / 2 - 5
    rail_rect = pygame.Rect(
        first_rect.x, int(rail_y), last_rect.right - first_rect.x, 10
    )
    pygame.draw.rect(surface, RAIL_COLOR, rail_rect, border_radius=3)

    for i in range(1, NUM_PITCHES_OUT + 1):
        draw_pitch(surface, label_font, i, output_main_pitch_rect(i), "O")


def draw_header_controls(
    surface, fonts, buttons, blue_speed_factor, yellow_speed_factor
):
    _, subtitle_font, _, _, button_font = fonts
    mouse_pos = pygame.mouse.get_pos()

    panel_rect = pygame.Rect(
        CONTROL_PANEL_X, CONTROL_PANEL_Y, CONTROL_PANEL_W, CONTROL_PANEL_H
    )
    pygame.draw.rect(surface, PANEL_BG, panel_rect, border_radius=12)
    pygame.draw.rect(surface, PANEL_BORDER, panel_rect, width=2, border_radius=12)

    draw_text(
        surface,
        "Blue Speed",
        subtitle_font,
        TITLE_COLOR,
        CONTROL_PANEL_X + 24,
        CONTROL_PANEL_Y + 14,
    )
    draw_text(
        surface,
        f"{blue_speed_factor:.2f}x",
        subtitle_font,
        TEXT_COLOR,
        CONTROL_PANEL_X + 24,
        CONTROL_PANEL_Y + 46,
    )

    draw_button(surface, buttons["blue_minus"], button_font, "-", mouse_pos)
    draw_button(surface, buttons["blue_plus"], button_font, "+", mouse_pos)

    draw_text(
        surface,
        "Yellow Speed",
        subtitle_font,
        TITLE_COLOR,
        CONTROL_PANEL_X + 250,
        CONTROL_PANEL_Y + 14,
    )
    draw_text(
        surface,
        f"{yellow_speed_factor:.2f}x",
        subtitle_font,
        TEXT_COLOR,
        CONTROL_PANEL_X + 250,
        CONTROL_PANEL_Y + 46,
    )

    draw_button(surface, buttons["yellow_minus"], button_font, "-", mouse_pos)
    draw_button(surface, buttons["yellow_plus"], button_font, "+", mouse_pos)

    draw_text(
        surface,
        "System",
        subtitle_font,
        TITLE_COLOR,
        CONTROL_PANEL_X + 500,
        CONTROL_PANEL_Y + 14,
    )
    draw_button(surface, buttons["reset"], button_font, "Reset", mouse_pos)


def draw_scene(
    surface,
    fonts,
    vehicles,
    takt_display,
    buttons,
    blue_speed_factor,
    yellow_speed_factor,
):
    surface.fill(BG_COLOR)

    title_font, subtitle_font, label_font, _, _ = fonts

    draw_text(
        surface,
        "Main Line Splits Into Blue and Yellow Branches, Then Merges Back",
        title_font,
        TITLE_COLOR,
        TITLE_X,
        TITLE_Y,
    )
    draw_text(
        surface, f"Takt: {takt_display}", subtitle_font, TEXT_COLOR, TAKT_X, TAKT_Y
    )

    draw_header_controls(
        surface, fonts, buttons, blue_speed_factor, yellow_speed_factor
    )

    draw_input_main_line(surface, label_font)
    draw_branch_line(surface, label_font, "blue_branch", "Blue Branch Line", "B")
    draw_branch_line(surface, label_font, "yellow_branch", "Yellow Branch Line", "Y")
    draw_output_main_line(surface, label_font)

    draw_split_connector(surface, "blue_branch", SPLIT_LINE_BLUE)
    draw_split_connector(surface, "yellow_branch", SPLIT_LINE_YELLOW)
    draw_merge_connector(surface, "blue_branch", SPLIT_LINE_BLUE)
    draw_merge_connector(surface, "yellow_branch", SPLIT_LINE_YELLOW)

    for vehicle in vehicles:
        if vehicle.route == "main" and vehicle.main_pitch_float is not None:
            x, y = get_vehicle_xy("main", vehicle.main_pitch_float)
            draw_vehicle(surface, x, y, 1.0, vehicle.color)
        elif vehicle.route == "blue_branch" and vehicle.branch_pitch_float is not None:
            x, y = get_vehicle_xy("blue_branch", vehicle.branch_pitch_float)
            draw_vehicle(surface, x, y, 1.0, vehicle.color)
        elif (
            vehicle.route == "yellow_branch" and vehicle.branch_pitch_float is not None
        ):
            x, y = get_vehicle_xy("yellow_branch", vehicle.branch_pitch_float)
            draw_vehicle(surface, x, y, 1.0, vehicle.color)
        elif vehicle.route == "out_main" and vehicle.out_pitch_float is not None:
            x, y = get_vehicle_xy("out_main", vehicle.out_pitch_float)
            draw_vehicle(surface, x, y, 1.0, vehicle.color)
        elif vehicle.route == "splitting":
            x, y = get_vehicle_xy(
                "splitting", 0.0, vehicle.split_target_route, vehicle.split_progress
            )
            draw_vehicle(surface, x, y, 1.0, vehicle.color)
        elif vehicle.route == "merging":
            x, y = get_vehicle_xy(
                "merging", 0.0, vehicle.merge_source_route, vehicle.merge_progress
            )
            draw_vehicle(surface, x, y, 1.0, vehicle.color)


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


def update_output_main_line(out_vehicles, delta_pitch_main):
    out_vehicles.sort(key=lambda v: v.out_pitch_float, reverse=True)

    for i, vehicle in enumerate(out_vehicles):
        if i == 0:
            vehicle.out_pitch_float += delta_pitch_main
        else:
            vehicle_ahead = out_vehicles[i - 1]
            target_position = vehicle_ahead.out_pitch_float - OUT_MAIN_MIN_SPACING
            proposed_position = vehicle.out_pitch_float + delta_pitch_main
            vehicle.out_pitch_float = min(proposed_position, target_position)


def update_splitting_vehicles(vehicles, dt):
    for vehicle in vehicles:
        if vehicle.route == "splitting":
            vehicle.split_progress += dt / SPLIT_TRAVEL_TIME
            if vehicle.split_progress >= 1.0:
                target_route = vehicle.split_target_route
                vehicle.route = target_route
                vehicle.branch_pitch_float = 1.0
                vehicle.main_pitch_float = None
                vehicle.split_progress = 0.0
                vehicle.split_target_route = None


def update_merging_vehicles(vehicles, dt):
    for vehicle in vehicles:
        if vehicle.route == "merging":
            vehicle.merge_progress += dt / MERGE_TRAVEL_TIME
            if vehicle.merge_progress >= 1.0:
                vehicle.route = "out_main"
                vehicle.out_pitch_float = 1.0
                vehicle.merge_progress = 0.0
                vehicle.merge_source_route = None
                vehicle.merge_reserved = False


def try_split_branch(vehicles, color_check, target_route, min_spacing):
    branch_vehicles = [
        v
        for v in vehicles
        if v.route == target_route and v.branch_pitch_float is not None
    ]
    splitting_vehicles = [
        v
        for v in vehicles
        if v.route == "splitting" and v.split_target_route == target_route
    ]

    last_branch_position = min(
        [v.branch_pitch_float for v in branch_vehicles], default=None
    )

    candidates = [
        v
        for v in vehicles
        if v.route == "main"
        and color_check(v)
        and v.main_pitch_float is not None
        and v.main_pitch_float >= SPLIT_PITCH
    ]
    candidates.sort(key=lambda v: v.vehicle_id)

    for vehicle in candidates:
        can_enter = False

        if len(splitting_vehicles) == 0:
            if last_branch_position is None:
                can_enter = True
            elif last_branch_position >= 1.0 + min_spacing:
                can_enter = True

        if can_enter:
            vehicle.route = "splitting"
            vehicle.split_target_route = target_route
            vehicle.split_progress = 0.0
            vehicle.main_pitch_float = None
            splitting_vehicles.append(vehicle)
        else:
            vehicle.main_pitch_float = SPLIT_PITCH


def find_merge_candidate(vehicles, source_route):
    last_branch_pitch = (
        NUM_PITCHES_BLUE if source_route == "blue_branch" else NUM_PITCHES_YELLOW
    )
    candidates = [
        v
        for v in vehicles
        if v.route == source_route
        and v.branch_pitch_float is not None
        and v.branch_pitch_float >= last_branch_pitch
    ]
    candidates.sort(key=lambda v: v.vehicle_id)
    return candidates[0] if candidates else None


def can_release_to_merge(vehicles):
    if any(v.route == "merging" for v in vehicles):
        return False

    out_vehicles = [
        v for v in vehicles if v.route == "out_main" and v.out_pitch_float is not None
    ]
    last_out_position = min([v.out_pitch_float for v in out_vehicles], default=None)

    if last_out_position is None:
        return True
    return last_out_position >= 1.0 + OUT_MAIN_MIN_SPACING


def try_merge_with_fairness(vehicles, merge_state):
    blue_candidate = find_merge_candidate(vehicles, "blue_branch")
    yellow_candidate = find_merge_candidate(vehicles, "yellow_branch")

    if not can_release_to_merge(vehicles):
        return

    chosen = None

    if blue_candidate and yellow_candidate:
        if merge_state["next_priority"] == "blue":
            chosen = blue_candidate
            merge_state["next_priority"] = "yellow"
        else:
            chosen = yellow_candidate
            merge_state["next_priority"] = "blue"
    elif blue_candidate:
        chosen = blue_candidate
        merge_state["next_priority"] = "yellow"
    elif yellow_candidate:
        chosen = yellow_candidate
        merge_state["next_priority"] = "blue"

    if chosen is not None:
        chosen.route = "merging"
        chosen.merge_source_route = (
            "blue_branch"
            if chosen.route != "yellow_branch" and chosen.is_blue()
            else "yellow_branch"
        )
        if chosen.color == VEHICLE_BLUE:
            chosen.merge_source_route = "blue_branch"
        else:
            chosen.merge_source_route = "yellow_branch"
        chosen.merge_progress = 0.0
        chosen.branch_pitch_float = None
        chosen.merge_reserved = True


def reset_simulation():
    vehicles = [Vehicle(1)]
    next_vehicle_id = 2
    elapsed_since_takt = 0.0
    current_takt = 1
    merge_state = {"next_priority": "blue"}
    return vehicles, next_vehicle_id, elapsed_since_takt, current_takt, merge_state


def clamp(value, min_value, max_value):
    return max(min_value, min(max_value, value))


# ----------------------------
# Main loop
# ----------------------------
def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Vehicle Production Line Split Merge Layout")
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
        "yellow_minus": pygame.Rect(
            CONTROL_PANEL_X + 380, CONTROL_PANEL_Y + 36, 44, 34
        ),
        "yellow_plus": pygame.Rect(CONTROL_PANEL_X + 432, CONTROL_PANEL_Y + 36, 44, 34),
        "reset": pygame.Rect(CONTROL_PANEL_X + 580, CONTROL_PANEL_Y + 34, 120, 38),
    }

    blue_branch_speed_factor = INITIAL_BLUE_BRANCH_SPEED_FACTOR
    yellow_branch_speed_factor = INITIAL_YELLOW_BRANCH_SPEED_FACTOR

    vehicles, next_vehicle_id, elapsed_since_takt, current_takt, merge_state = (
        reset_simulation()
    )

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0
        elapsed_since_takt += dt

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if buttons["reset"].collidepoint(event.pos):
                    (
                        vehicles,
                        next_vehicle_id,
                        elapsed_since_takt,
                        current_takt,
                        merge_state,
                    ) = reset_simulation()
                    blue_branch_speed_factor = INITIAL_BLUE_BRANCH_SPEED_FACTOR
                    yellow_branch_speed_factor = INITIAL_YELLOW_BRANCH_SPEED_FACTOR
                elif buttons["blue_minus"].collidepoint(event.pos):
                    blue_branch_speed_factor = clamp(
                        blue_branch_speed_factor - SPEED_STEP,
                        MIN_SPEED_FACTOR,
                        MAX_SPEED_FACTOR,
                    )
                elif buttons["blue_plus"].collidepoint(event.pos):
                    blue_branch_speed_factor = clamp(
                        blue_branch_speed_factor + SPEED_STEP,
                        MIN_SPEED_FACTOR,
                        MAX_SPEED_FACTOR,
                    )
                elif buttons["yellow_minus"].collidepoint(event.pos):
                    yellow_branch_speed_factor = clamp(
                        yellow_branch_speed_factor - SPEED_STEP,
                        MIN_SPEED_FACTOR,
                        MAX_SPEED_FACTOR,
                    )
                elif buttons["yellow_plus"].collidepoint(event.pos):
                    yellow_branch_speed_factor = clamp(
                        yellow_branch_speed_factor + SPEED_STEP,
                        MIN_SPEED_FACTOR,
                        MAX_SPEED_FACTOR,
                    )

        delta_pitch_main = dt / TAKT_TIME_MAIN

        for vehicle in vehicles:
            if vehicle.route == "main":
                vehicle.update_main(delta_pitch_main)

        try_split_branch(
            vehicles,
            color_check=lambda v: v.is_blue(),
            target_route="blue_branch",
            min_spacing=BLUE_BRANCH_MIN_SPACING,
        )
        try_split_branch(
            vehicles,
            color_check=lambda v: v.is_yellow(),
            target_route="yellow_branch",
            min_spacing=YELLOW_BRANCH_MIN_SPACING,
        )

        update_splitting_vehicles(vehicles, dt)

        blue_branch_vehicles = [
            v
            for v in vehicles
            if v.route == "blue_branch" and v.branch_pitch_float is not None
        ]
        yellow_branch_vehicles = [
            v
            for v in vehicles
            if v.route == "yellow_branch" and v.branch_pitch_float is not None
        ]

        update_branch_line(
            blue_branch_vehicles,
            speed_factor=blue_branch_speed_factor,
            min_spacing=BLUE_BRANCH_MIN_SPACING,
            delta_pitch_main=delta_pitch_main,
        )
        update_branch_line(
            yellow_branch_vehicles,
            speed_factor=yellow_branch_speed_factor,
            min_spacing=YELLOW_BRANCH_MIN_SPACING,
            delta_pitch_main=delta_pitch_main,
        )

        try_merge_with_fairness(vehicles, merge_state)
        update_merging_vehicles(vehicles, dt)

        out_main_vehicles = [
            v
            for v in vehicles
            if v.route == "out_main" and v.out_pitch_float is not None
        ]
        update_output_main_line(out_main_vehicles, delta_pitch_main)

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
            yellow_branch_speed_factor,
        )
        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
