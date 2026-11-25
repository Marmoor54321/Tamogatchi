import time
import model.dino_game as dino_game_module
from model.observer import Observer
from model.shop import Shop

# Menu to listy identyfikatorów akcji - napisy do wyświetlenia zna tylko widok.
MAIN_MENU = ["shop", "play", "sleep", "exit"]
DEATH_MENU = ["resurrect", "exit"]
SLEEP_MENU = ["wake", "exit"]


class GameController(Observer):

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
        self.shop_menu = [f"buy:{item_id}" for item_id in self.shop.items] + ["skins", "back"]
        self.skins_menu = [f"skin:{skin_id}" for skin_id in self.shop.skin_prices] + ["back"]
        self.death_menu = list(DEATH_MENU)
        self.sleep_menu = list(SLEEP_MENU)

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

        # Czy zwierzak żyje?
        self.model.add_observer(self)

    # Zmiana stanu zwierzaka
    def update(self, event_name, data=None):
        if event_name == "pet_died":
            self._open_menu(self.death_menu)
        elif event_name == "pet_resurrected":
            self._open_menu(self.main_menu)
        elif event_name == "action_sleep":
            self._open_menu(self.sleep_menu)
        elif event_name == "action_wake_up" and self.model.is_alive:
            self._open_menu(self.main_menu) 

    # Główna pętla
    def start(self):
        self.running = True
        self._show_menu()
        if self.ask_name_on_start:
            self._prompt_pet_name(is_resurrection=False)
        self._last_tick = time.monotonic()

    #Jeden tick czasu
    def step(self):
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
            # Zapis także przy ctrl+C
            self.finish()

    # Czas, który upłynął od poprzedniego wywoałania
    def _tick(self):
        now = time.monotonic()
        dt = now - self._last_tick
        self._last_tick = now
        self.model.pass_time(dt)
        return dt

    # Komendy
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
        if isinstance(idx, int) and 0 <= idx < len(self.menu) and idx != self.selected_idx:
            self.selected_idx = idx
            self._show_menu()

    def select_item(self, idx):
        if isinstance(idx, int) and 0 <= idx < len(self.menu):
            self.selected_idx = idx
            self._show_menu()
            self._execute(self.menu[self.selected_idx])

    def execute_action(self, action):
        if action == "exit":
            self.request_exit()
            return
        if action in self.menu:
            self.select_item(self.menu.index(action))

    def request_exit(self):
        if self.active_minigame is not None:
            self.finish_minigame_session(aborted=True)
        self.running = False

    # Helpery
    def _execute(self, action):
        if action == "exit":
            self.running = False
            return

        if action == "resurrect":
            self.model.resurrect()
            self._prompt_pet_name(is_resurrection=True)
            return
        # Martwy zwierzak
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
            if self.model.owns_skin(skin_id):
                self.model.equip_skin(skin_id)
            else:
                self.shop.buy_skin(skin_id)
        elif action == "play":
            if self.model.start_play():
                if self.event_driven:
                    self.start_minigame_session()
                else:
                    self._play_minigame()
        elif action == "sleep":
            self.model.start_sleep()
        elif action == "wake":
            self.model.wake_up()
        elif action.startswith("buy:"):
            self.shop.buy(action[len("buy:"):])

    def start_minigame_session(self):
        game = dino_game_module.DinoGame(
            track_width=self.track_width,
            high_score=self.model.high_score,
        )
        self.active_minigame = game
        self.view.start_minigame(game)
        self._tick()
        return game

    def handle_minigame_command(self, cmd):
        if self.active_minigame is None:
            return False
        if cmd in ("QUIT", "EXIT"):
            if cmd == "EXIT":
                self.running = False
            return False
        if cmd == "JUMP":
            self.active_minigame.jump()
        return True

    # Jeden tick minigry
    def step_minigame(self):
        game = self.active_minigame
        if game is None or game.is_game_over:
            return False
        dt = self._tick()
        if not self.model.is_alive:
            return False
        game.update(dt)
        self.view.draw_minigame(game)
        return not game.is_game_over

    def finish_minigame_session(self, aborted=False):
        game = self.active_minigame
        if game is None:
            return
        self.active_minigame = None

        self.model.record_minigame_result(game.score)

        if not aborted and game.is_game_over and self.model.is_alive:
            result = self.view.show_minigame_game_over(game)
            if result in ("EXIT", "QUIT"):
                self.running = False
            self._tick()

        self.view.end_minigame()
        self._show_menu()

    # Główna pętla gry
    def _play_minigame(self):
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
        ask = getattr(self.view, "ask_pet_name", None)
        if ask is None:
            return
        new_name = ask(self.model.name, is_resurrection=is_resurrection)
        if new_name and new_name.strip():
            self.model.rename(new_name)
        self._last_tick = time.monotonic()

    def _go_back(self):
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
