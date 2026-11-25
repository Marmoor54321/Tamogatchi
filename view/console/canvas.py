import curses

def acs(name, fallback):
    return getattr(curses, "ACS_" + name, ord(fallback))

class Canvas:

    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.too_small = False
        self.style = self._init_colors()

    @staticmethod
    def _init_colors():
        normal, bold = curses.A_NORMAL, curses.A_BOLD
        style = {
            "frame": normal, "title": bold, "text": normal, "info": bold,
            "good": bold, "warn": normal, "bad": bold, "money": bold,
            "selected": curses.A_REVERSE, "disabled": normal,
            "hint": normal, "empty": normal, "sleepy": normal,
        }
        try:
            if not curses.has_colors():
                return style
            curses.start_color()
            try:
                curses.use_default_colors()
                bg = -1
            except curses.error:
                bg = curses.COLOR_BLACK

            pairs = {
                "frame": (curses.COLOR_CYAN, bg, normal),
                "title": (curses.COLOR_YELLOW, bg, bold),
                "text": (curses.COLOR_WHITE, bg, normal),
                "info": (curses.COLOR_WHITE, bg, bold),
                "good": (curses.COLOR_GREEN, bg, bold),
                "warn": (curses.COLOR_YELLOW, bg, bold),
                "bad": (curses.COLOR_RED, bg, bold),
                "money": (curses.COLOR_YELLOW, bg, bold),
                "selected": (curses.COLOR_BLACK, curses.COLOR_CYAN, bold),
                "disabled": (curses.COLOR_RED, bg, normal),
                "hint": (curses.COLOR_BLUE, bg, bold),
                "empty": (curses.COLOR_WHITE, bg, normal),
                "sleepy": (curses.COLOR_CYAN, bg, bold),
            }
            for i, (name, (fg, back, extra)) in enumerate(pairs.items(), start=1):
                curses.init_pair(i, fg, back)
                style[name] = curses.color_pair(i) | extra
        except curses.error:
            pass
        return style

    def stat_style(self, value):
        if value >= 60:
            return self.style["good"]
        if value >= 30:
            return self.style["warn"]
        return self.style["bad"]

    def fits(self, min_h, min_w):
        rows, cols = self.stdscr.getmaxyx()
        return rows >= min_h and cols >= min_w

    def erase(self):
        self.stdscr.erase()

    def refresh(self):
        self.stdscr.refresh()

    def put(self, y, x, text, attr=curses.A_NORMAL):
        try:
            self.stdscr.addstr(y, x, text, attr)
        except curses.error:
            pass

    def hline(self, y, x, ch, n):
        if n > 0:
            try:
                self.stdscr.hline(y, x, ch, n)
            except curses.error:
                pass

    def fill(self, y, x, width):
        self.put(y, x, " " * width)

    def clear_inside(self, box):
        y, x, h, w = box
        for row in range(y + 1, y + h - 1):
            self.fill(row, x + 1, w - 2)

    def draw_box(self, box, title):
        y, x, h, w = box
        a = self.style["frame"]
        try:
            self.stdscr.addch(y, x, acs("ULCORNER", "+") | a)
            self.stdscr.addch(y, x + w - 1, acs("URCORNER", "+") | a)
            self.stdscr.addch(y + h - 1, x, acs("LLCORNER", "+") | a)
            self.stdscr.addch(y + h - 1, x + w - 1, acs("LRCORNER", "+") | a)
            self.stdscr.vline(y + 1, x, acs("VLINE", "|") | a, h - 2)
            self.stdscr.vline(y + 1, x + w - 1, acs("VLINE", "|") | a, h - 2)
        except curses.error:
            pass
        self.hline(y, x + 1, acs("HLINE", "-") | a, w - 2)
        self.hline(y + h - 1, x + 1, acs("HLINE", "-") | a, w - 2)
        self.put(y, x + 2, f" {title} ", self.style["title"])

