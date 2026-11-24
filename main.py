# main.py
import curses
from model.pet import Pet
from model.shop import Shop
from view.console_view import ConsoleView
from controller.game_controller import GameController

def main_app(stdscr):
    # 1. Inicjalizacja modelu
    pet = Pet("Reksio")
    pet.load_state() # Próba wczytania stanu gry z pliku JSON

    shop = Shop(pet)  # Sklep z przedmiotami i skórkami (model/shop.py)

    # 2. Inicjalizacja widoku
    view = ConsoleView(stdscr, pet, shop)

    # 3. Inicjalizacja kontrolera i start głównej pętli
    controller = GameController(pet, view, shop)
    controller.run()

if __name__ == "__main__":
    # wrapper z curses automatycznie przywraca konsolę do normy w razie błędu/wyjścia
    curses.wrapper(main_app)