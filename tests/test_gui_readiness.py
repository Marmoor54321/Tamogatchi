# test_gui_readiness.py
"""Testy przygotowania architektury pod GUI: obsługa akcji bezpośrednich/myszy,
pętli zdarzeniowej oraz inteligentnego odświeżania widoku."""
import os
import tempfile
import unittest
from unittest import mock

from controller.game_controller import GameController
from model.observer import Observer
from model.pet import Pet
from model.shop import Item, Shop
from view.base import GameView
from view.common import action_label, describe_action, is_action_available, message_for
from view.console_view import ConsoleView


class FakeClock:
    def __init__(self):
        self.now = 100.0

    def __call__(self):
        return self.now


class EventSpy(Observer):
    def __init__(self):
        self.events = []

    def update(self, event_name, data=None):
        self.events.append((event_name, data))


class GuiStubView(GameView):
    """Atrapa widoku zgodna z GameView (napędzana zdarzeniami z zewnątrz)."""

    def __init__(self):
        self.menus = []
        self.rendered_dts = []
        self.minigame_started = False
        self.minigame_ended = False
        self.drawn_games = 0
        self.game_over_count = 0

    def show_menu(self, items, selected_idx):
        self.menus.append((list(items), selected_idx))

    def render(self, dt=0.0):
        self.rendered_dts.append(dt)

    def start_minigame(self, game):
        self.minigame_started = True

    def draw_minigame(self, game):
        self.drawn_games += 1

    def show_minigame_game_over(self, game):
        self.game_over_count += 1

    def end_minigame(self):
        self.minigame_ended = True

    def update(self, event_name, data=None):
        pass


class MockStdscr:
    def timeout(self, ms): pass
    def getmaxyx(self): return 25, 80
    def erase(self): pass
    def refresh(self): pass
    def addstr(self, *args): pass
    def addch(self, *args): pass
    def hline(self, *args): pass
    def vline(self, *args): pass


class MouseAndExitControllerTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.pet = Pet("Reksio")
        self.pet.save_file = os.path.join(self._tmp.name, "save.json")
        self.view = GuiStubView()
        self.ctrl = GameController(self.pet, self.view, event_driven=True)

    def tearDown(self):
        self._tmp.cleanup()

    def test_hover_and_select_index_without_cursor_stepping(self):
        self.ctrl.start()
        self.ctrl.handle_command(("HOVER", 2))
        self.assertEqual(self.ctrl.selected_idx, 2)
        self.assertFalse(self.pet.is_sleeping)

        # Kliknięcie "shop" (indeks 0) wchodzi bezpośrednio do sklepu
        self.ctrl.handle_command(("SELECT", 0))
        self.assertIs(self.ctrl.menu, self.ctrl.shop_menu)
        self.assertEqual(self.ctrl.selected_idx, 0)

    def test_execute_action_and_exit_from_nested_menu(self):
        self.ctrl.start()
        self.pet.money = 100
        self.pet.hunger = 50
        self.ctrl.handle_command(("EXECUTE", "shop"))
        self.assertIs(self.ctrl.menu, self.ctrl.shop_menu)

        self.ctrl.handle_command(("EXECUTE", "buy:jablko"))
        self.assertEqual(self.pet.money, 90)
        self.assertEqual(self.pet.hunger, 70)

        # Wyjście z aplikacji działa nawet z zagnieżdżonego menu sklepu/skórek
        self.ctrl.handle_command(("EXECUTE", "skins"))
        self.assertIs(self.ctrl.menu, self.ctrl.skins_menu)
        self.ctrl.handle_command("EXIT")
        self.assertFalse(self.ctrl.running)


class EventDrivenLoopTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.pet = Pet("Reksio")
        self.pet.save_file = os.path.join(self._tmp.name, "save.json")

    def tearDown(self):
        self._tmp.cleanup()

    def test_step_drives_menu_render_and_nonblocking_minigame(self):
        clock = FakeClock()
        view = GuiStubView()
        ctrl = GameController(self.pet, view, event_driven=True)

        with mock.patch("time.monotonic", clock):
            ctrl.start()
            clock.now += 0.05
            self.assertTrue(ctrl.step())
            self.assertEqual(len(view.rendered_dts), 1)
            self.assertAlmostEqual(view.rendered_dts[0], 0.05, places=6)

            # Start minigry nie blokuje - aktywuje sesję sterowaną przez step()
            ctrl.execute_action("play")
            self.assertTrue(view.minigame_started)
            self.assertIsNotNone(ctrl.active_minigame)

            ctrl.handle_minigame_command("JUMP")
            clock.now += 0.1
            ctrl.step()
            self.assertEqual(view.drawn_games, 1)
            self.assertGreater(ctrl.active_minigame.player_y, 0.0)

            # Zamknięcie z zewnątrz w trakcie minigry sprząta sesję i kończy grę
            ctrl.request_exit()
            self.assertFalse(ctrl.running)
            self.assertIsNone(ctrl.active_minigame)
            self.assertTrue(view.minigame_ended)
            ctrl.finish()


class SmartObserverDiffTest(unittest.TestCase):
    def test_feed_and_minigame_emit_single_stats_changed_with_diff(self):
        pet = Pet("Reksio")
        pet.hunger = 50
        pet.energy = 50
        spy = EventSpy()
        pet.add_observer(spy)

        pet.feed()
        stats_events = [d for e, d in spy.events if e == "stats_changed"]
        self.assertEqual(len(stats_events), 1)
        self.assertTrue({"hunger", "energy"}.issubset(stats_events[0]["fields"]))

        spy.events.clear()
        pet.happiness = 50
        pet.record_minigame_result(score=2)
        stats_events = [d for e, d in spy.events if e == "stats_changed"]
        self.assertEqual(len(stats_events), 1)
        self.assertTrue({"money", "high_score", "happiness", "energy", "hunger"}.issubset(stats_events[0]["fields"]))

    def test_console_view_skips_redraw_when_rounded_stats_unchanged(self):
        pet = Pet("Reksio")
        view = ConsoleView(MockStdscr(), pet)

        calls = {"stats": 0, "pet": 0, "menu": 0}
        view.stats.redraw = lambda: calls.__setitem__("stats", calls["stats"] + 1)
        view.pet_panel.redraw = lambda: calls.__setitem__("pet", calls["pet"] + 1)
        view.menu.redraw = lambda: calls.__setitem__("menu", calls["menu"] + 1)

        # Bardzo mały krok czasowy nie zmienia zaokrąglonych wartości
        pet.pass_time(0.01)
        self.assertEqual(calls, {"stats": 0, "pet": 0, "menu": 0})

        # Zmiana samego głodu odświeża tylko panel statystyk (nie menu ani zwierzaka)
        pet.pass_time(5.0)
        self.assertEqual(calls["stats"], 1)
        self.assertEqual(calls["pet"], 0)
        self.assertEqual(calls["menu"], 0)


class CommonViewHelpersTest(unittest.TestCase):
    def test_common_helpers_work_without_curses(self):
        pet = Pet("Reksio")
        custom_item = Item("Napoj", 15, {"energy": 25})
        shop = Shop(pet, items={"napoj": custom_item})

        self.assertEqual(action_label("buy:napoj", pet, shop), "Napoj(15$)")
        self.assertFalse(is_action_available("buy:napoj", pet, shop))
        text, style = describe_action("buy:napoj", pet, shop)
        self.assertIn("Energia +25", text)
        self.assertEqual(style, "warn")

        msg, msg_style = message_for("action_buy_success", "napoj", shop=shop)
        self.assertIn("Napoj", msg)
        self.assertEqual(msg_style, "good")


if __name__ == "__main__":
    unittest.main()
