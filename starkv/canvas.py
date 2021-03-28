from functools import wraps
from math import cos, hypot, sin, tau

from igraph import Graph, Layout
from kivy.clock import Clock
from kivy.graphics import Color, Ellipse, Rectangle
from kivy.config import Config
from kivy.graphics.instructions import CanvasBase
from kivy.uix.widget import Widget
from kivy.core.window import Window

from .constants import (
    UPDATE_INTERVAL,
    BACKGROUND_COLOR,
    HIGHLIGHTED_EDGE,
)
from .graph_interface import GraphInterface
from .node import Node
from .edge import Edge

Config.set('input', 'mouse', 'mouse,multitouch_on_demand')

def circle_points(n):
    """Yield `n` points evenly space around a circle centered at (0, 0) with radius 1.
    """
    for i in range(n):
        yield cos(tau * i / n), sin(tau * i / n)


class GraphCanvas(Widget):
    _touches = []
    delay = .1

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.resize_event = Clock.schedule_once(lambda dt: None, 0)  # Dummy event to save a conditional
        self.update_layout = Clock.schedule_interval(self.step_layout, UPDATE_INTERVAL)

        self.scale = .3
        self.offset_x, self.offset_y = .5, .5

        self._mouse_pos_disabled = False
        self._selected_edge = None

        self.bind(size=self._delayed_resize, pos=self._delayed_resize)
        Window.bind(mouse_pos=self.on_mouse_pos)

        self.load_graph()
        self.setup_canvas()

    def load_graph(self):
        """Set initial graph.
        """
        # Need a dialogue for choosing number of nodes
        nnodes = 5  # TEMP
        self.G = G = GraphInterface.Star(nnodes, mode="out")
        self._unscaled_layout = Layout([(0.0, 0.0), *circle_points(nnodes - 1)])

    @property
    def selected_edge(self):
        return self._selected_edge

    @selected_edge.setter
    def selected_edge(self, edge):
        if self.selected_edge is not None:
            self.selected_edge.unselect()

        self._selected_edge = edge

    def on_touch_move(self, touch):
        """Zoom if multitouch, else a node is pinned, drag it, else move the entire graph.
        """
        if touch.grab_current is not self or touch.button == 'right':
            return

        if len(self._touches) > 1:
            self.transform_on_touch(touch)

        elif self.selected_edge is not None:
            px, py = self.invert_coords(touch.px, touch.py)
            x, y = self.invert_coords(touch.x, touch.y)
            self._fx += x - px
            self._fy += y - py

        else:
            self.offset_x += touch.dx / self.width
            self.offset_y += touch.dy / self.height

        self.update_canvas()
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
        x, y = self.transform_coords((x, y))

        self.offset_x += (ax - x) / self.width
        self.offset_y += (ay - y) / self.height

    def invert_coords(self, x, y):
        """Transform canvas coordinates to vertex coordinates.
        """
        return (x / self.width - self.offset_x) / self.scale, (y / self.height - self.offset_y) / self.scale

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            return

        touch.grab(self)
        self._touches.append(touch)
        self._mouse_pos_disabled = True

        if touch.button == 'right':
            touch.multitouch_sim = True
            # Change the color of multitouch dots to match our color scheme:
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

        if self.selected_edge is not None and self.selected_edge.collides(mx, my):
            self.selected_edge.select(mx, my)
            return

        for edge in self.edges.values():
            if edge.collides(mx, my):
                self.selected_edge = edge
                edge.select(mx, my)
                break
        else:
            self.selected_edge = None

    def _delayed_resize(self, *args):
        self.resize_event.cancel()
        self.resize_event = Clock.schedule_once(self.update_canvas, self.delay)

        self._background.size = self.size
        self._background.pos = self.pos

    def setup_canvas(self):
        """Populate the canvas with the initial instructions.
        """
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
        """Update node coordinates and edge colors.
        """
        if self.resize_event.is_triggered:
            return

        self.layout = self._unscaled_layout.copy()
        self.layout.transform(self.transform_coords)

        for node in self.nodes:
            node.update()

        for edge in self.edges.values():
            edge.update()

    def step_layout(self, dt):
        self._unscaled_layout = self.G.layout_graphopt(niter=1, seed=self._unscaled_layout, max_sa_movement=.1, node_charge=.00001)

        if self.selected_edge is not None:  # Keep pinned node from moving by reseting it's position after updating layout
            self._unscaled_layout[self._f] = self._fx, self._fy

        self.update_canvas()

    def transform_coords(self, coord):
        """Transform vertex coordinates to canvas coordinates.
        """
        return (
            (coord[0] * self.scale + self.offset_x) * self.width,
            (coord[1] * self.scale + self.offset_y) * self.height,
        )
