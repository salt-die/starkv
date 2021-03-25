from kivy.graphics import Color, Line
from .constants import (
    NODE_WIDTH,
    NODE_RADIUS,
    BOUNDS,
    NODE_COLOR,
    HIGHLIGHTED_NODE,
)


class Node(Line):
    __slots__ = 'color', 'vertex', 'canvas', 'group_name', 'is_pinned'

    def __init__(self, vertex, canvas):
        self.group_name = str(id(self))

        self.vertex = vertex
        self.canvas = canvas
        self.is_pinned = False

        self.color = Color(*NODE_COLOR, group=self.group_name)
        super().__init__(width=NODE_WIDTH, group=self.group_name)

    def update_out_edges(self):
        for edge in self.vertex.out_edges():
            self.canvas.edges[edge].update()

    def freeze(self):
        self.is_pinned = True
        self.color.rgba = HIGHLIGHTED_NODE
        self.update_out_edges()

    def unfreeze(self):
        self.is_pinned = False
        self.color.rgba = NODE_COLOR
        self.update_out_edges()

    def collides(self, mx, my):
        x, y = self.canvas.layouts[self.vertex.index]
        return abs(x - mx) <= BOUNDS and abs(y - my) <= BOUNDS

    def update(self):
        self.circle = *self.canvas.layout[self.vertex.index], NODE_RADIUS
