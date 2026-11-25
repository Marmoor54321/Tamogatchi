import tkinter as tk
from model.shop import Shop
from view.base import GameView
from view.common import DIED_WHILE_AWAY, WELCOME, message_for
from view.gui import theme
from view.gui.dialogs import GameOverDialog, NameDialog
from view.gui.menu_panel import MenuPanel
from view.gui.message_panel import MessagePanel
from view.gui.minigame_panel import MinigamePanel
from view.gui.pet_panel import PetPanel
from view.gui.stats_panel import StatsPanel

GUI_TICK_MS = 16

_STATS_FIELDS = frozenset({"hunger", "energy", "happiness", "health", "money", "high_score"})
_PET_FIELDS = frozenset({"mood", "active_skin", "is_sleeping", "is_alive"})
_MENU_FIELDS = frozenset({"money", "can_play", "is_alive", "is_sleeping"})

class GuiView(GameView):

    def __init__(self, root: tk.Tk, pet, shop=None, controller=None, tick_ms: int = GUI_TICK_MS):
        self.root = root
        self.pet = pet
        self.shop = shop or Shop(pet)
        self.controller = controller
        self.tick_ms = tick_ms

        self.in_minigame = False
        self._modal_open = False
        self._after_id = None
        self._closing = False

        self.pet.add_observer(self)

        self.root.title(f"Tamogatchi — {self.pet.name}")
        self.root.configure(bg=theme.BG_APP)
        self.root.minsize(780, 560)

        self.main_container = tk.Frame(self.root, bg=theme.BG_APP, padx=16, pady=14)
        self.main_container.pack(fill="both", expand=True)

        title_bar = tk.Frame(self.main_container, bg=theme.BG_APP)
        title_bar.pack(fill="x", pady=(0, 10))
        self.app_title_label = tk.Label(
            title_bar,
            text="🐾 Tamogatchi",
            font=("Segoe UI", 16, "bold"),
            bg=theme.BG_APP,
            fg=theme.TEXT_PRIMARY,
        )
        self.app_title_label.pack(side="left")

        top_grid = tk.Frame(self.main_container, bg=theme.BG_APP)
        top_grid.pack(fill="both", expand=True, pady=(0, 10))
        top_grid.columnconfigure(0, weight=1, uniform="top")
        top_grid.columnconfigure(1, weight=1, uniform="top")
        top_grid.rowconfigure(0, weight=1)

        self.stats = StatsPanel(top_grid, self.pet)
        self.stats.grid(row=0, column=0, sticky="nsew", padx=(0, 6))

        self.pet_panel = PetPanel(top_grid, self.pet)
        self.pet_panel.grid(row=0, column=1, sticky="nsew", padx=(6, 0))

        self.message = MessagePanel(self.main_container)
        self.message.pack(fill="x", pady=(0, 10))

        self.menu = MenuPanel(
            self.main_container,
            self.pet,
            self.shop,
            on_hover=self._on_menu_hover,
            on_select=self._on_menu_select,
        )
        self.menu.pack(fill="x")

        self.minigame_panel = MinigamePanel(
            self.root,
            self.pet,
            on_jump=lambda: self._handle_minigame_input("JUMP"),
            on_quit=lambda: self._handle_minigame_input("QUIT"),
        )

        self.message.set(*(WELCOME if self.pet.is_alive else DIED_WHILE_AWAY))
        self.message.redraw(force=True)

        self._bind_events()
        self.root.protocol("WM_DELETE_WINDOW", self._on_window_close)

    def set_controller(self, controller):
        self.controller = controller

    def _bind_events(self):
        self.root.bind("<Left>", lambda _e: self._on_key_menu("PREV"))
        self.root.bind("<Up>", lambda _e: self._on_key_up())
        self.root.bind("<Right>", lambda _e: self._on_key_menu("NEXT"))
        self.root.bind("<Down>", lambda _e: self._on_key_menu("NEXT"))
        self.root.bind("<Return>", lambda _e: self._on_key_confirm())
        self.root.bind("<space>", lambda _e: self._on_key_space())
        self.root.bind("<Escape>", lambda _e: self._on_key_escape())
        self.root.bind("<BackSpace>", lambda _e: self._on_key_menu("BACK"))
        self.root.bind("<KeyPress-w>", lambda _e: self._on_minigame_key("JUMP"))
        self.root.bind("<KeyPress-W>", lambda _e: self._on_minigame_key("JUMP"))
        self.root.bind("<KeyPress-q>", lambda _e: self._on_minigame_key("QUIT"))
        self.root.bind("<KeyPress-Q>", lambda _e: self._on_minigame_key("QUIT"))

    def _on_key_menu(self, cmd: str):
        if self._modal_open or self.in_minigame or self.controller is None:
            return
        self.controller.handle_command(cmd)

    def _on_key_up(self):
        if self._modal_open or self.controller is None:
            return
        if self.in_minigame:
            self._handle_minigame_input("JUMP")
        else:
            self.controller.handle_command("PREV")

    def _on_key_confirm(self):
        if self._modal_open or self.controller is None:
            return
        if self.in_minigame:
            self._handle_minigame_input("JUMP")
        else:
            self.controller.handle_command("CONFIRM")

    def _on_key_space(self):
        if self._modal_open or self.controller is None:
            return
        if self.in_minigame:
            self._handle_minigame_input("JUMP")
        else:
            self.controller.handle_command("CONFIRM")

    def _on_key_escape(self):
        if self._modal_open or self.controller is None:
            return
        if self.in_minigame:
            self._handle_minigame_input("QUIT")
        else:
            self.controller.handle_command("BACK")

    def _on_minigame_key(self, cmd: str):
        if self._modal_open or not self.in_minigame:
            return
        self._handle_minigame_input(cmd)

    def _on_menu_hover(self, idx: int):
        if self._modal_open or self.in_minigame or self.controller is None:
            return
        self.controller.handle_command(("HOVER", idx))

    def _on_menu_select(self, idx: int):
        if self._modal_open or self.in_minigame or self.controller is None:
            return
        self.controller.handle_command(("SELECT", idx))

    def _handle_minigame_input(self, cmd: str):
        if not self.in_minigame or self.controller is None:
            return
        if not self.controller.handle_minigame_command(cmd):
            self.controller.finish_minigame_session(aborted=True)

    def run_event_loop(self):
        if self.controller is None:
            raise RuntimeError("GuiView wymaga przypisanego kontrolera przed startem pętli.")
        self._center_root(880, 610)
        self.root.after(20, self._start_session)
        try:
            self.root.mainloop()
        finally:
            self._cancel_after()
            if self.controller.running:
                self.controller.finish()

    def _start_session(self):
        if self._closing:
            return
        self._modal_open = True
        try:
            self.controller.start()
        finally:
            self._modal_open = False
        self._schedule_next_tick()

    def _schedule_next_tick(self):
        if not self._closing and self.controller and self.controller.running:
            self._after_id = self.root.after(self.tick_ms, self._tick_step)

    def _tick_step(self):
        self._after_id = None
        if self._closing or self.controller is None:
            return
        if not self._modal_open:
            still_running = self.controller.step()
            if not still_running:
                self._shutdown()
                return
        self._schedule_next_tick()

    def _cancel_after(self):
        if self._after_id is not None:
            try:
                self.root.after_cancel(self._after_id)
            except tk.TclError:
                pass
            self._after_id = None

    def _on_window_close(self):
        if self.controller is not None:
            self.controller.request_exit()
        self._shutdown()

    def _shutdown(self):
        if self._closing:
            return
        self._closing = True
        self._cancel_after()
        if self.controller is not None:
            self.controller.finish()
        try:
            self.root.destroy()
        except tk.TclError:
            pass

    def _center_root(self, width: int, height: int):
        self.root.update_idletasks()
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = max(0, (sw - width) // 2)
        y = max(0, (sh - height) // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def show_menu(self, items, selected_idx):
        self.menu.set_items(items, selected_idx)
        self.pet_panel.preview_skin = self.menu.hovered_skin()
        self.message.show_hint(self.menu.describe_hovered())
        if self.in_minigame:
            return
        self.menu.redraw()
        self.pet_panel.redraw()
        self.message.redraw()

    def render(self, dt=0.0):
        if self.in_minigame or self._closing:
            return
        self.stats.animate(dt)
        self.pet_panel.animate(dt)

    def ask_pet_name(self, current_name, is_resurrection=False):
        self._modal_open = True
        try:
            dlg = NameDialog(self.root, current_name, is_resurrection=is_resurrection)
            self.root.wait_window(dlg)
            return dlg.result
        finally:
            self._modal_open = False

    def update(self, event_name, data=None):
        msg = message_for(event_name, data, shop=self.shop)
        if msg:
            self.message.set(*msg)

        if self.in_minigame:
            return

        if event_name == "stats_changed":
            changed = data.get("rounded") if isinstance(data, dict) else None
            if changed is not None and not changed:
                return
            if changed is None or changed & _STATS_FIELDS:
                self.stats.redraw(changed_fields=changed)
            if changed is None or changed & _PET_FIELDS:
                self.pet_panel.redraw()
            if changed is None or changed & _MENU_FIELDS:
                self.menu.redraw()
            if self.message.hint and (changed is None or changed & _MENU_FIELDS):
                self.message.show_hint(self.menu.describe_hovered())
                self.message.redraw()
            elif msg:
                self.message.redraw()
        elif event_name == "pet_died":
            self.stats.redraw()
            self.pet_panel.redraw()
            self.message.redraw()
            self.menu.redraw()
        elif event_name == "pet_resurrected":
            self.pet_panel.trigger_reaction("resurrect")
            self.pet_panel.redraw()
            self.message.redraw()
            self.menu.redraw()
        elif event_name == "pet_renamed":
            self.root.title(f"Tamogatchi — {self.pet.name}")
            self.pet_panel.redraw()
            self.message.redraw()
        elif event_name.startswith("action_"):
            if event_name == "action_feed":
                self.pet_panel.trigger_reaction("feed")
            self.stats.redraw()
            self.message.redraw()
            self.pet_panel.redraw()
            self.menu.redraw()

    def start_minigame(self, game):
        self.in_minigame = True
        self.main_container.pack_forget()
        self.minigame_panel.pack(fill="both", expand=True, padx=16, pady=14)
        self.minigame_panel.reset_scene()
        self.minigame_panel.draw(game)

    def draw_minigame(self, game):
        if self.in_minigame:
            self.minigame_panel.draw(game)

    def show_minigame_game_over(self, game):
        self._modal_open = True
        try:
            dlg = GameOverDialog(self.root, game)
            self.root.wait_window(dlg)
            return None
        finally:
            self._modal_open = False

    def end_minigame(self):
        self.in_minigame = False
        self.minigame_panel.pack_forget()
        self.main_container.pack(fill="both", expand=True)
        self.stats.redraw(force=True)
        self.pet_panel.redraw(force=True)
        self.message.redraw(force=True)
        self.menu.redraw(force=True)

