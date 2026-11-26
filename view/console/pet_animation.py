import random

class PetAnimator:
    BLINK_EVERY = (2.5, 5.5)
    BLINK_TIME = 0.15
    HOP_EVERY = (4.0, 8.0)
    HOP_TIME = 0.35
    ZZ_STEP = 0.6
    ZZ_FRAMES = ("z", "zZ", "zZz")

    def __init__(self, now, rng=None):
        self.rng = rng or random.Random()
        self._start = now
        self._next_blink = now + self.rng.uniform(*self.BLINK_EVERY)
        self._next_hop = now + self.rng.uniform(*self.HOP_EVERY)

    def _catch_up(self, now):
        if now >= self._next_blink + self.BLINK_TIME:
            self._next_blink = now + self.rng.uniform(*self.BLINK_EVERY)
        if now >= self._next_hop + self.HOP_TIME:
            self._next_hop = now + self.rng.uniform(*self.HOP_EVERY)

    def frame(self, now, mood):
        self._catch_up(now)
        blink = mood in ("happy", "sad") and self._next_blink <= now
        hop = mood == "happy" and self._next_hop <= now
        if mood == "asleep":
            zz = self.ZZ_FRAMES[int((now - self._start) / self.ZZ_STEP) % len(self.ZZ_FRAMES)]
        else:
            zz = "zZ"
        return blink, (1 if hop else 0), zz

    def next_change(self, now, mood):
        self._catch_up(now)
        moments = []
        if mood in ("happy", "sad"):
            moments += [self._next_blink, self._next_blink + self.BLINK_TIME]
        if mood == "happy":
            moments += [self._next_hop, self._next_hop + self.HOP_TIME]
        if mood == "asleep":
            steps = int((now - self._start) / self.ZZ_STEP) + 1
            moments.append(self._start + steps * self.ZZ_STEP)
        future = [t - now for t in moments if t > now]
        return min(future) if future else None
