from kivy.graphics import Color, Line

from .constants import (
    NODE_COLOR,
    NODE_RADIUS,
    NODE_WIDTH,
    NODE_BOUNDS
)


class Node(Line):
    __slots__ = 'index', 'canvas', 'color'

    def __init__(self, index, canvas):
        self.index = index
        self.canvas = canvas
        self.color = Color(*NODE_COLOR)

        super().__init__(width=NODE_WIDTH)

    def update(self):
        self.circle = *self.canvas.layout[self.index], NODE_RADIUS

    def collides(self, px, py):
        x, y = self.canvas.layout[self.index]
        return abs(x - px) <= NODE_BOUNDS and abs(y - py) <= NODE_BOUNDS
