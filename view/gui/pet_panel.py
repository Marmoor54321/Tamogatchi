# view/gui/pet_panel.py
"""Animowana scena zwierzaka z obsługą skórek, nastrojów, podglądu i efektów cząsteczkowych."""
import math
import random
import tkinter as tk
from view.common import MOOD_CAPTIONS, skin_name
from view.gui import theme
from view.gui.pet_sprites import draw_pet_body

MOOD_DISPLAY = {
    "happy": ("Szczęśliwy", "good"),
    "sad": ("Smutny", "warn"),
    "sleepy": ("Śpiący", "sleepy"),
    "asleep": ("Śpi... +1 energii / 2 s", "sleepy"),
    "dead": ("Nie żyje", "bad"),
}


class PetPanel(tk.Frame):
    """Wyświetla animowanego zwierzaka na scenie Canvas.

    Inteligentne odświeżanie:
    - Tło sceny przerysowywane jest tylko przy zmianie nastroju/trybu.
    - Korpus zwierzaka przerysowywany jest tylko przy zmianie skórki, nastroju lub mrugnięcia.
    - Płynne kołysanie (oddychanie) w klatkach animacji przesuwa istniejące obiekty przez `canvas.move()`.
    """

    STAGE_W = 300
    STAGE_H = 196

    def __init__(self, parent, pet):
        super().__init__(
            parent,
            bg=theme.BG_PANEL,
            highlightbackground=theme.BORDER_SUBTLE,
            highlightthickness=1,
            padx=16,
            pady=12,
        )
        self.pet = pet
        self.preview_skin = None

        # Stan animacji
        self._anim_time = 0.0
        self._blink_timer = 2.8
        self._is_blinking = False
        self._bob_offset = 0.0
        self._wiggle_time = 0.0
        self._wiggle_offset = 0.0
        self._particles = []  # lista słowników {id, x, y, vx, vy, life, max_life, text, color}
        self._sleep_spawn_timer = 0.0

        # Pamięć ostatnio wyrenderowanego stanu (do inteligentnego odświeżania)
        self._rendered_name = None
        self._rendered_caption = None
        self._rendered_backdrop = None
        self._rendered_pet = None

        # Nagłówek z imieniem zwierzaka i etykietą skórki
        top = tk.Frame(self, bg=theme.BG_PANEL)
        top.pack(fill="x", pady=(0, 8))

        self.name_label = tk.Label(
            top,
            text="",
            font=theme.FONT_TITLE,
            bg=theme.BG_PANEL,
            fg=theme.TEXT_PRIMARY,
            anchor="w",
        )
        self.name_label.pack(side="left")

        self.skin_badge = tk.Label(
            top,
            text="",
            font=theme.FONT_SMALL,
            bg=theme.BG_PANEL_INNER,
            fg=theme.TEXT_SECONDARY,
            padx=8,
            pady=2,
        )
        self.skin_badge.pack(side="right")

        self.canvas = tk.Canvas(
            self,
            width=self.STAGE_W,
            height=self.STAGE_H,
            bg=theme.BG_STAGE,
            highlightthickness=1,
            highlightbackground=theme.BORDER_SUBTLE,
        )
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", lambda _e: self.redraw(force=True))
        self.canvas.bind("<Button-1>", self._on_canvas_click)
        self.canvas.bind("<Motion>", self._on_canvas_motion)

        self.mood_label = tk.Label(
            self,
            text="",
            font=theme.FONT_SUBTITLE,
            bg=theme.BG_PANEL,
            fg=theme.STYLE_COLORS["good"],
            pady=6,
        )
        self.mood_label.pack(fill="x")

        self.redraw(force=True)

    def _effective_skin_and_caption(self):
        mood = self.pet.mood
        caption, style_name = MOOD_DISPLAY.get(mood, (MOOD_CAPTIONS.get(mood, mood), "text"))
        skin_id = self.pet.active_skin
        if self.preview_skin:
            skin_id = self.preview_skin
            caption = f"Podgląd: {skin_name(self.preview_skin)}"
            style_name = "info"
        return skin_id, mood, caption, style_name

    def redraw(self, force=False):
        """Odświeża wyłącznie zmienione elementy panelu zwierzaka."""
        if force or self._rendered_name != self.pet.name:
            self._rendered_name = self.pet.name
            self.name_label.configure(text=self.pet.name)

        skin_id, mood, caption, style_name = self._effective_skin_and_caption()

        badge_text = skin_name(skin_id)
        if self.skin_badge.cget("text") != badge_text:
            self.skin_badge.configure(text=badge_text)

        cap_state = (caption, style_name)
        if force or self._rendered_caption != cap_state:
            self._rendered_caption = cap_state
            self.mood_label.configure(text=caption, fg=theme.STYLE_COLORS[style_name])

        backdrop_state = mood
        if force or self._rendered_backdrop != backdrop_state:
            self._rendered_backdrop = backdrop_state
            self._draw_backdrop(mood)

        pet_state = (skin_id, mood, self._is_blinking)
        if force or self._rendered_pet != pet_state:
            self._rendered_pet = pet_state
            self._draw_pet(skin_id, mood, self._is_blinking)

    def _stage_size(self) -> tuple[float, float]:
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        return (
            float(w) if w > 50 else float(self.STAGE_W),
            float(h) if h > 50 else float(self.STAGE_H),
        )

    def _draw_backdrop(self, mood: str):
        c = self.canvas
        c.delete("backdrop")
        w, h = self._stage_size()

        if mood == "asleep":
            sky, floor = "#0F172A", "#1E293B"
        elif mood == "dead":
            sky, floor = "#1F1B24", "#27272A"
        elif mood == "sad":
            sky, floor = "#1E293B", "#263244"
        else:
            sky, floor = "#1B2A4A", "#1F3A3D"

        c.create_rectangle(0, 0, w, h * 0.76, fill=sky, outline="", tags="backdrop")
        c.create_rectangle(0, h * 0.76, w, h, fill=floor, outline="", tags="backdrop")
        c.create_line(0, h * 0.76, w, h * 0.76, fill=theme.BORDER_SUBTLE, width=2, tags="backdrop")

        if mood == "asleep":
            # Księżyc i gwiazdki
            c.create_oval(24, 20, 56, 52, fill="#FDE68A", outline="", tags="backdrop")
            c.create_oval(33, 16, 63, 46, fill=sky, outline="", tags="backdrop")
            for fx, fy in ((0.33, 0.14), (0.50, 0.09), (0.73, 0.17), (0.88, 0.11), (0.27, 0.30)):
                sx, sy = w * fx, h * fy
                c.create_oval(sx, sy, sx + 3, sy + 3, fill="#E2E8F0", outline="", tags="backdrop")
        elif mood == "happy":
            for fx, fy in ((0.12, 0.13), (0.86, 0.16), (0.78, 0.32)):
                sx, sy = w * fx, h * fy
                c.create_oval(sx, sy, sx + 4, sy + 4, fill="#38BDF8", outline="", tags="backdrop")
        elif mood == "dead":
            gx = w * 0.80
            gy = h * 0.76
            c.create_arc(gx - 24, gy - 50, gx + 24, gy + 4, start=0, extent=180,
                         fill="#475569", outline="#64748B", tags="backdrop")
            c.create_rectangle(gx - 24, gy - 23, gx + 24, gy, fill="#475569", outline="#64748B", tags="backdrop")
            c.create_text(gx, gy - 15, text="RIP", fill="#CBD5E1", font=theme.FONT_SMALL, tags="backdrop")

        c.tag_lower("backdrop")

    def _pet_bounds(self) -> tuple[float, float, float, float]:
        w, h = self._stage_size()
        cx = w / 2 + self._wiggle_offset
        cy = h * 0.50 + self._bob_offset
        scale = min(w / self.STAGE_W, h / self.STAGE_H)
        pw, ph = 116 * scale, 104 * scale
        return cx - pw / 2, cy - ph / 2, cx + pw / 2, cy + ph / 2

    def _is_over_pet(self, x: float, y: float) -> bool:
        x1, y1, x2, y2 = self._pet_bounds()
        return (x1 - 8 <= x <= x2 + 8) and (y1 - 8 <= y <= y2 + 8)

    def _on_canvas_motion(self, event):
        cursor = "hand2" if (self.pet.is_alive and self._is_over_pet(event.x, event.y)) else ""
        if self.canvas.cget("cursor") != cursor:
            self.canvas.configure(cursor=cursor)

    def _on_canvas_click(self, event):
        if self.pet.is_alive and self._is_over_pet(event.x, event.y):
            self.poke()

    def poke(self):
        """Reakcja na kliknięcie zwierzaka: buja się na boki i wypuszcza serduszko."""
        if not self.pet.is_alive:
            return
        self._wiggle_time = 0.45
        w, h = self._stage_size()
        hx = w / 2 + self._wiggle_offset + random.uniform(-8, 8)
        hy = h * 0.28 + self._bob_offset
        item_id = self.canvas.create_text(
            hx, hy, text="❤", fill="#FB7185", font=("Segoe UI", 14, "bold"), tags="particles"
        )
        self._particles.append({
            "id": item_id,
            "vx": random.uniform(-10, 10),
            "vy": -40.0,
            "life": 0.0,
            "max_life": 1.05,
        })

    def _draw_pet(self, skin_id: str, mood: str, blink: bool):
        c = self.canvas
        w, h = self._stage_size()
        c.delete("pet")
        x1, y1, x2, y2 = self._pet_bounds()
        scale = min(w / self.STAGE_W, h / self.STAGE_H)
        # Cień pod zwierzakiem (zostaje na podłodze, bez kołysania)
        c.delete("pet_shadow")
        c.create_oval(
            w / 2 - 42 * scale, h * 0.77,
            w / 2 + 42 * scale, h * 0.85,
            fill="#0B1120", outline="", tags="pet_shadow",
        )
        draw_pet_body(
            c,
            x1,
            y1,
            x2,
            y2,
            skin_id=skin_id,
            mood=mood,
            blink=blink,
            tag="pet",
        )
        c.tag_raise("particles")

    def trigger_reaction(self, kind: str):
        """Uruchamia krótką animację cząsteczkową po akcji użytkownika (np. jedzenie/odrodzenie)."""
        w, h = self._stage_size()
        cx, cy = w / 2, h * 0.35
        symbol = "❤" if kind == "feed" else "✨"
        color = "#FB7185" if kind == "feed" else "#FACC15"
        for _ in range(5):
            px = cx + random.uniform(-35, 35)
            py = cy + random.uniform(-10, 15)
            item_id = self.canvas.create_text(
                px, py, text=symbol, fill=color, font=("Segoe UI", 12, "bold"), tags="particles"
            )
            self._particles.append({
                "id": item_id,
                "vx": random.uniform(-12, 12),
                "vy": random.uniform(-38, -22),
                "life": 0.0,
                "max_life": random.uniform(0.9, 1.4),
            })

    def animate(self, dt: float):
        """Płynna animacja oddechu, mrugania i cząsteczek (Zzz / serduszka)."""
        if dt <= 0:
            return
        self._anim_time += dt
        mood = self.pet.mood
        skin_id = self.preview_skin or self.pet.active_skin

        # 1. Delikatne kołysanie (tylko gdy zwierzak żyje)
        if mood == "dead":
            target_bob = 6.0
        elif mood == "asleep":
            target_bob = math.sin(self._anim_time * 1.6) * 2.0
        else:
            target_bob = math.sin(self._anim_time * 3.0) * 3.5

        dy = target_bob - self._bob_offset
        if self._wiggle_time > 0.0:
            self._wiggle_time = max(0.0, self._wiggle_time - dt)
            progress = 1.0 - (self._wiggle_time / 0.45)
            target_wiggle = math.sin(progress * math.pi * 4.0) * 10.0 * (1.0 - progress)
        else:
            target_wiggle = 0.0

        dx = target_wiggle - self._wiggle_offset
        if abs(dx) > 0.05 or abs(dy) > 0.05 or (self._wiggle_time == 0.0 and self._wiggle_offset != 0.0):
            move_x = -self._wiggle_offset if self._wiggle_time == 0.0 else dx
            move_y = dy if abs(dy) > 0.05 else 0.0
            self.canvas.move("pet", move_x, move_y)
            self._wiggle_offset = 0.0 if self._wiggle_time == 0.0 else target_wiggle
            if move_y:
                self._bob_offset = target_bob

        # 2. Naturalne mruganie oczami
        if mood in ("happy", "sad"):
            self._blink_timer -= dt
            if self._blink_timer <= 0:
                self._is_blinking = not self._is_blinking
                self._blink_timer = 0.14 if self._is_blinking else random.uniform(2.6, 4.6)
                self.redraw()
        elif self._is_blinking:
            self._is_blinking = False
            self.redraw()

        # 3. Unoszące się "Zzz" podczas snu
        if mood == "asleep":
            self._sleep_spawn_timer -= dt
            if self._sleep_spawn_timer <= 0:
                self._sleep_spawn_timer = 0.85
                w, h = self._stage_size()
                sx = w / 2 + random.uniform(22, 36)
                sy = h * 0.34
                item_id = self.canvas.create_text(
                    sx, sy, text=random.choice(("Z", "z")), fill="#A5B4FC",
                    font=("Segoe UI", random.choice((11, 13)), "bold"), tags="particles"
                )
                self._particles.append({
                    "id": item_id,
                    "vx": random.uniform(8, 16),
                    "vy": -26.0,
                    "life": 0.0,
                    "max_life": 1.6,
                })

        # 4. Aktualizacja aktywnych cząsteczek
        if self._particles:
            alive = []
            for p in self._particles:
                p["life"] += dt
                if p["life"] >= p["max_life"]:
                    self.canvas.delete(p["id"])
                else:
                    self.canvas.move(p["id"], p["vx"] * dt, p["vy"] * dt)
                    alive.append(p)
            self._particles = alive
