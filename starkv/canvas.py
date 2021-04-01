from functools import wraps
from math import cos, hypot, sin, tau

from igraph import Graph, Layout

from kivy.animation import Animation
from kivy.clock import Clock
from kivy.config import Config
from kivy.graphics import Color, Ellipse, Rectangle, PushMatrix, PopMatrix, Rotate, Scale
from kivy.graphics.instructions import CanvasBase
from kivy.uix.widget import Widget
from kivy.core.window import Window

from .constants import (
    UPDATE_INTERVAL,
    BACKGROUND_COLOR,
    HIGHLIGHTED_EDGE,
    ANIMATION_HEIGHT,
    ANIMATION_WIDTH,
    ANIMATION_HEIGHT_2,
    ANIMATION_WIDTH_2,
    ROTATE_INCREMENT,
    SCALE_SPEED_OUT,
    SCALE_SPEED_IN,
)
from .graph_interface import GraphInterface
from .node import Node, AnimatedNode
from .edge import Edge

Config.set('input', 'mouse', 'mouse,multitouch_on_demand')

def circle_points(n):
    """Yield `n` points evenly space around a circle centered at (0, 0) with radius 1.
    """
    for i in range(n):
        yield cos(tau * i / n), sin(tau * i / n)


class GraphCanvas(Widget):
    __slots__ = (
        '_touches', 'delay', 'resize_event', 'update_layout',
        'scale', 'offset_x', 'offset_y', '_mouse_pos_disabled',
        '_selected_edge', '_unscaled_layout', 'layout', 'G',
        '_selected_node', '_selected_node_x', '_selected_node_y',
        'node_animation', 'nodes', 'edges',
        'rotation_instruction', 'scale_instruction', 'rotate_animation',
        'scale_animation',
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._touches = []
        self.delay = .1

        self.resize_event = None
        self.update_layout = Clock.schedule_interval(self.step_layout, UPDATE_INTERVAL)

        self.scale = .3
        self.offset_x, self.offset_y = .5, .5

        self._mouse_pos_disabled = False
        self._selected_edge = self._selected_node = None

        self.bind(size=self._delayed_resize, pos=self._delayed_resize)
        Window.bind(mouse_pos=self.on_mouse_pos)

        self.scale_animation = (
              Animation(size=(ANIMATION_WIDTH_2, ANIMATION_HEIGHT_2), duration=SCALE_SPEED_OUT, step=UPDATE_INTERVAL)
            + Animation(size=(ANIMATION_WIDTH, ANIMATION_HEIGHT), duration=SCALE_SPEED_IN, step=UPDATE_INTERVAL)
        )
        self.scale_animation.repeat = True

        self.load_graph()
        self.setup_canvas()

    def load_graph(self):
        """Set initial graph.
        """
        # Need a dialogue for choosing number of nodes
        nnodes = 10  # TEMP
        self.G = G = GraphInterface.Star(nnodes, mode="out")
        self._unscaled_layout = Layout([(0.0, 0.0), *circle_points(nnodes - 1)])

    @property
    def selected_edge(self):
        return self._selected_edge

    @selected_edge.setter
    def selected_edge(self, edge):
        if self.selected_edge is not None:
            self.selected_edge.tail_selected = None

        self._selected_edge = edge

    @property
    def selected_node(self):
        return self._selected_node

    @selected_node.setter
    def selected_node(self, node):
        self._selected_node = node
        if node is not None:
            self._selected_node_x, self._selected_node_y = x, y = self._unscaled_layout[node.index]
            self.node_animation.color.a = 1
            self.rotate_animation()
            self.scale_animation.start(self.node_animation)

        else:
            self.node_animation.color.a = 0
            self.rotate_animation.cancel()
            self.scale_animation.stop(self.node_animation)

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
            self._selected_node_x += x - px
            self._selected_node_y += y - py

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

        # If an edge is selected, just check collision with that edge.
        if self.selected_edge is not None:
            collides, tail_selected = self.selected_edge.collides(mx, my)
            if collides:
                self.selected_edge.tail_selected = tail_selected
            else:
                self.selected_edge = None
            return

        for edge in self.edges.values():
            collides, tail_selected = edge.collides(mx, my)
            if collides:
                edge.tail_selected = tail_selected
                self.selected_edge = edge
                break
        else:
            self.selected_edge = None

    def _delayed_resize(self, *args):
        if self.resize_event is not None:
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

        # Node instructions are kept separate from Edge instructions so that they're always drawn on top.
        self._node_instructions = CanvasBase()
        with self._node_instructions:
            PushMatrix()
            self.rotation_instruction = Rotate()
            self.node_animation = AnimatedNode(size=(ANIMATION_WIDTH, ANIMATION_HEIGHT))
            PopMatrix()
            self.nodes = [Node(vertex.index, self) for vertex in self.G.vs]

        self.canvas.add(self._node_instructions)

        self.rotate_animation = Clock.schedule_interval(self._rotate_node, UPDATE_INTERVAL)
        self.rotate_animation.cancel()

    def _rotate_node(self, dt):
        self.rotation_instruction.origin = self.layout[self.selected_node.index]
        self.rotation_instruction.angle = (self.rotation_instruction.angle + ROTATE_INCREMENT) % 360

    def update_canvas(self, *args):
        """Update node coordinates and edge colors.
        """
        if self.resize_event.is_triggered:
            return

        if self.selected_edge is not None:
            self._unscaled_layout[self._selected_node.index] = self._selected_node_x, self._selected_node_y

        self.layout = self._unscaled_layout.copy()
        self.layout.transform(self.transform_coords)

        if self.selected_node is not None:
            x, y = self.layout[self.selected_node.index]
            w, h = self.node_animation.size
            self.node_animation.pos = x - w // 2, y - h // 2

        for node in self.nodes:
            node.update()

        for edge in self.edges.values():
            edge.update()

    def step_layout(self, dt):
        self._unscaled_layout = self.G.layout_graphopt(niter=1, seed=self._unscaled_layout, max_sa_movement=.1, node_charge=.00001)
        self.update_canvas()

    def transform_coords(self, coord):
        """Transform vertex coordinates to canvas coordinates.
        """
        return (
            (coord[0] * self.scale + self.offset_x) * self.width,
            (coord[1] * self.scale + self.offset_y) * self.height,
        )
