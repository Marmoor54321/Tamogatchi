from model.dino_game import PropType

SKIN_PALETTES = {
    "classic": {
        "body": "#60A5FA",
        "body_dark": "#3B82F6",
        "accent": "#BFDBFE",
        "cheek": "#FDA4AF",
        "outline": "#1E3A8A",
    },
    "kotek": {
        "body": "#FB923C",
        "body_dark": "#EA580C",
        "accent": "#FED7AA",
        "cheek": "#FDA4AF",
        "outline": "#7C2D12",
    },
    "krolik": {
        "body": "#F1F5F9",
        "body_dark": "#CBD5E1",
        "accent": "#FBCFE8",
        "cheek": "#F9A8D4",
        "outline": "#475569",
    },
    "robot": {
        "body": "#94A3B8",
        "body_dark": "#475569",
        "accent": "#38BDF8",
        "cheek": "#22D3EE",
        "outline": "#1E293B",
    },
}

def _pt(x1: float, y1: float, w: float, h: float, fx: float, fy: float) -> tuple[float, float]:
    return x1 + fx * w, y1 + fy * h

def _box(x1: float, y1: float, w: float, h: float, fx1: float, fy1: float, fx2: float, fy2: float):
    return x1 + fx1 * w, y1 + fy1 * h, x1 + fx2 * w, y1 + fy2 * h

def _draw_eyes_and_mouth(canvas, x1, y1, w, h, mood, blink=False, tag="pet", is_robot=False):
    eye_color = "#38BDF8" if is_robot else "#0F172A"
    lx, ly = _pt(x1, y1, w, h, 0.36, 0.48)
    rx, ry = _pt(x1, y1, w, h, 0.64, 0.48)
    er = max(1.5, min(w, h) * 0.055)

    if mood == "dead":
        d = er * 1.1
        for cx, cy in ((lx, ly), (rx, ry)):
            canvas.create_line(cx - d, cy - d, cx + d, cy + d, fill="#EF4444", width=2, tags=tag)
            canvas.create_line(cx - d, cy + d, cx + d, cy - d, fill="#EF4444", width=2, tags=tag)
        mx1, my1, mx2, my2 = _box(x1, y1, w, h, 0.42, 0.64, 0.58, 0.72)
        canvas.create_line(mx1, my1 + (my2 - my1) * 0.5, mx2, my1 + (my2 - my1) * 0.5,
                           fill=eye_color, width=2, tags=tag)
        return

    if mood in ("sleepy", "asleep") or blink:
        d = er * 1.25
        for cx, cy in ((lx, ly), (rx, ry)):
            canvas.create_line(cx - d, cy, cx + d, cy, fill=eye_color, width=2, tags=tag)
        if mood == "asleep":
            mx, my = _pt(x1, y1, w, h, 0.50, 0.65)
            mr = max(2.0, min(w, h) * 0.04)
            canvas.create_oval(mx - mr, my - mr, mx + mr, my + mr, outline=eye_color, width=1.5, tags=tag)
        else:
            mx1, my1 = _pt(x1, y1, w, h, 0.44, 0.65)
            mx2, my2 = _pt(x1, y1, w, h, 0.56, 0.65)
            canvas.create_line(mx1, my1, mx2, my2, fill=eye_color, width=2, tags=tag)
        return

    if mood == "sad":
        for cx, cy in ((lx, ly), (rx, ry)):
            canvas.create_oval(cx - er, cy - er, cx + er, cy + er, fill=eye_color, outline="", tags=tag)
        canvas.create_line(lx - er * 1.2, ly - er * 1.2, lx + er, ly - er * 1.8, fill=eye_color, width=2, tags=tag)
        canvas.create_line(rx - er, ry - er * 1.8, rx + er * 1.2, ry - er * 1.2, fill=eye_color, width=2, tags=tag)
        tx, ty = _pt(x1, y1, w, h, 0.31, 0.59)
        tr = max(1.5, er * 0.6)
        canvas.create_oval(tx - tr, ty - tr, tx + tr, ty + tr * 1.4, fill="#60A5FA", outline="", tags=tag)
        mx1, my1, mx2, my2 = _box(x1, y1, w, h, 0.42, 0.63, 0.58, 0.74)
        canvas.create_arc(mx1, my1, mx2, my2, start=20, extent=140, style="arc", outline=eye_color, width=2, tags=tag)
        return

    for cx, cy in ((lx, ly), (rx, ry)):
        canvas.create_oval(cx - er, cy - er, cx + er, cy + er, fill=eye_color, outline="", tags=tag)
        if not is_robot:
            sr = er * 0.35
            canvas.create_oval(cx - sr, cy - er * 0.6, cx + sr * 0.5, cy - er * 0.1,
                               fill="#FFFFFF", outline="", tags=tag)
    mx1, my1, mx2, my2 = _box(x1, y1, w, h, 0.42, 0.57, 0.58, 0.69)
    canvas.create_arc(mx1, my1, mx2, my2, start=200, extent=140, style="arc", outline=eye_color, width=2, tags=tag)

def draw_pet_body(
    canvas,
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    skin_id: str,
    mood: str = "happy",
    blink: bool = False,
    leg_phase: int = 0,
    is_jumping: bool = False,
    tag: str = "pet",
):
    w = max(10.0, x2 - x1)
    h = max(10.0, y2 - y1)
    pal = SKIN_PALETTES.get(skin_id, SKIN_PALETTES["classic"])
    body_col = pal["body"]
    dark_col = pal["body_dark"]
    accent_col = pal["accent"]
    cheek_col = pal["cheek"]
    outline_col = pal["outline"]
    if mood == "dead":
        body_col = "#64748B"
        dark_col = "#475569"
        accent_col = "#94A3B8"

    if leg_phase == 1:
        l_leg = _box(x1, y1, w, h, 0.28, 0.80, 0.42, 0.98)
        r_leg = _box(x1, y1, w, h, 0.58, 0.75, 0.72, 0.90)
    elif leg_phase == 2:
        l_leg = _box(x1, y1, w, h, 0.28, 0.75, 0.42, 0.90)
        r_leg = _box(x1, y1, w, h, 0.58, 0.80, 0.72, 0.98)
    elif is_jumping:
        l_leg = _box(x1, y1, w, h, 0.24, 0.78, 0.40, 0.94)
        r_leg = _box(x1, y1, w, h, 0.60, 0.78, 0.76, 0.94)
    else:
        l_leg = _box(x1, y1, w, h, 0.30, 0.80, 0.44, 0.98)
        r_leg = _box(x1, y1, w, h, 0.56, 0.80, 0.70, 0.98)

    if skin_id == "kotek":
        tail_pts = [
            *_pt(x1, y1, w, h, 0.22, 0.74),
            *_pt(x1, y1, w, h, 0.06, 0.64),
            *_pt(x1, y1, w, h, 0.08, 0.48),
        ]
        canvas.create_line(*tail_pts, fill=dark_col, width=max(3, round(w * 0.06)),
                           capstyle="round", smooth=True, tags=tag)
        canvas.create_oval(*l_leg, fill=dark_col, outline=outline_col, width=1.5, tags=tag)
        canvas.create_oval(*r_leg, fill=dark_col, outline=outline_col, width=1.5, tags=tag)
        l_ear = [*_pt(x1, y1, w, h, 0.24, 0.34), *_pt(x1, y1, w, h, 0.28, 0.04), *_pt(x1, y1, w, h, 0.44, 0.24)]
        r_ear = [*_pt(x1, y1, w, h, 0.56, 0.24), *_pt(x1, y1, w, h, 0.72, 0.04), *_pt(x1, y1, w, h, 0.76, 0.34)]
        canvas.create_polygon(*l_ear, fill=body_col, outline=outline_col, width=1.5, tags=tag)
        canvas.create_polygon(*r_ear, fill=body_col, outline=outline_col, width=1.5, tags=tag)
        l_in = [*_pt(x1, y1, w, h, 0.28, 0.30), *_pt(x1, y1, w, h, 0.30, 0.11), *_pt(x1, y1, w, h, 0.40, 0.25)]
        r_in = [*_pt(x1, y1, w, h, 0.60, 0.25), *_pt(x1, y1, w, h, 0.70, 0.11), *_pt(x1, y1, w, h, 0.72, 0.30)]
        canvas.create_polygon(*l_in, fill=cheek_col, outline="", tags=tag)
        canvas.create_polygon(*r_in, fill=cheek_col, outline="", tags=tag)
        canvas.create_oval(*_box(x1, y1, w, h, 0.18, 0.20, 0.82, 0.86),
                           fill=body_col, outline=outline_col, width=2, tags=tag)
        canvas.create_oval(*_box(x1, y1, w, h, 0.32, 0.64, 0.68, 0.84),
                           fill=accent_col, outline="", tags=tag)
        for wy in (0.52, 0.58):
            canvas.create_line(*_pt(x1, y1, w, h, 0.14, wy - 0.02), *_pt(x1, y1, w, h, 0.28, wy),
                               fill=outline_col, width=1.3, tags=tag)
            canvas.create_line(*_pt(x1, y1, w, h, 0.72, wy), *_pt(x1, y1, w, h, 0.86, wy - 0.02),
                               fill=outline_col, width=1.3, tags=tag)
        _draw_eyes_and_mouth(canvas, x1, y1, w, h, mood, blink=blink, tag=tag)
        nx1, ny1, nx2, ny2 = _box(x1, y1, w, h, 0.47, 0.53, 0.53, 0.58)
        canvas.create_oval(nx1, ny1, nx2, ny2, fill=cheek_col, outline="", tags=tag)
        return

    if skin_id == "krolik":
        canvas.create_oval(*_box(x1, y1, w, h, 0.10, 0.64, 0.24, 0.79),
                           fill="#FFFFFF", outline=outline_col, width=1.3, tags=tag)
        canvas.create_oval(*l_leg, fill=dark_col, outline=outline_col, width=1.5, tags=tag)
        canvas.create_oval(*r_leg, fill=dark_col, outline=outline_col, width=1.5, tags=tag)
        canvas.create_oval(*_box(x1, y1, w, h, 0.27, 0.02, 0.43, 0.38),
                           fill=body_col, outline=outline_col, width=1.5, tags=tag)
        canvas.create_oval(*_box(x1, y1, w, h, 0.57, 0.02, 0.73, 0.38),
                           fill=body_col, outline=outline_col, width=1.5, tags=tag)
        canvas.create_oval(*_box(x1, y1, w, h, 0.31, 0.06, 0.39, 0.31),
                           fill=accent_col, outline="", tags=tag)
        canvas.create_oval(*_box(x1, y1, w, h, 0.61, 0.06, 0.69, 0.31),
                           fill=accent_col, outline="", tags=tag)
        canvas.create_oval(*_box(x1, y1, w, h, 0.19, 0.26, 0.81, 0.87),
                           fill=body_col, outline=outline_col, width=2, tags=tag)
        canvas.create_oval(*_box(x1, y1, w, h, 0.24, 0.54, 0.34, 0.62), fill=cheek_col, outline="", tags=tag)
        canvas.create_oval(*_box(x1, y1, w, h, 0.66, 0.54, 0.76, 0.62), fill=cheek_col, outline="", tags=tag)
        _draw_eyes_and_mouth(canvas, x1, y1, w, h, mood, blink=blink, tag=tag)
        canvas.create_oval(*_box(x1, y1, w, h, 0.47, 0.53, 0.53, 0.58), fill="#FB7185", outline="", tags=tag)
        return

    if skin_id == "robot":
        canvas.create_rectangle(*l_leg, fill=dark_col, outline=outline_col, width=1.5, tags=tag)
        canvas.create_rectangle(*r_leg, fill=dark_col, outline=outline_col, width=1.5, tags=tag)
        ax, ay1 = _pt(x1, y1, w, h, 0.50, 0.10)
        _, ay2 = _pt(x1, y1, w, h, 0.50, 0.24)
        canvas.create_line(ax, ay1, ax, ay2, fill=outline_col, width=2, tags=tag)
        tip_col = "#EF4444" if mood == "dead" else accent_col
        canvas.create_oval(*_box(x1, y1, w, h, 0.45, 0.02, 0.55, 0.12),
                           fill=tip_col, outline=outline_col, width=1.2, tags=tag)
        canvas.create_rectangle(*_box(x1, y1, w, h, 0.10, 0.46, 0.20, 0.66),
                                fill=dark_col, outline=outline_col, width=1.5, tags=tag)
        canvas.create_rectangle(*_box(x1, y1, w, h, 0.80, 0.46, 0.90, 0.66),
                                fill=dark_col, outline=outline_col, width=1.5, tags=tag)
        canvas.create_rectangle(*_box(x1, y1, w, h, 0.20, 0.24, 0.80, 0.84),
                                fill=body_col, outline=outline_col, width=2, tags=tag)
        canvas.create_rectangle(*_box(x1, y1, w, h, 0.27, 0.34, 0.73, 0.74),
                                fill="#0F172A", outline=dark_col, width=1.5, tags=tag)
        _draw_eyes_and_mouth(canvas, x1, y1, w, h, mood, blink=blink, tag=tag, is_robot=True)
        return

    canvas.create_oval(*l_leg, fill=dark_col, outline=outline_col, width=1.5, tags=tag)
    canvas.create_oval(*r_leg, fill=dark_col, outline=outline_col, width=1.5, tags=tag)
    canvas.create_oval(*_box(x1, y1, w, h, 0.20, 0.14, 0.36, 0.34),
                       fill=dark_col, outline=outline_col, width=1.5, tags=tag)
    canvas.create_oval(*_box(x1, y1, w, h, 0.64, 0.14, 0.80, 0.34),
                       fill=dark_col, outline=outline_col, width=1.5, tags=tag)
    canvas.create_oval(*_box(x1, y1, w, h, 0.10, 0.48, 0.24, 0.66),
                       fill=body_col, outline=outline_col, width=1.5, tags=tag)
    canvas.create_oval(*_box(x1, y1, w, h, 0.76, 0.48, 0.90, 0.66),
                       fill=body_col, outline=outline_col, width=1.5, tags=tag)
    canvas.create_oval(*_box(x1, y1, w, h, 0.18, 0.18, 0.82, 0.86),
                       fill=body_col, outline=outline_col, width=2, tags=tag)
    canvas.create_oval(*_box(x1, y1, w, h, 0.32, 0.65, 0.68, 0.83),
                       fill=accent_col, outline="", tags=tag)
    canvas.create_oval(*_box(x1, y1, w, h, 0.24, 0.53, 0.33, 0.61), fill=cheek_col, outline="", tags=tag)
    canvas.create_oval(*_box(x1, y1, w, h, 0.67, 0.53, 0.76, 0.61), fill=cheek_col, outline="", tags=tag)
    _draw_eyes_and_mouth(canvas, x1, y1, w, h, mood, blink=blink, tag=tag)

def draw_minigame_entity(
    canvas,
    prop_id: str,
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    skin_id: str = "classic",
    tag: str = "entity",
):
    w = max(4.0, x2 - x1)
    h = max(4.0, y2 - y1)

    if prop_id == PropType.PLAYER_RUN_1:
        draw_pet_body(canvas, x1, y1, x2, y2, skin_id, mood="happy", leg_phase=1, tag=tag)
    elif prop_id == PropType.PLAYER_RUN_2:
        draw_pet_body(canvas, x1, y1, x2, y2, skin_id, mood="happy", leg_phase=2, tag=tag)
    elif prop_id == PropType.PLAYER_JUMP:
        draw_pet_body(canvas, x1, y1, x2, y2, skin_id, mood="happy", is_jumping=True, tag=tag)
    elif prop_id == PropType.PLAYER_CRASH:
        draw_pet_body(canvas, x1, y1, x2, y2, skin_id, mood="dead", tag=tag)
    elif prop_id in (PropType.CACTUS_SMALL, PropType.CACTUS_LARGE):
        trunk_col = "#16A34A"
        outline_col = "#14532D"
        canvas.create_rectangle(*_box(x1, y1, w, h, 0.34, 0.04, 0.66, 0.98),
                                fill=trunk_col, outline=outline_col, width=1.5, tags=tag)
        canvas.create_rectangle(*_box(x1, y1, w, h, 0.08, 0.28, 0.34, 0.56),
                                fill=trunk_col, outline=outline_col, width=1.2, tags=tag)
        canvas.create_rectangle(*_box(x1, y1, w, h, 0.66, 0.22, 0.92, 0.50),
                                fill=trunk_col, outline=outline_col, width=1.2, tags=tag)
        canvas.create_line(*_pt(x1, y1, w, h, 0.48, 0.10), *_pt(x1, y1, w, h, 0.48, 0.92),
                           fill="#4ADE80", width=1.5, tags=tag)
    elif prop_id == PropType.ROCK:
        pts = [
            *_pt(x1, y1, w, h, 0.04, 0.96),
            *_pt(x1, y1, w, h, 0.22, 0.24),
            *_pt(x1, y1, w, h, 0.54, 0.06),
            *_pt(x1, y1, w, h, 0.84, 0.30),
            *_pt(x1, y1, w, h, 0.96, 0.96),
        ]
        canvas.create_polygon(*pts, fill="#94A3B8", outline="#475569", width=1.5, tags=tag)
        highlight = [
            *_pt(x1, y1, w, h, 0.28, 0.30),
            *_pt(x1, y1, w, h, 0.53, 0.14),
            *_pt(x1, y1, w, h, 0.65, 0.44),
        ]
        canvas.create_line(*highlight, fill="#CBD5E1", width=1.5, tags=tag)
    elif prop_id == PropType.CLOUD:
        canvas.create_oval(*_box(x1, y1, w, h, 0.05, 0.30, 0.45, 0.95), fill="#E2E8F0", outline="", tags=tag)
        canvas.create_oval(*_box(x1, y1, w, h, 0.28, 0.05, 0.72, 0.95), fill="#F8FAFC", outline="", tags=tag)
        canvas.create_oval(*_box(x1, y1, w, h, 0.55, 0.30, 0.95, 0.95), fill="#E2E8F0", outline="", tags=tag)

