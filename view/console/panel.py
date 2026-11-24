# view/console/panel.py


class Panel:
    """Fragment ekranu w ramce. Podklasy implementują tylko draw_content()."""

    def __init__(self, canvas, box, title):
        self.canvas = canvas
        self.box = box
        self.title = title

    def draw_frame(self):
        self.canvas.draw_box(self.box, self.title)

    def redraw(self):
        """Czyści wnętrze panelu i rysuje je od nowa (ramka zostaje)."""
        if self.canvas.too_small:
            return
        self.canvas.clear_inside(self.box)
        self.draw_content()
        self.canvas.refresh()

    def draw_content(self):
        raise NotImplementedError
