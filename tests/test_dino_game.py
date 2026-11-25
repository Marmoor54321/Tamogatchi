# test_dino_game.py
"""Testy jednostkowe dla minigry Dino oraz integracji z modelem Pet."""
import os
import unittest
from model.dino_game import DinoGame, PropType, Entity, Obstacle
from model.pet import Pet
from view.minigame_props import PROPS


class TestDinoGame(unittest.TestCase):

    def test_jump_physics(self):
        """Sprawdza, czy skok unosi gracza i po pewnym czasie gracz bezpiecznie ląduje na ziemi."""
        game = DinoGame(track_width=60, high_score=5)
        self.assertEqual(game.player_y, 0.0)
        self.assertFalse(game.is_jumping)

        # Skok
        game.jump()
        self.assertTrue(game.is_jumping)

        # Po 0.2s gracz powinien być w powietrzu
        game.update(0.2)
        self.assertGreater(game.player_y, 0.5)

        # Po kolejnych krokach czasowych gracz powinien opaść na ziemię (y=0)
        for _ in range(20):
            game.update(0.1)

        self.assertEqual(game.player_y, 0.0)
        self.assertFalse(game.is_jumping)

    def test_obstacle_scoring_and_money(self):
        """Sprawdza naliczanie punktów i monet (10$ za przeszkodę) po minięciu gracza."""
        game = DinoGame(track_width=60, high_score=2)
        # Tworzymy przeszkodę tuż przed graczem (player_x = 6.0)
        obs = Obstacle(PropType.CACTUS_SMALL, x=8.0, y=0.0, width=3, height=1)
        game.obstacles.append(obs)

        # Gracz skacze, by nie doszło do kolizji
        game.player_y = 3.0

        # Przesuwamy czas tak, by przeszkoda minęła gracza
        # Przy prędkości 20 jedn./s, w 0.5s przesunie się o 10 w lewo (z 8.0 na -2.0)
        game.update(0.5)

        self.assertTrue(obs.passed)
        self.assertEqual(game.score, 1)
        self.assertEqual(game.money_earned, 10)  # 1 * 10$ = 10$

    def test_collision_detection(self):
        """Sprawdza, czy uderzenie w przeszkodę kończy grę (is_game_over)."""
        game = DinoGame(track_width=60)
        # Przeszkoda dokładnie w miejscu gracza na ziemi
        obs = Obstacle(PropType.CACTUS_SMALL, x=game.player_x, y=0.0, width=3, height=1)
        game.obstacles.append(obs)

        game.update(0.01)
        self.assertTrue(game.is_game_over)

    def test_high_score_tracking(self):
        """Sprawdza aktualizację rekordu gracza."""
        game = DinoGame(track_width=60, high_score=3)
        self.assertEqual(game.high_score, 3)

        # Dodajemy 4 przeszkody i symulujemy ich przeskoczenie
        for i in range(4):
            obs = Obstacle(PropType.ROCK, x=1.0, y=0.0, width=2, height=1)
            game.obstacles = [obs]
            obs.x = -1.0  # Minęła gracza
            game.update(0.01)

        self.assertEqual(game.score, 4)
        self.assertEqual(game.high_score, 4)
        self.assertTrue(game.is_new_high_score)
        self.assertEqual(game.money_earned, 40)

    def test_high_obstacles_only_appear_after_10_points(self):
        """Sprawdza, czy przeszkody o wysokości 2 pojawiają się dopiero od 10 punktów."""
        # Poniżej 10 punktów - wyłącznie niskie przeszkody (wysokość 1)
        game = DinoGame(track_width=60)
        game.score = 5
        for _ in range(50):
            game.obstacles.clear()
            game._spawn_obstacle()
            self.assertEqual(len(game.obstacles), 1)
            obs = game.obstacles[0]
            self.assertEqual(obs.height, 1, f"Przeszkoda o wysokości {obs.height} pojawiła się przed 10 punktami!")

        # Od 10 punktów - mogą pojawić się przeszkody o wysokości 2
        game.score = 10
        spawned_heights = set()
        for _ in range(100):
            game.obstacles.clear()
            game._spawn_obstacle()
            obs = game.obstacles[0]
            spawned_heights.add(obs.height)

        self.assertIn(1, spawned_heights)
        self.assertIn(2, spawned_heights, "Przeszkoda o wysokości 2 powinna się pojawiać po osiągnięciu 10 punktów!")

    def test_jump_clears_height_2_obstacle(self):
        """Sprawdza, czy gracz jest w stanie przeskoczyć przeszkodę o wysokości 2 przy poprawnym wyczuciu czasu."""
        game = DinoGame(track_width=60)
        game.score = 10  # Prędkość przy 10 punktach
        # Przeszkoda o wysokości 2 zbliża się do gracza (player front jest na x=11, przeszkoda na x=18)
        obs = Obstacle(PropType.CACTUS_LARGE, x=18.0, y=0.0, width=4, height=2)
        game.obstacles.append(obs)

        # Gracz wykonuje skok
        game.jump()

        # Symulacja przelotu przeszkody pod graczem
        collided = False
        while obs.right > -1:
            game.update(0.04)
            if game.is_game_over:
                collided = True
                break

        self.assertFalse(collided, "Gracz nie powinien zderzyć się z wysoką przeszkodą przy prawidłowym skoku!")
        self.assertTrue(obs.passed)


class TestPetIntegration(unittest.TestCase):

    def setUp(self):
        self.test_save = "test_save.json"
        if os.path.exists(self.test_save):
            os.remove(self.test_save)

    def tearDown(self):
        if os.path.exists(self.test_save):
            os.remove(self.test_save)

    def test_record_minigame_result(self):
        """Sprawdza nagradzanie zwierzaka: 10 monet za przeszkodę i zapis rekordu."""
        pet = Pet("Reksio")
        pet.money = 0
        pet.high_score = 5

        # Wynik 8 przeskoczonych przeszkód
        money_earned = pet.record_minigame_result(score=8)

        self.assertEqual(money_earned, 80)
        self.assertEqual(pet.money, 80)
        self.assertEqual(pet.high_score, 8)

    def test_save_and_load_high_score(self):
        """Sprawdza zapis i odczyt najlepszego wyniku z pliku JSON."""
        pet1 = Pet("Reksio")
        pet1.save_file = self.test_save
        pet1.high_score = 15
        pet1.money = 150
        pet1.save_state()

        pet2 = Pet("Reksio")
        pet2.save_file = self.test_save
        pet2.load_state()

        self.assertEqual(pet2.high_score, 15)
        self.assertEqual(pet2.money, 150)


class TestPropsStructure(unittest.TestCase):

    def test_props_exist_for_all_types(self):
        """Upewnia się, że każdy PropType ma zdefiniowany tekstowy odpowiednik w PROPS."""
        expected_types = [
            PropType.PLAYER_RUN_1,
            PropType.PLAYER_RUN_2,
            PropType.PLAYER_JUMP,
            PropType.PLAYER_CRASH,
            PropType.CACTUS_SMALL,
            PropType.CACTUS_LARGE,
            PropType.ROCK,
            PropType.GROUND,
            PropType.CLOUD,
        ]
        for prop_id in expected_types:
            self.assertIn(prop_id, PROPS, f"Brak definicji rekwizytu {prop_id} w PROPS!")
            prop = PROPS[prop_id]
            self.assertGreater(prop.width, 0)
            self.assertGreater(prop.height, 0)
            self.assertGreater(len(prop.lines), 0)


if __name__ == "__main__":
    unittest.main()
