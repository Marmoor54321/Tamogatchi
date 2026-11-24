# view/minigame_props.py
"""Definicje tekstowych propsów (rekwizytów) dla minigry typu Chrome Dino.

=============================================================================
JAK ŁATWO ZAMIENIĆ WIDOK TEKSTOWY NA GRAFICZNY (np. Pygame, Arcade, Tkinter):
=============================================================================
Wszystkie elementy gry w warstwie logiki (model/dino_game.py) posługują się
jedynie stałymi identyfikatorami PropType (np. PropType.PLAYER_RUN_1, PropType.CACTUS_LARGE)
oraz współrzędnymi prostokąta kolizji (x, y, width, height).

W tym pliku definiujemy klasę TextProp, która przechowuje znaki ASCII oraz kolor.
Aby w przyszłości przejść na grafikę (np. bibliotekę Pygame):
  1. Tworzysz nową klasę, np. GraphicProp(image_path) ładującą plik PNG:
         class GraphicProp:
             def __init__(self, path):
                 self.surface = pygame.image.load(path).convert_alpha()
  2. Zastępujesz słownik PROPS słownikiem z obiektami GraphicProp:
         PROPS = {
             PropType.PLAYER_RUN_1: GraphicProp("assets/dino_run1.png"),
             PropType.PLAYER_RUN_2: GraphicProp("assets/dino_run2.png"),
             PropType.PLAYER_JUMP:  GraphicProp("assets/dino_jump.png"),
             PropType.PLAYER_CRASH: GraphicProp("assets/dino_crash.png"),
             PropType.CACTUS_SMALL: GraphicProp("assets/cactus_small.png"),
             PropType.CACTUS_LARGE: GraphicProp("assets/cactus_large.png"),
             PropType.ROCK:         GraphicProp("assets/rock.png"),
             PropType.GROUND:       GraphicProp("assets/ground.png"),
             PropType.CLOUD:        GraphicProp("assets/cloud.png"),
         }
  3. W widoku graficznym pętla rysująca zamiast addstr po prostu wywołuje:
         screen.blit(PROPS[entity.prop_id].surface, (entity.x * PIXEL_SCALE, screen_height - (entity.y + entity.height) * PIXEL_SCALE))
Model i Kontroler pozostają w 100% nienaruszone!
"""

from model.dino_game import PropType


class TextProp:
    """Tekstowy rekwizyt w konsoli (ASCII Art + styl/kolor)."""

    def __init__(self, lines: list[str], style: str = "text"):
        self.lines = lines
        self.height = len(lines)
        self.width = max(len(l) for l in lines) if lines else 0
        self.style = style


# Rejestr tekstowych reprezentacji propsów
# (szerokości i wysokości odpowiadają wymiarom logicznym w model/dino_game.py)
PROPS: dict[str, TextProp] = {
    # Postać gracza (nasz zwierzak Reksio w biegu, skoku i po kraksie)
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

    # Przeszkody
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

    # Tło
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
    """Klatka gracza w danej skórce, a gdy jej brak - domyślna z PROPS."""
    return SKIN_PLAYER_PROPS.get(skin_id, {}).get(prop_id) or PROPS.get(prop_id)
