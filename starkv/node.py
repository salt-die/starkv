from kivy.graphics import Color, Line
from .constants import (
    NODE_WIDTH,
    NODE_RADIUS,
    NODE_COLOR,
    HIGHLIGHTED_NODE,
    EDGE_COLOR,
    HIGHLIGHTED_EDGE,
    HEAD_COLOR,
    HIGHLIGHTED_HEAD,
)


class Node(Line):
    __slots__ = 'color', 'vertex', 'canvas', 'group_name'

    def __init__(self, vertex, canvas):
        self.group_name = str(id(self))
        self.vertex = vertex
        self.canvas = canvas
        self.color = Color(*NODE_COLOR, group=self.group_name)
        super().__init__(width=NODE_WIDTH, group=self.group_name)

    def freeze(self):
        # Storing frozen node position in a hidden attribute in the canvas:
        # Probably should refactor this!
        self.canvas._f = i = self.vertex.index
        self.canvas._fx, self.canvas._fy = self.canvas._unscaled_layout[i]

        self.color.rgba = HIGHLIGHTED_NODE

        for edge in self.vertex.out_edges():
            e = self.canvas.edges[edge]
            if e.tail_selected is None:
                e.color.rgba = HIGHLIGHTED_EDGE
                e.head.color.rgba = HIGHLIGHTED_HEAD

    def unfreeze(self):
        self.color.rgba = NODE_COLOR

        for edge in self.vertex.out_edges():
            e = self.canvas.edges[edge]
            if e.tail_selected is None:
                e.color.rgba = EDGE_COLOR
                e.head.color.rgba = HEAD_COLOR

    def update(self):
        self.circle = *self.canvas.layout[self.vertex.index], NODE_RADIUS
