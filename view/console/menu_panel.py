# view/console/menu_panel.py
from model.skins import SKIN_PRICES
from view.console.layout import MENU_BOX
from view.console.panel import Panel
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

    def __init__(self, canvas, pet):
        super().__init__(canvas, MENU_BOX, "Menu")
        self.pet = pet
        self.items = []
        self.selected_idx = 0

    def set_items(self, items, selected_idx):
        self.items = items
        self.selected_idx = selected_idx

    def hovered_skin(self):
        """Skórka zaznaczona w menu skórek (do podglądu) albo None."""
        if 0 <= self.selected_idx < len(self.items):
            action = self.items[self.selected_idx]
            if action.startswith("skin:"):
                return action[len("skin:"):]
        return None

    # --- RYSOWANIE ---
    def draw_content(self):
        c, s = self.canvas, self.canvas.style
        y, x, _, w = self.box
        labels = [f" {self.label(a)} " for a in self.items]
        for i, (action, text, pos) in enumerate(zip(self.items, labels, self._positions(labels, w - 4))):
            if i == self.selected_idx:
                attr = s["selected"]
            elif not self.can_afford(action):
                attr = s["disabled"]
            else:
                attr = s["text"]
            c.put(y + 1, x + 2 + pos, text, attr)

    @staticmethod
    def _positions(labels, inner):
        """Stały odstęp, a gdy menu się nie mieści - pozycje ciasno jedna za drugą."""
        if all(i * MENU_SPACING + len(l) <= inner for i, l in enumerate(labels)):
            return [i * MENU_SPACING for i in range(len(labels))]
        gap = max(0, (inner - sum(map(len, labels))) // max(1, len(labels) - 1))
        xs, pos = [], 0
        for l in labels:
            xs.append(pos)
            pos += len(l) + gap
        return xs

    # --- NAPISY ---
    def label(self, action):
        if action.startswith("buy:"):
            name = action[len("buy:"):]
            return f"{name}({self.pet.shop_items[name]['price']}$)"
        if action.startswith("skin:"):
            skin_id = action[len("skin:"):]
            if skin_id == self.pet.active_skin:
                return f"{skin_name(skin_id)}*"   # * = aktualnie założona
            if self.pet.owns_skin(skin_id):
                return skin_name(skin_id)
            return f"{skin_name(skin_id)}({SKIN_PRICES[skin_id]}$)"
        return ACTION_LABELS.get(action, action)

    def can_afford(self, action):
        if action.startswith("buy:"):
            return self.pet.money >= self.pet.shop_items[action[len("buy:"):]]["price"]
        if action.startswith("skin:"):
            skin_id = action[len("skin:"):]
            return self.pet.owns_skin(skin_id) or self.pet.money >= SKIN_PRICES[skin_id]
        return True
