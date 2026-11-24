# model/pet.py
import json
import os
from datetime import datetime
from model.observer import Observable
from model.skins import SKIN_PRICES, DEFAULT_SKIN


class Pet(Observable):
    # --- BALANS GRY ---
    # Ile punktów statystyki ubywa na sekundę
    HUNGER_DROP_PER_SEC = 1 / 5       # 1 punkt głodu co 5 sekund
    ENERGY_DROP_PER_SEC = 0.8 / 5
    HAPPINESS_DROP_PER_SEC = 1.2 / 5
    HEALTH_DROP_PER_SEC = 1.0         # gdy zwierzak jest głodny lub zmęczony
    LOW_STAT_THRESHOLD = 20           # poniżej tej wartości zwierzak traci zdrowie
    SLEEPY_THRESHOLD = 30             # poniżej - zwierzak jest śpiący
    SAD_THRESHOLD = 40                # poniżej - zwierzak jest smutny
    MIN_ENERGY_TO_PLAY = SLEEPY_THRESHOLD  # śpiący zwierzak nie chce się bawić
    MONEY_PER_OBSTACLE = 10           # $ za każdą przeskoczoną przeszkodę w minigrze

    def __init__(self, name="Tama"):
        super().__init__()
        self.name = name
        self.is_alive = True
        self.money = 0
        self.high_score = 0  # Najlepszy wynik w minigrze Dino

        # Skórki: kupione raz zostają na zawsze, założona może być jedna
        self.owned_skins = {DEFAULT_SKIN}
        self.active_skin = DEFAULT_SKIN

        # Statystyki (0-100)
        self.hunger = 100  # 100 = najedzony, 0 = głodujący
        self.energy = 100  # 100 = wypoczęty, 0 = wyczerpany
        self.happiness = 100  # 100 = szczęśliwy, 0 = smutny
        self.health = 100  # 100 = zdrowy, 0 = martwy

        self.last_update = datetime.now()
        self.save_file = "save.json"

    def _clamp(self, value):
        """Pomocnicza metoda trzymająca statystyki w ryzach (0-100).
        Wartości są zmiennoprzecinkowe, żeby małe przyrosty czasu się sumowały."""
        return max(0.0, min(100.0, float(value)))

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

    def play(self, score=0):
        """Zabawa ze zwierzakiem. Za każdą przeskoczoną przeszkodę w minigrze gracz otrzymuje 10$."""
        if not self.is_alive: return
        return self.record_minigame_result(score)

    def can_play(self):
        """Czy zwierzak ma dość siły na zabawę."""
        return self.is_alive and self.energy >= self.MIN_ENERGY_TO_PLAY

    def start_play(self):
        """Zwierzak próbuje zacząć zabawę. Gdy jest zbyt zmęczony, odmawia
        (zdarzenie "action_play_refused") i zwraca False."""
        if not self.is_alive:
            return False
        if not self.can_play():
            self.notify_observers("action_play_refused", self.MIN_ENERGY_TO_PLAY)
            return False
        return True

    def record_minigame_result(self, score: int = 0):
        """Aktualizuje statystyki po minigrze Dino.
        Zamiast stałej kasy za sam przycisk, gracz otrzymuje 10$ za każdą przeszkodę.
        """
        if not self.is_alive: return 0

        money_earned = max(0, score) * self.MONEY_PER_OBSTACLE
        self.money += money_earned

        is_new_record = score > self.high_score
        if is_new_record:
            self.high_score = score

        # Zabawa poprawia humor, ale zwierzak męczy się i robi głodny
        self._update_stat("happiness", 25)
        self._update_stat("energy", -15)
        self._update_stat("hunger", -15)

        self.notify_observers("action_play", {
            "score": score,
            "money": money_earned,
            "high_score": self.high_score,
            "is_new_record": is_new_record
        })
        return money_earned

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

    # --- KASA I EFEKTY (używa ich np. sklep z model/shop.py) ---

    def spend(self, amount):
        """Odejmuje kasę, jeśli zwierzaka na to stać. Zwraca True, gdy się udało."""
        if amount < 0 or self.money < amount:
            return False
        self.money -= amount
        return True

    def apply_effects(self, effects):
        """Zmienia kilka statystyk naraz, np. {"hunger": 20, "energy": -5}.
        Widok dostaje jedno zdarzenie "stats_changed" zamiast kilku."""
        if not self.is_alive:
            return
        for stat, amount in effects.items():
            setattr(self, stat, self._clamp(getattr(self, stat) + amount))
        if self.health == 0:
            self.is_alive = False
            self.notify_observers("pet_died")
        self.notify_observers("stats_changed")

    # --- SKÓRKI ---

    @property
    def mood(self):
        """Nastrój zwierzaka jako identyfikator: "dead" | "sleepy" | "sad" | "happy".
        Widok decyduje tylko, jak dany nastrój narysować."""
        if not self.is_alive:
            return "dead"
        if self.energy < self.SLEEPY_THRESHOLD:
            return "sleepy"
        if self.happiness < self.SAD_THRESHOLD:
            return "sad"
        return "happy"

    def owns_skin(self, skin_id):
        return skin_id in self.owned_skins

    def unlock_skin(self, skin_id):
        """Dodaje skórkę do kolekcji i ją zakłada (płaci za nią sklep)."""
        if skin_id not in SKIN_PRICES:
            return False
        self.owned_skins.add(skin_id)
        self.active_skin = skin_id
        return True

    def equip_skin(self, skin_id):
        """Zakłada wcześniej kupioną skórkę."""
        if not self.is_alive or not self.owns_skin(skin_id):
            return False
        self.active_skin = skin_id
        self.notify_observers("action_skin_equipped", skin_id)
        return True

    # --- LOGIKA UPŁYWU CZASU ---

    def _seconds_until_low(self, value, drop_per_sec):
        """Po ilu sekundach statystyka spadnie poniżej LOW_STAT_THRESHOLD (0 = już jest)."""
        return max(0.0, (value - self.LOW_STAT_THRESHOLD) / drop_per_sec)

    def pass_time(self, seconds):
        """Wywoływane przez Kontroler w głównej pętli gry. Obniża statystyki w czasie."""
        if not self.is_alive or seconds <= 0: return

        # Zdrowie spada tylko przez tę część czasu, w której zwierzak był już głodny
        # lub zmęczony. Liczymy to przed zmianą statystyk, więc wynik jest taki sam
        # dla jednego długiego kroku (np. powrót po nieobecności) i wielu krótkich.
        low_since = min(self._seconds_until_low(self.hunger, self.HUNGER_DROP_PER_SEC),
                        self._seconds_until_low(self.energy, self.ENERGY_DROP_PER_SEC))
        damage_seconds = max(0.0, seconds - low_since)

        self.hunger = self._clamp(self.hunger - seconds * self.HUNGER_DROP_PER_SEC)
        self.energy = self._clamp(self.energy - seconds * self.ENERGY_DROP_PER_SEC)
        self.happiness = self._clamp(self.happiness - seconds * self.HAPPINESS_DROP_PER_SEC)

        if damage_seconds > 0:
            self.health = self._clamp(self.health - damage_seconds * self.HEALTH_DROP_PER_SEC)
            if self.health == 0:
                self.is_alive = False
                self.notify_observers("pet_died")

        self.last_update = datetime.now()
        self.notify_observers("stats_changed")

    # --- ZAPIS I ODCZYT (Baza Danych/Plik) ---

    def save_state(self):
        """Zapisuje stan do pliku tymczasowego i dopiero potem podmienia save.json.
        Przerwany zapis (zamknięte okno, brak prądu) nie zniszczy starego zapisu."""
        data = {
            "name": self.name,
            "is_alive": self.is_alive,
            "money": self.money,
            "high_score": self.high_score,
            "owned_skins": sorted(self.owned_skins),
            "active_skin": self.active_skin,
            "hunger": self.hunger,
            "energy": self.energy,
            "happiness": self.happiness,
            "health": self.health,
            "last_update": self.last_update.isoformat()
        }
        tmp_file = self.save_file + ".tmp"
        with open(tmp_file, "w") as f:
            json.dump(data, f)
        os.replace(tmp_file, self.save_file)

    def load_state(self):
        """Wczytuje zapis. Zwraca False, gdy zapisu nie ma albo jest uszkodzony
        (wtedy gra zaczyna się od nowa, a zły plik zostaje jako save.json.bad)."""
        if not os.path.exists(self.save_file):
            return False  # Zaczynamy nową grę

        try:
            with open(self.save_file, "r") as f:
                data = json.load(f)
            if not isinstance(data, dict):
                raise ValueError("zapis nie jest obiektem JSON")
            state = {
                "name": str(data.get("name", self.name)),
                "is_alive": bool(data.get("is_alive", True)),
                "money": int(data.get("money", 0)),
                "high_score": int(data.get("high_score", 0)),
                "hunger": self._clamp(data.get("hunger", 100)),
                "energy": self._clamp(data.get("energy", 100)),
                "happiness": self._clamp(data.get("happiness", 100)),
                "health": self._clamp(data.get("health", 100)),
                "owned_skins": list(data.get("owned_skins", [])),
                "active_skin": data.get("active_skin", DEFAULT_SKIN),
            }
            last_update = data.get("last_update")
            saved_time = datetime.fromisoformat(last_update) if last_update else datetime.now()
        except (OSError, ValueError, TypeError):
            # json.JSONDecodeError też jest ValueError
            self._set_aside_bad_save()
            return False

        # Dopiero gdy wszystko się wczytało, zmieniamy stan zwierzaka
        self.name = state["name"]
        self.is_alive = state["is_alive"] and state["health"] > 0
        self.money = max(0, state["money"])
        self.high_score = max(0, state["high_score"])
        self.hunger = state["hunger"]
        self.energy = state["energy"]
        self.happiness = state["happiness"]
        self.health = state["health"]

        # Ignorujemy skórki, których nie ma już w katalogu (np. stary zapis)
        owned = {s for s in state["owned_skins"] if s in SKIN_PRICES}
        self.owned_skins = owned | {DEFAULT_SKIN}
        active = state["active_skin"]
        self.active_skin = active if active in self.owned_skins else DEFAULT_SKIN

        # Symulacja upływu czasu podczas nieobecności (Offline Progress)
        if self.is_alive:
            time_diff = (datetime.now() - saved_time).total_seconds()
            if time_diff > 0:
                self.pass_time(time_diff)
        return True

    def _set_aside_bad_save(self):
        """Odkłada uszkodzony zapis na bok, żeby nie zniknął bez śladu."""
        try:
            os.replace(self.save_file, self.save_file + ".bad")
        except OSError:
            pass
