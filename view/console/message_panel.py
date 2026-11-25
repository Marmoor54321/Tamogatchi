from view.console.layout import MESSAGE_BOX
from view.console.panel import Panel

class MessagePanel(Panel):

    def __init__(self, canvas):
        super().__init__(canvas, MESSAGE_BOX, "Komunikat")
        self.text = ""
        self.style_name = "info"
        self.hint = None

    def set(self, text, style_name):
        self.text = text
        self.style_name = style_name
        self.hint = None

    def show_hint(self, hint):
        self.hint = hint

    def draw_content(self):
        y, x, _, w = self.box
        if self.hint:
            text, style_name = f"? {self.hint[0]}", self.hint[1]
        else:
            text, style_name = f"> {self.text}", self.style_name
        self.canvas.put(y + 1, x + 2, text[: w - 4], self.canvas.style[style_name])

