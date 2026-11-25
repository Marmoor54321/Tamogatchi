import random

class PropType:
    PLAYER_RUN_1 = "player_run_1"
    PLAYER_RUN_2 = "player_run_2"
    PLAYER_JUMP = "player_jump"
    PLAYER_CRASH = "player_crash"

    CACTUS_SMALL = "cactus_small"
    CACTUS_LARGE = "cactus_large"
    ROCK = "rock"

    GROUND = "ground"
    CLOUD = "cloud"

class Entity:

    def __init__(self, prop_id: str, x: float, y: float, width: int, height: int):
        self.prop_id = prop_id
        self.x = float(x)
        self.y = float(y)
        self.width = width
        self.height = height

    @property
    def right(self) -> float:
        return self.x + self.width

    @property
    def top(self) -> float:
        return self.y + self.height

    def collides_with(self, other: "Entity") -> bool:
        horizontal_overlap = (self.x < other.right) and (self.right > other.x)
        vertical_overlap = (self.y < other.top) and (self.top > other.y)
        return horizontal_overlap and vertical_overlap

class Obstacle(Entity):

    def __init__(self, prop_id: str, x: float, y: float, width: int, height: int):
        super().__init__(prop_id, x, y, width, height)
        self.passed = False

class Cloud(Entity):

    def __init__(self, x: float, y: float, width: int, height: int, speed: float = 4.0):
        super().__init__(PropType.CLOUD, x, y, width, height)
        self.speed = speed

class DinoGame:

    MONEY_PER_OBSTACLE = 10
    JUMP_VELOCITY = 11.1
    GRAVITY = 22.0
    BASE_SPEED = 20.0
    MAX_SPEED = 36.0

    LOW_OBSTACLE_TEMPLATES = [
        (PropType.CACTUS_SMALL, 3, 1),
        (PropType.ROCK, 3, 1),
    ]
    HIGH_OBSTACLE_TEMPLATES = [
        (PropType.CACTUS_LARGE, 4, 2),
    ]
    HIGH_OBSTACLE_THRESHOLD = 10

    def __init__(self, track_width: int = 60, high_score: int = 0):
        self.track_width = track_width
        self.initial_high_score = high_score
        self.high_score = high_score
        self.score = 0

        self.player_x = 6.0
        self.player_y = 0.0
        self.player_vy = 0.0
        self.player_width = 7
        self.player_height = 3
        self.is_jumping = False

        self.is_game_over = False
        self.is_finished = False

        self.obstacles: list[Obstacle] = []
        self.clouds: list[Cloud] = []

        self.anim_timer = 0.0
        self.run_frame = 0
        self.spawn_timer = 1.0
        self.cloud_timer = 0.5

        self.obstacle_templates = self.LOW_OBSTACLE_TEMPLATES + self.HIGH_OBSTACLE_TEMPLATES

    @property
    def current_speed(self) -> float:
        return min(self.MAX_SPEED, self.BASE_SPEED + (self.score * 0.7))

    @property
    def money_earned(self) -> int:
        return self.score * self.MONEY_PER_OBSTACLE

    @property
    def is_new_high_score(self) -> bool:
        return self.score > self.initial_high_score

    def get_player_entity(self) -> Entity:
        if self.is_game_over:
            prop = PropType.PLAYER_CRASH
        elif self.is_jumping or self.player_y > 0.05:
            prop = PropType.PLAYER_JUMP
        else:
            prop = PropType.PLAYER_RUN_1 if self.run_frame == 0 else PropType.PLAYER_RUN_2

        return Entity(prop, self.player_x, self.player_y, self.player_width, self.player_height)

    def jump(self):
        if self.is_game_over:
            return
        if not self.is_jumping and self.player_y <= 0.01:
            self.player_vy = self.JUMP_VELOCITY
            self.is_jumping = True

    def update(self, dt: float):
        if self.is_game_over:
            return

        self.anim_timer += dt
        if self.anim_timer >= 0.15:
            self.anim_timer = 0.0
            self.run_frame = 1 - self.run_frame

        if self.is_jumping or self.player_y > 0:
            self.player_y += self.player_vy * dt
            self.player_vy -= self.GRAVITY * dt
            if self.player_y <= 0.0:
                self.player_y = 0.0
                self.player_vy = 0.0
                self.is_jumping = False

        speed = self.current_speed
        for obs in self.obstacles:
            obs.x -= speed * dt

            if not obs.passed and obs.right < self.player_x:
                obs.passed = True
                self.score += 1
                if self.score > self.high_score:
                    self.high_score = self.score

        self.obstacles = [obs for obs in self.obstacles if obs.right > -2]

        self.spawn_timer -= dt
        if self.spawn_timer <= 0:
            self._spawn_obstacle()
            min_gap_time = 1.3 - min(0.4, self.score * 0.02)
            max_gap_time = 2.4 - min(0.6, self.score * 0.02)
            self.spawn_timer = random.uniform(min_gap_time, max_gap_time)

        for cloud in self.clouds:
            cloud.x -= cloud.speed * dt
        self.clouds = [c for c in self.clouds if c.right > -2]

        self.cloud_timer -= dt
        if self.cloud_timer <= 0:
            self.clouds.append(Cloud(x=self.track_width, y=random.choice([4.0, 5.0]), width=6, height=1))
            self.cloud_timer = random.uniform(3.0, 6.0)

        player_entity = self.get_player_entity()
        for obs in self.obstacles:
            if player_entity.collides_with(obs):
                self.is_game_over = True
                break

    def _spawn_obstacle(self):
        if self.score >= self.HIGH_OBSTACLE_THRESHOLD:
            templates = self.LOW_OBSTACLE_TEMPLATES + self.HIGH_OBSTACLE_TEMPLATES
        else:
            templates = self.LOW_OBSTACLE_TEMPLATES

        prop_id, width, height = random.choice(templates)
        self.obstacles.append(Obstacle(prop_id, x=self.track_width, y=0.0, width=width, height=height))

