# controller/game_controller.py
import time
from model.observer import Observer

# Menu to listy identyfikatorów akcji - napisy do wyświetlenia zna tylko widok.
MAIN_MENU = ["shop", "play", "sleep", "exit"]
DEATH_MENU = ["resurrect", "exit"]


class GameController(Observer):
    """Steruje grą niezależnie od rodzaju widoku.

    Widok musi udostępniać tylko dwie metody:
      - get_command() -> "NEXT" | "PREV" | "CONFIRM" | "BACK" | None
        (czeka krótko na wejście użytkownika, ustala tempo pętli gry)
      - show_menu(items, selected_idx)
    Dzięki temu wersja graficzna wymaga jedynie nowej klasy widoku.
    """

    def __init__(self, model, view):
        self.model = model
        self.view = view

        self.main_menu = list(MAIN_MENU)
        self.shop_menu = [f"buy:{name}" for name in model.shop_items] + ["back"]
        self.death_menu = list(DEATH_MENU)

        # Zwierzak mógł umrzeć podczas nieobecności gracza (wczytany zapis)
        self.menu = self.main_menu if model.is_alive else self.death_menu
        self.selected_idx = 0
        self.running = False

        # Kontroler też obserwuje model, żeby zareagować np. na śmierć zwierzaka
        self.model.add_observer(self)

    # --- METODA Z WZORCA OBSERWATOR ---
    def update(self, event_name, data=None):
        if event_name == "pet_died":
            self._open_menu(self.death_menu)  # Zostaje tylko "Odródź" i "Wyjście"
        elif event_name == "pet_resurrected":
            self._open_menu(self.main_menu)

    # --- GŁÓWNA PĘTLA ---
    def run(self):
        self.running = True
        self._show_menu()
        last_tick = time.monotonic()
        try:
            while self.running:
                command = self.view.get_command()

                # Czas mija - liczymy ile faktycznie upłynęło od ostatniego obiegu,
                # więc naciskanie klawiszy nie przyspiesza gry.
                now = time.monotonic()
                self.model.pass_time(now - last_tick)
                last_tick = now

                if command:
                    self.handle_command(command)
        finally:
            # Zapis także przy Ctrl+C
            self.model.save_state()

    def handle_command(self, command):
        if command == "NEXT":
            self._move(1)
        elif command == "PREV":
            self._move(-1)
        elif command == "CONFIRM":
            self._execute(self.menu[self.selected_idx])
        elif command == "BACK":
            if self.menu is self.shop_menu:
                self._open_menu(self.main_menu)

    # --- POMOCNICZE ---
    def _execute(self, action):
        if action == "exit":
            self.running = False
            return

        if action == "resurrect":
            self.model.resurrect()  # Menu główne otworzy się po zdarzeniu "pet_resurrected"
            return

        # Martwy zwierzak nie może nic robić - tylko "Odródź" albo "Wyjście"
        if not self.model.is_alive:
            return

        if action == "shop":
            self._open_menu(self.shop_menu)
        elif action == "back":
            self._open_menu(self.main_menu)
        elif action == "play":
            self.model.play()
        elif action == "sleep":
            self.model.sleep()
        elif action.startswith("buy:"):
            self.model.buy_and_feed(action[len("buy:"):])

    def _move(self, direction):
        self.selected_idx = (self.selected_idx + direction) % len(self.menu)
        self._show_menu()

    def _open_menu(self, menu):
        self.menu = menu
        self.selected_idx = 0
        self._show_menu()

    def _show_menu(self):
        self.view.show_menu(self.menu, self.selected_idx)
