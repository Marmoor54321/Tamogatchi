import curses

from model.shop import Shop
from view.base import GameView
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

MINIGAME_TICK_MS = 45

_STATS_FIELDS = frozenset({"hunger", "energy", "happiness", "health", "money", "high_score"})
_PET_FIELDS = frozenset({"mood", "active_skin", "is_sleeping", "is_alive"})
_MENU_FIELDS = frozenset({"money", "can_play", "is_alive", "is_sleeping"})

class ConsoleView(GameView):
    def __init__(self, stdscr, pet, shop=None, tick_ms=500):
        self.stdscr = stdscr
        self.pet = pet
        self.shop = shop or Shop(pet)
        self.tick_ms = tick_ms
        self.in_minigame = False
        self.pet.add_observer(self)

        try:
            curses.curs_set(0)
        except curses.error:
            pass
        self.stdscr.timeout(tick_ms)
        if hasattr(curses, "set_escdelay"):
            try:
                curses.set_escdelay(25)
            except curses.error:
                pass

        self.canvas = Canvas(stdscr)
        self.stats = StatsPanel(self.canvas, pet)
        self.pet_panel = PetPanel(self.canvas, pet)
        self.message = MessagePanel(self.canvas)
        self.menu = MenuPanel(self.canvas, pet, self.shop)
        self.panels = [self.stats, self.pet_panel, self.message, self.menu]
        self.minigame = MinigameScreen(self.canvas, pet)
        self.name_dialog = NameDialog(self.canvas)

        self.message.set(*(messages.WELCOME if pet.is_alive else messages.DIED_WHILE_AWAY))
        self.full_redraw()

    def get_command(self):
        key = read_key(self.stdscr)
        if key == RESIZE:
            self.full_redraw()
            return None
        return MENU_KEYS.get(key)

    def get_minigame_command(self):
        key = read_key(self.stdscr)
        return None if key == RESIZE else MINIGAME_KEYS.get(key)

    def show_menu(self, items, selected_idx):
        self.menu.set_items(items, selected_idx)
        self.pet_panel.preview_skin = self.menu.hovered_skin()
        self.message.show_hint(self.menu.describe_hovered())
        if self.in_minigame:
            return
        self.menu.redraw()
        self.pet_panel.redraw()
        self.message.redraw()

    def ask_pet_name(self, current_name, is_resurrection=False):
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

    def update(self, event_name, data=None):
        msg = messages.message_for(event_name, data, shop=self.shop)
        if msg:
            self.message.set(*msg)

        if self.in_minigame:
            return

        if event_name == "stats_changed":
            changed = data.get("rounded") if isinstance(data, dict) else None
            if changed is not None and not changed:
                return
            panels = []
            if changed is None or changed & _STATS_FIELDS:
                panels.append(self.stats)
            if changed is None or changed & _PET_FIELDS:
                panels.append(self.pet_panel)
            if changed is None or changed & _MENU_FIELDS:
                panels.append(self.menu)
            if panels:
                self._redraw(*panels)
            if self.message.hint and (changed is None or changed & _MENU_FIELDS):
                self.message.show_hint(self.menu.describe_hovered())
                self.message.redraw()
        elif event_name == "pet_died":
            self.full_redraw()
        elif event_name == "pet_resurrected":
            self._redraw(self.message, self.pet_panel)
        elif event_name == "pet_renamed":
            self.full_redraw()
        elif event_name.startswith("action_"):
            self._redraw(self.stats, self.message, self.pet_panel, self.menu)

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

    def start_minigame(self, game):
        self.in_minigame = True
        self.stdscr.timeout(MINIGAME_TICK_MS)
        self.canvas.erase()
        self.canvas.refresh()

    def draw_minigame(self, game):
        self.minigame.draw(game)

    def show_minigame_game_over(self, game):
        self.minigame.draw_game_over(game)
        curses.napms(350)
        self.stdscr.timeout(-1)
        self.stdscr.getch()

    def end_minigame(self):
        self.in_minigame = False
        self.stdscr.timeout(self.tick_ms)
        self.full_redraw()

