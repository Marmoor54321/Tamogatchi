# view/console_view.py
"""Widok konsolowy (curses) - składa ekran z małych widoków z view/console/.

ConsoleView sam niczego nie rysuje. Udostępnia kontrolerowi to samo API co
wcześniej (get_command, show_menu, start_minigame, ...), odbiera zdarzenia
z modelu i mówi odpowiednim panelom, żeby się przerysowały.
"""
import curses

from model.observer import Observer
from model.shop import Shop
from view.console import messages
from view.console.canvas import Canvas
from view.console.keys import MENU_KEYS, MINIGAME_KEYS, RESIZE, read_key
from view.console.layout import HINT, ROW_HINT, SCREEN_H, SCREEN_W, TOO_SMALL
from view.console.menu_panel import MenuPanel
from view.console.message_panel import MessagePanel
from view.console.minigame_screen import MinigameScreen
from view.console.name_dialog import NameDialog
from view.console.pet_panel import PetPanel
from view.console.stats_panel import StatsPanel

MINIGAME_TICK_MS = 45  # ~22 FPS


class ConsoleView(Observer):
    def __init__(self, stdscr, pet, shop=None, tick_ms=500):
        self.stdscr = stdscr
        self.pet = pet
        self.tick_ms = tick_ms
        self.in_minigame = False
        # Podpinamy ten widok jako obserwatora naszego zwierzaka
        self.pet.add_observer(self)

        try:
            curses.curs_set(0)  # Ukryj migający kursor konsoli
        except curses.error:
            pass
        # get_command() czeka na klawisz maksymalnie tyle ms,
        # dzięki czemu czas w grze płynie także wtedy, gdy nic nie naciskamy.
        self.stdscr.timeout(tick_ms)
        if hasattr(curses, "set_escdelay"):
            try:
                curses.set_escdelay(25)  # Esc ma reagować od razu, a nie po 1 s
            except curses.error:
                pass

        # --- Małe widoki ---
        self.canvas = Canvas(stdscr)
        self.stats = StatsPanel(self.canvas, pet)
        self.pet_panel = PetPanel(self.canvas, pet)
        self.message = MessagePanel(self.canvas)
        self.menu = MenuPanel(self.canvas, pet, shop or Shop(pet))
        self.panels = [self.stats, self.pet_panel, self.message, self.menu]
        self.minigame = MinigameScreen(self.canvas, pet)
        self.name_dialog = NameDialog(self.canvas)

        self.message.set(*(messages.WELCOME if pet.is_alive else messages.DIED_WHILE_AWAY))
        self.full_redraw()

    # --- WEJŚCIE ---
    def get_command(self):
        """Czeka na klawisz (maks. jeden tick) i zwraca komendę albo None."""
        key = read_key(self.stdscr)
        if key == RESIZE:
            self.full_redraw()
            return None
        return MENU_KEYS.get(key)

    def get_minigame_command(self):
        """Odczytuje klawisz w trybie minigry: "JUMP", "QUIT" albo None."""
        key = read_key(self.stdscr)
        return None if key == RESIZE else MINIGAME_KEYS.get(key)

    # --- API DLA KONTROLERA ---
    def show_menu(self, items, selected_idx):
        """Wyświetla podane menu (identyfikatory akcji) z zaznaczoną pozycją."""
        self.menu.set_items(items, selected_idx)
        self.pet_panel.preview_skin = self.menu.hovered_skin()  # Podgląd w sklepie skórek
        self.message.show_hint(self.menu.describe_hovered())    # Co daje zaznaczony przedmiot
        if self.in_minigame:
            return  # Narysuje się po wyjściu z minigry (end_minigame)
        self.menu.redraw()
        self.pet_panel.redraw()
        self.message.redraw()

    def ask_pet_name(self, current_name, is_resurrection=False):
        """Pokazuje modalne okienko nadawania imienia i zwraca wybrane imię lub None."""
        self.full_redraw()
        self.stdscr.timeout(-1)
        try:
            return self.name_dialog.run(
                self.stdscr,
                current_name,
                is_resurrection=is_resurrection,
                redraw_bg=self.full_redraw,
            )
        finally:
            self.stdscr.timeout(self.tick_ms)
            self.full_redraw()

    # --- METODA Z WZORCA OBSERWATOR ---
    def update(self, event_name, data=None):
        # Komunikat zapamiętujemy zawsze - także ten z minigry (wynik biegu,
        # śmierć zwierzaka). Zobaczymy go po powrocie do menu.
        msg = messages.message_for(event_name, data)
        if msg:
            self.message.set(*msg)

        if self.in_minigame:
            # Podczas minigry nie przerysowujemy widoku Tamagotchi,
            # aby uniknąć migotania i nakładania się napisów.
            return

        if event_name == "stats_changed":
            # Energia spada z czasem - "Zabawa" może przestać (albo zacząć) być dostępna
            self._redraw(self.stats, self.pet_panel, self.menu)
            if self.message.hint:
                # Odśwież widoczną podpowiedź (np. "brakuje 10$", "za malo energii").
                # Gdy panel pokazuje wynik akcji, zostawiamy go w spokoju.
                self.message.show_hint(self.menu.describe_hovered())
                self.message.redraw()
        elif event_name == "pet_died":
            self.full_redraw()
        elif event_name == "pet_resurrected":
            self._redraw(self.message, self.pet_panel)
        elif event_name == "pet_renamed":
            self.full_redraw()
        elif event_name.startswith("action_"):
            # Kasa lub statystyki mogły się zmienić, a z nimi to, na co nas stać w sklepie
            self._redraw(self.stats, self.message, self.pet_panel, self.menu)

    # --- RYSOWANIE ---
    @staticmethod
    def _redraw(*panels):
        for panel in panels:
            panel.redraw()

    def full_redraw(self):
        c = self.canvas
        c.erase()
        c.too_small = not c.fits(SCREEN_H, SCREEN_W)
        if c.too_small:
            c.put(0, 0, TOO_SMALL, c.style["bad"])
            c.refresh()
            return

        for panel in self.panels:
            panel.draw_frame()
        c.put(ROW_HINT, 2, HINT, c.style["hint"])
        self._redraw(*self.panels)

    # --- MINIGRA ---
    def start_minigame(self, game):
        """Przygotowuje ekran i ustawia krótki timeout curses dla płynnej animacji."""
        self.in_minigame = True
        self.stdscr.timeout(MINIGAME_TICK_MS)
        self.canvas.erase()
        self.canvas.refresh()

    def draw_minigame(self, game):
        self.minigame.draw(game)

    def show_minigame_game_over(self, game):
        """Ekran podsumowania; czeka na dowolny klawisz."""
        self.minigame.draw_game_over(game)
        # Krótkie opóźnienie, by zapobiec przypadkowemu kliknięciu podczas skoku
        curses.napms(350)
        self.stdscr.timeout(-1)
        self.stdscr.getch()

    def end_minigame(self):
        """Przywraca normalny timeout konsoli i odświeża widok Tamagotchi."""
        self.in_minigame = False
        self.stdscr.timeout(self.tick_ms)
        self.full_redraw()
