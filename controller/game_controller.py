# controller/game_controller.py
import curses


class GameController:
    def __init__(self, model, view):
        self.model = model
        self.view = view

    def run(self):
        while True:
            # 1. Czas mija - update modelu (co 0.5s ze względu na timeout w Widoku)
            self.model.pass_time(0.5)

            # 2. Nasłuchujemy klawiszy
            key = self.view.stdscr.getch()

            # Obsługa strzałek i entera
            if key == curses.KEY_RIGHT:
                self.view.move_menu(1)
            elif key == curses.KEY_LEFT:
                self.view.move_menu(-1)
            elif key in [10, 13]:  # Klawisz ENTER
                action = self.view.get_selected_action()

                # Jeśli zwierzak nie żyje, blokujemy normalne akcje
                if not self.model.is_alive:
                    if action == "Wyjście":
                        self.model.save_state()
                        break
                    else:
                        self.model.resurrect()
                        continue

                # --- LOGIKA MENU GŁÓWNEGO ---
                if self.view.active_menu == self.view.main_menu:
                    if action == "Sklep":
                        self.view.active_menu = self.view.shop_menu
                        self.view.selected_idx = 0
                        self.view.draw_menu()
                    elif action == "Zabawa":
                        self.model.play()
                    elif action == "Śpij":
                        self.model.sleep()
                    elif action == "Wyjście":
                        self.model.save_state()
                        break

                # --- LOGIKA MENU SKLEPU ---
                elif self.view.active_menu == self.view.shop_menu:
                    if action == "Wróć":
                        self.view.active_menu = self.view.main_menu
                        self.view.selected_idx = 0
                        self.view.draw_menu()
                    elif "Jablko" in action:
                        self.model.buy_and_feed("Jablko")
                    elif "Burger" in action:
                        self.model.buy_and_feed("Burger")
                    elif "Kawa" in action:
                        self.model.buy_and_feed("Kawa")