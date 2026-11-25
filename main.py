import curses
from model.pet import Pet
from model.shop import Shop
from view.console_view import ConsoleView
from controller.game_controller import GameController

def main_app(stdscr):
    pet = Pet("Reksio")
    is_new_game = not pet.load_state() # Wczytanie z pliku

    shop = Shop(pet)

    view = ConsoleView(stdscr, pet, shop)

    controller = GameController(pet, view, shop, ask_name_on_start=is_new_game)
    controller.run()

if __name__ == "__main__":
    # wrapper z curses automatycznie przywraca konsolę do normy w razie błędu/wyjścia
    curses.wrapper(main_app)