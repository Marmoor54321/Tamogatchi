# view/gui/menu_panel.py
"""Panel interaktywnych przycisków menu (obsługa myszy i klawiatury)."""
import tkinter as tk
from view.common import action_label, describe_action, is_action_available
from view.gui import theme


class MenuPanel(tk.Frame):
    """Buduje przyciski dla aktywnego menu kontrolera.

    - Przyciski "Wyjście" ("exit") i "Wróć" ("back") są zawsze czerwone.
    - Przebudowuje widżety przycisków tylko przy zmianie listy akcji;
      przy zmianie zaznaczenia lub dostępności aktualizuje wyłącznie kolory/ramki.
    """

    def __init__(self, parent, pet, shop, on_hover, on_select):
        super().__init__(
            parent,
            bg=theme.BG_PANEL,
            highlightbackground=theme.BORDER_SUBTLE,
            highlightthickness=1,
            padx=14,
            pady=12,
        )
        self.pet = pet
        self.shop = shop
        self.on_hover = on_hover
        self.on_select = on_select

        self.items = []
        self.selected_idx = 0
        self._rendered_items = None
        self._buttons: list[tk.Button] = []
        self._button_states: list[tuple] = []

        header = tk.Frame(self, bg=theme.BG_PANEL)
        header.pack(fill="x", pady=(0, 8))

        tk.Label(
            header,
            text="Akcje",
            font=theme.FONT_SUBTITLE,
            bg=theme.BG_PANEL,
            fg=theme.TEXT_PRIMARY,
        ).pack(side="left")

        self.hint_label = tk.Label(
            header,
            text="← → wybór  •  Enter zatwierdź  •  Esc wstecz",
            font=theme.FONT_HINT,
            bg=theme.BG_PANEL,
            fg=theme.TEXT_SECONDARY,
        )
        self.hint_label.pack(side="right")

        # Stała wysokość kontenera przycisków dopasowana do największego menu (np. Sklep),
        # dzięki czemu panel zwierzaka nigdy nie zmienia rozmiaru przy przełączaniu menu.
        max_items = max(4, len(self.shop.items) + 2, len(self.shop.skin_prices) + 1)
        self._max_rows = (max_items + 3) // 4
        sample = tk.Button(self, text="Sample", font=theme.FONT_BODY_BOLD, padx=12, pady=10, bd=0)
        self._row_h = sample.winfo_reqheight() + 8
        sample.destroy()

        self.btn_container = tk.Frame(
            self,
            bg=theme.BG_PANEL,
            height=self._max_rows * self._row_h,
        )
        self.btn_container.pack(fill="x")
        self.btn_container.grid_propagate(False)
        for r in range(self._max_rows):
            self.btn_container.rowconfigure(r, minsize=self._row_h)

    def set_items(self, items, selected_idx):
        self.items = list(items)
        self.selected_idx = selected_idx

    def hovered_skin(self):
        if 0 <= self.selected_idx < len(self.items):
            action = self.items[self.selected_idx]
            if action.startswith("skin:"):
                return action[len("skin:"):]
        return None

    def describe_hovered(self):
        if not 0 <= self.selected_idx < len(self.items):
            return None
        return describe_action(self.items[self.selected_idx], self.pet, self.shop)

    def _rebuild_buttons(self):
        for btn in self._buttons:
            btn.destroy()
        self._buttons.clear()
        self._button_states.clear()

        # Rozkład w siatce (max 4 kolumny, żeby przyciski w sklepie wygodnie się mieściły)
        cols = min(4, max(1, len(self.items)))
        for c in range(4):
            self.btn_container.columnconfigure(c, weight=1 if c < cols else 0)

        for idx, action in enumerate(self.items):
            r, c = divmod(idx, 4)
            btn = tk.Button(
                self.btn_container,
                text="",
                font=theme.FONT_BODY_BOLD,
                relief="flat",
                bd=0,
                cursor="hand2",
                padx=12,
                pady=10,
                takefocus=0,
                command=lambda i=idx: self.on_select(i),
            )
            btn.bind("<Enter>", lambda _e, i=idx: self.on_hover(i))
            btn.grid(row=r, column=c, sticky="ew", padx=5, pady=4)
            self._buttons.append(btn)
            self._button_states.append(None)

        self._rendered_items = list(self.items)

    def redraw(self, force=False):
        """Aktualizuje tylko te przyciski, których stan (etykieta, zaznaczenie, dostępność) się zmienił."""
        if force or self._rendered_items != self.items:
            self._rebuild_buttons()

        for idx, action in enumerate(self.items):
            label = action_label(action, self.pet, self.shop)
            available = is_action_available(action, self.pet, self.shop)
            selected = idx == self.selected_idx
            is_red = action in theme.RED_ACTIONS
            state = (label, available, selected, is_red)

            if not force and self._button_states[idx] == state:
                continue
            self._button_states[idx] = state

            btn = self._buttons[idx]
            display_text = f"▸ {label}" if selected else label

            if is_red:
                bg = theme.BTN_RED_SELECTED_BG if selected else theme.BTN_RED_BG
                active_bg = theme.BTN_RED_HOVER
                fg = theme.BTN_RED_FG
                hl_col = theme.BTN_RED_SELECTED_BORDER if selected else "#991B1B"
            elif not available:
                bg = theme.BTN_DISABLED_SELECTED_BG if selected else theme.BTN_DISABLED_BG
                active_bg = theme.BTN_DISABLED_SELECTED_BG
                fg = theme.BTN_DISABLED_FG
                hl_col = theme.TEXT_SECONDARY if selected else theme.BORDER_SUBTLE
            elif selected:
                bg = theme.BTN_SELECTED_BG
                active_bg = "#2563EB"
                fg = theme.BTN_SELECTED_FG
                hl_col = theme.BTN_SELECTED_BORDER
            else:
                bg = theme.BTN_NORMAL_BG
                active_bg = theme.BTN_NORMAL_HOVER
                fg = theme.BTN_NORMAL_FG
                hl_col = theme.BORDER_SUBTLE

            btn.configure(
                text=display_text,
                bg=bg,
                fg=fg,
                activebackground=active_bg,
                activeforeground=fg,
                highlightthickness=2 if selected else 1,
                highlightbackground=hl_col,
                highlightcolor=hl_col,
            )
