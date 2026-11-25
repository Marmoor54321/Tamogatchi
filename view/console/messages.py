# view/console/messages.py
"""Zdarzenie z modelu -> (treść komunikatu, nazwa stylu) albo None."""
from model.shop import SHOP_ITEMS
from view.skin_art import skin_name


def _item_name(item_id):
    item = SHOP_ITEMS.get(item_id)
    return item.name if item else item_id


def _play_message(data):
    if not isinstance(data, dict):
        return "Super zabawa!", "good"
    score = data.get("score", 0)
    money = data.get("money", 0)
    if data.get("is_new_record") and score > 0:
        return f"NOWY REKORD ({score} pkt)! Zdobyto +{money}$!", "good"
    if score > 0:
        return f"Super bieg! Przeskoczono {score} przeszkod (+{money}$).", "good"
    return "Koniec biegu! Nastepnym razem pojdzie lepiej.", "warn"


_MESSAGES = {
    "pet_died": lambda d: ("Zwierzak umarl (X_X). Wybierz 'Odrodz', by go wskrzesic!", "bad"),
    "pet_resurrected": lambda d: ("Magia! Zwierzak dostal drugie zycie!", "good"),
    "pet_renamed": lambda d: (f"Zwierzak ma teraz na imie: {d}!", "good"),
    "action_play": _play_message,
    "action_play_refused": lambda d: ("Zwierzak jest zbyt zmeczony na zabawe. Niech sie przespi!", "warn"),
    "action_feed": lambda d: ("Mniam! (+Glod)", "good"),
    "action_sleep": lambda d: ("Zwierzak zasnal. Zzz... (+1 energii co 2 s)", "sleepy"),
    "action_sleep_refused": lambda d: ("Zwierzak jest wypoczety - nie chce spac.", "info"),
    "action_wake_up": lambda d: (("Zwierzak sie wyspal! Energia 100%.", "good")
                                 if isinstance(d, dict) and d.get("rested")
                                 else ("Pobudka! Zwierzak wstal przed czasem.", "info")),
    "action_buy_success": lambda d: (f"Kupiono i uzyto: {_item_name(d)}!", "good"),
    "action_buy_fail": lambda d: (f"Za malo kasy na: {_item_name(d)}! Baw sie, by zarobic.", "bad"),
    "action_skin_bought": lambda d: (f"Kupiono skorke: {skin_name(d)}! Zwierzak juz ja nosi.", "good"),
    "action_skin_buy_fail": lambda d: (f"Za malo kasy na skorke: {skin_name(d)}!", "bad"),
    "action_skin_equipped": lambda d: (f"Zalozono skorke: {skin_name(d)}.", "info"),
}

WELCOME = ("Witaj w Tamagotchi! Zadbaj o swojego zwierzaka.", "info")
DIED_WHILE_AWAY = ("Pod twoja nieobecnosc zwierzak umarl (X_X). Wybierz 'Odrodz'!", "bad")


def message_for(event_name, data=None):
    make = _MESSAGES.get(event_name)
    return make(data) if make else None
