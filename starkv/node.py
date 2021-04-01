from math import tau
from pathlib import Path

from kivy.graphics import Color, Line, Rectangle
from kivy.core.image import Image

from .constants import (
    NODE_WIDTH,
    NODE_RADIUS,
    NODE_COLOR,
    HIGHLIGHTED_NODE,
    HIGHLIGHTED_EDGE,
)

STAR = Image(str(Path("starkv") / "assets" / "star.png"))


class Node(Line):
    __slots__ = 'color', 'index', 'canvas',

    def __init__(self, index, canvas):
        self.index = index
        self.canvas = canvas
        self.color = Color(*NODE_COLOR)

        super().__init__(width=NODE_WIDTH)

    def update(self):
        self.circle = *self.canvas.layout[self.index], NODE_RADIUS


class AnimatedNode(Rectangle):
    __slots__ = 'color',

    def __init__(self, *args, **kwargs):
        self.color = Color(*HIGHLIGHTED_EDGE)
        self.color.a = 0

        super().__init__(*args, **kwargs)
        self.texture = STAR.texture
