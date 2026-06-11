import pygame
import sys

# ----------------------------
# Base configuration
# ----------------------------
BASE_SCREEN_WIDTH = 1600
BASE_SCREEN_HEIGHT = 980
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
# Base UI layout
# ----------------------------
BASE_TITLE_X = 30
BASE_TITLE_Y = 18
BASE_TAKT_X = 30
BASE_TAKT_Y = 68

BASE_CONTROL_PANEL_X = 30
BASE_CONTROL_PANEL_Y = 108
BASE_CONTROL_PANEL_W = 730
BASE_CONTROL_PANEL_H = 88

BLUE_MINUS_X_OFFSET = 120
BLUE_PLUS_X_OFFSET = 172
YELLOW_MINUS_X_OFFSET = 390
YELLOW_PLUS_X_OFFSET = 442

RESET_BUTTON_W = 100
RESET_BUTTON_H = 38
RESET_BUTTON_X_OFFSET = 560
RESET_BUTTON_Y_OFFSET = 32

# ----------------------------
# Base diagram layout
# ----------------------------
DIAGRAM_LEFT_MARGIN = 30
DIAGRAM_RIGHT_MARGIN = 30

# increase this to create more horizontal gap between main and branches
BRANCH_START_OFFSET_X = 42

BASE_BLUE_BRANCH_TOP = 180
BASE_MAIN_TOP = 430
BASE_YELLOW_BRANCH_TOP = 720

BASE_PITCH_HEIGHT = 88
BASE_BRANCH_LABEL_OFFSET = 55
BASE_MAIN_LABEL_OFFSET = 70
BASE_PITCH_LABEL_OFFSET = 15
BASE_RAIL_THICKNESS = 14
BASE_RAIL_OFFSET_Y = 7

MIN_PITCH_WIDTH = 54
MAX_PITCH_WIDTH = 88
MIN_PITCH_GAP = 4
MAX_PITCH_GAP = 10

YELLOW_BRANCH_MIN_SPACING = 1.0
BLUE_BRANCH_MIN_SPACING = 1.0

SPEED_STEP = 0.05
MIN_SPEED_FACTOR = 0.05
MAX_SPEED_FACTOR = 2.00

MIN_WINDOW_WIDTH = 1100
MIN_WINDOW_HEIGHT = 700

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
# Utility helpers
# ----------------------------
def clamp(value, min_value, max_value):
    return max(min_value, min(max_value, value))

def scaled_y(base_y, screen_height):
    top_reserved = 130
    bottom_reserved = 70
    base_drawable = BASE_SCREEN_HEIGHT - top_reserved - bottom_reserved
    current_drawable = max(300, screen_height - top_reserved - bottom_reserved)
    relative = (base_y - top_reserved) / base_drawable
    return int(top_reserved + relative * current_drawable)

def make_font(size, bold=False):
    return pygame.font.SysFont("arial", max(12, int(size)), bold=bold)

# ----------------------------
# Responsive proportional layout
# ----------------------------
def compute_layout(screen_width, screen_height):
    screen_width = max(MIN_WINDOW_WIDTH, screen_width)
    screen_height = max(MIN_WINDOW_HEIGHT, screen_height)

    width_scale = screen_width / BASE_SCREEN_WIDTH
    height_scale = screen_height / BASE_SCREEN_HEIGHT
    ui_scale = clamp(min(width_scale, height_scale), 0.78, 1.35)

    title_x = int(BASE_TITLE_X * width_scale)
    title_y = scaled_y(BASE_TITLE_Y, screen_height)
    takt_x = int(BASE_TAKT_X * width_scale)
    takt_y = scaled_y(BASE_TAKT_Y, screen_height)

    control_panel_x = int(BASE_CONTROL_PANEL_X * width_scale)
    control_panel_y = scaled_y(BASE_CONTROL_PANEL_Y, screen_height)
    control_panel_w = int(BASE_CONTROL_PANEL_W * width_scale)
    control_panel_h = int(BASE_CONTROL_PANEL_H * ui_scale)

    diagram_left = max(20, int(DIAGRAM_LEFT_MARGIN * width_scale))
    diagram_right = screen_width - max(20, int(DIAGRAM_RIGHT_MARGIN * width_scale))
    total_width = diagram_right - diagram_left

    branch_offset_x = int(BRANCH_START_OFFSET_X * width_scale)

    main_top = scaled_y(BASE_MAIN_TOP, screen_height)
    blue_branch_top = scaled_y(BASE_BLUE_BRANCH_TOP, screen_height)
    yellow_branch_top = scaled_y(BASE_YELLOW_BRANCH_TOP, screen_height)

    pitch_height = int(BASE_PITCH_HEIGHT * ui_scale)
    pitch_height = clamp(pitch_height, 68, 110)

    branch_label_offset = int(BASE_BRANCH_LABEL_OFFSET * ui_scale)
    main_label_offset = int(BASE_MAIN_LABEL_OFFSET * ui_scale)
    pitch_label_offset = int(BASE_PITCH_LABEL_OFFSET * ui_scale)
    rail_thickness = int(BASE_RAIL_THICKNESS * ui_scale)
    rail_thickness = clamp(rail_thickness, 10, 18)
    rail_offset_y = int(BASE_RAIL_OFFSET_Y * ui_scale)

    step_guess = int((total_width - branch_offset_x) / (NUM_PITCHES_MAIN + NUM_PITCHES_BLUE))
    step_guess = max(step_guess, MIN_PITCH_WIDTH + MIN_PITCH_GAP)

    pitch_gap = max(MIN_PITCH_GAP, min(MAX_PITCH_GAP, int(step_guess * 0.10)))
    pitch_width = step_guess - pitch_gap
    pitch_width = max(MIN_PITCH_WIDTH, min(MAX_PITCH_WIDTH, pitch_width))
    pitch_gap = max(MIN_PITCH_GAP, min(MAX_PITCH_GAP, pitch_gap))
    step = pitch_width + pitch_gap

    main_total_w = NUM_PITCHES_MAIN * step - pitch_gap
    branch_total_w = NUM_PITCHES_BLUE * step - pitch_gap

    # left align main line with control panel if possible
    main_left = control_panel_x
    branch_start_x = int(main_left + main_total_w + branch_offset_x)

    branch_end = branch_start_x + branch_total_w
    overflow = branch_end - diagram_right
    if overflow > 0:
        main_left -= int(overflow)
        branch_start_x -= int(overflow)

    if main_left < diagram_left:
        shift = diagram_left - main_left
        main_left += shift
        branch_start_x += shift

    blue_minus_w = int(44 * ui_scale)
    blue_minus_h = int(34 * ui_scale)
    plus_w = int(44 * ui_scale)
    plus_h = int(34 * ui_scale)
    reset_w = int(RESET_BUTTON_W * ui_scale)
    reset_h = int(RESET_BUTTON_H * ui_scale)

    buttons = {
        "blue_minus": pygame.Rect(
            control_panel_x + int(BLUE_MINUS_X_OFFSET * width_scale),
            control_panel_y + int(36 * ui_scale),
            blue_minus_w,
            blue_minus_h
        ),
        "blue_plus": pygame.Rect(
            control_panel_x + int(BLUE_PLUS_X_OFFSET * width_scale),
            control_panel_y + int(36 * ui_scale),
            plus_w,
            plus_h
        ),
        "yellow_minus": pygame.Rect(
            control_panel_x + int(YELLOW_MINUS_X_OFFSET * width_scale),
            control_panel_y + int(36 * ui_scale),
            blue_minus_w,
            blue_minus_h
        ),
        "yellow_plus": pygame.Rect(
            control_panel_x + int(YELLOW_PLUS_X_OFFSET * width_scale),
            control_panel_y + int(36 * ui_scale),
            plus_w,
            plus_h
        ),
        "reset": pygame.Rect(
            control_panel_x + int(RESET_BUTTON_X_OFFSET * width_scale),
            control_panel_y + int(RESET_BUTTON_Y_OFFSET * ui_scale),
            reset_w,
            reset_h
        ),
    }

    fonts = {
        "title": make_font(32 * ui_scale, bold=True),
        "subtitle": make_font(22 * ui_scale),
        "label": make_font(20 * ui_scale, bold=True),
        "small": make_font(16 * ui_scale),
        "button": make_font(22 * ui_scale, bold=True),
    }

    return {
        "screen_width": screen_width,
        "screen_height": screen_height,
        "title_x": title_x,
        "title_y": title_y,
        "takt_x": takt_x,
        "takt_y": takt_y,
        "control_panel_x": control_panel_x,
        "control_panel_y": control_panel_y,
        "control_panel_w": control_panel_w,
        "control_panel_h": control_panel_h,
        "main_top": main_top,
        "blue_branch_top": blue_branch_top,
        "yellow_branch_top": yellow_branch_top,
        "pitch_width": int(pitch_width),
        "pitch_gap": int(pitch_gap),
        "pitch_step": int(step),
        "pitch_height": int(pitch_height),
        "main_left": int(main_left),
        "branch_start_x": int(branch_start_x),
        "branch_offset_x": int(branch_offset_x),
        "diagram_right": int(diagram_right),
        "branch_label_offset": int(branch_label_offset),
        "main_label_offset": int(main_label_offset),
        "pitch_label_offset": int(pitch_label_offset),
        "rail_thickness": int(rail_thickness),
        "rail_offset_y": int(rail_offset_y),
        "buttons": buttons,
        "fonts": fonts,
        "ui_scale": ui_scale,
        "width_scale": width_scale,
        "height_scale": height_scale,
    }

# ----------------------------
# Geometry helpers
# ----------------------------
def main_pitch_rect(layout, pitch_num):
    x = layout["main_left"] + (pitch_num - 1) * layout["pitch_step"]
    y = layout["main_top"]
    return pygame.Rect(int(x), int(y), layout["pitch_width"], layout["pitch_height"])

def split_origin(layout):
    rect = main_pitch_rect(layout, SPLIT_PITCH)
    return rect.x + rect.width, rect.y + rect.height / 2

def branch_pitch_rect(layout, branch_name, pitch_num):
    x = layout["branch_start_x"] + (pitch_num - 1) * layout["pitch_step"]
    y = layout["blue_branch_top"] if branch_name == "blue_branch" else layout["yellow_branch_top"]
    return pygame.Rect(int(x), int(y), layout["pitch_width"], layout["pitch_height"])

def interpolate_position(rect_a, rect_b, frac):
    x = rect_a.x + (rect_b.x - rect_a.x) * frac
    y = rect_a.y + (rect_b.y - rect_a.y) * frac
    return x, y

def get_vehicle_xy(layout, route, pitch_float):
    if route == "main":
        if pitch_float <= 1:
            rect = main_pitch_rect(layout, 1)
            return rect.x + layout["pitch_width"] * 0.12, rect.y + layout["pitch_height"] * 0.42
        if pitch_float >= NUM_PITCHES_MAIN:
            rect = main_pitch_rect(layout, NUM_PITCHES_MAIN)
            return rect.x + layout["pitch_width"] * 0.12, rect.y + layout["pitch_height"] * 0.42
        base = int(pitch_float)
        frac = pitch_float - base
        rect_a = main_pitch_rect(layout, base)
        rect_b = main_pitch_rect(layout, base + 1)
        x, y = interpolate_position(rect_a, rect_b, frac)
        return x + layout["pitch_width"] * 0.12, y + layout["pitch_height"] * 0.42

    if route == "blue_branch":
        if pitch_float <= 1:
            rect = branch_pitch_rect(layout, "blue_branch", 1)
            return rect.x + layout["pitch_width"] * 0.12, rect.y + layout["pitch_height"] * 0.42
        if pitch_float >= NUM_PITCHES_BLUE:
            rect = branch_pitch_rect(layout, "blue_branch", NUM_PITCHES_BLUE)
            return rect.x + layout["pitch_width"] * 0.12, rect.y + layout["pitch_height"] * 0.42
        base = int(pitch_float)
        frac = pitch_float - base
        rect_a = branch_pitch_rect(layout, "blue_branch", base)
        rect_b = branch_pitch_rect(layout, "blue_branch", base + 1)
        x, y = interpolate_position(rect_a, rect_b, frac)
        return x + layout["pitch_width"] * 0.12, y + layout["pitch_height"] * 0.42

    if route == "yellow_branch":
        if pitch_float <= 1:
            rect = branch_pitch_rect(layout, "yellow_branch", 1)
            return rect.x + layout["pitch_width"] * 0.12, rect.y + layout["pitch_height"] * 0.42
        if pitch_float >= NUM_PITCHES_YELLOW:
            rect = branch_pitch_rect(layout, "yellow_branch", NUM_PITCHES_YELLOW)
            return rect.x + layout["pitch_width"] * 0.12, rect.y + layout["pitch_height"] * 0.42
        base = int(pitch_float)
        frac = pitch_float - base
        rect_a = branch_pitch_rect(layout, "yellow_branch", base)
        rect_b = branch_pitch_rect(layout, "yellow_branch", base + 1)
        x, y = interpolate_position(rect_a, rect_b, frac)
        return x + layout["pitch_width"] * 0.12, y + layout["pitch_height"] * 0.42

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

def draw_pitch(surface, font, pitch_num, rect, prefix, pitch_label_offset):
    pygame.draw.rect(surface, LINE_COLOR, rect, border_radius=8)
    pygame.draw.rect(surface, LINE_BORDER, rect, width=2, border_radius=8)

    label = font.render(f"{prefix}{pitch_num}", True, TEXT_COLOR)
    label_rect = label.get_rect(center=(rect.centerx, rect.bottom + pitch_label_offset))
    surface.blit(label, label_rect)

def draw_vehicle(surface, x, y, scale, body_color, current_pitch_width, ui_scale):
    body_w = int(min(62 * ui_scale, current_pitch_width * 0.78) * scale)
    body_h = int(22 * ui_scale * scale)
    cabin_w = int(min(28 * ui_scale, current_pitch_width * 0.34) * scale)
    cabin_h = int(16 * ui_scale * scale)
    wheel_d = int(11 * ui_scale * scale)

    body_rect = pygame.Rect(int(x), int(y), body_w, body_h)
    pygame.draw.rect(surface, body_color, body_rect, border_radius=max(5, int(8 * ui_scale)))

    cabin_rect = pygame.Rect(int(x + body_w * 0.28), int(y - 13 * ui_scale * scale), cabin_w, cabin_h)
    pygame.draw.rect(surface, VEHICLE_WINDOW, cabin_rect, border_radius=max(4, int(6 * ui_scale)))
    pygame.draw.rect(surface, body_color, cabin_rect, width=max(1, int(2 * ui_scale)), border_radius=max(4, int(6 * ui_scale)))

    pygame.draw.circle(surface, WHEEL_COLOR, (int(x + body_w * 0.20), int(y + 22 * ui_scale * scale)), max(2, wheel_d // 2))
    pygame.draw.circle(surface, WHEEL_COLOR, (int(x + body_w * 0.78), int(y + 22 * ui_scale * scale)), max(2, wheel_d // 2))

def draw_button(surface, rect, font, text, mouse_pos):
    is_hovered = rect.collidepoint(mouse_pos)
    color = BUTTON_BLUE_HOVER if is_hovered else BUTTON_BLUE
    pygame.draw.rect(surface, color, rect, border_radius=8)
    pygame.draw.rect(surface, ACCENT_BLUE, rect, width=2, border_radius=8)
    draw_text(surface, text, font, BUTTON_TEXT, rect.centerx, rect.centery, center=True)

def draw_branch_connector(surface, layout, branch_name, color):
    split_x, split_y = split_origin(layout)
    rect = branch_pitch_rect(layout, branch_name, 1)
    branch_center_y = rect.y + rect.height / 2

    elbow_x = split_x + max(6, int(8 * layout["ui_scale"]))
    end_x = rect.x - max(4, int(6 * layout["ui_scale"]))
    line_width = max(3, int(4 * layout["ui_scale"]))

    points = [
        (int(split_x), int(split_y)),
        (int(elbow_x), int(split_y)),
        (int(end_x), int(branch_center_y)),
        (int(rect.x), int(branch_center_y)),
    ]
    pygame.draw.lines(surface, color, False, points, line_width)

def draw_main_line(surface, layout, label_font):
    first_rect = main_pitch_rect(layout, 1)
    last_rect = main_pitch_rect(layout, NUM_PITCHES_MAIN)

    label_rect = pygame.Rect(
        first_rect.x,
        first_rect.y - layout["main_label_offset"],
        last_rect.right - first_rect.x,
        max(24, int(30 * layout["ui_scale"]))
    )
    pygame.draw.rect(surface, ACCENT_GREEN, label_rect, border_radius=4)
    draw_text(surface, "Main Line", label_font, (255, 255, 255), label_rect.centerx, label_rect.centery, center=True)

    rail_y = first_rect.y + layout["pitch_height"] / 2 - layout["rail_offset_y"]
    rail_rect = pygame.Rect(
        first_rect.x,
        int(rail_y),
        last_rect.right - first_rect.x,
        layout["rail_thickness"]
    )
    pygame.draw.rect(surface, RAIL_COLOR, rail_rect, border_radius=3)

    for i in range(1, NUM_PITCHES_MAIN + 1):
        draw_pitch(surface, label_font, i, main_pitch_rect(layout, i), "P", layout["pitch_label_offset"])

def draw_branch_line(surface, layout, label_font, branch_name, label, prefix):
    last_pitch = NUM_PITCHES_BLUE if branch_name == "blue_branch" else NUM_PITCHES_YELLOW
    rect1 = branch_pitch_rect(layout, branch_name, 1)
    rect_last = branch_pitch_rect(layout, branch_name, last_pitch)

    label_rect = pygame.Rect(
        rect1.x,
        rect1.y - layout["branch_label_offset"],
        rect_last.right - rect1.x,
        max(24, int(30 * layout["ui_scale"]))
    )
    pygame.draw.rect(surface, ACCENT_GREEN, label_rect, border_radius=4)
    draw_text(surface, label, label_font, (255, 255, 255), label_rect.centerx, label_rect.centery, center=True)

    rail_y = rect1.y + layout["pitch_height"] / 2 - layout["rail_offset_y"]
    rail_rect = pygame.Rect(
        rect1.x,
        int(rail_y),
        rect_last.right - rect1.x,
        layout["rail_thickness"]
    )
    pygame.draw.rect(surface, RAIL_COLOR, rail_rect, border_radius=3)

    for i in range(1, last_pitch + 1):
        draw_pitch(surface, label_font, i, branch_pitch_rect(layout, branch_name, i), prefix, layout["pitch_label_offset"])

def draw_header_controls(surface, layout, blue_speed_factor, yellow_speed_factor):
    fonts = layout["fonts"]
    subtitle_font = fonts["subtitle"]
    button_font = fonts["button"]
    mouse_pos = pygame.mouse.get_pos()
    buttons = layout["buttons"]

    panel_rect = pygame.Rect(
        layout["control_panel_x"],
        layout["control_panel_y"],
        layout["control_panel_w"],
        layout["control_panel_h"]
    )
    pygame.draw.rect(surface, PANEL_BG, panel_rect, border_radius=12)
    pygame.draw.rect(surface, PANEL_BORDER, panel_rect, width=2, border_radius=12)

    draw_text(surface, "Blue Speed", subtitle_font, TITLE_COLOR, layout["control_panel_x"] + int(22 * layout["ui_scale"]), layout["control_panel_y"] + int(13 * layout["ui_scale"]))
    draw_text(surface, f"{blue_speed_factor:.2f}x", subtitle_font, TEXT_COLOR, layout["control_panel_x"] + int(22 * layout["ui_scale"]), layout["control_panel_y"] + int(46 * layout["ui_scale"]))

    draw_button(surface, buttons["blue_minus"], button_font, "-", mouse_pos)
    draw_button(surface, buttons["blue_plus"], button_font, "+", mouse_pos)

    draw_text(surface, "Yellow Speed", subtitle_font, TITLE_COLOR, layout["control_panel_x"] + int(248 * layout["width_scale"]), layout["control_panel_y"] + int(13 * layout["ui_scale"]))
    draw_text(surface, f"{yellow_speed_factor:.2f}x", subtitle_font, TEXT_COLOR, layout["control_panel_x"] + int(248 * layout["width_scale"]), layout["control_panel_y"] + int(46 * layout["ui_scale"]))

    draw_button(surface, buttons["yellow_minus"], button_font, "-", mouse_pos)
    draw_button(surface, buttons["yellow_plus"], button_font, "+", mouse_pos)

    draw_text(surface, "System", subtitle_font, TITLE_COLOR, layout["control_panel_x"] + int(500 * layout["width_scale"]), layout["control_panel_y"] + int(13 * layout["ui_scale"]))
    draw_button(surface, buttons["reset"], button_font, "Reset", mouse_pos)

def draw_scene(surface, layout, vehicles, takt_display, blue_speed_factor, yellow_speed_factor):
    surface.fill(BG_COLOR)

    fonts = layout["fonts"]
    title_font = fonts["title"]
    subtitle_font = fonts["subtitle"]
    label_font = fonts["label"]

    draw_text(
        surface,
        "Main Line Splits into Horizontal Blue and Yellow Branch Lines",
        title_font,
        TITLE_COLOR,
        layout["title_x"],
        layout["title_y"]
    )
    draw_text(
        surface,
        f"Takt: {takt_display}",
        subtitle_font,
        TEXT_COLOR,
        layout["takt_x"],
        layout["takt_y"]
    )

    draw_header_controls(surface, layout, blue_speed_factor, yellow_speed_factor)

    draw_main_line(surface, layout, label_font)
    draw_branch_line(surface, layout, label_font, "blue_branch", "Blue Branch Line", "B")
    draw_branch_line(surface, layout, label_font, "yellow_branch", "Yellow Branch Line", "Y")

    draw_branch_connector(surface, layout, "blue_branch", SPLIT_LINE_BLUE)
    draw_branch_connector(surface, layout, "yellow_branch", SPLIT_LINE_YELLOW)

    for vehicle in vehicles:
        if vehicle.route == "main" and vehicle.main_pitch_float is not None:
            x, y = get_vehicle_xy(layout, "main", vehicle.main_pitch_float)
            draw_vehicle(surface, x, y, 1.0, vehicle.color, layout["pitch_width"], layout["ui_scale"])
        elif vehicle.route == "blue_branch" and vehicle.branch_pitch_float is not None:
            x, y = get_vehicle_xy(layout, "blue_branch", vehicle.branch_pitch_float)
            draw_vehicle(surface, x, y, 1.0, vehicle.color, layout["pitch_width"], layout["ui_scale"])
        elif vehicle.route == "yellow_branch" and vehicle.branch_pitch_float is not None:
            x, y = get_vehicle_xy(layout, "yellow_branch", vehicle.branch_pitch_float)
            draw_vehicle(surface, x, y, 1.0, vehicle.color, layout["pitch_width"], layout["ui_scale"])

    draw_text(
        surface,
        "Third version: proportional scaling for pitch height, vehicles, labels, rails, buttons, and connectors.",
        subtitle_font,
        ACCENT_BLUE,
        layout["screen_width"] // 2,
        layout["screen_height"] - max(30, int(35 * layout["ui_scale"])),
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

# ----------------------------
# Main loop
# ----------------------------
def main():
    pygame.init()

    screen_width = BASE_SCREEN_WIDTH
    screen_height = BASE_SCREEN_HEIGHT

    screen = pygame.display.set_mode((screen_width, screen_height), pygame.RESIZABLE)
    pygame.display.set_caption("Vehicle Production Line Split Layout")
    clock = pygame.time.Clock()

    layout = compute_layout(screen_width, screen_height)

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

            elif event.type == pygame.VIDEORESIZE:
                screen_width = max(MIN_WINDOW_WIDTH, event.w)
                screen_height = max(MIN_WINDOW_HEIGHT, event.h)
                screen = pygame.display.set_mode((screen_width, screen_height), pygame.RESIZABLE)
                layout = compute_layout(screen_width, screen_height)

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                buttons = layout["buttons"]

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
            layout,
            vehicles,
            current_takt,
            blue_branch_speed_factor,
            yellow_branch_speed_factor
        )
        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()