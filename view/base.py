# view/base.py
"""Kontrakt pomiędzy GameController a warstwą widoku (tekstową lub graficzną)."""
from model.observer import Observer


class GameView(Observer):
    """Bazowy interfejs widoku dla kontrolera gry.

    Widok może działać na dwa sposoby:
    1. Pętla napędzana przez `GameController.run()` (np. ConsoleView / Pygame):
       kontroler pobiera komendy z `get_command()` i `get_minigame_command()`.
    2. Pętla zdarzeń po stronie GUI (np. Tkinter / PyQt):
       widok wywołuje `controller.start()`, a następnie okresowo `controller.step(dt)`
       oraz `controller.handle_command(...)` / `controller.select_item(...)` /
       `controller.execute_action(...)` w reakcji na mysz i klawiaturę.
    """

    def show_menu(self, items, selected_idx):
        raise NotImplementedError

    def get_command(self):
        return None

    def render(self, dt=0.0):
        """Opcjonalny krok renderowania/animacji dla widoków z własną klatką."""
        pass

    def ask_pet_name(self, current_name, is_resurrection=False):
        return None

    def start_minigame(self, game):
        raise NotImplementedError

    def get_minigame_command(self):
        return None

    def draw_minigame(self, game):
        raise NotImplementedError

    def show_minigame_game_over(self, game):
        pass

    def end_minigame(self):
        raise NotImplementedError
