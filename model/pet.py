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
    SLEEP_ENERGY_PER_SEC = 1 / 2      # w czasie snu: 1 punkt energii co 2 sekundy
    MONEY_PER_OBSTACLE = 10           # $ za każdą przeskoczoną przeszkodę w minigrze
    MAX_NAME_LENGTH = 20              # limit długości imienia (mieści się w ramce widoku)

    def __init__(self, name="Tama"):
        super().__init__()
        self.name = name
        self.is_alive = True
        self.is_sleeping = False  # Śpiący zwierzak odzyskuje energię z czasem
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
        self._last_notified = self._snapshot()

    def _snapshot(self):
        """Migawka stanu używana do wykrywania faktycznych zmian dla obserwatorów."""
        return {
            "name": self.name,
            "is_alive": self.is_alive,
            "is_sleeping": self.is_sleeping,
            "money": self.money,
            "high_score": self.high_score,
            "active_skin": self.active_skin,
            "owned_skins": frozenset(self.owned_skins),
            "hunger": self.hunger,
            "energy": self.energy,
            "happiness": self.happiness,
            "health": self.health,
            "mood": self.mood,
            "can_play": self.can_play(),
        }

    def _collect_stats_diff(self):
        """Zwraca słownik zmienionych pól od ostatniego powiadomienia `stats_changed`."""
        current = self._snapshot()
        prev = self._last_notified
        fields = {k for k, v in current.items() if prev.get(k) != v}
        numeric = {"hunger", "energy", "happiness", "health"}
        rounded = {
            k for k in fields
            if (round(current[k]) != round(prev.get(k, 0)) if k in numeric else True)
        }
        self._last_notified = current
        return {"fields": fields, "rounded": rounded}

    def _notify_stats_changed(self, force=False):
        """Wysyła `stats_changed` z listą zmienionych pól (tylko gdy coś się zmieniło)."""
        diff = self._collect_stats_diff()
        if diff["fields"] or force:
            self.notify_observers("stats_changed", diff)

    def _clamp(self, value):
        """Pomocnicza metoda trzymająca statystyki w ryzach (0-100).
        Wartości są zmiennoprzecinkowe, żeby małe przyrosty czasu się sumowały."""
        return max(0.0, min(100.0, float(value)))

    def _apply_stat_changes(self, changes, force_notify=False):
        """Atomowo zmienia zestaw statystyk i wysyła jedno powiadomienie `stats_changed`."""
        if not self.is_alive:
            return
        for stat_name, amount in changes.items():
            current_val = getattr(self, stat_name)
            setattr(self, stat_name, self._clamp(current_val + amount))

        if self.health == 0:
            self.is_alive = False
            self.is_sleeping = False
            self.notify_observers("pet_died")

        self._notify_stats_changed(force=force_notify)

    def _update_stat(self, stat_name, amount):
        """Aktualizuje statystykę i powiadamia obserwatorów"""
        self._apply_stat_changes({stat_name: amount}, force_notify=True)

    # --- AKCJE UŻYTKOWNIKA ---

    def feed(self):
        if not self.is_alive: return
        self._apply_stat_changes({"hunger": 30, "energy": 5}, force_notify=True)
        self.notify_observers("action_feed")

    # --- SEN ---

    def start_sleep(self):
        """Zwierzak zasypia. Energia rośnie potem w pass_time() (1 pkt / 2 s),
        aż do 100% - wtedy budzi się sam. Wypoczęty zwierzak nie chce spać."""
        if not self.is_alive or self.is_sleeping:
            return False
        if self.energy >= 100:
            self.notify_observers("action_sleep_refused")
            return False
        self.is_sleeping = True
        self.notify_observers("action_sleep")
        return True

    def wake_up(self):
        """Budzi zwierzaka przed czasem (z taką energią, jaką zdążył odzyskać)."""
        if not self.is_sleeping:
            return False
        self._wake(rested=False)
        return True

    def _wake(self, rested):
        self.is_sleeping = False
        self.notify_observers("action_wake_up", {"rested": rested})

    def play(self, score=0):
        """Zabawa ze zwierzakiem. Za każdą przeskoczoną przeszkodę w minigrze gracz otrzymuje 10$."""
        if not self.is_alive: return
        return self.record_minigame_result(score)

    def can_play(self):
        """Czy zwierzak ma dość siły na zabawę (i czy nie śpi)."""
        return self.is_alive and not self.is_sleeping and self.energy >= self.MIN_ENERGY_TO_PLAY

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
        self._apply_stat_changes(
            {"happiness": 25, "energy": -15, "hunger": -15},
            force_notify=True,
        )

        self.notify_observers("action_play", {
            "score": score,
            "money": money_earned,
            "high_score": self.high_score,
            "is_new_record": is_new_record
        })
        return money_earned

    def resurrect(self):
        self.is_alive = True
        self.is_sleeping = False
        self.hunger = 100
        self.energy = 100
        self.happiness = 100
        self.health = 100
        self.last_update = datetime.now()
        # Informujemy widok o cudownym powrocie do życia
        self.notify_observers("pet_resurrected")
        self._notify_stats_changed(force=True)

    def rename(self, name):
        """Nadaje zwierzakowi nowe imię (ignoruje puste, obcina do MAX_NAME_LENGTH)."""
        cleaned = " ".join(str(name).split())[:self.MAX_NAME_LENGTH]
        if not cleaned:
            return False
        self.name = cleaned
        self.notify_observers("pet_renamed", self.name)
        return True

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
        self._apply_stat_changes(effects, force_notify=True)

    # --- SKÓRKI ---

    @property
    def mood(self):
        """Nastrój zwierzaka jako identyfikator:
        "dead" | "asleep" | "sleepy" | "sad" | "happy".
        Widok decyduje tylko, jak dany nastrój narysować."""
        if not self.is_alive:
            return "dead"
        if self.is_sleeping:
            return "asleep"
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
        """Wywoływane przez Kontroler w głównej pętli gry (i po wczytaniu zapisu
        za czas nieobecności). Zmienia statystyki w czasie.

        Wynik jest taki sam dla jednego długiego kroku i wielu krótkich, także gdy
        zwierzak w międzyczasie się wyśpi i obudzi."""
        if not self.is_alive or seconds <= 0: return

        if self.is_sleeping:
            # Najpierw sen - do pełnej energii albo do końca podanego czasu
            until_rested = (100 - self.energy) / self.SLEEP_ENERGY_PER_SEC
            asleep = min(seconds, until_rested)
            self._advance(asleep, self.SLEEP_ENERGY_PER_SEC)
            seconds -= asleep
            if self.is_alive and self.energy >= 100:
                self._wake(rested=True)

        if self.is_alive and seconds > 0:
            self._advance(seconds, -self.ENERGY_DROP_PER_SEC)

        self.last_update = datetime.now()
        self._notify_stats_changed(force=False)

    def _advance(self, seconds, energy_per_sec):
        """Jeden odcinek czasu ze stałym tempem zmian (sen albo czuwanie)."""
        # Zdrowie spada tylko wtedy, gdy zwierzak jest głodny LUB zmęczony.
        # Wyznaczamy te chwile z góry, więc wynik nie zależy od długości kroku.
        hungry_from = self._seconds_until_low(self.hunger, self.HUNGER_DROP_PER_SEC)
        if energy_per_sec < 0:
            # Energia spada: zmęczony od chwili tired_from do końca odcinka
            tired_from = self._seconds_until_low(self.energy, -energy_per_sec)
            harm = [(min(hungry_from, tired_from), seconds)]
        else:
            # Energia rośnie (sen): zmęczony tylko na początku, do chwili tired_until
            tired_until = min(seconds, max(0.0, (self.LOW_STAT_THRESHOLD - self.energy) / energy_per_sec))
            harm = [(0.0, tired_until), (max(tired_until, hungry_from), seconds)]

        # Kiedy zdrowie spadnie do zera? Jeśli w tym odcinku - czas kończy się na śmierci,
        # żeby pozostałe statystyki nie liczyły się dalej (np. martwy zwierzak się nie wysypia).
        health_left = self.health / self.HEALTH_DROP_PER_SEC   # sekundy szkody do śmierci
        damage_seconds, died_at = 0.0, None
        for start, end in harm:
            length = max(0.0, end - start)
            if damage_seconds + length >= health_left and died_at is None and length > 0:
                died_at = start + (health_left - damage_seconds)
            damage_seconds += length
        if died_at is not None:
            seconds, damage_seconds = died_at, health_left

        self.hunger = self._clamp(self.hunger - seconds * self.HUNGER_DROP_PER_SEC)
        self.energy = self._clamp(self.energy + seconds * energy_per_sec)
        self.happiness = self._clamp(self.happiness - seconds * self.HAPPINESS_DROP_PER_SEC)

        if damage_seconds > 0:
            self.health = self._clamp(self.health - damage_seconds * self.HEALTH_DROP_PER_SEC)
            if died_at is not None or self.health == 0:
                self.health = 0.0
                self.is_alive = False
                self.is_sleeping = False
                self.notify_observers("pet_died")

    # --- ZAPIS I ODCZYT (Baza Danych/Plik) ---

    def save_state(self):
        """Zapisuje stan do pliku tymczasowego i dopiero potem podmienia save.json.
        Przerwany zapis (zamknięte okno, brak prądu) nie zniszczy starego zapisu."""
        data = {
            "name": self.name,
            "is_alive": self.is_alive,
            "is_sleeping": self.is_sleeping,
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
                "is_sleeping": bool(data.get("is_sleeping", False)),
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
        self.is_sleeping = state["is_sleeping"] and self.is_alive
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
        self._last_notified = self._snapshot()
        return True

    def _set_aside_bad_save(self):
        """Odkłada uszkodzony zapis na bok, żeby nie zniknął bez śladu."""
        try:
            os.replace(self.save_file, self.save_file + ".bad")
        except OSError:
            pass
