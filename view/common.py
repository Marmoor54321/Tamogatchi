from model.shop import SHOP_ITEMS

STAT_LABELS = {
    "hunger": "Glod",
    "energy": "Energia",
    "happiness": "Szczescie",
    "health": "Zdrowie",
}

ACTION_LABELS = {
    "shop": "Sklep",
    "play": "Zabawa",
    "sleep": "Śpij",
    "wake": "Obudź",
    "exit": "Wyjście",
    "back": "Wróć",
    "resurrect": "Odródź",
    "skins": "Skórki",
}

SKIN_NAMES = {
    "classic": "Klasyczny",
    "kotek": "Kotek",
    "krolik": "Krolik",
    "robot": "Robot",
}

MOOD_CAPTIONS = {
    "happy": "Szczesliwy",
    "sad": "Smutny",
    "sleepy": "Spiacy",
    "asleep": "Spi... +1 energii / 2 s",
    "dead": "Nie zyje",
}

WELCOME = ("Witaj w Tamagotchi! Zadbaj o swojego zwierzaka.", "info")
DIED_WHILE_AWAY = ("Pod twoja nieobecnosc zwierzak umarl (X_X). Wybierz 'Odrodz'!", "bad")

def skin_name(skin_id):
    return SKIN_NAMES.get(skin_id, skin_id)

def _item_name(item_id, shop=None):
    items = shop.items if shop is not None else SHOP_ITEMS
    item = items.get(item_id)
    return item.name if item else item_id

def action_label(action, pet, shop):
    if action.startswith("buy:"):
        item = shop.items[action[len("buy:"):]]
        return f"{item.name}({item.price}$)"
    if action.startswith("skin:"):
        skin_id = action[len("skin:"):]
        if skin_id == pet.active_skin:
            return f"{skin_name(skin_id)}*"
        if pet.owns_skin(skin_id):
            return skin_name(skin_id)
        return f"{skin_name(skin_id)}({shop.skin_prices[skin_id]}$)"
    return ACTION_LABELS.get(action, action)

def is_action_available(action, pet, shop):
    if action == "play":
        return pet.can_play()
    if action.startswith("buy:"):
        return shop.can_afford(action[len("buy:"):])
    if action.startswith("skin:"):
        return shop.can_afford_skin(action[len("skin:"):])
    return True

def _with_missing_money(text, price, pet):
    missing = price - pet.money
    if missing > 0:
        return f"{text}  [brakuje {missing}$]", "warn"
    return text, "info"

def describe_action(action, pet, shop):
    if action == "play" and pet.is_alive and not pet.can_play():
        return (
            f"Za malo energii (min. {pet.MIN_ENERGY_TO_PLAY}%). "
            "Wybierz 'Spij' albo kup kawe.",
            "warn",
        )

    if action.startswith("buy:"):
        item = shop.items[action[len("buy:"):]]
        sep = "," if len(item.effects) > 2 else ", "
        effects = sep.join(
            f"{STAT_LABELS.get(stat, stat)} {amount:+g}"
            for stat, amount in item.effects.items()
        )
        text = f"{item.name} ({item.price}$): {effects or 'nic nie zmienia'}"
        return _with_missing_money(text, item.price, pet)

    if action.startswith("skin:"):
        skin_id = action[len("skin:"):]
        name = skin_name(skin_id)
        if skin_id == pet.active_skin:
            return f"Skorka {name} - zwierzak ma ja na sobie", "info"
        if pet.owns_skin(skin_id):
            return f"Skorka {name} - kupiona, Enter zaklada", "info"
        price = shop.skin_prices[skin_id]
        return _with_missing_money(f"Skorka {name} ({price}$): Enter = kup i zaloz", price, pet)

    return None

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

def message_for(event_name, data=None, shop=None):
    handlers = {
        "pet_died": lambda d: ("Zwierzak umarl (X_X). Wybierz 'Odrodz', by go wskrzesic!", "bad"),
        "pet_resurrected": lambda d: ("Magia! Zwierzak dostal drugie zycie!", "good"),
        "pet_renamed": lambda d: (f"Zwierzak ma teraz na imie: {d}!", "good"),
        "action_play": _play_message,
        "action_play_refused": lambda d: ("Zwierzak jest zbyt zmeczony na zabawe. Niech sie przespi!", "warn"),
        "action_feed": lambda d: ("Mniam! (+Glod)", "good"),
        "action_sleep": lambda d: ("Zwierzak zasnal. Zzz... (+1 energii co 2 s)", "sleepy"),
        "action_sleep_refused": lambda d: ("Zwierzak jest wypoczety - nie chce spac.", "info"),
        "action_wake_up": lambda d: (
            ("Zwierzak sie wyspal! Energia 100%.", "good")
            if isinstance(d, dict) and d.get("rested")
            else ("Pobudka! Zwierzak wstal przed czasem.", "info")
        ),
        "action_buy_success": lambda d: (f"Kupiono i uzyto: {_item_name(d, shop)}!", "good"),
        "action_buy_fail": lambda d: (f"Za malo kasy na: {_item_name(d, shop)}! Baw sie, by zarobic.", "bad"),
        "action_skin_bought": lambda d: (f"Kupiono skorke: {skin_name(d)}! Zwierzak juz ja nosi.", "good"),
        "action_skin_buy_fail": lambda d: (f"Za malo kasy na skorke: {skin_name(d)}!", "bad"),
        "action_skin_equipped": lambda d: (f"Zalozono skorke: {skin_name(d)}.", "info"),
    }
    make = handlers.get(event_name)
    return make(data) if make else None

