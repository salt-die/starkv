from kivy.graphics import Color, Line
from .constants import (
    NODE_WIDTH,
    NODE_RADIUS,
    NODE_COLOR,
    HIGHLIGHTED_NODE,
)


class Node(Line):
    __slots__ = 'color', 'vertex', 'canvas', 'group_name', '_x', '_y'

    def __init__(self, vertex, canvas):
        self.group_name = str(id(self))
        self.vertex = vertex
        self.canvas = canvas
        self.color = Color(*NODE_COLOR, group=self.group_name)
        self._x = self._y = None
        super().__init__(width=NODE_WIDTH, group=self.group_name)

    @property
    def is_frozen(self):
        return self._x is not None is not self._y

    def freeze(self):
        self._x, self._y = self.canvas._unscaled_layout[self.vertex.index]
        self.color.rgba = HIGHLIGHTED_NODE

    def unfreeze(self):
        self._x = self._y = None
        self.color.rgba = NODE_COLOR

    def update(self):
        if self.is_frozen:
            self.canvas._unscaled_layout[self.vertex.index] = self._x, self._y
        self.circle = *self.canvas.layout[self.vertex.index], NODE_RADIUS
