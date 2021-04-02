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
    NODE_COLOR,
    HIGHLIGHTED_NODE,
)

BASE =  -.5, 0.0, -4.0, 1.0, -4.0, -1.0
UNIT = 1.0, 1.0, 1.0, 1.0

def gradient(a, b):
    """Linear interpolation from color `a` to color `b`.
    """
    return (int(x * z + y * (255 - z)) for z in range(256) for x, y in zip(a, b))

SELECTED_GRADIENT = Texture.create(size=(256, 1))
SELECTED_GRADIENT.blit_buffer(
    bytes(gradient(EDGE_COLOR, HIGHLIGHTED_EDGE)),
    colorfmt='rgba',
    bufferfmt='ubyte'
)

SELECTED_GRADIENT_REVERSED = Texture.create(size=(256, 1))
SELECTED_GRADIENT_REVERSED.blit_buffer(
    bytes(gradient(HIGHLIGHTED_EDGE, EDGE_COLOR)),
    colorfmt='rgba',
    bufferfmt='ubyte'
)

del gradient


class Arrow(Triangle):
    __slots__ = 'base', 'color'

    def __init__(self, color, size, group=None):
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
        self.base =  tuple(x * size for x in BASE)
        group = group or str(id(self))

        self.color = Color(*color, group=group)
        super().__init__(group=group)

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
    __slots__ = "edge", "canvas", "_tail_selected", "color", 'head'

    def __init__(self, edge, canvas):
        group = str(id(self))

        self.edge = edge
        self.canvas = canvas
        self._tail_selected = None
        self.color = Color(*EDGE_COLOR, group=group)

        super().__init__(width=EDGE_WIDTH, group=group)
        self.head = Arrow(color=HEAD_COLOR, size=HEAD_SIZE, group=group)

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
        G = self.canvas.G

        if tail_selected is not None:
            unfrozen = nodes[source if tail_selected else target]
            unfrozen.color.rgba = NODE_COLOR

            for edge in G.vs[unfrozen.index].out_edges():
                e = edges[edge]
                e.color.rgba = EDGE_COLOR
                e.head.color.rgba = HEAD_COLOR

        if value is not None:
            self.color.rgba = UNIT
            self.head.color.rgba, frozen = (HEAD_COLOR, nodes[source]) if value else (HIGHLIGHTED_HEAD, nodes[target])
            self.canvas.selected_node = frozen
            frozen.color.rgba = HIGHLIGHTED_NODE

            for edge in G.vs[frozen.index].out_edges():
                e = edges[edge]
                if e is not self:
                    e.color.rgba = HIGHLIGHTED_EDGE
                    e.head.color.rgba = HIGHLIGHTED_HEAD

        else:
            self.color.rgba = EDGE_COLOR
            self.head.color.rgba = HEAD_COLOR
            self.canvas.selected_node = None

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
