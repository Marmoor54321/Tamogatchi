# view/gui/dialogs.py
"""Okna dialogowe GUI (nadawanie imienia oraz podsumowanie minigry)."""
import tkinter as tk
from model.pet import Pet
from view.gui import theme


def _center_over(win: tk.Toplevel, parent: tk.Misc, width: int, height: int):
    parent.update_idletasks()
    px = parent.winfo_rootx()
    py = parent.winfo_rooty()
    pw = max(parent.winfo_width(), width)
    ph = max(parent.winfo_height(), height)
    x = px + (pw - width) // 2
    y = py + (ph - height) // 2
    win.geometry(f"{width}x{height}+{max(0, x)}+{max(0, y)}")


class NameDialog(tk.Toplevel):
    """Modalne okno do nadawania imienia zwierzakowi (start gry lub odrodzenie)."""

    def __init__(self, parent, current_name: str, is_resurrection: bool = False):
        super().__init__(parent)
        self.result = None
        self.transient(parent)
        self.resizable(False, False)
        self.configure(bg=theme.BG_PANEL)

        title = "Odrodzenie zwierzaka" if is_resurrection else "Nowy zwierzak"
        prompt = (
            "Nadaj nowe imię odrodzonemu zwierzakowi:"
            if is_resurrection
            else "Jak chcesz nazwać swojego zwierzaka?"
        )
        self.title(title)

        body = tk.Frame(self, bg=theme.BG_PANEL, padx=22, pady=18)
        body.pack(fill="both", expand=True)

        tk.Label(
            body, text=prompt, font=theme.FONT_SUBTITLE,
            bg=theme.BG_PANEL, fg=theme.TEXT_PRIMARY, anchor="w",
        ).pack(fill="x", pady=(0, 10))

        vcmd = (self.register(lambda s: len(s) <= Pet.MAX_NAME_LENGTH), "%P")
        self.var = tk.StringVar()
        self.entry = tk.Entry(
            body,
            textvariable=self.var,
            font=theme.FONT_TITLE,
            bg=theme.BG_PANEL_INNER,
            fg=theme.TEXT_PRIMARY,
            insertbackground=theme.TEXT_PRIMARY,
            relief="flat",
            highlightthickness=2,
            highlightbackground=theme.BORDER_SUBTLE,
            highlightcolor=theme.BORDER_ACCENT,
            validate="key",
            validatecommand=vcmd,
        )
        self.entry.pack(fill="x", ipady=6)

        tk.Label(
            body,
            text=f"(puste = zostaje '{current_name}', maks. {Pet.MAX_NAME_LENGTH} znaków)",
            font=theme.FONT_SMALL,
            bg=theme.BG_PANEL,
            fg=theme.TEXT_SECONDARY,
            anchor="w",
        ).pack(fill="x", pady=(6, 14))

        btns = tk.Frame(body, bg=theme.BG_PANEL)
        btns.pack(fill="x")

        tk.Button(
            btns,
            text="Pomiń",
            font=theme.FONT_BODY_BOLD,
            bg=theme.BTN_RED_BG,
            fg=theme.BTN_RED_FG,
            activebackground=theme.BTN_RED_HOVER,
            activeforeground=theme.BTN_RED_FG,
            relief="flat",
            padx=16,
            pady=6,
            cursor="hand2",
            command=self._cancel,
        ).pack(side="right", padx=(8, 0))

        tk.Button(
            btns,
            text="Zatwierdź",
            font=theme.FONT_BODY_BOLD,
            bg=theme.BTN_SELECTED_BG,
            fg=theme.BTN_SELECTED_FG,
            activebackground="#2563EB",
            activeforeground=theme.BTN_SELECTED_FG,
            relief="flat",
            padx=16,
            pady=6,
            cursor="hand2",
            command=self._confirm,
        ).pack(side="right")

        self.bind("<Return>", lambda _e: self._confirm())
        self.bind("<Escape>", lambda _e: self._cancel())
        self.protocol("WM_DELETE_WINDOW", self._cancel)

        _center_over(self, parent, 420, 195)
        self.grab_set()
        self.entry.focus_set()

    def _confirm(self):
        self.result = self.var.get().strip()
        self.destroy()

    def _cancel(self):
        self.result = None
        self.destroy()


class GameOverDialog(tk.Toplevel):
    """Modalne okno podsumowania po kolizji w minigrze."""

    def __init__(self, parent, game):
        super().__init__(parent)
        self.transient(parent)
        self.resizable(False, False)
        self.configure(bg=theme.BG_PANEL)
        self.title("Koniec gry!")

        body = tk.Frame(self, bg=theme.BG_PANEL, padx=24, pady=20)
        body.pack(fill="both", expand=True)

        tk.Label(
            body, text="KONIEC GRY!", font=("Segoe UI", 16, "bold"),
            bg=theme.BG_PANEL, fg=theme.STYLE_COLORS["bad"],
        ).pack(pady=(0, 12))

        card = tk.Frame(body, bg=theme.BG_PANEL_INNER, padx=16, pady=12)
        card.pack(fill="x", pady=(0, 12))

        tk.Label(
            card, text=f"Przeskoczone przeszkody: {game.score}",
            font=theme.FONT_BODY_BOLD, bg=theme.BG_PANEL_INNER, fg=theme.STYLE_COLORS["info"], anchor="w",
        ).pack(fill="x", pady=2)

        money_color = theme.STYLE_COLORS["good"] if game.money_earned > 0 else theme.TEXT_PRIMARY
        tk.Label(
            card, text=f"Zdobyte monety: +{game.money_earned}$",
            font=theme.FONT_BODY_BOLD, bg=theme.BG_PANEL_INNER, fg=money_color, anchor="w",
        ).pack(fill="x", pady=2)

        tk.Label(
            card, text=f"Najlepszy wynik (Rekord): {game.high_score}",
            font=theme.FONT_BODY_BOLD, bg=theme.BG_PANEL_INNER, fg=theme.TEXT_PRIMARY, anchor="w",
        ).pack(fill="x", pady=2)

        if game.is_new_high_score and game.score > 0:
            tk.Label(
                body, text="★ NOWY REKORD! GRATULACJE! ★",
                font=theme.FONT_SUBTITLE, bg=theme.BG_PANEL, fg=theme.STYLE_COLORS["money"],
            ).pack(pady=(0, 10))

        tk.Button(
            body,
            text="Wróć do menu",
            font=theme.FONT_BODY_BOLD,
            bg=theme.BTN_RED_BG,
            fg=theme.BTN_RED_FG,
            activebackground=theme.BTN_RED_HOVER,
            activeforeground=theme.BTN_RED_FG,
            relief="flat",
            padx=18,
            pady=8,
            cursor="hand2",
            command=self._close,
        ).pack()

        tk.Label(
            body,
            text="Naciśnij Spację, Enter lub Esc, aby wrócić",
            font=theme.FONT_SMALL, bg=theme.BG_PANEL, fg=theme.TEXT_SECONDARY,
        ).pack(pady=(8, 0))

        self.bind("<Return>", lambda _e: self._close())
        self.bind("<space>", lambda _e: self._close())
        self.bind("<Escape>", lambda _e: self._close())
        self.protocol("WM_DELETE_WINDOW", self._close)

        h = 275 if (game.is_new_high_score and game.score > 0) else 245
        _center_over(self, parent, 400, h)
        self.grab_set()
        self.focus_set()

    def _close(self):
        self.destroy()
