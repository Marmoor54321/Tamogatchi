# view/console_view.py
import curses
import sys
from model.observer import Observer

# Tłumaczenie klawiszy na abstrakcyjne komendy rozumiane przez kontroler.
# Kontroler nie wie nic o curses - widok GUI może generować te same komendy
# np. z kliknięć przycisków.
KEY_COMMANDS = {
    curses.KEY_RIGHT: "NEXT",
    curses.KEY_LEFT: "PREV",
    curses.KEY_ENTER: "CONFIRM",
    10: "CONFIRM",   # Enter (LF)
    13: "CONFIRM",   # Enter (CR)
    27: "BACK",      # Esc
    curses.KEY_BACKSPACE: "BACK",
    8: "BACK",       # Backspace (Windows)
    127: "BACK",     # Backspace (Linux)
}

# Napisy wyświetlane dla identyfikatorów akcji z kontrolera.
ACTION_LABELS = {
    "shop": "Sklep",
    "play": "Zabawa",
    "sleep": "Śpij",
    "exit": "Wyjście",
    "back": "Wróć",
    "resurrect": "Odródź",
}

# --- UKŁAD EKRANU ---
# Każdy panel to (y, x, wysokość, szerokość) razem z ramką.
SCREEN_W = 66
SCREEN_H = 15
STATS_BOX = (0, 0, 8, 34)
PET_BOX = (0, 34, 8, 32)
MESSAGE_BOX = (8, 0, 3, 66)
MENU_BOX = (11, 0, 3, 66)
ROW_HINT = 14

BAR_WIDTH = 15
LABEL_WIDTH = 10
MENU_SPACING = 16

HINT = "<- -> wybor    Enter zatwierdz    Esc wroc ze sklepu"


def _acs(name, fallback):
    """Znak ramki z curses (dostępny dopiero po initscr) albo zwykły zamiennik."""
    return getattr(curses, "ACS_" + name, ord(fallback))


class ConsoleView(Observer):
    def __init__(self, stdscr, pet, tick_ms=500):
        self.stdscr = stdscr
        self.pet = pet
        # Podpinamy ten widok jako obserwatora naszego zwierzaka
        self.pet.add_observer(self)

        curses.curs_set(0)  # Ukryj migający kursor konsoli
        # get_command() czeka na klawisz maksymalnie tyle ms,
        # dzięki czemu czas w grze płynie także wtedy, gdy nic nie naciskamy.
        self.stdscr.timeout(tick_ms)
        if hasattr(curses, "set_escdelay"):
            try:
                curses.set_escdelay(25)  # Esc ma reagować od razu, a nie po 1 s
            except curses.error:
                pass

        self._init_colors()
        self.too_small = False

        # Menu przekazywane przez kontroler (lista identyfikatorów akcji)
        self.menu_items = []
        self.selected_idx = 0
        if pet.is_alive:
            self._set_message("Witaj w Tamagotchi! Zadbaj o swojego zwierzaka.", "info")
        else:
            self._set_message("Pod twoja nieobecnosc zwierzak umarl (X_X). Wybierz 'Odrodz'!", "bad")

        self.full_redraw()

    # --- KOLORY ---
    def _init_colors(self):
        """Tworzy style (kolor + atrybut). Bez obsługi kolorów zostają same atrybuty."""
        normal, bold = curses.A_NORMAL, curses.A_BOLD
        self.style = {
            "frame": normal, "title": bold, "text": normal, "info": bold,
            "good": bold, "warn": normal, "bad": bold, "money": bold,
            "selected": curses.A_REVERSE, "disabled": normal,
            "hint": normal, "empty": normal, "sleepy": normal,
        }
        try:
            if not curses.has_colors():
                return
            curses.start_color()
            try:
                curses.use_default_colors()
                bg = -1  # Przezroczyste tło - takie jak w terminalu
            except curses.error:
                bg = curses.COLOR_BLACK

            pairs = {
                # nazwa: (kolor tekstu, tło, dodatkowy atrybut)
                "frame": (curses.COLOR_CYAN, bg, normal),
                "title": (curses.COLOR_YELLOW, bg, bold),
                "text": (curses.COLOR_WHITE, bg, normal),
                "info": (curses.COLOR_WHITE, bg, bold),
                "good": (curses.COLOR_GREEN, bg, bold),
                "warn": (curses.COLOR_YELLOW, bg, bold),
                "bad": (curses.COLOR_RED, bg, bold),
                "money": (curses.COLOR_YELLOW, bg, bold),
                "selected": (curses.COLOR_BLACK, curses.COLOR_CYAN, bold),
                "disabled": (curses.COLOR_RED, bg, normal),
                "hint": (curses.COLOR_BLUE, bg, bold),
                "empty": (curses.COLOR_WHITE, bg, normal),
                "sleepy": (curses.COLOR_CYAN, bg, bold),
            }
            for i, (name, (fg, back, extra)) in enumerate(pairs.items(), start=1):
                curses.init_pair(i, fg, back)
                self.style[name] = curses.color_pair(i) | extra
        except curses.error:
            pass  # Terminal bez kolorów - zostają style awaryjne

    def _stat_style(self, value):
        """Zielony / żółty / czerwony zależnie od poziomu statystyki."""
        if value >= 60:
            return self.style["good"]
        if value >= 30:
            return self.style["warn"]
        return self.style["bad"]

    # --- WEJŚCIE ---
    def get_command(self):
        """Czeka na klawisz (maks. jeden tick) i zwraca komendę albo None."""
        key = self.stdscr.getch()
        if key == getattr(curses, "KEY_RESIZE", None):
            if sys.platform == "win32":
                try:
                    curses.resize_term(0, 0)  # PDCurses wymaga ręcznego odczytu nowego rozmiaru
                except curses.error:
                    pass
            self.full_redraw()
            return None
        return KEY_COMMANDS.get(key)

    # --- API DLA KONTROLERA ---
    def show_menu(self, items, selected_idx):
        """Wyświetla podane menu (identyfikatory akcji) z zaznaczoną pozycją."""
        self.menu_items = items
        self.selected_idx = selected_idx
        self.draw_menu()

    # --- METODA Z WZORCA OBSERWATOR ---
    def update(self, event_name, data=None):
        if event_name == "stats_changed":
            self.draw_stats()
            self.draw_art()

        elif event_name == "pet_died":
            self._set_message("Zwierzak umarl (X_X). Wybierz 'Odrodz', by go wskrzesic!", "bad")
            self.full_redraw()

        elif event_name == "pet_resurrected":
            self._set_message("Magia! Zwierzak dostal drugie zycie!", "good")
            self.draw_message()
            self.draw_art()

        elif event_name.startswith("action_"):
            messages = {
                "action_feed": ("Mniam! (+Glod)", "good"),
                "action_play": (f"Super zabawa! (+Szczescie, -Energia, +{self.pet.PLAY_REWARD}$)", "good"),
                "action_sleep": ("Zzz... (+Energia)", "sleepy"),
                "action_buy_success": (f"Kupiono i zjedzono: {data}!", "good"),
                "action_buy_fail": (f"Za malo kasy na: {data}! Baw sie, by zarobic.", "bad"),
            }
            if event_name in messages:
                self._set_message(*messages[event_name])
            self.draw_stats()  # Kasa lub statystyki mogły się zmienić
            self.draw_message()
            self.draw_art()
            self.draw_menu()   # Zmiana kasy zmienia, na co nas stać w sklepie

    # --- POMOCNICZE ---
    def _set_message(self, text, style_name):
        self.current_message = text
        self.message_style = style_name

    def _put(self, y, x, text, attr=curses.A_NORMAL):
        """Bezpieczny addstr - za małe okno nie wywraca gry."""
        try:
            self.stdscr.addstr(y, x, text, attr)
        except curses.error:
            pass

    def _hline(self, y, x, ch, n):
        if n > 0:
            try:
                self.stdscr.hline(y, x, ch, n)
            except curses.error:
                pass

    def _fill(self, y, x, width):
        """Czyści fragment wiersza wewnątrz panelu (nie rusza ramek obok)."""
        self._put(y, x, " " * width)

    def _clear_inside(self, box):
        y, x, h, w = box
        for row in range(y + 1, y + h - 1):
            self._fill(row, x + 1, w - 2)

    def _draw_box(self, box, title):
        y, x, h, w = box
        a = self.style["frame"]
        try:
            self.stdscr.addch(y, x, _acs("ULCORNER", "+") | a)
            self.stdscr.addch(y, x + w - 1, _acs("URCORNER", "+") | a)
            self.stdscr.addch(y + h - 1, x, _acs("LLCORNER", "+") | a)
            self.stdscr.addch(y + h - 1, x + w - 1, _acs("LRCORNER", "+") | a)
            self.stdscr.vline(y + 1, x, _acs("VLINE", "|") | a, h - 2)
            self.stdscr.vline(y + 1, x + w - 1, _acs("VLINE", "|") | a, h - 2)
        except curses.error:
            pass
        self._hline(y, x + 1, _acs("HLINE", "-") | a, w - 2)
        self._hline(y + h - 1, x + 1, _acs("HLINE", "-") | a, w - 2)
        self._put(y, x + 2, f" {title} ", self.style["title"])

    def _label(self, action):
        if action.startswith("buy:"):
            name = action[len("buy:"):]
            return f"{name}({self.pet.shop_items[name]['price']}$)"
        return ACTION_LABELS.get(action, action)

    def _can_afford(self, action):
        if not action.startswith("buy:"):
            return True
        return self.pet.money >= self.pet.shop_items[action[len("buy:"):]]["price"]

    def _draw_bar(self, y, x, label, value):
        """Rysuje np.:  Energia   ██████████▒▒▒▒▒  67%  (kolor zależny od wartości)"""
        value = round(value)
        filled = round(value * BAR_WIDTH / 100)
        self._put(y, x, label.ljust(LABEL_WIDTH), self.style["text"])
        bar_x = x + LABEL_WIDTH
        self._hline(y, bar_x, _acs("BLOCK", "#") | self._stat_style(value), filled)
        self._hline(y, bar_x + filled, _acs("CKBOARD", "-") | self.style["empty"], BAR_WIDTH - filled)
        self._put(y, bar_x + BAR_WIDTH, f"{value:4}%", self._stat_style(value))

    # --- RYSOWANIE POSZCZEGÓLNYCH SEKCJI ---
    def draw_menu(self):
        if self.too_small:
            return
        y, x, h, w = MENU_BOX
        self._clear_inside(MENU_BOX)
        for i, action in enumerate(self.menu_items):
            if i == self.selected_idx:
                attr = self.style["selected"]
            elif not self._can_afford(action):
                attr = self.style["disabled"]
            else:
                attr = self.style["text"]
            self._put(y + 1, x + 2 + i * MENU_SPACING, f" {self._label(action)} ", attr)
        self.stdscr.refresh()

    def draw_stats(self):
        if self.too_small:
            return
        y, x, h, w = STATS_BOX
        cx = x + 2
        self._clear_inside(STATS_BOX)
        self._put(y + 1, cx, "Kasa:", self.style["text"])
        self._put(y + 1, cx + LABEL_WIDTH, f"{self.pet.money}$", self.style["money"])
        self._draw_bar(y + 3, cx, "Glod", self.pet.hunger)
        self._draw_bar(y + 4, cx, "Energia", self.pet.energy)
        self._draw_bar(y + 5, cx, "Szczescie", self.pet.happiness)
        self._draw_bar(y + 6, cx, "Zdrowie", self.pet.health)
        self.stdscr.refresh()

    def draw_art(self):
        """Dynamiczny ASCII Art zależny od statystyk z Modelu"""
        if self.too_small:
            return
        if not self.pet.is_alive:
            art, mood, style = [" (X_X) ", " /| |\\ "], "Nie zyje", "bad"
        elif self.pet.energy < 30:
            art, mood, style = [" (-_-)zZ", " /| |\\ "], "Spiacy", "sleepy"
        elif self.pet.happiness < 40:
            art, mood, style = [" (T_T) ", " /| |\\ "], "Smutny", "warn"
        else:
            art, mood, style = [" (^o^) ", " /| |\\ "], "Szczesliwy", "good"

        y, x, h, w = PET_BOX
        self._clear_inside(PET_BOX)  # Czyść tylko panel zwierzaka
        for i, line in enumerate(art):
            self._put(y + 2 + i, x + (w - len(line)) // 2, line, self.style[style])
        self._put(y + h - 2, x + (w - len(mood)) // 2, mood, self.style[style])
        self.stdscr.refresh()

    def draw_message(self):
        if self.too_small:
            return
        y, x, h, w = MESSAGE_BOX
        self._clear_inside(MESSAGE_BOX)  # Czyść tylko linijkę z wiadomością
        text = f"> {self.current_message}"[: w - 4]
        self._put(y + 1, x + 2, text, self.style[self.message_style])
        self.stdscr.refresh()

    def full_redraw(self):
        self.stdscr.erase()
        rows, cols = self.stdscr.getmaxyx()
        self.too_small = rows < SCREEN_H or cols < SCREEN_W
        if self.too_small:
            self._put(0, 0, f"Powieksz okno terminala (min. {SCREEN_W}x{SCREEN_H}).", self.style["bad"])
            self.stdscr.refresh()
            return

        self._draw_box(STATS_BOX, "Statystyki")
        self._draw_box(PET_BOX, self.pet.name)
        self._draw_box(MESSAGE_BOX, "Komunikat")
        self._draw_box(MENU_BOX, "Menu")
        self._put(ROW_HINT, 2, HINT, self.style["hint"])

        self.draw_stats()
        self.draw_art()
        self.draw_message()
        self.draw_menu()
