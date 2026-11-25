# view/skin_art.py
"""Wygląd skórek zwierzaka w wersji tekstowej (ASCII).
"""
from view.common import MOOD_CAPTIONS, SKIN_NAMES, skin_name

SKIN_ART = {
    "classic": {
        "name": SKIN_NAMES["classic"],
        "lines": ["({f})", "/| |\\"],
        "faces": {"happy": "^o^", "sad": "T_T", "sleepy": "-_-", "dead": "X_X"},
    },
    "kotek": {
        "name": SKIN_NAMES["kotek"],
        "lines": [" /\\_/\\ ", "( {f} )", " > ^ < "],
        "faces": {"happy": "^.^", "sad": "T.T", "sleepy": "-.-", "dead": "x.x"},
    },
    "krolik": {
        "name": SKIN_NAMES["krolik"],
        "lines": [" (\\_/) ", " ({f}) ", '(")(")'],
        "faces": {"happy": "^.^", "sad": "T.T", "sleepy": "-.-", "dead": "x.x"},
    },
    "robot": {
        "name": SKIN_NAMES["robot"],
        "lines": [" .-T-. ", "[ {f} ]", " /|_|\\ "],
        "faces": {"happy": "^_^", "sad": ";_;", "sleepy": "-_-", "dead": "x_x"},
    },
}

# Nastrój z modelu -> (podpis, nazwa stylu kolorów)
MOODS = {
    "happy": (MOOD_CAPTIONS["happy"], "good"),
    "sad": (MOOD_CAPTIONS["sad"], "warn"),
    "sleepy": (MOOD_CAPTIONS["sleepy"], "sleepy"),
    "asleep": (MOOD_CAPTIONS["asleep"], "sleepy"),
    "dead": (MOOD_CAPTIONS["dead"], "bad"),
}


def render_skin(skin_id, mood):
    """Zwraca linie rysunku o równej szerokości (łatwo je wyśrodkować jako blok)."""
    art = SKIN_ART.get(skin_id, SKIN_ART["classic"])
    if mood == "asleep":
        mood = "sleepy"   # Śpi - zamknięte oczy i "zZ" jak u śpiącego
    face = art["faces"].get(mood, art["faces"]["happy"])
    lines = [line.replace("{f}", face) for line in art["lines"]]
    width = max(len(line) for line in lines)
    lines = [line.center(width) for line in lines]
    if mood == "sleepy":
        lines = [line + ("zZ" if "{f}" in src else "  ") for line, src in zip(lines, art["lines"])]
    return lines
