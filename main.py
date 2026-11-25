import argparse
import curses
import tkinter as tk
from model.pet import Pet
from model.shop import Shop
from view.console_view import ConsoleView
from view.gui_view import GuiView
from controller.game_controller import GameController

def main_app(stdscr):
    pet = Pet("Reksio")
    is_new_game = not pet.load_state()

    shop = Shop(pet)

    view = ConsoleView(stdscr, pet, shop)

    controller = GameController(pet, view, shop, ask_name_on_start=is_new_game)
    controller.run()

def main_gui():
    pet = Pet("Reksio")
    is_new_game = not pet.load_state()
    shop = Shop(pet)

    root = tk.Tk()
    view = GuiView(root, pet, shop)
    controller = GameController(
        pet,
        view,
        shop,
        ask_name_on_start=is_new_game,
        event_driven=True,
    )
    view.set_controller(controller)
    view.run_event_loop()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Tamagotchi (GUI lub tryb tekstowy)")
    parser.add_argument(
        "--console",
        action="store_true",
        help="Uruchom klasyczną wersję tekstową w terminalu (curses)",
    )
    args = parser.parse_args()
    if args.console:
        curses.wrapper(main_app)
    else:
        main_gui()
