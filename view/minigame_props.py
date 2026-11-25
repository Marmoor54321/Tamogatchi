from model.dino_game import PropType

class TextProp:

    def __init__(self, lines: list[str], style: str = "text"):
        self.lines = lines
        self.height = len(lines)
        self.width = max(len(l) for l in lines) if lines else 0
        self.style = style

PROPS: dict[str, TextProp] = {
    PropType.PLAYER_RUN_1: TextProp(
        lines=[
            " (^o^) ",
            " /| \\  "
        ],
        style="good"
    ),

    PropType.PLAYER_RUN_2: TextProp(
        lines=[
            " (^o^) ",
            "  / |\\ "
        ],
        style="good"
    ),

    PropType.PLAYER_JUMP: TextProp(
        lines=[
            " (^o^) ",
            " <| |> "
        ],
        style="title"
    ),

    PropType.PLAYER_CRASH: TextProp(
        lines=[
            " (X_X) ",
            " /| |\\ "
        ],
        style="bad"
    ),

    PropType.CACTUS_SMALL: TextProp(
        lines=[
            "|#|"
        ],
        style="warn"
    ),

    PropType.CACTUS_LARGE: TextProp(
        lines=[
            " |#| ",
            "|###|"
        ],
        style="warn"
    ),

    PropType.ROCK: TextProp(
        lines=[
            "/=\\"
        ],
        style="warn"
    ),

    PropType.CLOUD: TextProp(
        lines=[
            ".--."
        ],
        style="empty"
    ),

    PropType.GROUND: TextProp(
        lines=[
            "="
        ],
        style="frame"
    ),
}

def _skin_frames(run_1, run_2, jump, crash):
    return {
        PropType.PLAYER_RUN_1: TextProp(run_1, style="good"),
        PropType.PLAYER_RUN_2: TextProp(run_2, style="good"),
        PropType.PLAYER_JUMP: TextProp(jump, style="title"),
        PropType.PLAYER_CRASH: TextProp(crash, style="bad"),
    }

SKIN_PLAYER_PROPS: dict[str, dict[str, TextProp]] = {
    "kotek": _skin_frames(
        run_1=[" /\\_/\\ ","( ^.^ )", "~> ^ < "],
        run_2=[" |\\_|\\ ", "( ^.^ )", "-< ^ > "],
        jump=[" /\\_/\\ ","( ^o^ )", "~> ^ < "],
        crash=[" /\\_/\\ ","( x.x )", "~> ^ < "],
    ),
    "krolik": _skin_frames(
        run_1=["(\\_/) ","(^.^)", '(")(")'],
        run_2=[" )\\_/( "," (^.^)", '("(("( '],
        jump=[")\\_/( ","(^o^)", '(")(")'],
        crash=[" )\\_/( ","(x.x)", '(")(")'],
    ),
    "robot": _skin_frames(
        run_1=[" .-T-. ","[ ^_^ ]", " /|_|\\"],
        run_2=[" .-\\-. ", "[ ^_^ ]", " \\|_|/"],
        jump=[" .-T-. ","[ ^o^ ]", " <|_|>"],
        crash=[" .-T-. ","[ x_x ]", " /|_|\\"],
    ),
}

def get_player_prop(skin_id: str, prop_id: str):
    return SKIN_PLAYER_PROPS.get(skin_id, {}).get(prop_id) or PROPS.get(prop_id)

