import time
import tkinter as tk
from view.gui import theme
from view.gui.pet_sprites import draw_minigame_entity

class MinigamePanel(tk.Frame):

    CANVAS_W = 820
    CANVAS_H = 340
    MARGIN_X = 20
    GROUND_MARGIN_BOTTOM = 52
    GROUND_Y = CANVAS_H - GROUND_MARGIN_BOTTOM

    def __init__(self, parent, pet, on_jump, on_quit):
        super().__init__(
            parent,
            bg=theme.BG_PANEL,
            highlightbackground=theme.BORDER_SUBTLE,
            highlightthickness=1,
            padx=14,
            pady=12,
        )
        self.pet = pet
        self.on_jump = on_jump
        self.on_quit = on_quit

        self._rendered_hud = None
        self._bg_size = None
        self._ground_offset = 0.0
        self._last_draw_time = time.monotonic()

        hud = tk.Frame(self, bg=theme.BG_PANEL_INNER, padx=12, pady=8)
        hud.pack(fill="x", pady=(0, 10))

        self.score_label = tk.Label(
            hud, text="Wynik: 0", font=theme.FONT_SUBTITLE,
            bg=theme.BG_PANEL_INNER, fg=theme.TEXT_PRIMARY,
        )
        self.score_label.pack(side="left", padx=(0, 18))

        self.record_label = tk.Label(
            hud, text="Rekord: 0", font=theme.FONT_BODY_BOLD,
            bg=theme.BG_PANEL_INNER, fg=theme.STYLE_COLORS["info"],
        )
        self.record_label.pack(side="left", padx=(0, 18))

        self.money_label = tk.Label(
            hud, text="Zdobyte monety: +0$", font=theme.FONT_BODY_BOLD,
            bg=theme.BG_PANEL_INNER, fg=theme.STYLE_COLORS["money"],
        )
        self.money_label.pack(side="left")

        self.back_button = tk.Button(
            hud,
            text="Wróć",
            font=theme.FONT_BODY_BOLD,
            bg=theme.BTN_RED_BG,
            fg=theme.BTN_RED_FG,
            activebackground=theme.BTN_RED_HOVER,
            activeforeground=theme.BTN_RED_FG,
            relief="flat",
            bd=0,
            padx=14,
            pady=4,
            cursor="hand2",
            takefocus=0,
            command=self.on_quit,
        )
        self.back_button.pack(side="right")

        self.canvas = tk.Canvas(
            self,
            width=self.CANVAS_W,
            height=self.CANVAS_H,
            bg="#0F172A",
            highlightthickness=1,
            highlightbackground=theme.BORDER_SUBTLE,
        )
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Button-1>", lambda _e: self.on_jump())
        self.canvas.bind("<Configure>", lambda _e: self._on_canvas_resize())

        tk.Label(
            self,
            text="Spacja / ↑ / W / Klik myszą: SKOK       Esc / Q / Wróć: WYJŚCIE Z MINIGRY",
            font=theme.FONT_HINT,
            bg=theme.BG_PANEL,
            fg=theme.TEXT_SECONDARY,
            pady=6,
        ).pack(fill="x")

    def _canvas_dims(self) -> tuple[float, float, float]:
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        cw = float(w) if w > 100 else float(self.CANVAS_W)
        ch = float(h) if h > 100 else float(self.CANVAS_H)
        ground_y = ch - self.GROUND_MARGIN_BOTTOM
        return cw, ch, ground_y

    def _on_canvas_resize(self):
        cw, ch, _ = self._canvas_dims()
        if self._bg_size != (cw, ch):
            self._draw_static_background()

    @classmethod
    def world_scale(
        cls,
        track_width: float,
        canvas_w: float = None,
        ground_y: float = None,
    ) -> tuple[float, float]:
        w = canvas_w or cls.CANVAS_W
        gy = ground_y or cls.GROUND_Y
        play_w = max(200.0, w - 2 * cls.MARGIN_X)
        sx = play_w / max(1.0, float(track_width))
        sy = min(sx * 2.0, max(10.0, (gy - 12.0) / 6.5))
        return sx, sy

    @classmethod
    def entity_bbox(
        cls,
        entity,
        track_width: float,
        canvas_w: float = None,
        ground_y: float = None,
    ) -> tuple[float, float, float, float]:
        gy = ground_y or cls.GROUND_Y
        sx, sy = cls.world_scale(track_width, canvas_w, gy)
        x1 = cls.MARGIN_X + entity.x * sx
        x2 = cls.MARGIN_X + (entity.x + entity.width) * sx
        y2 = gy - entity.y * sy
        y1 = gy - (entity.y + entity.height) * sy
        return x1, y1, x2, y2

    def reset_scene(self):
        self._rendered_hud = None
        self._bg_size = None
        self._ground_offset = 0.0
        self._last_draw_time = time.monotonic()
        self.canvas.delete("all")
        self._draw_static_background()

    def _draw_static_background(self):
        c = self.canvas
        w, h, ground_y = self._canvas_dims()
        c.delete("static_bg")
        c.create_rectangle(0, 0, w, ground_y, fill="#162238", outline="", tags="static_bg")
        c.create_rectangle(0, ground_y, w, h, fill="#334155", outline="", tags="static_bg")
        c.create_line(0, ground_y, w, ground_y, fill="#94A3B8", width=2, tags="static_bg")
        for fx, fy in ((0.10, 0.14), (0.26, 0.10), (0.48, 0.16), (0.68, 0.09), (0.88, 0.17)):
            sx, sy = w * fx, ground_y * fy
            c.create_oval(sx, sy, sx + 3, sy + 3, fill="#475569", outline="", tags="static_bg")
        c.tag_lower("static_bg")
        self._bg_size = (w, h)

    def draw(self, game):
        cw, ch, ground_y = self._canvas_dims()
        if self._bg_size != (cw, ch):
            self._draw_static_background()

        hud_state = (game.score, game.high_score, game.money_earned)
        if hud_state != self._rendered_hud:
            self._rendered_hud = hud_state
            self.score_label.configure(text=f"Wynik: {game.score}")
            self.record_label.configure(text=f"Rekord: {game.high_score}")
            self.money_label.configure(text=f"Zdobyte monety: +{game.money_earned}$")

        c = self.canvas
        c.delete("entity")
        c.delete("ground_scroll")

        now = time.monotonic()
        dt = min(0.1, max(0.0, now - self._last_draw_time))
        self._last_draw_time = now
        sx, _ = self.world_scale(game.track_width, cw, ground_y)
        if not game.is_game_over:
            self._ground_offset = (self._ground_offset + game.current_speed * sx * dt) % 44.0
        for gx in range(-44, int(cw) + 44, 44):
            x = gx - self._ground_offset
            c.create_line(x, ground_y + 14, x + 18, ground_y + 14,
                          fill="#475569", width=2, tags="ground_scroll")

        for cloud in game.clouds:
            x1, y1, x2, y2 = self.entity_bbox(cloud, game.track_width, cw, ground_y)
            draw_minigame_entity(c, cloud.prop_id, x1, y1, x2, y2, tag="entity")

        for obs in game.obstacles:
            x1, y1, x2, y2 = self.entity_bbox(obs, game.track_width, cw, ground_y)
            draw_minigame_entity(c, obs.prop_id, x1, y1, x2, y2, tag="entity")

        player = game.get_player_entity()
        px1, py1, px2, py2 = self.entity_bbox(player, game.track_width, cw, ground_y)
        draw_minigame_entity(
            c, player.prop_id, px1, py1, px2, py2,
            skin_id=self.pet.active_skin, tag="entity"
        )

