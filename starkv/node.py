from kivy.graphics import Color, Line
from .constants import NODE_WIDTH, NODE_RADIUS, BOUNDS


class Node(Line):
    __slots__ = 'color', 'vertex', 'canvas', 'group_name', 'list_item'

    def __init__(self, vertex, canvas, color):
        self.group_name = str(id(self))

        self.vertex = vertex
        self.canvas = canvas
        self.is_pinned = False

        self._color = color
        self.color = Color(*color, group=self.group_name)
        super().__init__(width=NODE_WIDTH, group=self.group_name)

    def update_out_edges(self):
        for edge in self.vertex.out_edges():
            self.canvas.edges[edge].update()

    def freeze(self, color=None):
        self.is_pinned = True

        if color is not None:
            self.color.rgba = color

        self.update_out_edges()

    def unfreeze(self):
        self.is_pinned = False
        self.color.rgba = self._color
        self.update_out_edges()

    def collides(self, mx, my):
        x, y = self.canvas.node_positions[self.vertex]
        return abs(x - mx) <= BOUNDS and abs(y - my) <= BOUNDS

    def update(self):
        if not self.is_pinned:
            self.color.rgba = self._color

        self.circle = *self.canvas.node_positions[self.vertex], NODE_RADIUS
