# view/console/stats_panel.py
from view.console.canvas import acs
from view.console.layout import STATS_BOX
from view.console.panel import Panel

BAR_WIDTH = 15
LABEL_WIDTH = 10


class StatsPanel(Panel):
    """Kasa, rekord i paski statystyk zwierzaka."""

    def __init__(self, canvas, pet):
        super().__init__(canvas, STATS_BOX, "Statystyki")
        self.pet = pet

    def draw_content(self):
        c, s = self.canvas, self.canvas.style
        y, x, _, _ = self.box
        cx = x + 2
        c.put(y + 1, cx, "Kasa:", s["text"])
        c.put(y + 1, cx + LABEL_WIDTH, f"{self.pet.money}$", s["money"])
        c.put(y + 2, cx, "Rekord:", s["text"])
        c.put(y + 2, cx + LABEL_WIDTH, f"{self.pet.high_score} pkt", s["good"])
        self._draw_bar(y + 3, cx, "Glod", self.pet.hunger)
        self._draw_bar(y + 4, cx, "Energia", self.pet.energy)
        self._draw_bar(y + 5, cx, "Szczescie", self.pet.happiness)
        self._draw_bar(y + 6, cx, "Zdrowie", self.pet.health)

    def _draw_bar(self, y, x, label, value):
        """Rysuje np.:  Energia   ██████████▒▒▒▒▒  67%  (kolor zależny od wartości)"""
        c = self.canvas
        value = round(value)
        filled = round(value * BAR_WIDTH / 100)
        c.put(y, x, label.ljust(LABEL_WIDTH), c.style["text"])
        bar_x = x + LABEL_WIDTH
        c.hline(y, bar_x, acs("BLOCK", "#") | c.stat_style(value), filled)
        c.hline(y, bar_x + filled, acs("CKBOARD", "-") | c.style["empty"], BAR_WIDTH - filled)
        c.put(y, bar_x + BAR_WIDTH, f"{value:4}%", c.stat_style(value))
