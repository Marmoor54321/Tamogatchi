# test_skins.py
# Uruchom:  python -m unittest test_skins.py
import os
import tempfile
import unittest

from controller.game_controller import GameController
from model.observer import Observer
from model.pet import Pet
from model.shop import Shop
from model.skins import DEFAULT_SKIN, SKIN_PRICES


class EventSpy(Observer):
    def __init__(self):
        self.events = []

    def update(self, event_name, data=None):
        self.events.append((event_name, data))


class FakeView:
    """Atrapa widoku - kontroler nie potrzebuje curses."""
    def show_menu(self, items, selected_idx):
        self.items, self.selected_idx = items, selected_idx


class SkinModelTest(unittest.TestCase):
    def setUp(self):
        self.pet = Pet("Test")
        self.shop = Shop(self.pet)
        self.spy = EventSpy()
        self.pet.add_observer(self.spy)

    def test_starts_with_free_default_skin(self):
        self.assertEqual(self.pet.active_skin, DEFAULT_SKIN)
        self.assertTrue(self.pet.owns_skin(DEFAULT_SKIN))
        self.assertEqual(SKIN_PRICES[DEFAULT_SKIN], 0)

    def test_buy_takes_money_and_equips(self):
        self.pet.money = 150
        self.assertTrue(self.shop.buy_skin("kotek"))
        self.assertEqual(self.pet.money, 150 - SKIN_PRICES["kotek"])
        self.assertTrue(self.pet.owns_skin("kotek"))
        self.assertEqual(self.pet.active_skin, "kotek")
        self.assertIn(("action_skin_bought", "kotek"), self.spy.events)

    def test_cannot_buy_without_money(self):
        self.pet.money = 10
        self.assertFalse(self.shop.buy_skin("robot"))
        self.assertEqual(self.pet.money, 10)
        self.assertFalse(self.pet.owns_skin("robot"))
        self.assertIn(("action_skin_buy_fail", "robot"), self.spy.events)

    def test_owned_skin_is_not_paid_twice(self):
        self.pet.money = 100
        self.shop.buy_skin("kotek")
        self.pet.equip_skin(DEFAULT_SKIN)
        self.shop.buy_skin("kotek")
        self.assertEqual(self.pet.money, 0)
        self.assertEqual(self.pet.active_skin, "kotek")

    def test_cannot_equip_unowned_or_unknown(self):
        self.assertFalse(self.pet.equip_skin("robot"))
        self.assertFalse(self.shop.buy_skin("nie_ma_takiej"))
        self.assertEqual(self.pet.active_skin, DEFAULT_SKIN)

    def test_mood(self):
        self.assertEqual(self.pet.mood, "happy")
        self.pet.happiness = 10
        self.assertEqual(self.pet.mood, "sad")
        self.pet.energy = 10
        self.assertEqual(self.pet.mood, "sleepy")
        self.pet.is_alive = False
        self.assertEqual(self.pet.mood, "dead")

    def test_skins_survive_save_and_load(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "save.json")
            self.pet.save_file = path
            self.pet.money = 500
            self.shop.buy_skin("krolik")
            self.pet.save_state()

            loaded = Pet("Test")
            loaded.save_file = path
            loaded.load_state()
            self.assertTrue(loaded.owns_skin("krolik"))
            self.assertEqual(loaded.active_skin, "krolik")

    def test_old_save_without_skins_loads(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "save.json")
            with open(path, "w") as f:
                f.write('{"name": "Stary", "money": 5, "active_skin": "usunieta"}')
            pet = Pet()
            pet.save_file = path
            pet.load_state()
            self.assertEqual(pet.active_skin, DEFAULT_SKIN)
            self.assertEqual(pet.owned_skins, {DEFAULT_SKIN})


class SkinControllerTest(unittest.TestCase):
    def setUp(self):
        self.pet = Pet("Test")
        self.view = FakeView()
        self.ctrl = GameController(self.pet, self.view)

    def _select(self, action):
        self.ctrl.selected_idx = self.ctrl.menu.index(action)
        self.ctrl.handle_command("CONFIRM")

    def test_navigate_shop_to_skins_and_back(self):
        self._select("shop")
        self._select("skins")
        self.assertIs(self.ctrl.menu, self.ctrl.skins_menu)
        self.ctrl.handle_command("BACK")
        self.assertIs(self.ctrl.menu, self.ctrl.shop_menu)
        self.ctrl.handle_command("BACK")
        self.assertIs(self.ctrl.menu, self.ctrl.main_menu)

    def test_confirm_buys_then_equips(self):
        self.pet.money = 100
        self._select("shop")
        self._select("skins")
        self._select("skin:kotek")
        self.assertEqual(self.pet.active_skin, "kotek")
        self._select(f"skin:{DEFAULT_SKIN}")
        self.assertEqual(self.pet.active_skin, DEFAULT_SKIN)
        self.assertEqual(self.pet.money, 0)


class MinigameSkinTest(unittest.TestCase):
    def test_every_skin_has_all_player_frames(self):
        from model.dino_game import DinoGame, PropType
        from view.minigame_props import get_player_prop
        frames = [PropType.PLAYER_RUN_1, PropType.PLAYER_RUN_2, PropType.PLAYER_JUMP, PropType.PLAYER_CRASH]
        game = DinoGame()
        for skin_id in SKIN_PRICES:
            for frame in frames:
                prop = get_player_prop(skin_id, frame)
                self.assertIsNotNone(prop, (skin_id, frame))
                # Widoczne znaki muszą mieścić się w hitboxie - inaczej przeszkoda
                # wchodziłaby w rysunek bez kolizji
                visible_cols = [i for line in prop.lines for i, ch in enumerate(line) if ch != " "]
                self.assertLessEqual(prop.height, game.player_height, (skin_id, frame))
                self.assertLess(max(visible_cols), game.player_width, (skin_id, frame))


if __name__ == "__main__":
    unittest.main()
