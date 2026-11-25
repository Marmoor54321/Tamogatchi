# view/console/keys.py
"""Tłumaczenie klawiszy na komendy dla kontrolera

"""
import curses
import sys

MENU_KEYS = {
    curses.KEY_RIGHT: "NEXT",
    curses.KEY_LEFT: "PREV",
    curses.KEY_ENTER: "CONFIRM",
    10: "CONFIRM",   # Enter (LF)
    13: "CONFIRM",   # Enter (CR)
    27: "BACK",      # Esc
    curses.KEY_BACKSPACE: "BACK",
    8: "BACK",       # Backspace (Windows)
    127: "BACK",     # Backspace (Linux)
}

MINIGAME_KEYS = {
    # Skok: Spacja, Strzałka w górę, 'w', 'W', Enter
    **{k: "JUMP" for k in (ord(" "), curses.KEY_UP, ord("w"), ord("W"), 10, 13, curses.KEY_ENTER)},
    # Wyjście: Esc, 'q', 'Q'
    **{k: "QUIT" for k in (27, ord("q"), ord("Q"))},
}

RESIZE = "RESIZE"


def read_key(stdscr):
    """Czyta klawisz. Zmianę rozmiaru okna zwraca jako RESIZE."""
    key = stdscr.getch()
    if key == getattr(curses, "KEY_RESIZE", None):
        if sys.platform == "win32":
            try:
                curses.resize_term(0, 0)  # PDCurses wymaga ręcznego odczytu nowego rozmiaru
            except curses.error:
                pass
        return RESIZE
    return key


def read_text_key(stdscr):
    """Czyta pojedynczy znak lub klawisz sterujący do wpisywania tekstu."""
    try:
        key = stdscr.get_wch() if hasattr(stdscr, "get_wch") else stdscr.getch()
    except curses.error:
        return None

    if key == getattr(curses, "KEY_RESIZE", None):
        if sys.platform == "win32":
            try:
                curses.resize_term(0, 0)
            except curses.error:
                pass
        return RESIZE

    if key in (curses.KEY_ENTER, 10, 13, "\n", "\r"):
        return "CONFIRM"
    if key in (27, "\x1b"):
        return "CANCEL"
    if key in (curses.KEY_BACKSPACE, 8, 127, "\x08", "\x7f", "\b"):
        return "BACKSPACE"
    if key in (3, "\x03"):
        raise KeyboardInterrupt

    if isinstance(key, int):
        return chr(key) if 32 <= key < 127 else None
    if isinstance(key, str) and len(key) == 1 and key.isprintable() and key not in ("\n", "\r", "\t"):
        return key
    return None
