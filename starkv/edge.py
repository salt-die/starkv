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

def distance_to_segment(px, py, ax, ay, bx, by):
    abx, aby = bx - ax, by - ay

    apx, apy = px - ax, py - ay
    ab_ap = abx * apx + aby * apy
    if ab_ap < 0:
        return hypot(px - ax, py - ay)

    bpx, bpy = px - bx, py - by
    ab_bp = abx * bpx + aby * bpy
    if ab_bp > 0:
        return hypot(px - bx, py - by)

    return abs(abx * apy - aby * apx) / hypot(abx, aby)


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
        self._tail_selected = value

        if value is None:
            return

        self.color.rgba = UNIT

        if self.tail_selected:
            self.canvas.nodes[self.edge.source].freeze()
        else:
            self.canvas.nodes[self.edge.target].freeze()

    def update(self):
        source, target = self.edge.tuple
        layout = self.canvas.layout
        (x1, y1), (x2, y2) = layout[source], layout[target]

        self.points = x1, y1, x2, y2
        self.head.update(x1, y1, x2, y2)

        if self.tail_selected is None:
            return

        if self.tail_selected:
            self.texture = SELECTED_GRADIENT
            self.head.color.rgba = HEAD_COLOR
        else:
            self.texture = SELECTED_GRADIENT_REVERSED
            self.head.color.rgba = HIGHLIGHTED_HEAD

    def collides(self, mx, my):
        source, target = self.edge.tuple
        layout = self.canvas.layout
        return distance_to_segment(mx, my, *layout[source], *layout[target]) <= EDGE_BOUNDS

    def select(self, mx, my):
        """Selects the endpoint which is closest to the point (mx, my)."""
        source, target = self.edge.tuple
        layout = self.canvas.layout
        (x1, y1), (x2, y2) = layout[source], layout[target]

        closer_to_tail = hypot(mx - x1, my - y1) < hypot(mx - x2, my - y2)

        if self.tail_selected == closer_to_tail:
            return

        if self.tail_selected is not None:  # If we're already selected but the closest endpoint has changed.
            self.unselect()

        self.tail_selected = closer_to_tail

    def unselect(self):
        """Unfreeze the frozen node and re-color this edge."""
        if self.tail_selected is None:
            return

        if self.tail_selected:
            self.canvas.nodes[self.edge.source].unfreeze()
        else:
            self.canvas.nodes[self.edge.target].unfreeze()

        self.color.rgba = EDGE_COLOR
        self.head.color.rgba = HEAD_COLOR

        self.tail_selected = None
