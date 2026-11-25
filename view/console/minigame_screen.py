import curses

from view.console.canvas import acs
from view.console.layout import SCREEN_H, SCREEN_W, TOO_SMALL
from view.minigame_props import PROPS, get_player_prop

GROUND_ROW = 10
TOP_ROW = 3
HINT = "Spacja / Strzalka w gore: SKOK       Esc / q: WYJSCIE"

class MinigameScreen:

    def __init__(self, canvas, pet):
        self.canvas = canvas
        self.pet = pet

    def draw(self, game):
        c, s = self.canvas, self.canvas.style
        c.erase()
        if not c.fits(SCREEN_H, SCREEN_W):
            c.put(0, 0, TOO_SMALL, s["bad"])
            c.refresh()
            return

        c.draw_box((0, 0, SCREEN_H, SCREEN_W), "Mini-gra: Zabawa (Chrome Dino)")

        status = f"Wynik: {game.score}    Rekord: {game.high_score}    Zdobyte monety: +{game.money_earned}$"
        c.put(1, 3, status, s["title"])
        c.hline(2, 1, acs("HLINE", "-") | s["frame"], SCREEN_W - 2)

        for cloud in game.clouds:
            self._draw_prop(PROPS.get(cloud.prop_id), cloud)

        c.hline(GROUND_ROW, 1, acs("HLINE", "=") | s["frame"], SCREEN_W - 2)

        for obs in game.obstacles:
            self._draw_prop(PROPS.get(obs.prop_id), obs)

        player = game.get_player_entity()
        self._draw_prop(get_player_prop(self.pet.active_skin, player.prop_id), player)

        c.hline(12, 1, acs("HLINE", "-") | s["frame"], SCREEN_W - 2)
        c.put(13, 3, HINT, s["hint"])
        c.refresh()

    def _draw_prop(self, prop, entity):
        if not prop:
            return
        c = self.canvas
        attr = c.style.get(prop.style, c.style["text"])
        base_x = 2 + round(entity.x)
        top_row = GROUND_ROW - 1 - round(entity.y) - prop.height + 1

        for i, line in enumerate(prop.lines):
            row = top_row + i
            if TOP_ROW <= row <= GROUND_ROW - 1:
                for col_idx, ch in enumerate(line):
                    col = base_x + col_idx
                    if 1 < col < SCREEN_W - 1 and ch != " ":
                        c.put(row, col, ch, attr)

    def draw_game_over(self, game):
        self.draw(game)
        c, s = self.canvas, self.canvas.style

        box_w, box_h = 48, 9
        box_y = (SCREEN_H - box_h) // 2
        box_x = (SCREEN_W - box_w) // 2
        box = (box_y, box_x, box_h, box_w)
        c.draw_box(box, "KONIEC GRY!")
        c.clear_inside(box)

        c.put(box_y + 2, box_x + 4, f"Przeskoczone przeszkody: {game.score}", s["info"])
        c.put(box_y + 3, box_x + 4, f"Zdobyte monety:          +{game.money_earned}$",
              s["good"] if game.money_earned > 0 else s["text"])
        c.put(box_y + 4, box_x + 4, f"Najlepszy wynik (Rekord): {game.high_score}", s["title"])
        if game.is_new_high_score and game.score > 0:
            c.put(box_y + 5, box_x + 4, "*** NOWY REKORD! GRATULACJE! ***", s["good"])
        c.put(box_y + 7, box_x + 4, "Nacisnij dowolny klawisz, aby wrocic...", s["hint"])
        c.refresh()

