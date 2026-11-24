# controller/game_controller.py
import time
from model.observer import Observer
from model.shop import Shop

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

    def __init__(self, model, view, shop=None):
        self.model = model
        self.view = view
        self.shop = shop or Shop(model)

        self.main_menu = list(MAIN_MENU)
        # Menu sklepu buduje się samo z katalogu - nowy przedmiot w model/shop.py
        # od razu pojawia się w grze
        self.shop_menu = [f"buy:{item_id}" for item_id in self.shop.items] + ["skins", "back"]
        self.skins_menu = [f"skin:{skin_id}" for skin_id in self.shop.skin_prices] + ["back"]
        self.death_menu = list(DEATH_MENU)

        # Zwierzak mógł umrzeć podczas nieobecności gracza (wczytany zapis)
        self.menu = self.main_menu if model.is_alive else self.death_menu
        self.selected_idx = 0
        self.running = False
        self._last_tick = time.monotonic()

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
        self._last_tick = time.monotonic()
        try:
            while self.running:
                command = self.view.get_command()
                self._tick()
                if command:
                    self.handle_command(command)
        finally:
            # Zapis także przy Ctrl+C
            self.model.save_state()

    def _tick(self):
        """Przekazuje zwierzakowi czas, który upłynął od poprzedniego wywołania.

        Jeden zegar dla całej gry (menu i minigra), więc żadna sekunda nie jest
        liczona dwa razy, a naciskanie klawiszy nie przyspiesza gry.
        Zwraca liczbę sekund (przydaje się minigrze do fizyki).
        """
        now = time.monotonic()
        dt = now - self._last_tick
        self._last_tick = now
        self.model.pass_time(dt)
        return dt

    def handle_command(self, command):
        if command == "NEXT":
            self._move(1)
        elif command == "PREV":
            self._move(-1)
        elif command == "CONFIRM":
            self._execute(self.menu[self.selected_idx])
        elif command == "BACK":
            self._go_back()

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
            self._go_back()
        elif action == "skins":
            self._open_menu(self.skins_menu)
        elif action.startswith("skin:"):
            skin_id = action[len("skin:"):]
            # Kupiona -> zakładamy, niekupiona -> sklep próbuje sprzedać
            if self.model.owns_skin(skin_id):
                self.model.equip_skin(skin_id)
            else:
                self.shop.buy_skin(skin_id)
        elif action == "play":
            self._play_minigame()
        elif action == "sleep":
            self.model.sleep()
        elif action.startswith("buy:"):
            self.shop.buy(action[len("buy:"):])

    def _play_minigame(self):
        """Uruchamia minigrę typu Chrome Dino.
        Zamiast natychmiastowej kasy za samo kliknięcie, gracz zdobywa 10$ za każdą przeskoczoną przeszkodę.
        """
        from model.dino_game import DinoGame
        game = DinoGame(track_width=58, high_score=self.model.high_score)
        self.view.start_minigame(game)
        self._tick()  # Od tej chwili liczymy czas gry

        while not game.is_game_over:
            cmd = self.view.get_minigame_command()
            if cmd == "QUIT":
                break
            elif cmd == "JUMP":
                game.jump()

            # Czas płynie też dla zwierzaka - ten sam zegar co w menu
            dt = self._tick()
            if not self.model.is_alive:
                break  # Zwierzak padł w trakcie biegu - koniec zabawy, bez nagrody

            game.update(dt)
            self.view.draw_minigame(game)

        # Zapisujemy wynik zabawy w modelu (10$ za przeszkodę + aktualizacja rekordu).
        # Martwy zwierzak nic nie dostaje - model sam to sprawdza.
        self.model.record_minigame_result(game.score)

        # Ekran końcowy tylko po kolizji (nie po ESC/Q ani po śmierci zwierzaka)
        if game.is_game_over and self.model.is_alive:
            self.view.show_minigame_game_over(game)
            self._tick()  # Czas na ekranie końcowym też się liczy (raz)

        self.view.end_minigame()
        self._show_menu()

    def _go_back(self):
        """Skórki -> Sklep -> Menu główne."""
        if self.menu is self.skins_menu:
            self._open_menu(self.shop_menu)
        elif self.menu is self.shop_menu:
            self._open_menu(self.main_menu)

    def _move(self, direction):
        self.selected_idx = (self.selected_idx + direction) % len(self.menu)
        self._show_menu()

    def _open_menu(self, menu):
        self.menu = menu
        self.selected_idx = 0
        self._show_menu()

    def _show_menu(self):
        self.view.show_menu(self.menu, self.selected_idx)
