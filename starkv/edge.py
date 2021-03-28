from math import atan2, sin, cos

from kivy.graphics import Color, Line, Triangle
from kivy.uix.widget import Widget

from .constants import (
    EDGE_WIDTH,
    HEAD_SIZE,
    EDGE_COLOR,
    HIGHLIGHTED_EDGE,
    HEAD_COLOR,
    HIGHLIGHTED_HEAD,
)

BASE =  -.5, 0, -4, 1, -4, -1


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
        self.base =  tuple(c * size for c in BASE)
        self.group_name = str(id(self)) if group_name is None else group_name

        self.color = Color(*color, group=self.group_name)
        super().__init__(group=self.group_name)

    def update(self, x1, y1, x2, y2):
        theta = atan2(y2 - y1, x2 - x1)

        cosine = cos(theta)
        sine = sin(theta)

        bx1, by1, bx2, by2, bx3, by3 = self.base
        self.points = (
            cosine * bx1 + by1 *  -sine + x2,
            sine   * bx1 + by1 * cosine + y2,
            cosine * bx2 + by2 *  -sine + x2,
            sine   * bx2 + by2 * cosine + y2,
            cosine * bx3 + by3 *  -sine + x2,
            sine   * bx3 + by3 * cosine + y2,
        )

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
        self.canvas = canvas

        super().__init__(width=EDGE_WIDTH, head_size=HEAD_SIZE)

    def update(self):
        source, target = self.edge.tuple
        canvas = self.canvas

        (x1, y1), (x2, y2) = canvas.layout[source], canvas.layout[target]
        super().update(x1, y1, x2, y2)

        if canvas.nodes[source].is_pinned:
            self.color.rgba = HIGHLIGHTED_EDGE
            self.head.color.rgba = HIGHLIGHTED_HEAD
        else:
            self.color.rgba = EDGE_COLOR
            self.head.color.rgba = HEAD_COLOR
