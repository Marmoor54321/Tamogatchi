# view/gui/stats_panel.py
"""Panel statystyk z inteligentnym odświeżaniem i płynną animacją pasków."""
import tkinter as tk
from view.common import STAT_LABELS
from view.gui import theme

STAT_DISPLAY_NAMES = {
    "hunger": "Głód",
    "energy": "Energia",
    "happiness": "Szczęście",
    "health": "Zdrowie",
}

STAT_ICONS = {
    "hunger": "🍖",
    "energy": "⚡",
    "happiness": "😊",
    "health": "❤",
}


class StatsPanel(tk.Frame):
    """Wyświetla kasę, rekord i płynnie animowane paski statystyk.

    Odświeża wyłącznie te etykiety i paski, których wartość faktycznie się zmieniła.
    """

    BAR_W = 210
    BAR_H = 16

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
        self._rendered = {}
        self._targets = {stat: float(getattr(pet, stat)) for stat in STAT_LABELS}
        self._visual = {stat: float(getattr(pet, stat)) for stat in STAT_LABELS}

        header = tk.Label(
            self,
            text="Statystyki",
            font=theme.FONT_TITLE,
            bg=theme.BG_PANEL,
            fg=theme.TEXT_PRIMARY,
            anchor="w",
        )
        header.pack(fill="x", pady=(0, 10))

        # Górna karta: Kasa i Rekord
        top_row = tk.Frame(self, bg=theme.BG_PANEL_INNER, padx=12, pady=8)
        top_row.pack(fill="x", pady=(0, 12))

        tk.Label(
            top_row, text="💰 Kasa:", font=theme.FONT_BODY_BOLD,
            bg=theme.BG_PANEL_INNER, fg=theme.TEXT_SECONDARY,
        ).pack(side="left")
        self.money_label = tk.Label(
            top_row, text="", font=theme.FONT_MONO,
            bg=theme.BG_PANEL_INNER, fg=theme.STYLE_COLORS["money"],
        )
        self.money_label.pack(side="left", padx=(6, 18))

        tk.Label(
            top_row, text="🏆 Rekord:", font=theme.FONT_BODY_BOLD,
            bg=theme.BG_PANEL_INNER, fg=theme.TEXT_SECONDARY,
        ).pack(side="left")
        self.record_label = tk.Label(
            top_row, text="", font=theme.FONT_MONO,
            bg=theme.BG_PANEL_INNER, fg=theme.STYLE_COLORS["good"],
        )
        self.record_label.pack(side="left", padx=(6, 0))

        # Paski statystyk
        self._stat_rows = {}
        for stat in STAT_LABELS:
            row = tk.Frame(self, bg=theme.BG_PANEL)
            row.pack(fill="x", pady=5)

            name = STAT_DISPLAY_NAMES.get(stat, STAT_LABELS[stat])
            icon = STAT_ICONS.get(stat, "•")
            tk.Label(
                row,
                text=f"{icon} {name}",
                width=12,
                anchor="w",
                font=theme.FONT_BODY_BOLD,
                bg=theme.BG_PANEL,
                fg=theme.TEXT_PRIMARY,
            ).pack(side="left")

            canvas = tk.Canvas(
                row,
                width=self.BAR_W,
                height=self.BAR_H,
                bg=theme.BG_PANEL_INNER,
                highlightthickness=1,
                highlightbackground=theme.BORDER_SUBTLE,
            )
            canvas.pack(side="left", padx=(6, 10))
            fill_id = canvas.create_rectangle(0, 0, self.BAR_W, self.BAR_H, fill="#22C55E", outline="")

            pct_label = tk.Label(
                row,
                text="100%",
                width=5,
                anchor="e",
                font=theme.FONT_MONO,
                bg=theme.BG_PANEL,
                fg=theme.TEXT_PRIMARY,
            )
            pct_label.pack(side="left")

            self._stat_rows[stat] = (canvas, fill_id, pct_label)

        self.redraw(force=True)

    def redraw(self, changed_fields=None, force=False):
        """Aktualizuje wyłącznie te elementy statystyk, które uległy zmianie."""
        if force or changed_fields is None or "money" in changed_fields:
            if force or self._rendered.get("money") != self.pet.money:
                self._rendered["money"] = self.pet.money
                self.money_label.configure(text=f"{self.pet.money}$")

        if force or changed_fields is None or "high_score" in changed_fields:
            if force or self._rendered.get("high_score") != self.pet.high_score:
                self._rendered["high_score"] = self.pet.high_score
                self.record_label.configure(text=f"{self.pet.high_score} pkt")

        for stat in STAT_LABELS:
            if not force and changed_fields is not None and stat not in changed_fields:
                continue
            raw_val = float(getattr(self.pet, stat))
            rounded_val = round(raw_val)
            self._targets[stat] = raw_val
            if force:
                self._visual[stat] = raw_val
                self._apply_bar(stat, raw_val)
            if force or self._rendered.get(stat) != rounded_val:
                self._rendered[stat] = rounded_val
                _, _, pct_label = self._stat_rows[stat]
                pct_label.configure(text=f"{rounded_val:3d}%", fg=theme.stat_color(rounded_val))

    def animate(self, dt: float):
        """Płynnie dogania docelową długość pasków tylko wtedy, gdy trwa zmiana."""
        if dt <= 0:
            return
        alpha = min(1.0, dt * 12.0)
        for stat in STAT_LABELS:
            target = self._targets[stat]
            current = self._visual[stat]
            if abs(target - current) > 0.08:
                new_val = current + (target - current) * alpha
                if abs(target - new_val) <= 0.08:
                    new_val = target
                self._visual[stat] = new_val
                self._apply_bar(stat, new_val)

    def _apply_bar(self, stat: str, value: float):
        canvas, fill_id, _ = self._stat_rows[stat]
        clamped = max(0.0, min(100.0, value))
        width = max(0.0, (clamped / 100.0) * self.BAR_W)
        canvas.coords(fill_id, 0, 0, width, self.BAR_H)
        canvas.itemconfigure(fill_id, fill=theme.stat_color(clamped))
