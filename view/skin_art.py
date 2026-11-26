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

MOODS = {
    "happy": (MOOD_CAPTIONS["happy"], "good"),
    "sad": (MOOD_CAPTIONS["sad"], "warn"),
    "sleepy": (MOOD_CAPTIONS["sleepy"], "sleepy"),
    "asleep": (MOOD_CAPTIONS["asleep"], "sleepy"),
    "dead": (MOOD_CAPTIONS["dead"], "bad"),
}

def blink_face(face):
    if len(face) < 2:
        return face
    return "-" + face[1:-1] + "-"

ZZ_WIDTH = 3

def render_skin(skin_id, mood, blink=False, zz="zZ"):
    art = SKIN_ART.get(skin_id, SKIN_ART["classic"])
    faces = art["faces"]
    face_mood = "sleepy" if mood == "asleep" else mood
    face = faces.get(face_mood, faces["happy"])
    if blink and mood in ("happy", "sad"):
        face = faces.get("blink") or blink_face(face)
    lines = [line.replace("{f}", face) for line in art["lines"]]
    width = max(len(line) for line in lines)
    lines = [line.center(width) for line in lines]
    if mood in ("sleepy", "asleep"):
        lines = [line + (zz.ljust(ZZ_WIDTH) if "{f}" in src else " " * ZZ_WIDTH)
                 for line, src in zip(lines, art["lines"])]
    return lines
