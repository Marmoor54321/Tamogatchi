# view/gui/message_panel.py
"""Panel komunikatów i podpowiedzi z inteligentnym odświeżaniem."""
import tkinter as tk
from view.gui import theme

STYLE_ICONS = {
    "good": "✔",
    "info": "ℹ",
    "warn": "⚠",
    "bad": "✖",
    "sleepy": "💤",
    "text": "•",
}


class MessagePanel(tk.Frame):
    """Wyświetla ostatni komunikat gry albo podpowiedź zaznaczonego przycisku."""

    def __init__(self, parent):
        super().__init__(
            parent,
            bg=theme.BG_PANEL,
            highlightbackground=theme.BORDER_SUBTLE,
            highlightthickness=1,
            padx=14,
            pady=10,
        )
        self.text = ""
        self.style_name = "info"
        self.hint = None
        self._rendered = None

        self.accent_bar = tk.Frame(self, width=5, bg=theme.STYLE_COLORS["info"])
        self.accent_bar.pack(side="left", fill="y", padx=(0, 12))

        content = tk.Frame(self, bg=theme.BG_PANEL)
        content.pack(side="left", fill="both", expand=True)

        self.title_label = tk.Label(
            content,
            text="Komunikat",
            font=theme.FONT_SMALL,
            bg=theme.BG_PANEL,
            fg=theme.TEXT_MUTED,
            anchor="w",
        )
        self.title_label.pack(fill="x")

        self.msg_label = tk.Label(
            content,
            text="",
            font=theme.FONT_BODY_BOLD,
            bg=theme.BG_PANEL,
            fg=theme.STYLE_COLORS["info"],
            anchor="w",
            justify="left",
        )
        self.msg_label.pack(fill="x", pady=(2, 0))

    def set(self, text: str, style_name: str):
        self.text = text
        self.style_name = style_name
        self.hint = None

    def show_hint(self, hint):
        self.hint = hint

    def redraw(self, force=False):
        """Aktualizuje widżety wyłącznie wtedy, gdy treść lub styl uległy zmianie."""
        if self.hint:
            raw_text, style_name = self.hint
            header = "Podpowiedź"
            prefix = "?"
        else:
            raw_text, style_name = self.text, self.style_name
            header = "Komunikat"
            prefix = STYLE_ICONS.get(style_name, "•")

        state = (header, prefix, raw_text, style_name)
        if not force and state == self._rendered:
            return
        self._rendered = state

        color = theme.STYLE_COLORS.get(style_name, theme.TEXT_PRIMARY)
        self.accent_bar.configure(bg=color)
        self.title_label.configure(text=header)
        self.msg_label.configure(text=f"{prefix}  {raw_text}", fg=color)
