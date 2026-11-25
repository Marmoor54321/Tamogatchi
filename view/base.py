from model.observer import Observer


class GameView(Observer):
    def show_menu(self, items, selected_idx):
        raise NotImplementedError

    def get_command(self):
        return None

    def render(self, dt=0.0):
        pass

    def ask_pet_name(self, current_name, is_resurrection=False):
        return None

    def start_minigame(self, game):
        raise NotImplementedError

    def get_minigame_command(self):
        return None

    def draw_minigame(self, game):
        raise NotImplementedError

    def show_minigame_game_over(self, game):
        pass

    def end_minigame(self):
        raise NotImplementedError
