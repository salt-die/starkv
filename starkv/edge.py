import numpy as np
from math import atan2, sin, cos

from kivy.graphics import Color, Line, Triangle
from kivy.uix.widget import Widget

from .constants import (
    EDGE_WIDTH,
    HEAD_SIZE,
    EDGE_COLOR,
    HIGHLIGHTED_EDGE,
)

BASE = np.array(
    [
        [-0.5,  0],
        [  -4,  1],
        [  -4, -1],
    ],
    dtype=float,
)
ROTATION = np.zeros((2, 2), dtype=float)  # Used as a buffer for Triangle rotation matrix
BUFFER = np.zeros((3, 2), dtype=float)    # Buffer for matmul with ROTATION

class ArrowHead(Triangle):
    __slots__ = 'base', 'color', 'group_name'

    def __init__(self, color, size, group_name=None):
        """
        Triangle points are: (-0.5, 0), (-4, 1), (-4, -1). Looks like:
        (Two characters per x unit, One line per y unit, O is origin)

                        |
               o        |
            ----------o-O---
               o        |
                        |

        Tip is off origin so that arrow is less covered by nodes.
        """
        self.base =  BASE * size
        self.group_name = str(id(self)) if group_name is None else group_name

        self.color = Color(*color, group=self.group_name)
        super().__init__(group=self.group_name)

    def update(self, x1, y1, x2, y2):
        theta = atan2(y2 - y1, x2 - x1)

        ROTATION[(0, 1), (0, 1)] = cos(theta)

        sine = sin(theta)
        ROTATION[0, 1] = sine
        ROTATION[1, 0] = -sine

        np.matmul(self.base, ROTATION, out=BUFFER)
        np.add(BUFFER, (x2, y2), out=BUFFER)

        self.points = *BUFFER.reshape(1, -1)[0],

    def resize(self, size):
        self.base = BASE * size


class Arrow(Line):
    __slots__ = 'group_name', 'color', 'head'

    def __init__(self, width, head_size, line_color=(0, 0, 0, 0), head_color=(0, 0, 0, 0)):
        self.group_name = str(id(self))

        self.color = Color(*line_color, group=self.group_name)
        super().__init__(width=width, group=self.group_name)

        self.head = ArrowHead(color=head_color, size=head_size, group_name=self.group_name)

    def update(self, x1, y1, x2, y2):
        self.points = x1, y1, x2, y2
        self.head.update(x1, y1, x2, y2)

    def resize_head(self, size):
        self.head.resize(size)


class Edge(Arrow):
    __slots__ = 'edge', 's', 't', 'canvas'

    def __init__(self, edge, canvas):
        self.edge = edge
        self.s, self.t = edge.tuple
        self.canvas = canvas

        super().__init__(width=EDGE_WIDTH, head_size=HEAD_SIZE)

    def update(self):
        (x1, y1), (x2, y2) = self.canvas.layout[self.s], self.canvas.layout[self.t]
        super().update(x1, y1, x2, y2)

        self.color.rgba = color = HIGHLIGHTED_EDGE if self.canvas.G.nodes[self.s].is_pinned else EDGE_COLOR
        self.head.color.rgba = *(min(component * 1.2, 1) for component in color),
