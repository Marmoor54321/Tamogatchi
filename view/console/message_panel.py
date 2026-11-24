# view/console/message_panel.py
from view.console.layout import MESSAGE_BOX
from view.console.panel import Panel


class MessagePanel(Panel):
    """Jedna linijka z ostatnim komunikatem dla gracza."""

    def __init__(self, canvas):
        super().__init__(canvas, MESSAGE_BOX, "Komunikat")
        self.text = ""
        self.style_name = "info"

    def set(self, text, style_name):
        self.text = text
        self.style_name = style_name

    def draw_content(self):
        y, x, _, w = self.box
        text = f"> {self.text}"[: w - 4]
        self.canvas.put(y + 1, x + 2, text, self.canvas.style[self.style_name])
