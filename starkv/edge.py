from math import atan2, cos, hypot, sin

from kivy.graphics import Color, Line, Triangle
from kivy.graphics.texture import Texture
from kivy.uix.widget import Widget

from .constants import (
    EDGE_BOUNDS,
    EDGE_WIDTH,
    HEAD_SIZE,
    EDGE_COLOR,
    HIGHLIGHTED_EDGE,
    HEAD_COLOR,
    HIGHLIGHTED_HEAD,
)

BASE =  -.5, 0.0, -4.0, 1.0, -4.0, -1.0
UNIT = 1.0, 1.0, 1.0, 1.0

### Create textures for selected edges ###
gradient_length = 256

def lerp(a, b, pct):
    return a * pct + b * (255 - pct)

def gradient(a, b):
    return (int(lerp(x, y, z)) for z in range(gradient_length) for x, y in zip(a, b))

SELECTED_GRADIENT = Texture.create(size=(gradient_length, 1))
buf = bytes(gradient(EDGE_COLOR, HIGHLIGHTED_EDGE))
SELECTED_GRADIENT.blit_buffer(buf, colorfmt='rgba', bufferfmt='ubyte')

SELECTED_GRADIENT_REVERSED = Texture.create(size=(gradient_length, 1))
buf = bytes(gradient(HIGHLIGHTED_EDGE, EDGE_COLOR))
SELECTED_GRADIENT_REVERSED.blit_buffer(buf, colorfmt='rgba', bufferfmt='ubyte')

del buf
del lerp
del gradient
del gradient_length
##########################################


class Arrow(Triangle):
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


class Edge(Line):
    __slots__ = 'group_name', 'edge', 'canvas', '_tail_selected', 'color', 'head'

    def __init__(self, edge, canvas):
        self.group_name = str(id(self))

        self.edge = edge
        self.canvas = canvas
        self._tail_selected = None

        self.color = Color(*EDGE_COLOR, group=self.group_name)
        super().__init__(width=EDGE_WIDTH, group=self.group_name)

        self.head = Arrow(color=HEAD_COLOR, size=HEAD_SIZE, group_name=self.group_name)

    @property
    def tail_selected(self):
        return self._tail_selected

    @tail_selected.setter
    def tail_selected(self, value):
        tail_selected = self.tail_selected

        if tail_selected == value:
            return

        source, target = self.edge.tuple
        nodes = self.canvas.nodes
        edges = self.canvas.edges

        if tail_selected is not None:
            unfrozen = nodes[source if tail_selected else target]
            unfrozen.unfreeze()

            for edge in unfrozen.vertex.out_edges():
                e = edges[edge]
                e.color.rgba = EDGE_COLOR
                e.head.color.rgba = HEAD_COLOR

        if value is not None:
            self.color.rgba = UNIT
            self.head.color.rgba, frozen = (HEAD_COLOR, nodes[source]) if value else (HIGHLIGHTED_HEAD, nodes[target])
            frozen.freeze()

            for edge in frozen.vertex.out_edges():
                e = edges[edge]
                if e is not self:
                    e.color.rgba = HIGHLIGHTED_EDGE
                    e.head.color.rgba = HIGHLIGHTED_HEAD

        else:
            self.color.rgba = EDGE_COLOR
            self.head.color.rgba = HEAD_COLOR

        self._tail_selected = value

    @property
    def layout_points(self):
        source, target = self.edge.tuple
        layout = self.canvas.layout
        return *layout[source], *layout[target],

    def update(self):
        x1, y1, x2, y2 = self.layout_points

        self.points = x1, y1, x2, y2
        self.head.update(x1, y1, x2, y2)

        if self.tail_selected is None:
            return

        if self.tail_selected:
            self.texture = SELECTED_GRADIENT
        else:
            self.texture = SELECTED_GRADIENT_REVERSED

    def collides(self, px, py):
        """
        Returns a 2-tuple (is_close, closer_to_tail), where `is_close` indicates if `(px, py)` is within
        `EDGE_BOUNDS` of this edge and `closer_to_tail` indicates if the point is closer to
        the tail or the head of this edge.
        """
        ax, ay, bx, by = self.layout_points

        # Distance from a point to a segment:
        # We compare dot products of point with either end of segment
        # to determine if point is closest to that end
        abx, aby = bx - ax, by - ay
        apx, apy = px - ax, py - ay
        ab_ap = abx * apx + aby * apy
        if ab_ap < 0:
            return hypot(px - ax, py - ay) <= EDGE_BOUNDS, True

        bpx, bpy = px - bx, py - by
        ab_bp = abx * bpx + aby * bpy
        if ab_bp > 0:
            return hypot(px - bx, py - by) <= EDGE_BOUNDS, False

        # Project segment down to point
        return abs(abx * apy - aby * apx) / hypot(abx, aby) <= EDGE_BOUNDS, hypot(px - ax, py - ay) < hypot(px - bx, py - by)
