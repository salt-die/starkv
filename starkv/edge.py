from math import atan2, cos, hypot, sin

from kivy.graphics import Color, Line, Triangle

from .constants import (
    HEAD_BASE,
    WHITE,
    EDGE_BOUNDS,
    EDGE_WIDTH,
    HEAD_SIZE,
    EDGE_COLOR,
    HIGHLIGHTED_EDGE,
    HEAD_COLOR,
    HIGHLIGHTED_HEAD,
    NODE_COLOR,
    HIGHLIGHTED_NODE,
    SELECTED_GRADIENT,
    SELECTED_GRADIENT_REVERSED,
)


class Edge(Line):
    __slots__ = "edge", "canvas", "_is_tail_selected", "color", 'head_color', 'head'

    HEAD = tuple(x * HEAD_SIZE for x in HEAD_BASE)

    def __init__(self, edge, canvas):
        self.edge = edge
        self.canvas = canvas
        self._is_tail_selected = None
        self.color = Color(*EDGE_COLOR)

        super().__init__(width=EDGE_WIDTH)

        self.head_color = Color(*HEAD_COLOR)
        self.head = Triangle(points=(0, 0, 0, 0, 0, 0))

    @property
    def is_tail_selected(self):
        return self._is_tail_selected

    @is_tail_selected.setter
    def is_tail_selected(self, value):
        is_tail_selected = self.is_tail_selected

        if is_tail_selected == value:
            return

        source, target = self.edge
        nodes = self.canvas.nodes
        edges = self.canvas.edges
        G = self.canvas.G

        if is_tail_selected is not None:
            unfrozen = nodes[source if is_tail_selected else target]
            unfrozen.color.rgba = NODE_COLOR

            for edge in G.vs[unfrozen.index].out_edges():
                e = edges[edge.tuple]
                e.color.rgba = EDGE_COLOR
                e.head_color.rgba = HEAD_COLOR

        if value is not None:
            self.color.rgba = WHITE
            self.head_color.rgba, frozen = (HEAD_COLOR, nodes[source]) if value else (HIGHLIGHTED_HEAD, nodes[target])
            self.canvas.selected_node = frozen
            frozen.color.rgba = HIGHLIGHTED_NODE

            for edge in G.vs[frozen.index].out_edges():
                e = edges[edge.tuple]
                if e is not self:
                    e.color.rgba = HIGHLIGHTED_EDGE
                    e.head_color.rgba = HIGHLIGHTED_HEAD

        else:
            self.color.rgba = EDGE_COLOR
            self.head_color.rgba = HEAD_COLOR
            self.canvas.selected_node = None

        self._is_tail_selected = value

    def update_points(self, x1, y1, x2, y2):
        theta = atan2(y2 - y1, x2 - x1)
        cosine = cos(theta)
        sine = sin(theta)
        bx1, by1, bx2, by2, bx3, by3 = Edge.HEAD

        self.points = x1, y1, x2, y2
        # Triangle points are determined by multiplying Edge.Head by rotation matrix and translating to (x2, y2).
        self.head.points = (
            cosine * bx1 + by1 *  -sine + x2,
            sine   * bx1 + by1 * cosine + y2,
            cosine * bx2 + by2 *  -sine + x2,
            sine   * bx2 + by2 * cosine + y2,
            cosine * bx3 + by3 *  -sine + x2,
            sine   * bx3 + by3 * cosine + y2,
        )

    def update(self):
        source, target = self.edge
        layout = self.canvas.layout
        self.update_points(*layout[source], *layout[target])

        if self.is_tail_selected is not None:
            self.texture = SELECTED_GRADIENT if self.is_tail_selected else SELECTED_GRADIENT_REVERSED

    def collides(self, px, py):
        """
        Returns a 2-tuple (is_close, is_closer_to_tail), where `is_close` indicates if `(px, py)` is within
        `EDGE_BOUNDS` of this edge and `is_closer_to_tail` indicates if the point is closer to the tail or the head.
        """
        ax, ay, bx, by = self.points

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
