# test_shop.py
# Uruchom:  python -m unittest test_shop.py
import unittest

from controller.game_controller import GameController
from model.observer import Observer
from model.pet import Pet
from model.shop import SHOP_ITEMS, Item, Shop


class EventSpy(Observer):
    def __init__(self):
        self.events = []

    def update(self, event_name, data=None):
        self.events.append((event_name, data))


class FakeView:
    def show_menu(self, items, selected_idx):
        self.items = items


class ShopTest(unittest.TestCase):
    def setUp(self):
        self.pet = Pet("Test")
        self.spy = EventSpy()
        self.pet.add_observer(self.spy)

    def test_buy_takes_money_and_applies_effects(self):
        shop = Shop(self.pet)
        self.pet.money, self.pet.hunger, self.pet.energy = 30, 50, 50
        self.assertTrue(shop.buy("jablko"))
        self.assertEqual(self.pet.money, 20)
        self.assertEqual((self.pet.hunger, self.pet.energy), (70, 55))
        self.assertIn(("action_buy_success", "jablko"), self.spy.events)

    def test_buy_without_money_changes_nothing(self):
        shop = Shop(self.pet)
        self.pet.money, self.pet.hunger = 5, 50
        self.assertFalse(shop.buy("burger"))
        self.assertEqual((self.pet.money, self.pet.hunger), (5, 50))
        self.assertIn(("action_buy_fail", "burger"), self.spy.events)

    def test_unknown_item_and_dead_pet(self):
        shop = Shop(self.pet)
        self.pet.money = 100
        self.assertFalse(shop.buy("nie_ma"))
        self.pet.is_alive = False
        self.assertFalse(shop.buy("jablko"))
        self.assertEqual(self.pet.money, 100)

    def test_effects_are_clamped_and_sent_once(self):
        shop = Shop(self.pet, items={"uczta": Item("Uczta", 0, {"hunger": 500, "happiness": -500})})
        self.assertTrue(shop.buy("uczta"))
        self.assertEqual((self.pet.hunger, self.pet.happiness), (100, 0))
        self.assertEqual([e for e, _ in self.spy.events].count("stats_changed"), 1)

    def test_item_that_kills(self):
        shop = Shop(self.pet, items={"trucizna": Item("Trucizna", 0, {"health": -100})})
        shop.buy("trucizna")
        self.assertFalse(self.pet.is_alive)
        self.assertIn(("pet_died", None), self.spy.events)

    def test_invalid_item_definition_fails_early(self):
        with self.assertRaises(ValueError):
            Item("Zle", 10, {"glod": 10})     # literówka w nazwie statystyki
        with self.assertRaises(ValueError):
            Item("Zle", -1)

    def test_every_catalog_item_is_valid(self):
        for item_id, item in SHOP_ITEMS.items():
            self.assertTrue(item.name)
            self.assertGreaterEqual(item.price, 0, item_id)


class NewItemShowsUpTest(unittest.TestCase):
    def test_new_catalog_item_appears_in_shop_menu(self):
        """Dodanie przedmiotu do katalogu wystarcza, żeby był w menu sklepu."""
        pet = Pet("Test")
        items = dict(SHOP_ITEMS, lody=Item("Lody", 15, {"happiness": 20}))
        ctrl = GameController(pet, FakeView(), shop=Shop(pet, items=items))
        self.assertIn("buy:lody", ctrl.shop_menu)

        pet.money, pet.happiness = 15, 50
        ctrl.menu = ctrl.shop_menu
        ctrl.selected_idx = ctrl.shop_menu.index("buy:lody")
        ctrl.handle_command("CONFIRM")
        self.assertEqual((pet.money, pet.happiness), (0, 70))


class HoverDescriptionTest(unittest.TestCase):
    """Opis w panelu komunikatu dla pozycji, na której stoi kursor."""

    def setUp(self):
        from view.console.menu_panel import MenuPanel
        self.pet = Pet("Test")
        self.menu = MenuPanel(canvas=None, pet=self.pet, shop=Shop(self.pet))

    def describe(self, action):
        self.menu.set_items([action], 0)
        return self.menu.describe_hovered()

    def test_item_lists_its_effects(self):
        self.pet.money = 100
        self.assertEqual(self.describe("buy:burger"), ("Burger (30$): Glod +60, Energia -10", "info"))

    def test_item_shows_missing_money(self):
        self.pet.money = 40
        text, style = self.describe("buy:lek")
        self.assertIn("Zdrowie +30", text)
        self.assertIn("brakuje 10$", text)
        self.assertEqual(style, "warn")

    def test_skins(self):
        self.pet.money = 0
        self.assertIn("ma ja na sobie", self.describe("skin:classic")[0])
        self.assertIn("brakuje 100$", self.describe("skin:kotek")[0])
        self.pet.owned_skins.add("kotek")
        self.assertIn("kupiona", self.describe("skin:kotek")[0])

    def test_other_entries_have_no_description(self):
        self.assertIsNone(self.describe("back"))

    def test_every_description_fits_on_screen(self):
        from view.console.layout import MESSAGE_BOX
        width = MESSAGE_BOX[3] - 4 - 2   # ramka, marginesy i znak "? "
        self.pet.money = 0               # najdłuższa wersja - z "[brakuje ...]"
        for action in [f"buy:{i}" for i in SHOP_ITEMS] + [f"skin:{s}" for s in Shop(self.pet).skin_prices]:
            text, _ = self.describe(action)
            self.assertLessEqual(len(text), width, text)


if __name__ == "__main__":
    unittest.main()
