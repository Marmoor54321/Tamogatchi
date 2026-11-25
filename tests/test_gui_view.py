import os
import tempfile
import tkinter as tk
import unittest
from unittest import mock

import main
from controller.game_controller import GameController
from model.dino_game import DinoGame, PropType
from model.pet import Pet
from model.skins import SKIN_PRICES
from view.gui import theme
from view.gui.minigame_panel import MinigamePanel
from view.gui.pet_sprites import draw_minigame_entity
from view.gui_view import GuiView

class RecordingCanvas:

    def __init__(self):
        self.calls = []

    def _record(self, kind, coords):
        self.calls.append((kind, list(coords)))

    def create_oval(self, *coords, **_kw):
        self._record("oval", coords)

    def create_rectangle(self, *coords, **_kw):
        self._record("rect", coords)

    def create_polygon(self, *coords, **_kw):
        self._record("poly", coords)

    def create_line(self, *coords, **_kw):
        self._record("line", coords)

    def create_arc(self, *coords, **_kw):
        self._record("arc", coords)

class TkTestBase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.pet = Pet("Reksio")
        self.pet.save_file = os.path.join(self._tmp.name, "save.json")
        self.root = tk.Tk()
        self.root.withdraw()
        self.view = GuiView(self.root, self.pet)
        self.ctrl = GameController(self.pet, self.view, event_driven=True)
        self.view.set_controller(self.ctrl)

    def tearDown(self):
        try:
            self.view._cancel_after()
            self.root.destroy()
        except tk.TclError:
            pass
        self._tmp.cleanup()

class RedButtonsTest(TkTestBase):
    def test_exit_and_back_buttons_are_red_in_all_menus(self):
        self.ctrl.start()
        menus = [
            self.ctrl.main_menu,
            self.ctrl.shop_menu,
            self.ctrl.skins_menu,
            self.ctrl.sleep_menu,
            self.ctrl.death_menu,
        ]
        red_colors = {theme.BTN_RED_BG, theme.BTN_RED_SELECTED_BG}

        for menu_items in menus:
            for selected_idx, action in enumerate(menu_items):
                if action in ("exit", "back"):
                    self.view.show_menu(menu_items, selected_idx)
                    btn = self.view.menu._buttons[selected_idx]
                    self.assertIn(btn.cget("bg"), red_colors, (menu_items, action))
                if action in ("exit", "back") and len(menu_items) > 1:
                    other_idx = 0 if selected_idx != 0 else 1
                    self.view.show_menu(menu_items, other_idx)
                    btn = self.view.menu._buttons[selected_idx]
                    self.assertEqual(btn.cget("bg"), theme.BTN_RED_BG, (menu_items, action))

    def test_minigame_back_button_is_red(self):
        self.assertEqual(self.view.minigame_panel.back_button.cget("bg"), theme.BTN_RED_BG)

class MinigameSizingAndHitboxTest(unittest.TestCase):
    def test_player_and_obstacle_dimensions_match_hitbox_proportions(self):
        game = DinoGame(track_width=58)
        player = game.get_player_entity()
        x1, y1, x2, y2 = MinigamePanel.entity_bbox(player, game.track_width)
        pw = x2 - x1
        ph = y2 - y1

        self.assertGreater(pw, 70)
        self.assertGreater(ph, 65)
        self.assertAlmostEqual(ph / pw, (game.player_height * 2.0) / game.player_width, places=4)

        from model.dino_game import Obstacle
        cactus = Obstacle(PropType.CACTUS_LARGE, 20, 0, 4, 2)
        cx1, cy1, cx2, cy2 = MinigamePanel.entity_bbox(cactus, game.track_width)
        self.assertAlmostEqual(cx2 - cx1, cy2 - cy1, delta=1.0)
        self.assertGreater(ph, cy2 - cy1)

    def test_all_skin_sprites_and_obstacles_stay_inside_hitbox_bounds(self):
        canvas = RecordingCanvas()
        x1, y1, x2, y2 = 100.0, 120.0, 195.0, 201.0
        player_props = [
            PropType.PLAYER_RUN_1,
            PropType.PLAYER_RUN_2,
            PropType.PLAYER_JUMP,
            PropType.PLAYER_CRASH,
        ]
        for skin_id in SKIN_PRICES:
            for prop_id in player_props:
                canvas.calls.clear()
                draw_minigame_entity(canvas, prop_id, x1, y1, x2, y2, skin_id=skin_id)
                self.assertTrue(canvas.calls, (skin_id, prop_id))
                for kind, coords in canvas.calls:
                    xs = coords[0::2]
                    ys = coords[1::2]
                    for x in xs:
                        self.assertGreaterEqual(x, x1 - 0.01, (skin_id, prop_id, kind))
                        self.assertLessEqual(x, x2 + 0.01, (skin_id, prop_id, kind))
                    for y in ys:
                        self.assertGreaterEqual(y, y1 - 0.01, (skin_id, prop_id, kind))
                        self.assertLessEqual(y, y2 + 0.01, (skin_id, prop_id, kind))

class SmartRefreshGuiTest(TkTestBase):
    def test_skips_redraw_when_rounded_stats_unchanged(self):
        self.ctrl.start()
        with mock.patch.object(self.view.stats, "redraw", wraps=self.view.stats.redraw) as s_spy, \
             mock.patch.object(self.view.pet_panel, "redraw", wraps=self.view.pet_panel.redraw) as p_spy, \
             mock.patch.object(self.view.menu, "redraw", wraps=self.view.menu.redraw) as m_spy:
            self.pet.pass_time(0.01)
            self.assertEqual((s_spy.call_count, p_spy.call_count, m_spy.call_count), (0, 0, 0))

            self.pet.pass_time(5.0)
            self.assertEqual(s_spy.call_count, 1)
            self.assertEqual(p_spy.call_count, 0)
            self.assertEqual(m_spy.call_count, 0)

    def test_menu_reuses_buttons_when_hovering_within_same_menu(self):
        self.ctrl.start()
        initial_buttons = list(self.view.menu._buttons)
        self.ctrl.handle_command(("HOVER", 1))
        self.assertEqual(self.view.menu._buttons, initial_buttons)
        self.assertEqual(self.ctrl.selected_idx, 1)

class GuiControllerIntegrationTest(TkTestBase):
    def test_mouse_shop_skins_and_minigame_quit_flow(self):
        self.ctrl.start()
        self.pet.money = 200
        self.ctrl.handle_command(("EXECUTE", "shop"))
        self.assertIs(self.ctrl.menu, self.ctrl.shop_menu)

        self.ctrl.handle_command(("EXECUTE", "buy:jablko"))
        self.assertEqual(self.pet.money, 190)

        self.ctrl.handle_command(("EXECUTE", "skins"))
        self.assertIs(self.ctrl.menu, self.ctrl.skins_menu)

        self.ctrl.handle_command(("EXECUTE", "back"))
        self.assertIs(self.ctrl.menu, self.ctrl.shop_menu)

        self.ctrl.handle_command(("EXECUTE", "back"))
        self.assertIs(self.ctrl.menu, self.ctrl.main_menu)

        self.ctrl.handle_command(("EXECUTE", "play"))
        self.assertTrue(self.view.in_minigame)
        self.assertIsNotNone(self.ctrl.active_minigame)

        self.view._handle_minigame_input("JUMP")
        self.ctrl.step()
        self.assertGreater(self.ctrl.active_minigame.player_y, 0.0)

        self.view._handle_minigame_input("QUIT")
        self.assertFalse(self.view.in_minigame)
        self.assertIsNone(self.ctrl.active_minigame)

    def test_header_title_hints_and_pet_click_reaction(self):
        self.ctrl.start()
        self.assertEqual(self.view.app_title_label.cget("text"), "🐾 Tamogatchi")
        self.assertIn("Tamogatchi", self.root.title())
        self.assertNotIn("mysz", self.view.menu.hint_label.cget("text").lower())

        x1, y1, x2, y2 = self.view.pet_panel._pet_bounds()
        cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
        event = type("ClickEvent", (), {"x": cx, "y": cy})()
        self.view.pet_panel._on_canvas_click(event)

        self.assertGreater(self.view.pet_panel._wiggle_time, 0.0)
        self.assertEqual(len(self.view.pet_panel._particles), 1)
        self.view.pet_panel.animate(0.05)
        self.assertNotEqual(self.view.pet_panel._wiggle_offset, 0.0)

        for _ in range(25):
            self.view.pet_panel.animate(0.03)
        self.assertEqual(self.view.pet_panel._wiggle_offset, 0.0)

    def test_pet_panel_keeps_identical_size_across_all_menus(self):
        self.root.deiconify()
        self.root.geometry("880x610")
        self.ctrl.start()
        self.root.update()

        base_panel_size = (self.view.pet_panel.winfo_width(), self.view.pet_panel.winfo_height())
        base_canvas_size = (
            self.view.pet_panel.canvas.winfo_width(),
            self.view.pet_panel.canvas.winfo_height(),
        )

        for menu in (
            self.ctrl.shop_menu,
            self.ctrl.skins_menu,
            self.ctrl.sleep_menu,
            self.ctrl.death_menu,
            self.ctrl.main_menu,
        ):
            self.view.show_menu(menu, 0)
            self.root.update()
            self.assertEqual(
                (self.view.pet_panel.winfo_width(), self.view.pet_panel.winfo_height()),
                base_panel_size,
                menu,
            )
            self.assertEqual(
                (self.view.pet_panel.canvas.winfo_width(), self.view.pet_panel.canvas.winfo_height()),
                base_canvas_size,
                menu,
            )

    def test_main_gui_wires_event_driven_controller(self):
        with mock.patch("main.Pet") as mock_pet_cls, \
             mock.patch("main.Shop"), \
             mock.patch("main.tk.Tk"), \
             mock.patch("main.GuiView") as mock_view_cls, \
             mock.patch("main.GameController") as mock_ctrl_cls:
            mock_pet_cls.return_value.load_state.return_value = True
            main.main_gui()
            self.assertTrue(mock_ctrl_cls.call_args.kwargs["event_driven"])
            self.assertFalse(mock_ctrl_cls.call_args.kwargs["ask_name_on_start"])
            mock_view_cls.return_value.set_controller.assert_called_once()
            mock_view_cls.return_value.run_event_loop.assert_called_once()

if __name__ == "__main__":
    unittest.main()

