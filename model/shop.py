# model/shop.py
from dataclasses import dataclass, field

from model.skins import SKIN_PRICES

STATS = ("hunger", "energy", "happiness", "health")

@dataclass(frozen=True)
class Item:
    name: str
    price: int
    effects: dict = field(default_factory=dict)

    def __post_init__(self):
        unknown = set(self.effects) - set(STATS)
        if unknown:
            raise ValueError(f"Przedmiot {self.name!r}: nieznane statystyki {sorted(unknown)}")
        if self.price < 0:
            raise ValueError(f"Przedmiot {self.name!r}: cena nie może być ujemna")


SHOP_ITEMS = {
    "jablko": Item("Jablko", price=10, effects={"hunger": 20, "energy": 5}),
    "burger": Item("Burger", price=30, effects={"hunger": 60, "energy": -10}),
    "kawa": Item("Kawa", price=20, effects={"hunger": 5, "energy": 40}), 
    "lek": Item("Lek", price=50, effects={"health": 30, "happiness": -5}),
    "lody": Item("Lody", price=20, effects={"hunger": 10, "health": -3, "happiness": 10}),
}


class Shop:
    def __init__(self, pet, items=None, skin_prices=None):
        self.pet = pet
        self.items = SHOP_ITEMS if items is None else items
        self.skin_prices = SKIN_PRICES if skin_prices is None else skin_prices

    def can_afford(self, item_id):
        item = self.items.get(item_id)
        return item is not None and self.pet.money >= item.price

    def buy(self, item_id):
        item = self.items.get(item_id)
        if item is None or not self.pet.is_alive:
            return False
        if not self.pet.spend(item.price):
            self.pet.notify_observers("action_buy_fail", item_id)
            return False
        self.pet.apply_effects(item.effects)
        self.pet.notify_observers("action_buy_success", item_id)
        return True

    def can_afford_skin(self, skin_id):
        return self.pet.owns_skin(skin_id) or self.pet.money >= self.skin_prices.get(skin_id, float("inf"))

    def buy_skin(self, skin_id):
        if skin_id not in self.skin_prices or not self.pet.is_alive:
            return False
        if self.pet.owns_skin(skin_id):
            return self.pet.equip_skin(skin_id)
        if not self.pet.spend(self.skin_prices[skin_id]):
            self.pet.notify_observers("action_skin_buy_fail", skin_id)
            return False
        self.pet.unlock_skin(skin_id)
        self.pet.notify_observers("action_skin_bought", skin_id)
        return True
