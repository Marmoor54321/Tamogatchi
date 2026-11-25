# view/skin_art.py
"""Wygląd skórek zwierzaka w wersji tekstowej (ASCII).
"""

SKIN_ART = {
    "classic": {
        "name": "Klasyczny",
        "lines": ["({f})", "/| |\\"],
        "faces": {"happy": "^o^", "sad": "T_T", "sleepy": "-_-", "dead": "X_X"},
    },
    "kotek": {
        "name": "Kotek",
        "lines": [" /\\_/\\ ", "( {f} )", " > ^ < "],
        "faces": {"happy": "^.^", "sad": "T.T", "sleepy": "-.-", "dead": "x.x"},
    },
    "krolik": {
        "name": "Krolik",
        "lines": [" (\\_/) ", " ({f}) ", '(")(")'],
        "faces": {"happy": "^.^", "sad": "T.T", "sleepy": "-.-", "dead": "x.x"},
    },
    "robot": {
        "name": "Robot",
        "lines": [" .-T-. ", "[ {f} ]", " /|_|\\ "],
        "faces": {"happy": "^_^", "sad": ";_;", "sleepy": "-_-", "dead": "x_x"},
    },
}

# Nastrój z modelu -> (podpis, nazwa stylu kolorów)
MOODS = {
    "happy": ("Szczesliwy", "good"),
    "sad": ("Smutny", "warn"),
    "sleepy": ("Spiacy", "sleepy"),
    "asleep": ("Spi... +1 energii / 2 s", "sleepy"),
    "dead": ("Nie zyje", "bad"),
}


def skin_name(skin_id):
    return SKIN_ART.get(skin_id, {}).get("name", skin_id)


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
