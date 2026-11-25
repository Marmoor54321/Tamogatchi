# test_naming.py
# Uruchom:  python -m unittest test_naming.py
import curses
import os
import tempfile
import unittest
from unittest import mock

import main
from controller.game_controller import GameController
from model.observer import Observer
from model.pet import Pet
from view.console.keys import RESIZE
from view.console_view import ConsoleView


class FakeClock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now


class EventSpy(Observer):
    def __init__(self):
        self.events = []

    def update(self, event_name, data=None):
        self.events.append((event_name, data))


class NamingView:
    def __init__(self, commands, prompted_names=None, clock=None, prompt_delay=0.0):
        self.commands = list(commands)
        self.prompted_names = list(prompted_names or [])
        self.prompts = []
        self.clock = clock
        self.prompt_delay = prompt_delay

    def show_menu(self, items, selected_idx):
        pass

    def get_command(self):
        return self.commands.pop(0) if self.commands else "CONFIRM"

    def ask_pet_name(self, current_name, is_resurrection=False):
        self.prompts.append((current_name, is_resurrection))
        if self.clock is not None:
            self.clock.now += self.prompt_delay
        return self.prompted_names.pop(0) if self.prompted_names else None


class MockStdscr:
    def __init__(self, keys=()):
        self.keys = list(keys)
        self.timeouts = []
        self.drawn_texts = []

    def timeout(self, ms):
        self.timeouts.append(ms)

    def getmaxyx(self):
        return 25, 80

    def erase(self):
        pass

    def refresh(self):
        pass

    def addstr(self, y, x, text, *args):
        self.drawn_texts.append((y, x, text))

    def addch(self, *args):
        pass

    def hline(self, *args):
        pass

    def vline(self, *args):
        pass

    def get_wch(self):
        if not self.keys:
            return "\n"
        return self.keys.pop(0)


class PetRenameTest(unittest.TestCase):
    def test_rename_updates_name_and_notifies(self):
        pet = Pet("Reksio")
        spy = EventSpy()
        pet.add_observer(spy)

        self.assertTrue(pet.rename("  Burek   II  "))
        self.assertEqual(pet.name, "Burek II")
        self.assertIn(("pet_renamed", "Burek II"), spy.events)

    def test_rename_ignores_blank_and_truncates_long_names(self):
        pet = Pet("Reksio")
        spy = EventSpy()
        pet.add_observer(spy)

        self.assertFalse(pet.rename("   "))
        self.assertEqual(pet.name, "Reksio")
        self.assertEqual(spy.events, [])

        long_name = "A" * 50
        self.assertTrue(pet.rename(long_name))
        self.assertEqual(len(pet.name), Pet.MAX_NAME_LENGTH)


class ControllerNamingFlowTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.save_path = os.path.join(self._tmp.name, "save.json")

    def tearDown(self):
        self._tmp.cleanup()

    def _new_pet(self, name="Reksio"):
        pet = Pet(name)
        pet.save_file = self.save_path
        return pet

    def test_first_launch_prompts_for_name_and_saves_it(self):
        clock = FakeClock()
        pet = self._new_pet("Reksio")
        # Menu główne: Wyjście to ostatnia pozycja (indeks 3)
        view = NamingView(
            commands=["PREV", "CONFIRM"],
            prompted_names=["Pimpek"],
            clock=clock,
            prompt_delay=20.0,
        )
        with mock.patch("time.monotonic", clock):
            ctrl = GameController(pet, view, ask_name_on_start=True)
            ctrl.run()

        self.assertEqual(view.prompts, [("Reksio", False)])
        self.assertEqual(pet.name, "Pimpek")
        # Czas spędzony na wpisywaniu imienia nie obniża statystyk
        self.assertEqual(pet.hunger, 100)

        loaded = self._new_pet("Inny")
        self.assertTrue(loaded.load_state())
        self.assertEqual(loaded.name, "Pimpek")

    def test_first_launch_escape_keeps_default_name(self):
        pet = self._new_pet("Reksio")
        view = NamingView(commands=["PREV", "CONFIRM"], prompted_names=[None])
        ctrl = GameController(pet, view, ask_name_on_start=True)
        ctrl.run()

        self.assertEqual(view.prompts, [("Reksio", False)])
        self.assertEqual(pet.name, "Reksio")

    def test_loaded_game_does_not_prompt_on_start(self):
        pet = self._new_pet("Reksio")
        view = NamingView(commands=["PREV", "CONFIRM"])
        ctrl = GameController(pet, view, ask_name_on_start=False)
        ctrl.run()
        self.assertEqual(view.prompts, [])

    def test_resurrection_prompts_for_name_and_resets_tick_timer(self):
        clock = FakeClock()
        pet = self._new_pet("Reksio")
        pet.is_alive = False
        pet.health = 0

        # W death_menu: 0="resurrect", po odrodzeniu w main_menu: PREV->3="exit"
        view = NamingView(
            commands=["CONFIRM", "PREV", "CONFIRM"],
            prompted_names=["Reksio II"],
            clock=clock,
            prompt_delay=30.0,
        )
        with mock.patch("time.monotonic", clock):
            ctrl = GameController(pet, view, ask_name_on_start=False)
            ctrl.run()

        self.assertEqual(view.prompts, [("Reksio", True)])
        self.assertTrue(pet.is_alive)
        self.assertEqual(pet.name, "Reksio II")
        self.assertEqual(pet.hunger, 100)
        self.assertIs(ctrl.menu, ctrl.main_menu)

    def test_main_passes_ask_name_on_start_only_when_no_save(self):
        with mock.patch("main.Pet") as mock_pet_cls, \
             mock.patch("main.Shop"), \
             mock.patch("main.ConsoleView"), \
             mock.patch("main.GameController") as mock_ctrl_cls:
            mock_pet = mock_pet_cls.return_value
            mock_pet.load_state.return_value = False
            main.main_app(MockStdscr())
            self.assertTrue(mock_ctrl_cls.call_args.kwargs["ask_name_on_start"])

            mock_pet.load_state.return_value = True
            main.main_app(MockStdscr())
            self.assertFalse(mock_ctrl_cls.call_args.kwargs["ask_name_on_start"])


class ConsoleNameDialogTest(unittest.TestCase):
    def test_typing_backspace_polish_chars_and_confirm(self):
        pet = Pet("Reksio")
        stdscr = MockStdscr(["A", "z", "o", "x", curses.KEY_BACKSPACE, "r", "ą", "\n"])
        view = ConsoleView(stdscr, pet, tick_ms=500)

        result = view.ask_pet_name(pet.name, is_resurrection=False)
        self.assertEqual(result, "Azorą")
        self.assertEqual(stdscr.timeouts[-2:], [-1, 500])

    def test_escape_returns_none_and_resize_redraws(self):
        pet = Pet("Reksio")
        stdscr = MockStdscr(["B", curses.KEY_RESIZE, "\x1b"])
        view = ConsoleView(stdscr, pet, tick_ms=500)

        with mock.patch.object(view, "full_redraw", wraps=view.full_redraw) as redraw_spy:
            result = view.ask_pet_name(pet.name, is_resurrection=True)

        self.assertIsNone(result)
        # Raz przy otwarciu, raz na RESIZE, raz w finally przy zamknięciu
        self.assertEqual(redraw_spy.call_count, 3)

    def test_pet_panel_updates_frame_title_after_rename(self):
        pet = Pet("Reksio")
        stdscr = MockStdscr()
        view = ConsoleView(stdscr, pet)
        stdscr.drawn_texts.clear()

        pet.rename("Burek")

        titles = [text for _, _, text in stdscr.drawn_texts if "Burek" in text]
        self.assertTrue(titles, "Ramka panelu zwierzaka powinna pokazywac nowe imie")


if __name__ == "__main__":
    unittest.main()
