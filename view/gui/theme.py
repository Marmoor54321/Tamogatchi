BG_APP = "#111622"
BG_PANEL = "#1A2234"
BG_PANEL_INNER = "#141B2B"
BG_STAGE = "#1E2940"
BORDER_SUBTLE = "#2B3652"
BORDER_ACCENT = "#4F6DF5"

TEXT_PRIMARY = "#F1F5F9"
TEXT_SECONDARY = "#94A3B8"
TEXT_MUTED = "#64748B"

STYLE_COLORS = {
    "good": "#22C55E",
    "info": "#38BDF8",
    "warn": "#F59E0B",
    "bad": "#EF4444",
    "sleepy": "#818CF8",
    "money": "#FACC15",
    "text": TEXT_PRIMARY,
    "hint": TEXT_SECONDARY,
}

BTN_NORMAL_BG = "#242F49"
BTN_NORMAL_HOVER = "#2E3C5C"
BTN_NORMAL_FG = "#F8FAFC"

BTN_SELECTED_BG = "#3B82F6"
BTN_SELECTED_BORDER = "#93C5FD"
BTN_SELECTED_FG = "#FFFFFF"

BTN_DISABLED_BG = "#1D2436"
BTN_DISABLED_FG = "#64748B"
BTN_DISABLED_SELECTED_BG = "#475569"

RED_ACTIONS = frozenset({"exit", "back"})
BTN_RED_BG = "#C62828"
BTN_RED_HOVER = "#E53935"
BTN_RED_SELECTED_BG = "#EF4444"
BTN_RED_SELECTED_BORDER = "#FECACA"
BTN_RED_FG = "#FFFFFF"

FONT_FAMILY = "Segoe UI"
FONT_TITLE = (FONT_FAMILY, 14, "bold")
FONT_SUBTITLE = (FONT_FAMILY, 11, "bold")
FONT_BODY = (FONT_FAMILY, 10)
FONT_BODY_BOLD = (FONT_FAMILY, 10, "bold")
FONT_SMALL = (FONT_FAMILY, 9)
FONT_HINT = (FONT_FAMILY, 9)
FONT_MONO = ("Consolas", 10, "bold")

def stat_color(value: float) -> str:
    if value >= 60:
        return "#22C55E"
    if value >= 30:
        return "#F59E0B"
    return "#EF4444"

def interpolate_hex(color_a: str, color_b: str, t: float) -> str:
    t = max(0.0, min(1.0, t))
    ra, ga, ba = int(color_a[1:3], 16), int(color_a[3:5], 16), int(color_a[5:7], 16)
    rb, gb, bb = int(color_b[1:3], 16), int(color_b[3:5], 16), int(color_b[5:7], 16)
    r = round(ra + (rb - ra) * t)
    g = round(ga + (gb - ga) * t)
    b = round(ba + (bb - ba) * t)
    return f"#{r:02x}{g:02x}{b:02x}"

