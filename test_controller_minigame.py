# test_controller_minigame.py
"""Test integracji GameController z minigrą Dino i modelem Pet (symulacja widoku)."""
import unittest
from model.pet import Pet
from controller.game_controller import GameController


class MockView:
    def __init__(self):
        self.menu_shown = None
        self.selected_idx = None
        self.commands = []
        self.minigame_commands = []
        self.rendered_frames = 0
        self.minigame_started = False
        self.minigame_ended = False
        self.game_over_shown = False

    def get_command(self):
        if self.commands:
            return self.commands.pop(0)
        return None

    def show_menu(self, items, selected_idx):
        self.menu_shown = list(items)
        self.selected_idx = selected_idx

    def start_minigame(self, game):
        self.minigame_started = True

    def get_minigame_command(self):
        if self.minigame_commands:
            return self.minigame_commands.pop(0)
        return None

    def draw_minigame(self, game):
        self.rendered_frames += 1

    def show_minigame_game_over(self, game):
        self.game_over_shown = True

    def end_minigame(self):
        self.minigame_ended = True


class TestGameControllerMinigame(unittest.TestCase):

    def test_play_action_triggers_minigame_and_rewards(self):
        pet = Pet("Reksio")
        pet.money = 0
        pet.high_score = 0
        view = MockView()
        controller = GameController(pet, view)

        # Gracz wybiera "play" (indeks 1), uruchamia minigrę, a potem przechodzi do "exit" (indeks 3)
        view.commands = ["NEXT", "CONFIRM", "NEXT", "NEXT", "CONFIRM"]
        # W minigrze: najpierw skok, potem wyjście
        view.minigame_commands = ["JUMP", "QUIT"]

        controller.run()

        self.assertTrue(view.minigame_started)
        self.assertTrue(view.minigame_ended)
        # Gra powraca do menu głównego
        self.assertEqual(controller.menu, controller.main_menu)

    def test_play_minigame_crash_rewards_money(self):
        pet = Pet("Reksio")
        pet.money = 10
        pet.high_score = 1
        view = MockView()
        controller = GameController(pet, view)

        # Uruchomienie minigry przez _play_minigame
        # Symulujemy minigrę z bezpośrednim uderzeniem lub ukończeniem
        from model.dino_game import DinoGame
        # Podmieniamy chwilowo _play_minigame by przetestować nagrodę
        original_dino = DinoGame

        class CustomDinoGame(DinoGame):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.score = 5  # Gracz przeskoczył 5 przeszkód
                self.is_game_over = True  # Zakończyło się kolizją

        import model.dino_game
        model.dino_game.DinoGame = CustomDinoGame
        try:
            controller._play_minigame()
        finally:
            model.dino_game.DinoGame = original_dino

        self.assertTrue(view.game_over_shown)
        # 5 przeszkód * 10$ = 50$, plus początkowe 10$ = 60$
        self.assertEqual(pet.money, 60)
        # Rekord zaktualizowany z 1 na 5
        self.assertEqual(pet.high_score, 5)

    def test_console_view_suppresses_stats_redraw_during_minigame(self):
        """Upewnia się, że ConsoleView nie przerysowuje widoku głównego (draw_stats) podczas trwania minigry."""
        from view.console_view import ConsoleView
        pet = Pet("Reksio")

        # Tworzymy atrapę curses stdscr
        class MockStdscr:
            def timeout(self, ms): pass
            def getmaxyx(self): return 25, 80
            def erase(self): pass
            def refresh(self): pass
            def addstr(self, *args): pass
            def addch(self, *args): pass
            def hline(self, *args): pass
            def vline(self, *args): pass

        stdscr = MockStdscr()
        view = ConsoleView(stdscr, pet)

        # Rozpoczynamy minigrę
        from model.dino_game import DinoGame
        game = DinoGame()
        view.start_minigame(game)
        self.assertTrue(view.in_minigame)

        # Symulujemy zdarzenie stats_changed (np. pass_time zwierzaka)
        stats_drawn = [False]
        view.draw_stats = lambda: stats_drawn.__setitem__(0, True)

        view.update("stats_changed")
        self.assertFalse(stats_drawn[0], "draw_stats NIE może być wywoływany w trakcie minigry!")

        # Po zakończeniu minigry
        view.end_minigame()
        self.assertFalse(view.in_minigame)
        view.update("stats_changed")
        self.assertTrue(stats_drawn[0], "draw_stats powinien działać normalnie po wyjściu z minigry!")


if __name__ == "__main__":
    unittest.main()
