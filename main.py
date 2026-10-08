# main.py
import curses
from model.pet import Pet
from view.console_view import ConsoleView
from controller.game_controller import GameController

def main_app(stdscr):
    # 1. Inicjalizacja modelu
    pet = Pet("Reksio")
    pet.load_state() # Próba wczytania stanu gry z pliku JSON

    # 2. Inicjalizacja widoku
    view = ConsoleView(stdscr, pet)

    # 3. Inicjalizacja kontrolera i start głównej pętli
    controller = GameController(pet, view)
    controller.run()

if __name__ == "__main__":
    # wrapper z curses automatycznie przywraca konsolę do normy w razie błędu/wyjścia
    curses.wrapper(main_app)