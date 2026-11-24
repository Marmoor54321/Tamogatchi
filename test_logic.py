# test_logic.py
# Uruchom:  python -m unittest test_logic.py
import json
import os
import tempfile
import unittest
from datetime import datetime, timedelta
from unittest import mock

from controller.game_controller import GameController
from model.pet import Pet


class FakeClock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now


class ScriptedView:
    """Atrapa widoku: podaje z góry ustalone komendy i przesuwa sztuczny zegar."""

    def __init__(self, clock, menu_commands, minigame_frames=0, seconds_per_frame=1.0, on_frame=None):
        self.clock = clock
        self.menu_commands = list(menu_commands)
        self.frames_left = minigame_frames
        self.seconds_per_frame = seconds_per_frame
        self.on_frame = on_frame
        self.game_over_shown = False

    def show_menu(self, items, selected_idx): pass
    def start_minigame(self, game): pass
    def draw_minigame(self, game): pass
    def end_minigame(self): pass

    def show_minigame_game_over(self, game):
        self.game_over_shown = True

    def get_command(self):
        return self.menu_commands.pop(0) if self.menu_commands else "CONFIRM"

    def get_minigame_command(self):
        if self.frames_left <= 0:
            return "QUIT"
        self.frames_left -= 1
        self.clock.now += self.seconds_per_frame
        if self.on_frame:
            self.on_frame()
        return None


class TempSaveMixin:
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.save_path = os.path.join(self._tmp.name, "save.json")

    def tearDown(self):
        self._tmp.cleanup()

    def new_pet(self):
        pet = Pet("Test")
        pet.save_file = self.save_path
        return pet


class OfflineTimeTest(unittest.TestCase):
    def test_one_long_step_equals_many_short_steps(self):
        once, steps = Pet(), Pet()
        once.pass_time(450)
        for _ in range(900):
            steps.pass_time(0.5)
        self.assertTrue(once.is_alive)
        self.assertAlmostEqual(once.health, steps.health, delta=0.6)
        self.assertAlmostEqual(once.hunger, steps.hunger, places=6)

    def test_health_drops_only_after_hunger_gets_low(self):
        pet = Pet()
        pet.pass_time(450)  # Głód spada poniżej 20 po 400 s -> 50 s utraty zdrowia
        self.assertAlmostEqual(pet.health, 50, places=6)

    def test_no_health_loss_while_stats_are_fine(self):
        pet = Pet()
        pet.pass_time(399)
        self.assertEqual(pet.health, 100)

    def test_long_absence_still_kills(self):
        pet = Pet()
        pet.pass_time(3600)
        self.assertFalse(pet.is_alive)


class GameClockTest(TempSaveMixin, unittest.TestCase):
    def _run_play_then_exit(self, pet, view):
        ctrl = GameController(pet, view)
        ctrl.selected_idx = ctrl.menu.index("play")
        ctrl.run()
        return ctrl

    def test_minigame_time_is_counted_once(self):
        clock = FakeClock()
        pet = self.new_pet()
        # CONFIRM na "Zabawa", potem przejście do "Wyjście" i CONFIRM
        view = ScriptedView(clock, ["CONFIRM", "NEXT", "NEXT", "CONFIRM"], minigame_frames=10)
        with mock.patch("time.monotonic", clock):
            self._run_play_then_exit(pet, view)
        # 10 s minigry * 0.2 głodu/s = 2, plus 15 za samą zabawę
        self.assertAlmostEqual(pet.hunger, 100 - 2 - 15, places=6)

    def test_pet_dying_during_minigame_ends_it_without_reward(self):
        clock = FakeClock()
        pet = self.new_pet()
        pet.health, pet.hunger = 1, 0   # Padnie po ~1 s głodowania
        pet.money = 0
        view = ScriptedView(clock, ["CONFIRM", "NEXT", "CONFIRM"], minigame_frames=50)
        with mock.patch("time.monotonic", clock):
            ctrl = self._run_play_then_exit(pet, view)
        self.assertFalse(pet.is_alive)
        self.assertEqual(pet.money, 0)
        self.assertGreater(view.frames_left, 40, "minigra powinna skończyć się zaraz po śmierci")
        self.assertFalse(view.game_over_shown)
        self.assertIs(ctrl.menu, ctrl.death_menu)


class SaveFileTest(TempSaveMixin, unittest.TestCase):
    def test_save_and_load_roundtrip(self):
        pet = self.new_pet()
        pet.money, pet.high_score, pet.hunger = 123, 7, 55.5
        pet.save_state()
        self.assertFalse(os.path.exists(self.save_path + ".tmp"))

        loaded = self.new_pet()
        self.assertTrue(loaded.load_state())
        self.assertEqual((loaded.money, loaded.high_score), (123, 7))
        self.assertAlmostEqual(loaded.hunger, 55.5, delta=0.1)

    def test_corrupted_save_starts_fresh_and_is_kept_aside(self):
        with open(self.save_path, "w") as f:
            f.write('{"name": "Reksio", "money": 2')   # Ucięty w połowie zapis
        pet = self.new_pet()
        self.assertFalse(pet.load_state())
        self.assertEqual(pet.money, 0)
        self.assertTrue(pet.is_alive)
        self.assertTrue(os.path.exists(self.save_path + ".bad"))

    def test_wrong_types_do_not_crash(self):
        with open(self.save_path, "w") as f:
            json.dump({"money": "duzo", "last_update": "wczoraj"}, f)
        pet = self.new_pet()
        self.assertFalse(pet.load_state())
        self.assertEqual(pet.money, 0)

    def test_failed_write_keeps_old_save(self):
        pet = self.new_pet()
        pet.money = 50
        pet.save_state()
        pet.money = 999
        with mock.patch("json.dump", side_effect=OSError("dysk pelny")):
            with self.assertRaises(OSError):
                pet.save_state()
        loaded = self.new_pet()
        loaded.load_state()
        self.assertEqual(loaded.money, 50)

    def test_offline_progress_after_load(self):
        pet = self.new_pet()
        pet.last_update = datetime.now() - timedelta(seconds=100)
        pet.save_state()
        loaded = self.new_pet()
        loaded.load_state()
        self.assertAlmostEqual(loaded.hunger, 80, delta=0.5)


if __name__ == "__main__":
    unittest.main()
