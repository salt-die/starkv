from math import atan2, cos, hypot, sin

from kivy.graphics import Color, Line, Triangle

from .constants import (
    HEAD_BASE,
    WHITE,
    EDGE_BOUNDS,
    EDGE_WIDTH,
    HEAD_SIZE,
    EDGE_COLOR,
    HEAD_COLOR,
    HIGHLIGHTED_HEAD,
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
        """Returns a bool only if the edge is selected otherwise None.
        """
        return self._is_tail_selected

    @is_tail_selected.setter
    def is_tail_selected(self, is_tail_selected):
        """Re-colors this edge and adjacent edges before updating `_is_tail_selected`.
        """
        old_is_tail_selected = self.is_tail_selected

        if old_is_tail_selected is is_tail_selected:
            return

        source, target = self.edge

        if is_tail_selected is not None:
            self.color.rgba = WHITE
            if is_tail_selected:
                self.head_color.rgba = HEAD_COLOR
                self.canvas.selected_node = self.canvas.nodes[source]
            else:
                self.head_color.rgba = HIGHLIGHTED_HEAD
                self.canvas.selected_node = self.canvas.nodes[target]

        else:  # Return this edge's colors to their defaults and unselect the selected_node
            self.color.rgba = EDGE_COLOR
            self.head_color.rgba = HEAD_COLOR
            self.canvas.selected_node = None

        self._is_tail_selected = is_tail_selected

    def update_points(self, x1, y1, x2, y2):
        theta = atan2(y2 - y1, x2 - x1)
        cosine = cos(theta)
        sine = sin(theta)
        bx1, by1, bx2, by2, bx3, by3 = Edge.HEAD

        self.points = x1, y1, x2, y2
        # Triangle points are determined by multiplying Edge.HEAD by rotation matrix and translating to (x2, y2).
        self.head.points = (
            cosine * bx1 + by1 *  -sine + x2,
            sine   * bx1 + by1 * cosine + y2,
            cosine * bx2 + by2 *  -sine + x2,
            sine   * bx2 + by2 * cosine + y2,
            cosine * bx3 + by3 *  -sine + x2,
            sine   * bx3 + by3 * cosine + y2,
        )

    def update(self):
        """Update points based on canvas's current layout.
        """
        source, target = self.edge
        layout = self.canvas.layout
        self.update_points(*layout[source], *layout[target])

        # Textures will be lost when points are changed, so we re-apply them.
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
