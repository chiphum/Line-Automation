import pygame
import sys

try:
    import version
except ImportError:

    class version:
        APP_NAME = "Assembly Line Simulator"

        @staticmethod
        def get_version():
            return "0.4.1"


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
SUBTLE_TEXT = (95, 110, 125)
TITLE_COLOR = (36, 52, 71)
LINE_COLOR = (210, 214, 220)
LINE_BORDER = (130, 140, 150)
ACCENT_GREEN = (76, 175, 80)
ACCENT_BLUE = (52, 120, 189)
ACCENT_ORANGE = (227, 138, 50)
BUTTON_BLUE = (52, 120, 189)
BUTTON_BLUE_HOVER = (72, 140, 209)
BUTTON_GREEN = (76, 175, 80)
BUTTON_GREEN_HOVER = (96, 195, 100)
BUTTON_ORANGE = (227, 138, 50)
BUTTON_ORANGE_HOVER = (240, 156, 72)
BUTTON_GRAY = (110, 122, 136)
BUTTON_GRAY_HOVER = (128, 140, 154)
BUTTON_TEXT = (255, 255, 255)
PANEL_BG = (232, 237, 243)
PANEL_BORDER = (190, 198, 208)
LEGEND_BG = (248, 250, 252)
OVERLAY_BG = (255, 255, 255, 220)

VEHICLE_BLUE = (47, 99, 163)
VEHICLE_YELLOW = (232, 193, 33)
VEHICLE_WINDOW = (180, 210, 235)
WHEEL_COLOR = (45, 45, 45)
RAIL_COLOR = (180, 185, 192)
SPLIT_LINE_BLUE = (120, 150, 210)
SPLIT_LINE_YELLOW = (220, 190, 80)

TITLE_X = 40
TITLE_Y = 20
TAKT_X = 40
TAKT_Y = 70
VERSION_X = 250
VERSION_Y = 70
STATUS_X = 410
STATUS_Y = 70

CONTROL_PANEL_X = 40
CONTROL_PANEL_Y = 110
CONTROL_PANEL_W = 1520
CONTROL_PANEL_H = 132  # increased to support two clean rows

MAIN_LABEL_OFFSET_Y = 60
BRANCH_LABEL_OFFSET_Y = 45
OUT_LABEL_OFFSET_Y = 60
LABEL_BLOCK_HEIGHT = 30

DIAGRAM_LEFT = 70
DIAGRAM_RIGHT = SCREEN_WIDTH - 40

BRANCH_START_OFFSET_X = int(24 * DIAGRAM_SCALE)
OUT_START_OFFSET_X = 120

# ----------------------------
# Dynamic vertical layout (prevents overlap)
# ----------------------------
TOP_UI_BOTTOM = CONTROL_PANEL_Y + CONTROL_PANEL_H
VERTICAL_SPACING = 70

BLUE_BRANCH_TOP = TOP_UI_BOTTOM + VERTICAL_SPACING
MAIN_TOP = BLUE_BRANCH_TOP + 200
YELLOW_BRANCH_TOP = MAIN_TOP + 280
OUT_MAIN_TOP = MAIN_TOP

PITCH_HEIGHT = max(28, int(88 * DIAGRAM_SCALE))
MIN_PITCH_WIDTH = max(28, int(62 * DIAGRAM_SCALE))
MAX_PITCH_WIDTH = max(40, int(86 * DIAGRAM_SCALE))
MIN_PITCH_GAP = max(2, int(4 * DIAGRAM_SCALE))
MAX_PITCH_GAP = max(4, int(10 * DIAGRAM_SCALE))

MAIN_MIN_SPACING = 1.0
YELLOW_BRANCH_MIN_SPACING = 1.0
BLUE_BRANCH_MIN_SPACING = 1.0
OUT_MAIN_MIN_SPACING = 1.0

SPEED_STEP = 0.05
MIN_SPEED_FACTOR = 0.05
MAX_SPEED_FACTOR = 2.00

SPLIT_TRAVEL_TIME = 0.99
MERGE_TRAVEL_TIME = 0.99

AUTO_DEMO_INTERVAL = 8.0
AUTO_DEMO_SEQUENCE = ["balanced", "blue_faster", "yellow_faster"]

PRESETS = {
    "balanced": (0.50, 0.50),
    "blue_faster": (0.90, 0.30),
    "yellow_faster": (0.35, 0.90),
}

# CAD-style connector geometry
CONNECTOR_OFFSET = 22


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

    def is_on_screen(self):
        if self.route == "main" and self.main_pitch_float is not None:
            return self.main_pitch_float <= NUM_PITCHES_MAIN + 0.8
        if self.route == "blue_branch" and self.branch_pitch_float is not None:
            return self.branch_pitch_float <= NUM_PITCHES_BLUE + 0.8
        if self.route == "yellow_branch" and self.branch_pitch_float is not None:
            return self.branch_pitch_float <= NUM_PITCHES_YELLOW + 0.8
        if self.route == "out_main" and self.out_pitch_float is not None:
            return self.out_pitch_float <= NUM_PITCHES_OUT + 0.8
        if self.route in ("splitting", "merging"):
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
    target_x = rect.x
    target_y = rect.y + rect.height / 2

    elbow_x = split_x + CONNECTOR_OFFSET
    lead_in_x = target_x - CONNECTOR_OFFSET
    mid_y = (split_y + target_y) / 2

    return [
        (float(split_x), float(split_y)),
        (float(elbow_x), float(split_y)),
        (float(elbow_x), float(mid_y)),
        (float(lead_in_x), float(mid_y)),
        (float(lead_in_x), float(target_y)),
        (float(target_x), float(target_y)),
    ]


def get_merge_path_points(source_route):
    last_pitch = (
        NUM_PITCHES_BLUE if source_route == "blue_branch" else NUM_PITCHES_YELLOW
    )
    rect = branch_pitch_rect(source_route, last_pitch)

    start_x = rect.x + rect.width
    start_y = rect.y + rect.height / 2

    target_x, target_y = merge_target()

    elbow_x = start_x + CONNECTOR_OFFSET
    lead_in_x = target_x - CONNECTOR_OFFSET
    mid_y = (start_y + target_y) / 2

    return [
        (float(start_x), float(start_y)),
        (float(elbow_x), float(start_y)),
        (float(elbow_x), float(mid_y)),
        (float(lead_in_x), float(mid_y)),
        (float(lead_in_x), float(target_y)),
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
def create_fonts(presentation_mode=False):
    if presentation_mode:
        title_font = pygame.font.SysFont("arial", 42, bold=True)
        subtitle_font = pygame.font.SysFont("arial", 28)
        label_font = pygame.font.SysFont("arial", 26, bold=True)
        small_font = pygame.font.SysFont("arial", 20)
        button_font = pygame.font.SysFont("arial", 22, bold=True)
    else:
        title_font = pygame.font.SysFont("arial", 32, bold=True)
        subtitle_font = pygame.font.SysFont("arial", 22)
        label_font = pygame.font.SysFont("arial", 20, bold=True)
        small_font = pygame.font.SysFont("arial", 16)
        button_font = pygame.font.SysFont("arial", 20, bold=True)
    return (title_font, subtitle_font, label_font, small_font, button_font)


def draw_text(surface, text, font, color, x, y, center=False):
    rendered = font.render(text, True, color)
    rect = rendered.get_rect()
    if center:
        rect.center = (x, y)
    else:
        rect.topleft = (x, y)
    surface.blit(rendered, rect)


def draw_pitch(surface, font, pitch_num, rect, prefix, show_labels=True):
    pygame.draw.rect(surface, LINE_COLOR, rect, border_radius=6)
    pygame.draw.rect(surface, LINE_BORDER, rect, width=2, border_radius=6)

    if show_labels:
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
        int(x + body_w * 0.28),
        int(y - 13 * DIAGRAM_SCALE * scale),
        cabin_w,
        cabin_h,
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


def draw_button(
    surface,
    rect,
    font,
    text,
    mouse_pos,
    base_color=BUTTON_BLUE,
    hover_color=BUTTON_BLUE_HOVER,
):
    is_hovered = rect.collidepoint(mouse_pos)
    color = hover_color if is_hovered else base_color
    pygame.draw.rect(surface, color, rect, border_radius=8)
    border_color = ACCENT_BLUE if base_color == BUTTON_BLUE else PANEL_BORDER
    pygame.draw.rect(surface, border_color, rect, width=2, border_radius=8)
    draw_text(surface, text, font, BUTTON_TEXT, rect.centerx, rect.centery, center=True)


def draw_connector(surface, points, color):
    pygame.draw.lines(surface, color, False, [(int(x), int(y)) for x, y in points], 3)


def draw_input_main_line(surface, label_font, show_labels=True):
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
        "INPUT MAIN",
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
        draw_pitch(
            surface, label_font, i, main_pitch_rect(i), "P", show_labels=show_labels
        )


def draw_branch_line(surface, label_font, branch_name, label, prefix, show_labels=True):
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
        draw_pitch(
            surface,
            label_font,
            i,
            branch_pitch_rect(branch_name, i),
            prefix,
            show_labels=show_labels,
        )


def draw_output_main_line(surface, label_font, show_labels=True):
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
        "OUTPUT MAIN",
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
        draw_pitch(
            surface,
            label_font,
            i,
            output_main_pitch_rect(i),
            "O",
            show_labels=show_labels,
        )


def draw_header_controls(
    surface,
    fonts,
    buttons,
    blue_speed_factor,
    yellow_speed_factor,
    paused,
    show_labels,
    fullscreen,
    presentation_mode,
    auto_demo_mode,
):
    _, subtitle_font, _, _, button_font = fonts
    mouse_pos = pygame.mouse.get_pos()

    # Panel background
    panel_rect = pygame.Rect(
        CONTROL_PANEL_X, CONTROL_PANEL_Y, CONTROL_PANEL_W, CONTROL_PANEL_H
    )
    pygame.draw.rect(surface, PANEL_BG, panel_rect, border_radius=12)
    pygame.draw.rect(surface, PANEL_BORDER, panel_rect, width=2, border_radius=12)

    # ============================
    # LEFT SIDE (Blue / Yellow)
    # ============================
    draw_text(
        surface,
        "Blue Speed",
        subtitle_font,
        TITLE_COLOR,
        CONTROL_PANEL_X + 18,
        CONTROL_PANEL_Y + 12,
    )
    draw_text(
        surface,
        f"{blue_speed_factor:.2f}x",
        subtitle_font,
        TEXT_COLOR,
        CONTROL_PANEL_X + 20,
        CONTROL_PANEL_Y + 44,
    )

    draw_button(surface, buttons["blue_minus"], button_font, "-", mouse_pos)
    draw_button(surface, buttons["blue_plus"], button_font, "+", mouse_pos)

    draw_text(
        surface,
        "Yellow Speed",
        subtitle_font,
        TITLE_COLOR,
        CONTROL_PANEL_X + 226,
        CONTROL_PANEL_Y + 12,
    )
    draw_text(
        surface,
        f"{yellow_speed_factor:.2f}x",
        subtitle_font,
        TEXT_COLOR,
        CONTROL_PANEL_X + 228,
        CONTROL_PANEL_Y + 44,
    )

    draw_button(surface, buttons["yellow_minus"], button_font, "-", mouse_pos)
    draw_button(surface, buttons["yellow_plus"], button_font, "+", mouse_pos)

    # ============================
    # PLAYBACK
    # ============================
    draw_text(
        surface,
        "Playback",
        subtitle_font,
        TITLE_COLOR,
        CONTROL_PANEL_X + 450,
        CONTROL_PANEL_Y + 12,
    )

    draw_button(
        surface,
        buttons["play_pause"],
        button_font,
        "Play" if paused else "Pause",
        mouse_pos,
        base_color=BUTTON_GREEN,
        hover_color=BUTTON_GREEN_HOVER,
    )

    draw_button(
        surface,
        buttons["step"],
        button_font,
        "Step",
        mouse_pos,
        base_color=BUTTON_ORANGE,
        hover_color=BUTTON_ORANGE_HOVER,
    )

    draw_button(
        surface,
        buttons["reset"],
        button_font,
        "Reset",
        mouse_pos,
        base_color=BUTTON_GRAY,
        hover_color=BUTTON_GRAY_HOVER,
    )

    # ============================
    # PRESETS (MIDDLE COLUMN)
    # ============================
    draw_text(
        surface,
        "Presets",
        subtitle_font,
        TITLE_COLOR,
        CONTROL_PANEL_X + 790,
        CONTROL_PANEL_Y + 12,
    )

    # Bottom row buttons (safe row)
    draw_button(surface, buttons["preset_balanced"], button_font, "Balanced", mouse_pos)
    draw_button(surface, buttons["preset_blue"], button_font, "Blue Faster", mouse_pos)
    draw_button(
        surface, buttons["preset_yellow"], button_font, "Yellow Faster", mouse_pos
    )

    # ============================
    # RIGHT-SIDE STATUS + TOGGLES
    # ============================
    status_x = CONTROL_PANEL_X + 1160
    status_y = CONTROL_PANEL_Y + 12
    line_spacing = subtitle_font.get_height() + 6

    draw_text(
        surface,
        f"Labels: {'On' if show_labels else 'Off'}",
        subtitle_font,
        SUBTLE_TEXT,
        status_x,
        status_y,
    )

    draw_text(
        surface,
        f"Auto Demo: {'On' if auto_demo_mode else 'Off'}",
        subtitle_font,
        SUBTLE_TEXT,
        status_x,
        status_y + line_spacing,
    )

    draw_text(
        surface,
        f"Present: {'On' if presentation_mode else 'Off'}",
        subtitle_font,
        SUBTLE_TEXT,
        status_x,
        status_y + line_spacing * 2,
    )

    # Divider
    divider_x = status_x - 12
    pygame.draw.line(
        surface,
        PANEL_BORDER,
        (divider_x, CONTROL_PANEL_Y + 10),
        (divider_x, CONTROL_PANEL_Y + CONTROL_PANEL_H - 10),
        1,
    )

    # Buttons arranged in a 2x2 grid to the right
    draw_button(
        surface,
        buttons["toggle_labels"],
        button_font,
        "Labels",
        mouse_pos,
        base_color=BUTTON_GRAY,
        hover_color=BUTTON_GRAY_HOVER,
    )

    draw_button(
        surface,
        buttons["toggle_fullscreen"],
        button_font,
        "Windowed" if fullscreen else "Fullscreen",
        mouse_pos,
        base_color=BUTTON_BLUE,
        hover_color=BUTTON_BLUE_HOVER,
    )

    draw_button(
        surface,
        buttons["toggle_presentation"],
        button_font,
        "Present On" if presentation_mode else "Present Off",
        mouse_pos,
        base_color=BUTTON_GRAY,
        hover_color=BUTTON_GRAY_HOVER,
    )

    draw_button(
        surface,
        buttons["toggle_auto_demo"],
        button_font,
        "Auto Demo",
        mouse_pos,
        base_color=BUTTON_ORANGE,
        hover_color=BUTTON_ORANGE_HOVER,
    )


def draw_legend(
    surface,
    fonts,
    paused,
    blue_speed_factor,
    yellow_speed_factor,
    fullscreen,
    presentation_mode,
    auto_demo_mode,
):
    _, _, label_font, small_font, _ = fonts

    left_items = [
        "Blue vehicle → blue branch",
        "Yellow vehicle → yellow branch",
        "Blue split / merge path",
        "Yellow split / merge path",
    ]

    right_items = [
        f"Status: {'Paused' if paused else 'Running'}",
        f"Blue: {blue_speed_factor:.2f}x",
        f"Yellow: {yellow_speed_factor:.2f}x",
        f"Auto Demo: {'On' if auto_demo_mode else 'Off'}",
        f"Fullscreen: {'On' if fullscreen else 'Off'}",
        f"Present: {'On' if presentation_mode else 'Off'}",
        "Step advances one takt",
    ]

    max_left_width = 0
    for text in left_items:
        w = small_font.render(text, True, TEXT_COLOR).get_width()
        max_left_width = max(max_left_width, w)

    max_right_width = 0
    for text in right_items:
        w = small_font.render(text, True, TEXT_COLOR).get_width()
        max_right_width = max(max_right_width, w)

    icon_offset = 46
    padding = 16
    column_spacing = 40

    box_w = (
        padding * 2 + icon_offset + max_left_width + column_spacing + max_right_width
    )
    box_h = 210

    box_x = SCREEN_WIDTH - box_w - 36
    box_y = SCREEN_HEIGHT - box_h - 54
    box = pygame.Rect(int(box_x), int(box_y), int(box_w), int(box_h))

    pygame.draw.rect(surface, LEGEND_BG, box, border_radius=12)
    pygame.draw.rect(surface, PANEL_BORDER, box, width=2, border_radius=12)

    draw_text(surface, "Legend", label_font, TITLE_COLOR, box.x + 16, box.y + 12)

    left_x = box.x + icon_offset
    right_x = left_x + max_left_width + column_spacing

    pygame.draw.circle(surface, VEHICLE_BLUE, (box.x + 28, box.y + 52), 10)
    draw_text(surface, left_items[0], small_font, TEXT_COLOR, left_x, box.y + 43)

    pygame.draw.circle(surface, VEHICLE_YELLOW, (box.x + 28, box.y + 82), 10)
    draw_text(surface, left_items[1], small_font, TEXT_COLOR, left_x, box.y + 73)

    pygame.draw.line(
        surface,
        SPLIT_LINE_BLUE,
        (box.x + 16, box.y + 112),
        (box.x + 40, box.y + 112),
        4,
    )
    draw_text(surface, left_items[2], small_font, TEXT_COLOR, left_x, box.y + 103)

    pygame.draw.line(
        surface,
        SPLIT_LINE_YELLOW,
        (box.x + 16, box.y + 142),
        (box.x + 40, box.y + 142),
        4,
    )
    draw_text(surface, left_items[3], small_font, TEXT_COLOR, left_x, box.y + 133)

    y = box.y + 14
    line_height = small_font.get_height() + 6

    for text in right_items:
        draw_text(surface, text, small_font, SUBTLE_TEXT, right_x, y)
        y += line_height

    divider_x = right_x - 12
    pygame.draw.line(
        surface, PANEL_BORDER, (divider_x, box.y + 10), (divider_x, box.bottom - 10), 1
    )


def draw_shortcuts_bar(surface, small_font, presentation_mode):
    text = "Space Pause/Play   Right Step   F Fullscreen   P Presentation   A Auto Demo   L Labels   R Reset"
    if presentation_mode:
        overlay = pygame.Surface((1130, 34), pygame.SRCALPHA)
        overlay.fill(OVERLAY_BG)
        surface.blit(overlay, (40, SCREEN_HEIGHT - 52))
        pygame.draw.rect(
            surface,
            PANEL_BORDER,
            pygame.Rect(40, SCREEN_HEIGHT - 52, 1130, 34),
            width=1,
            border_radius=8,
        )
        draw_text(surface, text, small_font, TITLE_COLOR, 54, SCREEN_HEIGHT - 45)
    else:
        draw_text(surface, text, small_font, SUBTLE_TEXT, 40, SCREEN_HEIGHT - 32)


def draw_presentation_banner(
    surface, fonts, paused, blue_speed_factor, yellow_speed_factor, auto_demo_mode
):
    _, subtitle_font, _, small_font, _ = fonts
    overlay = pygame.Surface((520, 96), pygame.SRCALPHA)
    overlay.fill(OVERLAY_BG)
    surface.blit(overlay, (SCREEN_WIDTH - 560, 18))
    box = pygame.Rect(SCREEN_WIDTH - 560, 18, 520, 96)
    pygame.draw.rect(surface, PANEL_BORDER, box, width=1, border_radius=10)
    draw_text(
        surface, "Presentation Mode", subtitle_font, TITLE_COLOR, box.x + 16, box.y + 12
    )
    draw_text(
        surface,
        f"Status: {'Paused' if paused else 'Running'}",
        small_font,
        SUBTLE_TEXT,
        box.x + 18,
        box.y + 50,
    )
    draw_text(
        surface,
        f"Blue {blue_speed_factor:.2f}x   Yellow {yellow_speed_factor:.2f}x",
        small_font,
        SUBTLE_TEXT,
        box.x + 180,
        box.y + 50,
    )
    draw_text(
        surface,
        f"Auto Demo {'On' if auto_demo_mode else 'Off'}",
        small_font,
        SUBTLE_TEXT,
        box.x + 18,
        box.y + 72,
    )


def draw_scene(
    surface,
    vehicles,
    takt_display,
    buttons,
    blue_speed_factor,
    yellow_speed_factor,
    paused,
    show_labels,
    fullscreen,
    presentation_mode,
    auto_demo_mode,
):
    surface.fill(BG_COLOR)

    fonts = create_fonts(presentation_mode=presentation_mode)
    title_font, subtitle_font, label_font, small_font, _ = fonts

    effective_show_labels = False if presentation_mode else show_labels

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
    draw_text(
        surface,
        f"Version: {version.get_version()}",
        subtitle_font,
        TEXT_COLOR,
        VERSION_X,
        VERSION_Y,
    )
    draw_text(
        surface,
        f"Status: {'Paused' if paused else 'Running'}",
        subtitle_font,
        TEXT_COLOR,
        STATUS_X,
        STATUS_Y,
    )

    if presentation_mode:
        draw_presentation_banner(
            surface,
            fonts,
            paused,
            blue_speed_factor,
            yellow_speed_factor,
            auto_demo_mode,
        )
    else:
        draw_header_controls(
            surface,
            fonts,
            buttons,
            blue_speed_factor,
            yellow_speed_factor,
            paused,
            show_labels,
            fullscreen,
            presentation_mode,
            auto_demo_mode,
        )
        draw_legend(
            surface,
            fonts,
            paused,
            blue_speed_factor,
            yellow_speed_factor,
            fullscreen,
            presentation_mode,
            auto_demo_mode,
        )

    draw_input_main_line(surface, label_font, show_labels=effective_show_labels)
    draw_branch_line(
        surface,
        label_font,
        "blue_branch",
        "BLUE BRANCH",
        "B",
        show_labels=effective_show_labels,
    )
    draw_branch_line(
        surface,
        label_font,
        "yellow_branch",
        "YELLOW BRANCH",
        "Y",
        show_labels=effective_show_labels,
    )
    draw_output_main_line(surface, label_font, show_labels=effective_show_labels)

    draw_connector(surface, get_split_path_points("blue_branch"), SPLIT_LINE_BLUE)
    draw_connector(surface, get_split_path_points("yellow_branch"), SPLIT_LINE_YELLOW)
    draw_connector(surface, get_merge_path_points("blue_branch"), SPLIT_LINE_BLUE)
    draw_connector(surface, get_merge_path_points("yellow_branch"), SPLIT_LINE_YELLOW)

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

    draw_shortcuts_bar(surface, small_font, presentation_mode)


# ----------------------------
# Simulation helpers
# ----------------------------
def clamp(value, min_value, max_value):
    return max(min_value, min(max_value, value))


def update_line_positions(vehicles_on_line, position_attr, speed, min_spacing):
    vehicles_on_line.sort(key=lambda v: getattr(v, position_attr), reverse=True)

    for i, vehicle in enumerate(vehicles_on_line):
        current_position = getattr(vehicle, position_attr)
        proposed_position = current_position + speed

        if i == 0:
            setattr(vehicle, position_attr, proposed_position)
        else:
            vehicle_ahead = vehicles_on_line[i - 1]
            ahead_position = getattr(vehicle_ahead, position_attr)
            target_position = ahead_position - min_spacing
            setattr(vehicle, position_attr, min(proposed_position, target_position))


def update_main_line(main_vehicles, delta_pitch_main):
    update_line_positions(
        main_vehicles, "main_pitch_float", delta_pitch_main, MAIN_MIN_SPACING
    )


def update_branch_line(branch_vehicles, speed_factor, min_spacing, delta_pitch_main):
    branch_speed = delta_pitch_main * speed_factor
    update_line_positions(
        branch_vehicles, "branch_pitch_float", branch_speed, min_spacing
    )


def update_output_main_line(out_vehicles, delta_pitch_main):
    update_line_positions(
        out_vehicles, "out_pitch_float", delta_pitch_main, OUT_MAIN_MIN_SPACING
    )


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
        source_route = chosen.route
        chosen.route = "merging"
        chosen.merge_source_route = source_route
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


def apply_preset(preset_name):
    return PRESETS[preset_name]


def simulate_increment(
    vehicles,
    next_vehicle_id,
    elapsed_since_takt,
    current_takt,
    merge_state,
    blue_branch_speed_factor,
    yellow_branch_speed_factor,
    dt,
):
    elapsed_since_takt += dt
    delta_pitch_main = dt / TAKT_TIME_MAIN

    main_vehicles = [
        v for v in vehicles if v.route == "main" and v.main_pitch_float is not None
    ]
    update_main_line(main_vehicles, delta_pitch_main)

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
        v for v in vehicles if v.route == "out_main" and v.out_pitch_float is not None
    ]
    update_output_main_line(out_main_vehicles, delta_pitch_main)

    while elapsed_since_takt >= TAKT_TIME_MAIN:
        elapsed_since_takt -= TAKT_TIME_MAIN
        current_takt += 1
        if next_vehicle_id <= MAX_VEHICLES:
            vehicles.append(Vehicle(next_vehicle_id))
            next_vehicle_id += 1

    vehicles = [v for v in vehicles if v.is_on_screen()]
    return vehicles, next_vehicle_id, elapsed_since_takt, current_takt, merge_state


def step_one_takt(
    vehicles,
    next_vehicle_id,
    elapsed_since_takt,
    current_takt,
    merge_state,
    blue_branch_speed_factor,
    yellow_branch_speed_factor,
):
    substeps = max(1, int(FPS * TAKT_TIME_MAIN))
    dt = TAKT_TIME_MAIN / substeps
    for _ in range(substeps):
        vehicles, next_vehicle_id, elapsed_since_takt, current_takt, merge_state = (
            simulate_increment(
                vehicles,
                next_vehicle_id,
                elapsed_since_takt,
                current_takt,
                merge_state,
                blue_branch_speed_factor,
                yellow_branch_speed_factor,
                dt,
            )
        )
    return vehicles, next_vehicle_id, elapsed_since_takt, current_takt, merge_state


def create_display(fullscreen=False):
    flags = pygame.SCALED
    if fullscreen:
        flags |= pygame.FULLSCREEN
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), flags)
    pygame.display.set_caption(f"{version.APP_NAME} v{version.get_version()}")
    return screen


def toggle_auto_demo(
    auto_demo_mode, blue_branch_speed_factor, yellow_branch_speed_factor
):
    if auto_demo_mode:
        auto_demo_index = 0
        preset_name = AUTO_DEMO_SEQUENCE[auto_demo_index]
        blue_branch_speed_factor, yellow_branch_speed_factor = apply_preset(preset_name)
        auto_demo_timer = 0.0
        return (
            True,
            auto_demo_index,
            auto_demo_timer,
            blue_branch_speed_factor,
            yellow_branch_speed_factor,
        )
    return False, 0, 0.0, blue_branch_speed_factor, yellow_branch_speed_factor


# ----------------------------
# Main loop
# ----------------------------
def main():
    pygame.init()
    screen = create_display(fullscreen=False)
    clock = pygame.time.Clock()

    buttons = {
        "blue_minus": pygame.Rect(CONTROL_PANEL_X + 100, CONTROL_PANEL_Y + 34, 42, 34),
        "blue_plus": pygame.Rect(CONTROL_PANEL_X + 148, CONTROL_PANEL_Y + 34, 42, 34),
        "yellow_minus": pygame.Rect(
            CONTROL_PANEL_X + 312, CONTROL_PANEL_Y + 34, 42, 34
        ),
        "yellow_plus": pygame.Rect(CONTROL_PANEL_X + 360, CONTROL_PANEL_Y + 34, 42, 34),
        "play_pause": pygame.Rect(CONTROL_PANEL_X + 440, CONTROL_PANEL_Y + 34, 90, 38),
        "step": pygame.Rect(CONTROL_PANEL_X + 540, CONTROL_PANEL_Y + 34, 84, 38),
        "reset": pygame.Rect(CONTROL_PANEL_X + 634, CONTROL_PANEL_Y + 34, 84, 38),
        # Presets moved to lower row
        "preset_balanced": pygame.Rect(
            CONTROL_PANEL_X + 768, CONTROL_PANEL_Y + 58, 110, 38
        ),
        "preset_blue": pygame.Rect(
            CONTROL_PANEL_X + 888, CONTROL_PANEL_Y + 58, 132, 38
        ),
        "preset_yellow": pygame.Rect(
            CONTROL_PANEL_X + 1030, CONTROL_PANEL_Y + 58, 142, 38
        ),
        # Right-side toggles
        "toggle_labels": pygame.Rect(
            CONTROL_PANEL_X + 1170, CONTROL_PANEL_Y + 16, 114, 34
        ),
        "toggle_fullscreen": pygame.Rect(
            CONTROL_PANEL_X + 1298, CONTROL_PANEL_Y + 16, 136, 34
        ),
        "toggle_presentation": pygame.Rect(
            CONTROL_PANEL_X + 1170, CONTROL_PANEL_Y + 60, 140, 34
        ),
        "toggle_auto_demo": pygame.Rect(
            CONTROL_PANEL_X + 1322, CONTROL_PANEL_Y + 60, 124, 34
        ),
    }

    blue_branch_speed_factor = INITIAL_BLUE_BRANCH_SPEED_FACTOR
    yellow_branch_speed_factor = INITIAL_YELLOW_BRANCH_SPEED_FACTOR
    paused = False
    show_labels = True
    fullscreen = False
    presentation_mode = False
    auto_demo_mode = False
    auto_demo_index = 0
    auto_demo_timer = 0.0

    vehicles, next_vehicle_id, elapsed_since_takt, current_takt, merge_state = (
        reset_simulation()
    )

    running = True
    while running:
        frame_dt = clock.tick(FPS) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    paused = not paused
                elif event.key == pygame.K_r:
                    (
                        vehicles,
                        next_vehicle_id,
                        elapsed_since_takt,
                        current_takt,
                        merge_state,
                    ) = reset_simulation()
                elif event.key == pygame.K_l:
                    show_labels = not show_labels
                elif event.key == pygame.K_f:
                    fullscreen = not fullscreen
                    screen = create_display(fullscreen=fullscreen)
                elif event.key == pygame.K_p:
                    presentation_mode = not presentation_mode
                elif event.key == pygame.K_a:
                    auto_demo_mode = not auto_demo_mode
                    if auto_demo_mode:
                        (
                            auto_demo_mode,
                            auto_demo_index,
                            auto_demo_timer,
                            blue_branch_speed_factor,
                            yellow_branch_speed_factor,
                        ) = toggle_auto_demo(
                            auto_demo_mode,
                            blue_branch_speed_factor,
                            yellow_branch_speed_factor,
                        )
                elif event.key == pygame.K_RIGHT and paused:
                    (
                        vehicles,
                        next_vehicle_id,
                        elapsed_since_takt,
                        current_takt,
                        merge_state,
                    ) = step_one_takt(
                        vehicles,
                        next_vehicle_id,
                        elapsed_since_takt,
                        current_takt,
                        merge_state,
                        blue_branch_speed_factor,
                        yellow_branch_speed_factor,
                    )

            if (
                event.type == pygame.MOUSEBUTTONDOWN
                and event.button == 1
                and not presentation_mode
            ):
                if buttons["play_pause"].collidepoint(event.pos):
                    paused = not paused
                elif buttons["step"].collidepoint(event.pos):
                    (
                        vehicles,
                        next_vehicle_id,
                        elapsed_since_takt,
                        current_takt,
                        merge_state,
                    ) = step_one_takt(
                        vehicles,
                        next_vehicle_id,
                        elapsed_since_takt,
                        current_takt,
                        merge_state,
                        blue_branch_speed_factor,
                        yellow_branch_speed_factor,
                    )
                elif buttons["reset"].collidepoint(event.pos):
                    (
                        vehicles,
                        next_vehicle_id,
                        elapsed_since_takt,
                        current_takt,
                        merge_state,
                    ) = reset_simulation()
                    blue_branch_speed_factor = INITIAL_BLUE_BRANCH_SPEED_FACTOR
                    yellow_branch_speed_factor = INITIAL_YELLOW_BRANCH_SPEED_FACTOR
                    paused = False
                    auto_demo_timer = 0.0
                elif buttons["blue_minus"].collidepoint(event.pos):
                    blue_branch_speed_factor = clamp(
                        blue_branch_speed_factor - SPEED_STEP,
                        MIN_SPEED_FACTOR,
                        MAX_SPEED_FACTOR,
                    )
                    auto_demo_mode = False
                elif buttons["blue_plus"].collidepoint(event.pos):
                    blue_branch_speed_factor = clamp(
                        blue_branch_speed_factor + SPEED_STEP,
                        MIN_SPEED_FACTOR,
                        MAX_SPEED_FACTOR,
                    )
                    auto_demo_mode = False
                elif buttons["yellow_minus"].collidepoint(event.pos):
                    yellow_branch_speed_factor = clamp(
                        yellow_branch_speed_factor - SPEED_STEP,
                        MIN_SPEED_FACTOR,
                        MAX_SPEED_FACTOR,
                    )
                    auto_demo_mode = False
                elif buttons["yellow_plus"].collidepoint(event.pos):
                    yellow_branch_speed_factor = clamp(
                        yellow_branch_speed_factor + SPEED_STEP,
                        MIN_SPEED_FACTOR,
                        MAX_SPEED_FACTOR,
                    )
                    auto_demo_mode = False
                elif buttons["preset_balanced"].collidepoint(event.pos):
                    blue_branch_speed_factor, yellow_branch_speed_factor = apply_preset(
                        "balanced"
                    )
                    auto_demo_mode = False
                elif buttons["preset_blue"].collidepoint(event.pos):
                    blue_branch_speed_factor, yellow_branch_speed_factor = apply_preset(
                        "blue_faster"
                    )
                    auto_demo_mode = False
                elif buttons["preset_yellow"].collidepoint(event.pos):
                    blue_branch_speed_factor, yellow_branch_speed_factor = apply_preset(
                        "yellow_faster"
                    )
                    auto_demo_mode = False
                elif buttons["toggle_labels"].collidepoint(event.pos):
                    show_labels = not show_labels
                elif buttons["toggle_fullscreen"].collidepoint(event.pos):
                    fullscreen = not fullscreen
                    screen = create_display(fullscreen=fullscreen)
                elif buttons["toggle_presentation"].collidepoint(event.pos):
                    presentation_mode = not presentation_mode
                elif buttons["toggle_auto_demo"].collidepoint(event.pos):
                    auto_demo_mode = not auto_demo_mode
                    if auto_demo_mode:
                        (
                            auto_demo_mode,
                            auto_demo_index,
                            auto_demo_timer,
                            blue_branch_speed_factor,
                            yellow_branch_speed_factor,
                        ) = toggle_auto_demo(
                            auto_demo_mode,
                            blue_branch_speed_factor,
                            yellow_branch_speed_factor,
                        )

        if auto_demo_mode and not paused:
            auto_demo_timer += frame_dt
            if auto_demo_timer >= AUTO_DEMO_INTERVAL:
                auto_demo_timer = 0.0
                auto_demo_index = (auto_demo_index + 1) % len(AUTO_DEMO_SEQUENCE)
                preset_name = AUTO_DEMO_SEQUENCE[auto_demo_index]
                blue_branch_speed_factor, yellow_branch_speed_factor = apply_preset(
                    preset_name
                )

        if not paused:
            vehicles, next_vehicle_id, elapsed_since_takt, current_takt, merge_state = (
                simulate_increment(
                    vehicles,
                    next_vehicle_id,
                    elapsed_since_takt,
                    current_takt,
                    merge_state,
                    blue_branch_speed_factor,
                    yellow_branch_speed_factor,
                    frame_dt,
                )
            )

        draw_scene(
            screen,
            vehicles,
            current_takt,
            buttons,
            blue_branch_speed_factor,
            yellow_branch_speed_factor,
            paused,
            show_labels,
            fullscreen,
            presentation_mode,
            auto_demo_mode,
        )
        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
