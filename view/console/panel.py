class Panel:

    def __init__(self, canvas, box, title):
        self.canvas = canvas
        self.box = box
        self.title = title

    def draw_frame(self):
        self.canvas.draw_box(self.box, self.title)

    def redraw(self):
        if self.canvas.too_small:
            return
        self.canvas.clear_inside(self.box)
        self.draw_content()
        self.canvas.refresh()

    def draw_content(self):
        raise NotImplementedError

