from model.pet import Pet
from view.console.keys import RESIZE, read_text_key
from view.console.layout import SCREEN_H, SCREEN_W


class NameDialog:
    BOX_W = 52
    BOX_H = 9

    def __init__(self, canvas):
        self.canvas = canvas

    def draw(self, text, default_name, is_resurrection=False):
        c, s = self.canvas, self.canvas.style
        if c.too_small or not c.fits(SCREEN_H, SCREEN_W):
            return

        box_y = (SCREEN_H - self.BOX_H) // 2
        box_x = (SCREEN_W - self.BOX_W) // 2
        box = (box_y, box_x, self.BOX_H, self.BOX_W)

        title = "Odrodzenie zwierzaka" if is_resurrection else "Nowy zwierzak"
        prompt = (
            "Nadaj nowe imie odrodzonemu zwierzakowi:"
            if is_resurrection
            else "Jak chcesz nazwac swojego zwierzaka?"
        )

        c.draw_box(box, title)
        c.clear_inside(box)

        c.put(box_y + 2, box_x + 3, prompt, s["info"])
        field = f"{text}_".ljust(Pet.MAX_NAME_LENGTH + 1)
        c.put(box_y + 4, box_x + 3, "Imie: ", s["text"])
        c.put(box_y + 4, box_x + 9, f"[{field}]", s["selected"])
        c.put(box_y + 5, box_x + 3, f"(puste = zostaje '{default_name}')", s["text"])
        c.put(box_y + 7, box_x + 3, "Enter zatwierdz    Esc pomin", s["hint"])
        c.refresh()

    def run(self, stdscr, default_name, is_resurrection=False, redraw_bg=None):
        text = ""
        while True:
            self.draw(text, default_name, is_resurrection=is_resurrection)
            key = read_text_key(stdscr)
            if key == RESIZE:
                if redraw_bg:
                    redraw_bg()
            elif key == "CONFIRM":
                return text.strip()
            elif key == "CANCEL":
                return None
            elif key == "BACKSPACE":
                text = text[:-1]
            elif key is not None and len(text) < Pet.MAX_NAME_LENGTH:
                text += key
