# view/console/pet_panel.py
from view.console.layout import PET_BOX
from view.console.panel import Panel
from view.skin_art import MOODS, render_skin, skin_name


class PetPanel(Panel):
    """Rysunek zwierzaka: założona skórka + nastrój z modelu.

    W sklepie ze skórkami pokazuje podgląd skórki zaznaczonej w menu
    (ConsoleView ustawia wtedy preview_skin).
    """

    def __init__(self, canvas, pet):
        super().__init__(canvas, PET_BOX, pet.name)
        self.pet = pet
        self.preview_skin = None

    def draw_frame(self):
        self.title = self.pet.name
        super().draw_frame()

    def draw_content(self):
        caption, style_name = MOODS[self.pet.mood]
        skin_id = self.pet.active_skin
        if self.preview_skin:
            skin_id, caption = self.preview_skin, f"Podglad: {skin_name(self.preview_skin)}"
        art = render_skin(skin_id, self.pet.mood)

        c, attr = self.canvas, self.canvas.style[style_name]
        y, x, h, w = self.box
        art_x = x + (w - len(art[0])) // 2
        for i, line in enumerate(art):
            c.put(y + 2 + i, art_x, line, attr)
        c.put(y + h - 2, x + (w - len(caption)) // 2, caption, attr)
