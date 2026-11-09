# view/console_view.py
import curses
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

# Układ ekranu
ROW_STATS = 0
STATS_X = 2
ROW_ART = 8
ART_X = 15
ROW_MESSAGE = 12
MESSAGE_X = 5
ROW_MENU = 15
MENU_X = 5
MENU_SPACING = 14


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

        # Menu przekazywane przez kontroler (lista identyfikatorów akcji)
        self.menu_items = []
        self.selected_idx = 0
        if pet.is_alive:
            self.current_message = "Witaj w Tamagotchi! Strzalki: wybor, Enter: akcja, Esc: wroc."
        else:
            self.current_message = "Pod twoja nieobecnosc zwierzak umarl (X_X). Wybierz 'Odrodz'!"

        self.full_redraw()

    # --- WEJŚCIE ---
    def get_command(self):
        """Czeka na klawisz (maks. jeden tick) i zwraca komendę albo None."""
        key = self.stdscr.getch()
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
            self.current_message = "Zwierzak umarl (X_X). Wybierz 'Odrodz', by go wskrzesic!"
            self.full_redraw()

        elif event_name == "pet_resurrected":
            self.current_message = "Magia! Zwierzak dostal drugie zycie!"
            self.draw_message()
            self.draw_art()

        elif event_name.startswith("action_"):
            messages = {
                "action_feed": "Mniam! (+Glod)",
                "action_play": f"Super zabawa! (+Szczescie, -Energia, +{self.pet.PLAY_REWARD}$)",
                "action_sleep": "Zzz... (+Energia)",
                "action_buy_success": f"Kupiono i zjedzono: {data}!",
                "action_buy_fail": f"Za malo kasy na: {data}! Baw sie, by zarobic.",
            }
            self.current_message = messages.get(event_name, self.current_message)
            self.draw_stats()  # Kasa lub statystyki mogły się zmienić
            self.draw_message()
            self.draw_art()

    # --- POMOCNICZE ---
    def _put(self, y, x, text, attr=curses.A_NORMAL):
        """Bezpieczny addstr - za małe okno nie wywraca gry."""
        try:
            self.stdscr.addstr(y, x, text, attr)
        except curses.error:
            pass

    def _clear_line(self, y, x=0):
        """Czyści wiersz od kolumny x do końca (bez resztek dłuższych napisów)."""
        try:
            self.stdscr.move(y, x)
            self.stdscr.clrtoeol()
        except curses.error:
            pass

    def _label(self, action):
        if action.startswith("buy:"):
            name = action[len("buy:"):]
            return f"{name}({self.pet.shop_items[name]['price']}$)"
        return ACTION_LABELS.get(action, action)

    def _bar(self, value):
        """Generuje pasek postępu np: [######----]  60%"""
        value = round(value)
        bars = value // 10
        return "[" + "#" * bars + "-" * (10 - bars) + f"] {value:3}%"

    # --- RYSOWANIE POSZCZEGÓLNYCH SEKCJI ---
    def draw_menu(self):
        self._clear_line(ROW_MENU)
        for i, action in enumerate(self.menu_items):
            x = MENU_X + i * MENU_SPACING
            attr = curses.A_REVERSE if i == self.selected_idx else curses.A_NORMAL
            self._put(ROW_MENU, x, f" {self._label(action)} ", attr)
        self.stdscr.refresh()

    def draw_stats(self):
        lines = [
            f" Zwierzak: {self.pet.name} | Kasa: {self.pet.money}$",
            f" Glod:     {self._bar(self.pet.hunger)}",
            f" Energia:  {self._bar(self.pet.energy)}",
            f" Szczescie:{self._bar(self.pet.happiness)}",
            f" Zdrowie:  {self._bar(self.pet.health)}",
        ]
        for i, line in enumerate(lines):
            self._clear_line(ROW_STATS + i, STATS_X)
            self._put(ROW_STATS + i, STATS_X, line)
        self.stdscr.refresh()

    def draw_art(self):
        """Dynamiczny ASCII Art zależny od statystyk z Modelu"""
        if not self.pet.is_alive:
            art = [" (X_X) ", " /| |\\ "]
        elif self.pet.energy < 30:
            art = [" (-_-)zZ", " /| |\\ "]  # Śpiący
        elif self.pet.happiness < 40:
            art = [" (T_T) ", " /| |\\ "]  # Smutny
        else:
            art = [" (^o^) ", " /| |\\ "]  # Szczęśliwy

        for i, line in enumerate(art):
            self._clear_line(ROW_ART + i, ART_X)  # Czyść tylko miejsce na obrazek
            self._put(ROW_ART + i, ART_X, line)
        self.stdscr.refresh()

    def draw_message(self):
        self._clear_line(ROW_MESSAGE, MESSAGE_X)  # Czyść tylko linijkę z wiadomością
        self._put(ROW_MESSAGE, MESSAGE_X, f"> {self.current_message}")
        self.stdscr.refresh()

    def full_redraw(self):
        self.stdscr.erase()
        self.draw_stats()
        self.draw_art()
        self.draw_message()
        self.draw_menu()
