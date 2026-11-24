# model/shop.py
"""Sklep: katalog przedmiotów i logika kupowania.

Zwierzak (model/pet.py) nie wie nic o sklepie - ma tylko kasę, statystyki
i skórki. Sklep sprawdza warunki, pobiera pieniądze i mówi zwierzakowi,
co ma się zmienić.

=====================================================================
JAK DODAĆ NOWY PRZEDMIOT
=====================================================================
Dopisz jedną linijkę do SHOP_ITEMS poniżej, np.:

    "lody": Item("Lody", price=15, effects={"happiness": 20, "hunger": 5}),

i to wszystko: pojawi się w menu sklepu, z ceną i komunikatem po zakupie.
  - klucz ("lody") to identyfikator używany w kodzie i w menu,
  - name to napis wyświetlany graczowi,
  - effects to zmiany statystyk: "hunger", "energy", "happiness", "health"
    (liczby ujemne zmniejszają statystykę).
Kolejność w słowniku = kolejność w menu.
"""
from dataclasses import dataclass, field

from model.skins import SKIN_PRICES

# Statystyki, które przedmiot może zmieniać
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
    "burger": Item("Burger", price=30, effects={"hunger": 60, "energy": -10}),  # Dużo jedzenia, ale męczy
    "kawa": Item("Kawa", price=20, effects={"hunger": 5, "energy": 40}),        # Kawa daje energię
    "lek": Item("Lek", price=50, effects={"health": 30, "happiness": -5}),      # Leczy, ale nikt nie lubi leków
}


class Shop:
    """Kupowanie przedmiotów i skórek dla danego zwierzaka.

    Zdarzenia (np. "action_buy_success") wysyła przez zwierzaka, bo to jego
    stan się zmienia i to jego obserwują widok i kontroler.
    """

    def __init__(self, pet, items=None, skin_prices=None):
        self.pet = pet
        self.items = SHOP_ITEMS if items is None else items
        self.skin_prices = SKIN_PRICES if skin_prices is None else skin_prices

    # --- PRZEDMIOTY ---
    def can_afford(self, item_id):
        item = self.items.get(item_id)
        return item is not None and self.pet.money >= item.price

    def buy(self, item_id):
        """Kupuje przedmiot i od razu go używa. Zwraca True, gdy się udało."""
        item = self.items.get(item_id)
        if item is None or not self.pet.is_alive:
            return False
        if not self.pet.spend(item.price):
            self.pet.notify_observers("action_buy_fail", item_id)
            return False
        self.pet.apply_effects(item.effects)
        self.pet.notify_observers("action_buy_success", item_id)
        return True

    # --- SKÓRKI ---
    def can_afford_skin(self, skin_id):
        return self.pet.owns_skin(skin_id) or self.pet.money >= self.skin_prices.get(skin_id, float("inf"))

    def buy_skin(self, skin_id):
        """Kupuje skórkę i od razu ją zakłada (kupionej nie kupuje drugi raz)."""
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
