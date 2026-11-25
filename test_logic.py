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

    def test_stats_stop_at_the_moment_of_death(self):
        once, steps = Pet(), Pet()
        for pet in (once, steps):
            pet.hunger, pet.health = 10, 5    # umiera po 5 s głodu
        once.pass_time(100)
        for _ in range(200):
            steps.pass_time(0.5)
        self.assertFalse(once.is_alive)
        self.assertAlmostEqual(once.energy, steps.energy, delta=0.2)
        self.assertAlmostEqual(once.energy, 100 - 5 * Pet.ENERGY_DROP_PER_SEC, delta=0.01)

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


class PlayEnergyTest(TempSaveMixin, unittest.TestCase):
    """Zmęczony zwierzak (energia < MIN_ENERGY_TO_PLAY) nie może się bawić."""

    def test_can_play_threshold(self):
        pet = Pet()
        pet.energy = Pet.MIN_ENERGY_TO_PLAY
        self.assertTrue(pet.can_play())
        pet.energy = Pet.MIN_ENERGY_TO_PLAY - 0.1
        self.assertFalse(pet.can_play())

    def test_tired_pet_refuses_and_minigame_does_not_start(self):
        clock = FakeClock()
        pet = self.new_pet()
        pet.energy, pet.money = 10, 0
        events = []
        pet.add_observer(type("Spy", (), {"update": lambda self, e, d=None: events.append(e)})())
        started = []
        view = ScriptedView(clock, ["CONFIRM", "NEXT", "NEXT", "CONFIRM"], minigame_frames=5)
        view.start_minigame = lambda game: started.append(game)
        with mock.patch("time.monotonic", clock):
            ctrl = GameController(pet, view)
            ctrl.selected_idx = ctrl.menu.index("play")
            ctrl.run()
        self.assertEqual(started, [])
        self.assertIn("action_play_refused", events)
        self.assertNotIn("action_play", events)
        self.assertEqual(pet.money, 0)

    def test_rested_pet_can_play(self):
        clock = FakeClock()
        pet = self.new_pet()
        started = []
        view = ScriptedView(clock, ["CONFIRM", "NEXT", "NEXT", "CONFIRM"], minigame_frames=1)
        view.start_minigame = lambda game: started.append(game)
        with mock.patch("time.monotonic", clock):
            ctrl = GameController(pet, view)
            ctrl.selected_idx = ctrl.menu.index("play")
            ctrl.run()
        self.assertEqual(len(started), 1)

    def test_menu_marks_play_unavailable_and_explains_why(self):
        from model.shop import Shop
        from view.console.layout import MESSAGE_BOX
        from view.console.menu_panel import MenuPanel
        pet = Pet()
        menu = MenuPanel(canvas=None, pet=pet, shop=Shop(pet))
        menu.set_items(["play"], 0)
        self.assertTrue(menu.is_available("play"))
        self.assertIsNone(menu.describe_hovered())

        pet.energy = 5
        self.assertFalse(menu.is_available("play"))
        text, style = menu.describe_hovered()
        self.assertIn("energii", text)
        self.assertEqual(style, "warn")
        self.assertLessEqual(len(text), MESSAGE_BOX[3] - 6)


class SleepTest(TempSaveMixin, unittest.TestCase):
    """Sen to stan: +1 energii co 2 s, pobudka sama przy 100% albo ręcznie."""

    def setUp(self):
        super().setUp()
        self.pet = self.new_pet()
        self.events = []
        self.pet.add_observer(type("Spy", (), {"update": lambda _, e, d=None: self.events.append((e, d))})())

    def test_sleep_does_not_restore_energy_instantly(self):
        self.pet.energy = 40
        self.assertTrue(self.pet.start_sleep())
        self.assertEqual(self.pet.energy, 40)
        self.assertTrue(self.pet.is_sleeping)
        self.assertEqual(self.pet.mood, "asleep")

    def test_two_seconds_of_sleep_give_one_point(self):
        self.pet.energy = 40
        self.pet.start_sleep()
        self.pet.pass_time(2)
        self.assertAlmostEqual(self.pet.energy, 41)
        for _ in range(20):
            self.pet.pass_time(0.5)
        self.assertAlmostEqual(self.pet.energy, 46)

    def test_hunger_still_drops_while_sleeping(self):
        self.pet.energy, self.pet.hunger = 40, 80
        self.pet.start_sleep()
        self.pet.pass_time(10)
        self.assertAlmostEqual(self.pet.hunger, 78)

    def test_wakes_up_by_itself_when_rested(self):
        self.pet.energy = 90
        self.pet.start_sleep()
        self.pet.pass_time(30)   # 20 s snu do 100%, potem 10 s czuwania
        self.assertFalse(self.pet.is_sleeping)
        self.assertAlmostEqual(self.pet.energy, 100 - 10 * Pet.ENERGY_DROP_PER_SEC)
        self.assertIn(("action_wake_up", {"rested": True}), self.events)

    def test_manual_wake_up_keeps_gained_energy(self):
        self.pet.energy = 40
        self.pet.start_sleep()
        self.pet.pass_time(20)
        self.assertTrue(self.pet.wake_up())
        self.assertFalse(self.pet.is_sleeping)
        self.assertAlmostEqual(self.pet.energy, 50)
        self.assertIn(("action_wake_up", {"rested": False}), self.events)

    def test_rested_pet_refuses_to_sleep(self):
        self.assertFalse(self.pet.start_sleep())
        self.assertIn(("action_sleep_refused", None), self.events)

    def test_cannot_play_while_sleeping(self):
        self.pet.energy = 90
        self.pet.start_sleep()
        self.assertFalse(self.pet.can_play())

    def test_long_step_equals_short_steps_with_waking_in_between(self):
        a, b = self.new_pet(), self.new_pet()
        for pet in (a, b):
            pet.energy, pet.hunger = 10, 30   # zmęczony i prawie głodny
            pet.start_sleep()
        a.pass_time(400)
        for _ in range(800):
            b.pass_time(0.5)
        self.assertEqual(a.is_sleeping, b.is_sleeping)
        for stat in ("energy", "hunger", "happiness", "health"):
            self.assertAlmostEqual(getattr(a, stat), getattr(b, stat), delta=0.6, msg=stat)

    def test_sleeping_survives_save_and_continues_offline(self):
        self.pet.energy = 40
        self.pet.start_sleep()
        self.pet.last_update = datetime.now() - timedelta(seconds=40)
        self.pet.save_state()
        loaded = self.new_pet()
        loaded.load_state()
        self.assertTrue(loaded.is_sleeping)
        self.assertAlmostEqual(loaded.energy, 60, delta=0.5)   # 40 s snu = +20

    def test_controller_switches_menus(self):
        from controller.game_controller import GameController
        view = ScriptedView(FakeClock(), [])
        ctrl = GameController(self.pet, view)
        self.pet.energy = 98
        ctrl.selected_idx = ctrl.menu.index("sleep")
        ctrl.handle_command("CONFIRM")
        self.assertIs(ctrl.menu, ctrl.sleep_menu)
        self.pet.pass_time(10)            # wysypia się po 4 s
        self.assertIs(ctrl.menu, ctrl.main_menu)

        self.pet.energy = 50
        ctrl.selected_idx = ctrl.menu.index("sleep")
        ctrl.handle_command("CONFIRM")
        ctrl.selected_idx = ctrl.menu.index("wake")
        ctrl.handle_command("CONFIRM")
        self.assertIs(ctrl.menu, ctrl.main_menu)

    def test_loaded_sleeping_pet_opens_sleep_menu(self):
        from controller.game_controller import GameController
        self.pet.energy = 10
        self.pet.start_sleep()
        ctrl = GameController(self.pet, ScriptedView(FakeClock(), []))
        self.assertIs(ctrl.menu, ctrl.sleep_menu)


if __name__ == "__main__":
    unittest.main()
