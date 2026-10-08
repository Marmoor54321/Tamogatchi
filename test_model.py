# test_model.py
from model.pet import Pet
from model.observer import Observer
import time

class ConsoleSpy(Observer):
    """Prosty obserwator symulujący zachowanie Widoku"""
    def update(self, event_name, data=None):
        if event_name == "stats_changed":
            print("--- ZMIANA W MODELU ---")
            print(f"Głód: {my_pet.hunger}, Energia: {my_pet.energy}, Szczęście: {my_pet.happiness}, Zdrowie: {my_pet.health}, Kasa: {my_pet.money}")
        elif event_name == "action_feed":
            print(">>> ZWIERZAK COŚ ZJADŁ! <<<")

# 1. Tworzymy zwierzaka
my_pet = Pet("Reksio")

# 2. Podpinamy szpiega (nasz "widok")
spy = ConsoleSpy()
my_pet.add_observer(spy)

# 3. Wykonujemy akcje (logika Controller'a)
print("Początek gry:")
my_pet.notify_observers("stats_changed")

print("\nBawimy się:")
my_pet.play()

print("\nKarmimy:")
my_pet.feed()

print("\nSymulacja upływu 50 sekund w tle...")
my_pet.pass_time(50)

print("\nZapisujemy stan gry do save.json...")
my_pet.save_state()
print("Koniec testu.")