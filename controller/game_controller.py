# controller/game_controller.py
import time
import model.dino_game as dino_game_module
from model.observer import Observer
from model.shop import Shop

# Menu to listy identyfikatorów akcji - napisy do wyświetlenia zna tylko widok.
MAIN_MENU = ["shop", "play", "sleep", "exit"]
DEATH_MENU = ["resurrect", "exit"]
SLEEP_MENU = ["wake", "exit"]   # Śpiący zwierzak: można go tylko obudzić


class GameController(Observer):
    """Steruje grą niezależnie od rodzaju widoku (tekstowego lub graficznego).

    Kontrakt widoku opisuje `view/base.py` (`GameView`).
    Obsługiwane komendy w `handle_command`:
      - klawiatura: "NEXT", "PREV", "CONFIRM", "BACK", "EXIT" / "QUIT"
      - mysz / akcje bezpośrednie:
          ("HOVER", idx)      - zaznacza pozycję bez uruchamiania
          ("SELECT", idx)     - zaznacza i uruchamia pozycję o indeksie idx
          ("EXECUTE", action) - uruchamia wskazaną akcję z aktywnego menu
    """

    def __init__(
        self,
        model,
        view,
        shop=None,
        ask_name_on_start=False,
        track_width=58,
        event_driven=False,
    ):
        self.model = model
        self.view = view
        self.shop = shop or Shop(model)
        self.ask_name_on_start = ask_name_on_start
        self.track_width = track_width
        self.event_driven = event_driven

        self.main_menu = list(MAIN_MENU)
        # Menu sklepu buduje się samo z katalogu - nowy przedmiot w model/shop.py
        # od razu pojawia się w grze
        self.shop_menu = [f"buy:{item_id}" for item_id in self.shop.items] + ["skins", "back"]
        self.skins_menu = [f"skin:{skin_id}" for skin_id in self.shop.skin_prices] + ["back"]
        self.death_menu = list(DEATH_MENU)
        self.sleep_menu = list(SLEEP_MENU)

        # Zwierzak mógł umrzeć albo dalej spać po wczytaniu zapisu
        if not model.is_alive:
            self.menu = self.death_menu
        elif model.is_sleeping:
            self.menu = self.sleep_menu
        else:
            self.menu = self.main_menu
        self.selected_idx = 0
        self.running = False
        self.active_minigame = None
        self._last_tick = time.monotonic()

        # Kontroler też obserwuje model, żeby zareagować np. na śmierć zwierzaka
        self.model.add_observer(self)

    # --- METODA Z WZORCA OBSERWATOR ---
    def update(self, event_name, data=None):
        if event_name == "pet_died":
            self._open_menu(self.death_menu)  # Zostaje tylko "Odródź" i "Wyjście"
        elif event_name == "pet_resurrected":
            self._open_menu(self.main_menu)
        elif event_name == "action_sleep":
            self._open_menu(self.sleep_menu)
        elif event_name == "action_wake_up" and self.model.is_alive:
            self._open_menu(self.main_menu)  # Obudzony ręcznie albo sam się wyspał

    # --- CYKL ŻYCIA (PĘTLA I TRYB ZDARZENIOWY GUI) ---
    def start(self):
        """Inicjuje sesję gry (wspólne dla `run()` oraz pętli zdarzeń GUI)."""
        self.running = True
        self._show_menu()
        if self.ask_name_on_start:
            self._prompt_pet_name(is_resurrection=False)
        self._last_tick = time.monotonic()

    def step(self):
        """Wykonuje jeden krok czasowy gry (przydatne dla timerów w GUI)."""
        if not self.running:
            return False
        if self.active_minigame is not None:
            still_going = self.step_minigame()
            if not still_going and self.active_minigame is not None:
                self.finish_minigame_session(aborted=False)
            return self.running

        dt = self._tick()
        render = getattr(self.view, "render", None)
        if callable(render):
            render(dt)
        return self.running

    def finish(self):
        """Kończy sesję i zapisuje stan modelu."""
        self.running = False
        self.model.save_state()

    def run(self):
        try:
            self.start()
            while self.running:
                command = self.view.get_command()
                dt = self._tick()
                if command:
                    self.handle_command(command)
                if self.running:
                    render = getattr(self.view, "render", None)
                    if callable(render):
                        render(dt)
        finally:
            # Zapis także przy Ctrl+C
            self.finish()

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

    # --- KOMENDY (KLAWIATURA I MYSZ) ---
    def handle_command(self, command):
        if command == "NEXT":
            self._move(1)
        elif command == "PREV":
            self._move(-1)
        elif command == "CONFIRM":
            self._execute(self.menu[self.selected_idx])
        elif command == "BACK":
            self._go_back()
        elif command in ("EXIT", "QUIT"):
            self.request_exit()
        elif isinstance(command, tuple) and len(command) == 2:
            kind, arg = command
            if kind == "HOVER":
                self.hover_item(arg)
            elif kind == "SELECT":
                self.select_item(arg)
            elif kind in ("EXECUTE", "ACTION"):
                self.execute_action(arg)

    def hover_item(self, idx):
        """Ustawia zaznaczenie na wskazanym elemencie menu (np. najechanie myszą)."""
        if isinstance(idx, int) and 0 <= idx < len(self.menu) and idx != self.selected_idx:
            self.selected_idx = idx
            self._show_menu()

    def select_item(self, idx):
        """Zaznacza i od razu wykonuje element menu o indeksie `idx` (np. klik myszą)."""
        if isinstance(idx, int) and 0 <= idx < len(self.menu):
            self.selected_idx = idx
            self._show_menu()
            self._execute(self.menu[self.selected_idx])

    def execute_action(self, action):
        """Wykonuje wskazaną akcję z aktywnego menu (lub globalne 'exit')."""
        if action == "exit":
            self.request_exit()
            return
        if action in self.menu:
            self.select_item(self.menu.index(action))

    def request_exit(self):
        """Zamyka grę z dowolnego ekranu lub podmenu."""
        if self.active_minigame is not None:
            self.finish_minigame_session(aborted=True)
        self.running = False

    # --- POMOCNICZE ---
    def _execute(self, action):
        if action == "exit":
            self.running = False
            return

        if action == "resurrect":
            self.model.resurrect()  # Menu główne otworzy się po zdarzeniu "pet_resurrected"
            self._prompt_pet_name(is_resurrection=True)
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
            # O tym, czy zwierzak ma siłę na zabawę, decyduje model
            if self.model.start_play():
                if self.event_driven:
                    self.start_minigame_session()
                else:
                    self._play_minigame()
        elif action == "sleep":
            self.model.start_sleep()   # Menu snu otworzy się po zdarzeniu "action_sleep"
        elif action == "wake":
            self.model.wake_up()
        elif action.startswith("buy:"):
            self.shop.buy(action[len("buy:"):])

    # --- MINIGRA ---
    def start_minigame_session(self):
        """Rozpoczyna sesję minigry Dino (działa też w trybie zdarzeniowym GUI)."""
        game = dino_game_module.DinoGame(
            track_width=self.track_width,
            high_score=self.model.high_score,
        )
        self.active_minigame = game
        self.view.start_minigame(game)
        self._tick()  # Od tej chwili liczymy czas gry
        return game

    def handle_minigame_command(self, cmd):
        """Obsługuje pojedynczą komendę gracza w minigrze. Zwraca False przy wyjściu."""
        if self.active_minigame is None:
            return False
        if cmd in ("QUIT", "EXIT"):
            if cmd == "EXIT":
                self.running = False
            return False
        if cmd == "JUMP":
            self.active_minigame.jump()
        return True

    def step_minigame(self):
        """Wykonuje jedną klatkę logiki i rysowania minigry. Zwraca True, gdy gra trwa."""
        game = self.active_minigame
        if game is None or game.is_game_over:
            return False
        dt = self._tick()
        if not self.model.is_alive:
            return False  # Zwierzak padł w trakcie biegu - koniec zabawy, bez nagrody
        game.update(dt)
        self.view.draw_minigame(game)
        return not game.is_game_over

    def finish_minigame_session(self, aborted=False):
        """Kończy sesję minigry, przyznaje nagrodę i przywraca menu główne."""
        game = self.active_minigame
        if game is None:
            return
        self.active_minigame = None

        # Zapisujemy wynik zabawy w modelu (10$ za przeszkodę + aktualizacja rekordu).
        # Martwy zwierzak nic nie dostaje - model sam to sprawdza.
        self.model.record_minigame_result(game.score)

        # Ekran końcowy tylko po kolizji (nie po ESC/Q ani po śmierci zwierzaka)
        if not aborted and game.is_game_over and self.model.is_alive:
            result = self.view.show_minigame_game_over(game)
            if result in ("EXIT", "QUIT"):
                self.running = False
            self._tick()  # Czas na ekranie końcowym też się liczy (raz)

        self.view.end_minigame()
        self._show_menu()

    def _play_minigame(self):
        """Uruchamia minigrę typu Chrome Dino w trybie pętli synchronicznej."""
        game = self.start_minigame_session()
        aborted = False

        while not game.is_game_over:
            cmd = self.view.get_minigame_command()
            if not self.handle_minigame_command(cmd):
                aborted = True
                break
            if not self.step_minigame():
                break

        self.finish_minigame_session(aborted=aborted)

    def _prompt_pet_name(self, is_resurrection=False):
        """Wywołuje okno nadania imienia w widoku (przy pierwszym starcie lub odrodzeniu)."""
        ask = getattr(self.view, "ask_pet_name", None)
        if ask is None:
            return
        new_name = ask(self.model.name, is_resurrection=is_resurrection)
        if new_name and new_name.strip():
            self.model.rename(new_name)
        self._last_tick = time.monotonic()

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
