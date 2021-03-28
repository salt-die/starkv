from functools import wraps
from math import hypot

from igraph import Graph
from kivy.clock import Clock
from kivy.graphics import Color, Ellipse, Line, Rectangle
from kivy.config import Config
from kivy.graphics.instructions import CanvasBase
from kivy.properties import OptionProperty, ObjectProperty
from kivy.uix.layout import Layout
from kivy.uix.widget import Widget
from kivy.core.window import Window

from .constants import (
    UPDATE_INTERVAL,
    BACKGROUND_COLOR,
    HIGHLIGHTED_EDGE,
    BOUNDS,
)
from .graph_interface import GraphInterface
from .node import Node
from .edge import Edge

Config.set('input', 'mouse', 'mouse,multitouch_on_demand')

def redraw_canvas_after(func):
    """For methods that change vertex coordinates."""
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        results = func(self, *args, **kwargs)
        self.update_canvas()
        return results

    return wrapper


class GraphCanvas(Widget):
    _touches = []
    delay = .3

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.resize_event = Clock.schedule_once(lambda dt: None, 0)  # Dummy event to save a conditional
        # self.update_layout = Clock.schedule_interval(self.step_layout, UPDATE_INTERVAL)

        self.offset_x = .25
        self.offset_y = .25
        self.scale = .5

        self._mouse_pos_disabled = False
        self._highlighted = None

        self.bind(size=self._delayed_resize, pos=self._delayed_resize)
        Window.bind(mouse_pos=self.on_mouse_pos)

        self.load_graph()
        self.setup_canvas()

    def load_graph(self):
        """Set initial graph."""
        # Need a dialogue for choosing number of nodes
        nnodes = 5  # TEMP
        self.G = G = GraphInterface.Star(nnodes, mode="out")
        self._unscaled_layout = G.layout_fruchterman_reingold(niter=2)

    @property
    def highlighted(self):
        return self._highlighted

    @highlighted.setter
    def highlighted(self, node):
        """Freezes highlighted nodes or returns un-highlighted nodes to the proper color."""
        if self.highlighted is not None:
            self.highlighted.unfreeze()

        if node is not None:
            node.freeze()

        self._highlighted = node

    @redraw_canvas_after
    def on_touch_move(self, touch):
        """Zoom if multitouch, else if a node is highlighted, drag it, else move the entire graph."""

        if touch.grab_current is not self:
            return

        if len(self._touches) > 1:
            self.transform_on_touch(touch)
            return True

        if touch.button == 'right':
            return

        if self.highlighted is not None:
            self._unscaled_layout[self.highlighted.vertex.index] = self.invert_coords(touch.x, touch.y)
            return True

        self.offset_x += touch.dx / self.width
        self.offset_y += touch.dy / self.height
        return True

    def transform_on_touch(self, touch):
        ax, ay = self._touches[-2].pos  # Anchor coords
        x, y = self.invert_coords(ax, ay)

        cx = (touch.x - ax) / self.width
        cy = (touch.y - ay) / self.height
        current_length = hypot(cx, cy)

        px = (touch.px - ax) / self.width
        py = (touch.py - ay) / self.height
        previous_length = hypot(px, py)

        self.scale += current_length - previous_length

        # Make sure the anchor is a fixed point:
        x, y = self.transform_coords(x, y)
        self.offset_x += (ax - x) / self.width
        self.offset_y += (ay - y) / self.height

    def invert_coords(self, x, y):
        """Transform canvas coordinates to vertex coordinates."""
        return (x / self.width - self.offset_x) / self.scale, (y / self.height - self.offset_y) / self.scale

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            return

        touch.grab(self)
        self._touches.append(touch)
        self._mouse_pos_disabled = True

        if touch.button == 'right':
            touch.multitouch_sim = True
            # We're going to change the color of multitouch dots to match our color scheme:
            with Window.canvas.after:
                touch.ud._drawelement = _, ellipse = Color(*HIGHLIGHTED_EDGE), Ellipse(size=(20, 20), segments=15)
            ellipse.pos = touch.x - 10, touch.y - 10

        return True

    def on_touch_up(self, touch):
        if touch.grab_current is not self:
            return

        touch.ungrab(self)
        self._touches.remove(touch)
        self._mouse_pos_disabled = False

    def on_mouse_pos(self, *args):
        mx, my = args[-1]

        if self._mouse_pos_disabled or not self.collide_point(mx, my):
            return

        for node in self.nodes:
            if node.collides(mx, my):
                self.highlighted = node
                break
        else:
            self.highlighted = None

    def _delayed_resize(self, *args):
        self.resize_event.cancel()
        self.resize_event = Clock.schedule_once(self.update_canvas, self.delay)

    def setup_canvas(self):
        """Populate the canvas with the initial instructions."""
        self.canvas.clear()

        with self.canvas.before:
            self.background_color = Color(*BACKGROUND_COLOR)
            self._background = Rectangle(size=self.size, pos=self.pos)

        self._edge_instructions = CanvasBase()
        with self._edge_instructions:
            self.edges = {edge: Edge(edge, self) for edge in self.G.es}
        self.canvas.add(self._edge_instructions)

        self._node_instructions = CanvasBase()
        with self._node_instructions:
            self.nodes = [Node(vertex, self) for vertex in self.G.vs]

        self.canvas.add(self._node_instructions)

    def update_canvas(self, *args):
        """Update node coordinates and edge colors."""
        if self.resize_event.is_triggered:
            return

        self._background.size = self.size
        self._background.pos = self.pos

        self.transform_coords()

        for node in self.nodes:
            node.update()

        for edge in self.edges.values():
            edge.update()

    @redraw_canvas_after
    def step_layout(self, dt):
        self._unscaled_layout = self.G.layout_fruchterman_reingold(niter=1, seed=self._unscaled_layout)

    def transform_coords(self, x=None, y=None):
        """
        Transform vertex coordinates to canvas coordinates.  If no specific coordinate is passed
        transform all coordinates in the unscaled layout.
        """

        if x is not None and y is not None:
            return (
                (x * self.scale + self.offset_x) * self.width,
                (y * self.scale + self.offset_y) * self.height,
            )

        self.layout = self._unscaled_layout.copy()
        self.layout.scale(self.scale)
        self.layout.translate(self.offset_x, self.offset_y)
        self.layout.scale(self.width, self.height)
