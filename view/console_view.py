# view/console_view.py
import curses
from model.observer import Observer


class ConsoleView(Observer):
    def __init__(self, stdscr, pet):
        self.stdscr = stdscr
        self.pet = pet
        # Podpinamy ten widok jako obserwatora naszego zwierzaka
        self.pet.add_observer(self)

        curses.curs_set(0)  # Ukryj migający kursor konsoli
        self.stdscr.nodelay(True)  # Nie blokuj gry podczas czekania na klawisz
        self.stdscr.timeout(500)  # Odświeżaj pętlę (i czas gry) co 0.5 sekundy

        # Menu
        self.main_menu = ["Sklep", "Zabawa", "Śpij", "Wyjście"]
        self.shop_menu = ["Jablko(10$)", "Burger(30$)", "Kawa(20$)", "Wróć"]

        self.active_menu = self.main_menu  # Zmienna trzymająca aktualnie wyświetlane menu
        self.selected_idx = 0
        self.current_message = "Witaj w Tamagotchi! Uzyj strzalek Lewo/Prawo."

        self.full_redraw()

    # --- METODA Z WZORCA OBSERWATOR ---
    def update(self, event_name, data=None):
        if event_name == "stats_changed":
            self.draw_stats()
            self.draw_art()
        elif event_name.startswith("action_"):
            if event_name == "action_play":
                self.current_message = "Super zabawa! (+Szczescie, -Energia, +40$)"
            elif event_name == "action_sleep":
                self.current_message = "Zzz... (+Energia)"
            elif event_name == "action_buy_success":
                self.current_message = f"Kupiono i zjedzono: {data}!"
            elif event_name == "action_buy_fail":
                self.current_message = f"Za malo kasy na: {data}! Baw sie by zarobic."

            self.draw_stats()  # Kasa lub statystyki mogły się zmienić
            self.draw_message()
            self.draw_art()

        elif event_name == "pet_died":
            self.active_menu = self.main_menu  # Wymuszenie powrotu do głownego menu
            self.selected_idx = 0
            self.current_message = "Zwierzak umarl (X_X). Wcisnij ENTER, by wskrzesic!"
            self.full_redraw()

        elif event_name == "pet_resurrected":
            self.current_message = "Magia! Zwierzak dostal drugie zycie!"
            self.draw_message()
            self.draw_art()

    # --- RYSOWANIE POSZCZEGÓLNYCH SEKCJI ---
    def move_menu(self, direction):
        self.selected_idx = (self.selected_idx + direction) % len(self.active_menu)
        self.draw_menu()

    def draw_menu(self):
        # Czyścimy całą linię menu przed narysowaniem nowego
        self.stdscr.addstr(15, 0, " " * 70)
        for i, option in enumerate(self.active_menu):
            x = 5 + (i * 14)  # Zwiększyłem lekko odstępy, bo nazwy w sklepie są dłuższe
            y = 15
            if i == self.selected_idx:
                self.stdscr.attron(curses.A_REVERSE)
                self.stdscr.addstr(y, x, f" {option} ")
                self.stdscr.attroff(curses.A_REVERSE)
            else:
                self.stdscr.addstr(y, x, f" {option} ")
        self.stdscr.refresh()

    def get_selected_action(self):
        return self.active_menu[self.selected_idx]

    def draw_bar(self, value):
        """Generuje pasek postępu np: [######----] 60%"""
        bars = int(value / 10)
        return "[" + "#" * bars + "-" * (10 - bars) + f"] {value:3}%"

    def draw_stats(self):
        self.stdscr.addstr(0, 2, f" Zwierzak: {self.pet.name} | Kasa: {self.pet.money}$ ")
        self.stdscr.addstr(1, 2, f" Glod:     {self.draw_bar(self.pet.hunger)}")
        self.stdscr.addstr(2, 2, f" Energia:  {self.draw_bar(self.pet.energy)}")
        self.stdscr.addstr(3, 2, f" Szczescie:{self.draw_bar(self.pet.happiness)}")
        self.stdscr.addstr(4, 2, f" Zdrowie:  {self.draw_bar(self.pet.health)}")
        self.stdscr.refresh()

    def draw_art(self):
        """Dynamiczny ASCII Art zależny od statystyk z Modelu"""
        if not self.pet.is_alive:
            art = [" (X_X) ", " /| |\\ "]
        elif self.pet.energy < 30:
            art = [" (-_-)zZ", " /| |\\ "]  # Śpiący
        elif self.pet.happiness < 40:
            art = [" (T_T) ", " /| |\\ "]  # Smutny
        else:
            art = [" (^o^) ", " /| |\\ "]  # Szczęśliwy

        start_y = 8
        for i, line in enumerate(art):
            self.stdscr.addstr(start_y + i, 15, " " * 20)  # Czyść tylko miejsce na obrazek
            self.stdscr.addstr(start_y + i, 15, line)
        self.stdscr.refresh()

    def draw_message(self):
        self.stdscr.addstr(12, 5, " " * 50)  # Czyść tylko linijkę z wiadomością
        self.stdscr.addstr(12, 5, f"> {self.current_message}")
        self.stdscr.refresh()


    def full_redraw(self):
        self.stdscr.clear()
        self.draw_stats()
        self.draw_art()
        self.draw_message()
        self.draw_menu()