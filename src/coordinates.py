import random


class MouseMoveCoordinates():
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.li = []

    def _up_right(self):
        for i in range(random.randint(2, 6)):
            dx, dy = random.randint(5, 10), random.randint(5, 10)
            self.x += dx
            self.y += dy
            self.li.append((self.x, self.y))

    def _up_left(self):
        for i in range(random.randint(2, 6)):
            dx, dy = random.randint(5, 10), random.randint(5, 10)
            self.x -= dx
            self.y += dy
            self.li.append((self.x, self.y))

    def _down_right(self):
        for i in range(random.randint(2, 6)):
            dx, dy = random.randint(5, 10), random.randint(5, 10)
            self.x += dx
            self.y -= dy
            self.li.append((self.x, self.y))

    def _down_left(self):
        for i in range(random.randint(2, 6)):
            dx, dy = random.randint(5, 10), random.randint(5, 10)
            self.x -= dx
            self.y -= dy
            self.li.append((self.x, self.y))

    def get_random_move(self):
        for i in range(random.randint(2, 6)):
            f = random.choice([self._up_right,
                               self._up_left,
                               self._down_right,
                               self._down_left])
            f()
        return self.li
