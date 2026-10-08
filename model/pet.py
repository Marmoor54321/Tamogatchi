# model/pet.py
import json
import os
from datetime import datetime
from model.observer import Observable


class Pet(Observable):
    def __init__(self, name="Tama"):
        super().__init__()
        self.name = name
        self.is_alive = True
        self.money = 0

        # Statystyki (0-100)
        self.hunger = 100  # 100 = najedzony, 0 = głodujący
        self.energy = 100  # 100 = wypoczęty, 0 = wyczerpany
        self.happiness = 100  # 100 = szczęśliwy, 0 = smutny
        self.health = 100  # 100 = zdrowy, 0 = martwy

        self.last_update = datetime.now()
        self.save_file = "save.json"

        self.shop_items = {
            "Jablko": {"price": 10, "hunger": 20, "energy": 5},
            "Burger": {"price": 30, "hunger": 60, "energy": -10},  # Burger daje dużo głodu, ale męczy
            "Kawa": {"price": 20, "hunger": 5, "energy": 40}  # Kawa daje energię
        }

    def _clamp(self, value):
        """Pomocnicza metoda trzymająca statystyki w ryzach (0-100)"""
        return max(0, min(100, int(value)))

    def _update_stat(self, stat_name, amount):
        """Aktualizuje statystykę i powiadamia obserwatorów"""
        if not self.is_alive:
            return

        current_val = getattr(self, stat_name)
        new_val = self._clamp(current_val + amount)
        setattr(self, stat_name, new_val)

        # Jeśli zdrowie spadnie do 0, zwierzak umiera
        if self.health == 0:
            self.is_alive = False
            self.notify_observers("pet_died")

        self.notify_observers("stats_changed")

    # --- AKCJE UŻYTKOWNIKA ---

    def feed(self):
        if not self.is_alive: return
        self._update_stat("hunger", 30)
        self._update_stat("energy", 5)
        self.notify_observers("action_feed")

    def sleep(self):
        if not self.is_alive: return
        self._update_stat("energy", 50)
        self._update_stat("hunger", -10)
        self.notify_observers("action_sleep")

    def play(self):
        if not self.is_alive: return
        self._update_stat("happiness", 30)
        self._update_stat("energy", -20)
        self._update_stat("hunger", -20)
        self.money += 30  # Nagroda za zabawę!
        self.notify_observers("action_play")

    def resurrect(self):
        self.is_alive = True
        self.hunger = 100
        self.energy = 100
        self.happiness = 100
        self.health = 100
        self.last_update = datetime.now()
        # Informujemy widok o cudownym powrocie do życia
        self.notify_observers("pet_resurrected")
        self.notify_observers("stats_changed")

    def buy_and_feed(self, item_name):
        if not self.is_alive: return
        if item_name not in self.shop_items: return

        item = self.shop_items[item_name]

        if self.money >= item["price"]:
            self.money -= item["price"]
            self._update_stat("hunger", item["hunger"])
            self._update_stat("energy", item["energy"])
            # Wysyłamy do widoku sygnał sukcesu wraz z nazwą przedmiotu (jako 'data')
            self.notify_observers("action_buy_success", item_name)
        else:
            # Wysyłamy sygnał o braku środków
            self.notify_observers("action_buy_fail", item_name)

    # --- LOGIKA UPŁYWU CZASU ---

    def pass_time(self, seconds):
        """Wywoływane przez Kontroler w głównej pętli gry. Obniża statystyki w czasie."""
        if not self.is_alive: return

        # Przykładowy przelicznik: 1 punkt głodu spada co 5 sekund (do dostrojenia później)
        drop_rate = seconds / 5.0

        self.hunger -= drop_rate
        self.energy -= (drop_rate * 0.8)
        self.happiness -= (drop_rate * 1.2)

        # Konwersja na inty za pomocą clamp
        self.hunger = self._clamp(self.hunger)
        self.energy = self._clamp(self.energy)
        self.happiness = self._clamp(self.happiness)

        # Jeśli zwierzak jest głodny lub zmęczony, traci zdrowie
        if self.hunger < 20 or self.energy < 20:
            self.health = self._clamp(self.health - 5)
            if self.health == 0:
                self.is_alive = False
                self.notify_observers("pet_died")

        self.last_update = datetime.now()
        self.notify_observers("stats_changed")

    # --- ZAPIS I ODCZYT (Baza Danych/Plik) ---

    def save_state(self):
        data = {
            "name": self.name,
            "is_alive": self.is_alive,
            "money": self.money,
            "hunger": self.hunger,
            "energy": self.energy,
            "happiness": self.happiness,
            "health": self.health,
            "last_update": self.last_update.isoformat()
        }
        with open(self.save_file, "w") as f:
            json.dump(data, f)

    def load_state(self):
        if not os.path.exists(self.save_file):
            return  # Zaczynamy nową grę

        with open(self.save_file, "r") as f:
            data = json.load(f)

        self.name = data.get("name", self.name)
        self.is_alive = data.get("is_alive", True)
        self.money = data.get("money", 0)
        self.hunger = data.get("hunger", 100)
        self.energy = data.get("energy", 100)
        self.happiness = data.get("happiness", 100)
        self.health = data.get("health", 100)

        saved_time = datetime.fromisoformat(data.get("last_update", datetime.now().isoformat()))

        # Symulacja upływu czasu podczas nieobecności (Offline Progress)
        if self.is_alive:
            time_diff = (datetime.now() - saved_time).total_seconds()
            if time_diff > 0:
                self.pass_time(time_diff)