# view/console/menu_panel.py
from view.console.layout import MENU_BOX
from view.console.panel import Panel
from view.console.stats_panel import STAT_LABELS
from view.skin_art import skin_name

# Napisy wyświetlane dla identyfikatorów akcji z kontrolera.
ACTION_LABELS = {
    "shop": "Sklep",
    "play": "Zabawa",
    "sleep": "Śpij",
    "exit": "Wyjście",
    "back": "Wróć",
    "resurrect": "Odródź",
    "skins": "Skórki",
}

MENU_SPACING = 16


class MenuPanel(Panel):
    """Menu z kontrolera (lista identyfikatorów akcji) z zaznaczoną pozycją."""

    def __init__(self, canvas, pet, shop):
        super().__init__(canvas, MENU_BOX, "Menu")
        self.pet = pet
        self.shop = shop
        self.items = []
        self.selected_idx = 0
        self.scroll = 0   # Pierwsza widoczna pozycja, gdy menu się nie mieści

    def set_items(self, items, selected_idx):
        if items is not self.items:
            self.scroll = 0   # Nowe menu - zaczynamy od początku
        self.items = items
        self.selected_idx = selected_idx

    def hovered_skin(self):
        """Skórka zaznaczona w menu skórek (do podglądu) albo None."""
        if 0 <= self.selected_idx < len(self.items):
            action = self.items[self.selected_idx]
            if action.startswith("skin:"):
                return action[len("skin:"):]
        return None

    def describe_hovered(self):
        """Opis zaznaczonej pozycji (co daje przedmiot / skórka) albo None.
        Zwraca (tekst, nazwa stylu)."""
        if not 0 <= self.selected_idx < len(self.items):
            return None
        action = self.items[self.selected_idx]

        if action.startswith("buy:"):
            item = self.shop.items[action[len("buy:"):]]
            effects = ", ".join(f"{STAT_LABELS.get(stat, stat)} {amount:+g}"
                                for stat, amount in item.effects.items())
            text = f"{item.name} ({item.price}$): {effects or 'nic nie zmienia'}"
            return self._with_missing_money(text, item.price)

        if action.startswith("skin:"):
            skin_id = action[len("skin:"):]
            name = skin_name(skin_id)
            if skin_id == self.pet.active_skin:
                return f"Skorka {name} - zwierzak ma ja na sobie", "info"
            if self.pet.owns_skin(skin_id):
                return f"Skorka {name} - kupiona, Enter zaklada", "info"
            price = self.shop.skin_prices[skin_id]
            return self._with_missing_money(f"Skorka {name} ({price}$): Enter = kup i zaloz", price)

        return None

    def _with_missing_money(self, text, price):
        missing = price - self.pet.money
        if missing > 0:
            return f"{text}  [brakuje {missing}$]", "warn"
        return text, "info"

    # --- RYSOWANIE ---
    def draw_content(self):
        c, s = self.canvas, self.canvas.style
        y, x, _, w = self.box
        inner = w - 4
        labels = [f" {self.label(a)} " for a in self.items]

        if sum(map(len, labels)) <= inner:
            first, last = 0, len(labels)
            xs = self._positions(labels, inner)
        else:
            # Za dużo pozycji - pokazujemy fragment wokół zaznaczonej, ze strzałkami
            first, last = self._visible_range(labels, inner - 4)
            xs, pos = [], 2
            for text in labels[first:last]:
                xs.append(pos)
                pos += len(text) + 1
            if first > 0:
                c.put(y + 1, x + 2, "<", s["hint"])
            if last < len(labels):
                c.put(y + 1, x + 2 + inner - 1, ">", s["hint"])

        for i, pos in zip(range(first, last), xs):
            if i == self.selected_idx:
                attr = s["selected"]
            elif not self.can_afford(self.items[i]):
                attr = s["disabled"]
            else:
                attr = s["text"]
            c.put(y + 1, x + 2 + pos, labels[i], attr)

    @staticmethod
    def _positions(labels, inner):
        """Stały odstęp, a gdy się nie mieści - pozycje ciasno jedna za drugą."""
        if all(i * MENU_SPACING + len(l) <= inner for i, l in enumerate(labels)):
            return [i * MENU_SPACING for i in range(len(labels))]
        gap = max(0, (inner - sum(map(len, labels))) // max(1, len(labels) - 1))
        xs, pos = [], 0
        for l in labels:
            xs.append(pos)
            pos += len(l) + gap
        return xs

    def _visible_range(self, labels, width):
        """Zakres [first, last) pozycji mieszczących się w width, z zaznaczoną w środku.
        Okno przesuwa się dopiero, gdy zaznaczenie wyjdzie poza nie."""
        def fits(a, b):
            return sum(len(l) + 1 for l in labels[a:b]) - 1 <= width

        sel = self.selected_idx
        first = min(self.scroll, sel)
        while first < sel and not fits(first, sel + 1):
            first += 1
        last = first + 1
        while last < len(labels) and fits(first, last + 1):
            last += 1
        self.scroll = first
        return first, last

    # --- NAPISY ---
    def label(self, action):
        if action.startswith("buy:"):
            item = self.shop.items[action[len("buy:"):]]
            return f"{item.name}({item.price}$)"
        if action.startswith("skin:"):
            skin_id = action[len("skin:"):]
            if skin_id == self.pet.active_skin:
                return f"{skin_name(skin_id)}*"   # * = aktualnie założona
            if self.pet.owns_skin(skin_id):
                return skin_name(skin_id)
            return f"{skin_name(skin_id)}({self.shop.skin_prices[skin_id]}$)"
        return ACTION_LABELS.get(action, action)

    def can_afford(self, action):
        if action.startswith("buy:"):
            return self.shop.can_afford(action[len("buy:"):])
        if action.startswith("skin:"):
            return self.shop.can_afford_skin(action[len("skin:"):])
        return True
