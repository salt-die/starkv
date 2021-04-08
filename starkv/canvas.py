from math import cos, hypot, sin, tau

from igraph import Graph, Layout

from kivy.animation import Animation
from kivy.clock import Clock
from kivy.config import Config
from kivy.graphics import Color, Ellipse, Line, PopMatrix, PushMatrix, Rectangle, Rotate, Scale
from kivy.graphics.instructions import CanvasBase
from kivy.uix.widget import Widget
from kivy.core.window import Window

from .constants import (
    UNIT,
    UPDATE_INTERVAL,
    BACKGROUND_COLOR,
    MIN_SCALE,
    HIGHLIGHTED_NODE,
    HIGHLIGHTED_EDGE,
    HIGHLIGHTED_HEAD,
    ANIMATION_HEIGHT,
    ANIMATION_WIDTH,
    ANIMATION_HEIGHT_2,
    ANIMATION_WIDTH_2,
    ANIMATED_NODE_SOURCE,
    ANIMATED_NODE_COLOR,
    ANIMATED_EDGE_WIDTH,
    ROTATE_INCREMENT,
    SCALE_SPEED_OUT,
    SCALE_SPEED_IN,
    TOUCH_INTERVAL,
    MOVE_STEPS,
)
from .node import Node
from .edge import Edge

Config.set('input', 'mouse', 'mouse,multitouch_on_demand')  # This setting so we can set the color of multitouch dots manually.

def circle_points(n):
    """Yield `n` points evenly space around a circle centered at (0, 0) with radius 1.
    """
    for i in range(n):
        yield cos(tau * i / n), sin(tau * i / n)

def lerp(a, b, k):
    """Linear interpolation from `a` to `b` by `k` amount. (0 <= k <= 1)
    """
    return a * (1 - k) + b * k


class GraphCanvas(Widget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._touches = []
        self.delay = .1

        self.scale = .3
        self.offset_x, self.offset_y = .5, .5

        self._mouse_pos_disabled = False
        self._selected_edge = self._selected_node = None
        self._source_node = self._target_edge = None

        self.load_graph()
        self.setup_canvas()

        # Animations
        self.scale_animation = (
              Animation(size=(ANIMATION_WIDTH_2, ANIMATION_HEIGHT_2), duration=SCALE_SPEED_OUT, step=UPDATE_INTERVAL)
            + Animation(size=(ANIMATION_WIDTH, ANIMATION_HEIGHT), duration=SCALE_SPEED_IN, step=UPDATE_INTERVAL)
        )
        self.scale_animation.repeat = True
        self.scale_animation.bind(on_progress=self._reposition_animated_node)

        self.rotate_animation = Clock.schedule_interval(self._rotate_node, UPDATE_INTERVAL)
        self.rotate_animation.cancel()

        self.edge_color_animation = Animation(a=0)
        self.edge_animation = Animation(width=ANIMATED_EDGE_WIDTH)
        self.edge_animation.bind(on_start=self._reset_edge_animation, on_complete=self._reschedule_edge_animation)
        self._restart_edge_animation = Clock.schedule_once(lambda dt: self.edge_animation.start(self.animated_edge))
        self._restart_edge_animation.cancel()

        # Schedule events
        self.layout_stepper = Clock.schedule_interval(self.step_layout, UPDATE_INTERVAL)
        self.resize_event = Clock.schedule_once(self.update_canvas, self.delay)
        self.resize_event.cancel()

        self.bind(size=self._delayed_resize, pos=self._delayed_resize)
        Window.bind(mouse_pos=self.on_mouse_pos)

    def load_graph(self):
        """Set initial graph.
        """
        # Need a dialogue for choosing number of nodes
        nnodes = 10  # TEMP
        self.G = Graph.Star(nnodes, mode="out")
        self._unscaled_layout = Layout([(0.0, 0.0), *circle_points(nnodes - 1)])

    def setup_canvas(self):
        """Populate the canvas with the initial instructions.
        """
        self.canvas.clear()

        with self.canvas.before:
            self.background_color = Color(*BACKGROUND_COLOR)
            self._background = Rectangle(size=self.size, pos=self.pos)

        with self.canvas:
            self.animated_edge_color = Color(*HIGHLIGHTED_EDGE)
            self.animated_edge_color.a = 0
            self.animated_edge = Line(width=1.1)

        # Edge instructions before Node instructions so they're drawn underneath nodes.
        self._edge_instructions = CanvasBase()
        with self._edge_instructions:
            self.edges = {edge.tuple: Edge(edge.tuple, self) for edge in self.G.es}
        self.canvas.add(self._edge_instructions)

        # Animated node drawn above edges but below other nodes.
        with self.canvas:
            PushMatrix()
            self.rotation_instruction = Rotate()
            self.animated_node_color = Color(*ANIMATED_NODE_COLOR)
            self.animated_node_color.a = 0
            self.animated_node = Rectangle(size=(ANIMATION_WIDTH, ANIMATION_HEIGHT), source=ANIMATED_NODE_SOURCE)
            PopMatrix()

        self._node_instructions = CanvasBase()
        with self._node_instructions:
            self.nodes = [Node(vertex.index, self) for vertex in self.G.vs]
        self.canvas.add(self._node_instructions)

    @property
    def selected_edge(self):
        """While there is no source node, the selected edge is just the edge that is currently colliding with the mouse.
        """
        return self._selected_edge

    @selected_edge.setter
    def selected_edge(self, edge):
        if self.selected_edge is not None:
            self.selected_edge.tail_selected = None

        self._selected_edge = edge

    @property
    def selected_node(self):
        """This is the end of selected edge that is closest to the mouse position.
        """
        return self._selected_node

    @selected_node.setter
    def selected_node(self, node):
        self._selected_node = node
        if node is not None:
            self._selected_node_x, self._selected_node_y = x, y = self._unscaled_layout[node.index]
            self.animated_node_color.a = 1
            self.rotate_animation()
            self.scale_animation.start(self.animated_node)

        else:
            self.animated_node_color.a = 0
            self.rotate_animation.cancel()
            self.scale_animation.stop(self.animated_node)

    @property
    def source_node(self):
        """Source node is set to selected node when the selected node is clicked.
        """
        return self._source_node

    @source_node.setter
    def source_node(self, node):
        if self.source_node is not None:
            self.animated_node_color.rgba = HIGHLIGHTED_EDGE

        self._source_node = node

        if node is not None:
            self.animated_node_color.rgba = HIGHLIGHTED_NODE

    @property
    def target_edge(self):
        """The target edge is the edge we move along.
        """
        return self._target_edge

    @target_edge.setter
    def target_edge(self, edge):
        if self.target_edge is not None:
            self.target_edge.color.rgba = HIGHLIGHTED_EDGE
            self.target_edge.head.color.rgba = HIGHLIGHTED_HEAD

            self._keep_animating = False
            self.edge_animation.stop(self.animated_edge)

        self._target_edge = edge

        if edge is not None:
            edge.color.rgba = HIGHLIGHTED_NODE
            edge.head.color.rgba = UNIT
            self._keep_animating = True
            self.edge_animation.start(self.animated_edge)

    def _transform_coords(self, coord):
        """Transform vertex coordinates to canvas coordinates.
        """
        return (
            (coord[0] * self.scale + self.offset_x) * self.width,
            (coord[1] * self.scale + self.offset_y) * self.height,
        )

    def _invert_coords(self, x, y):
        """Transform canvas coordinates to vertex coordinates.
        """
        return (x / self.width - self.offset_x) / self.scale, (y / self.height - self.offset_y) / self.scale

    def _rotate_node(self, dt):
        """This rotates `animated_node` when called. `dt` does nothing, but is required for kivy's scheduler.
        """
        self.rotation_instruction.origin = self.layout[self.selected_node.index]
        self.rotation_instruction.angle = (self.rotation_instruction.angle + ROTATE_INCREMENT) % 360

    def _reposition_animated_node(self, *args):
        x, y = self.layout[self.selected_node.index]
        w, h = self.animated_node.size
        self.animated_node.pos = x - w // 2, y - h // 2

    def _delayed_resize(self, *args):
        self.resize_event.cancel()
        self.resize_event()

        self._background.size = self.size
        self._background.pos = self.pos

    def _reset_edge_animation(self, *args):
        self.animated_edge_color.a = 1
        self.animated_edge.width = 1.1
        self.edge_color_animation.start(self.animated_edge_color)

    def _reschedule_edge_animation(self, *args):
        self.edge_color_animation.stop(self.animated_edge_color)
        self.animated_edge_color.a = 0
        self.animated_edge.width = 1.1
        if self._keep_animating:
            self._restart_edge_animation()

    def _move_intermediate(self, i=0):
        """Lerp the selected edge to it's new position and update the underlying graph when finished.
        """
        (start_x, start_y, stop_x, stop_y), selected, tail_selected, new_end = self._move_information
        sx, sy, tx, ty = selected.points

        k = i / MOVE_STEPS
        lxy = lerp(start_x, stop_x, k), lerp(start_y, stop_y, k)
        if tail_selected:
            selected.points = *lxy, tx, ty
            selected.head.update(*lxy, tx, ty)
        else:
            selected.points = sx, sy, *lxy
            selected.head.update(sx, sy, *lxy)

        if i < MOVE_STEPS:
            # Reschedule this function
            Clock.schedule_once(lambda dt: self._move_intermediate(i + 1))
        else:
            self.G.delete_edges((selected.edge,))
            del self.edges[selected.edge]

            source, target = selected.edge
            if tail_selected:
                selected.edge =self.G.add_edge(new_end, target).tuple
                self.edges[new_end, target] = selected
            else:
                selected.edge = self.G.add_edge(source, new_end).tuple
                self.edges[source, new_end] = selected

            self.layout_stepper()
            self._mouse_pos_disabled = False

    def move_edge(self):
        self._move_information = (
            self.target_edge.points,
            self.selected_edge,
            self.selected_edge.tail_selected,
            self.target_edge.edge[1]
        )

        self.source_node = self.target_edge = self.selected_edge = None  # WARNING: The order of these assignments is important.

        self.layout_stepper.cancel()
        self._mouse_pos_disabled = True

        Clock.schedule_once(lambda dt: self._move_intermediate())

    def on_touch_move(self, touch):
        """Zoom if multitouch, else if a node is selected, drag it, else move the entire graph.
        """
        if touch.grab_current is not self or touch.button == 'right':
            return

        if len(self._touches) > 1:
            self.transform_on_touch(touch)

        elif self.selected_edge is not None:
            px, py = self._invert_coords(touch.px, touch.py)
            x, y = self._invert_coords(touch.x, touch.y)
            self._selected_node_x += x - px
            self._selected_node_y += y - py

        else:
            self.offset_x += touch.dx / self.width
            self.offset_y += touch.dy / self.height

        self.update_canvas()
        return True

    def transform_on_touch(self, touch):
        """Rescales the canvas.
        """
        ax, ay = self._touches[-2].pos  # Anchor coords
        x, y = self._invert_coords(ax, ay)

        cx = (touch.x - ax) / self.width
        cy = (touch.y - ay) / self.height
        current_length = hypot(cx, cy)

        px = (touch.px - ax) / self.width
        py = (touch.py - ay) / self.height
        previous_length = hypot(px, py)

        self.scale = max(self.scale + current_length - previous_length, MIN_SCALE)

        # Make sure the anchor is a fixed point:
        # Note we can't use `ax, ay` as `self.scale` has changed.
        x, y = self._transform_coords((x, y))

        self.offset_x += (ax - x) / self.width
        self.offset_y += (ay - y) / self.height

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            return

        touch.grab(self)
        self._touches.append(touch)
        self._mouse_pos_disabled = True

        # Change the color of multitouch dots to match our color scheme:
        if touch.button == 'right':
            touch.multitouch_sim = True
            with Window.canvas.after:
                touch.ud._drawelement = (
                    Color(*HIGHLIGHTED_EDGE),
                    Ellipse(size=(20, 20), segments=15, pos=(touch.x - 10, touch.y - 10)),
                )

        return True

    def on_touch_up(self, touch):
        if touch.grab_current is not self:
            return

        touch.ungrab(self)
        self._touches.remove(touch)
        self._mouse_pos_disabled = False

        if touch.time_end - touch.time_start > TOUCH_INTERVAL:
            return

        if self.source_node is not None:
            if self.target_edge is not None:
                self.move_edge()
            else:
                self.source_node = None
                # Recheck collision with edge:
                collides, tail_selected = self.selected_edge.collides(touch.x, touch.y)
                if collides:
                    self.selected_edge.tail_selected = tail_selected
                else:
                    self.selected_edge = None

        elif self.selected_node is not None:
            self.source_node = self.selected_node

    def on_mouse_pos(self, *args):
        mx, my = args[-1]

        if self._mouse_pos_disabled or not self.collide_point(mx, my):
            return

        # If source node is set, check collision with a target node.
        if self.source_node is not None:
            if self.target_edge is None:
                for edge in self.G.vs[self.source_node.index].out_edges():
                    target = self.edges[edge.tuple]
                    if target is not self.selected_edge and target.collides(mx, my)[0]:
                        self.target_edge = target
                        break
            else:
                if not self.target_edge.collides(mx, my)[0]:
                    self.target_edge = None

        # If an edge is selected, just check collision with that edge.
        elif self.selected_edge is not None:
            collides, tail_selected = self.selected_edge.collides(mx, my)
            if collides:
                self.selected_edge.tail_selected = tail_selected
            else:
                self.selected_edge = None

        # Check collision with all edges.
        else:
            for edge in self.edges.values():
                collides, tail_selected = edge.collides(mx, my)
                if collides:
                    edge.tail_selected = tail_selected
                    self.selected_edge = edge
                    break
            else:
                self.selected_edge = None

    def update_canvas(self, dt=0):
        """Update coordinates of all elements. `dt` is a dummy arg required for kivy's scheduler.
        """
        if self.resize_event.is_triggered:  # We use a delayed resize, this will make sure we're done resizing before we update.
            return

        for edge in self.edges.values():
            edge.update()

        if self.target_edge is not None:
            self.animated_edge.points = self.target_edge.points

        for node in self.nodes:
            node.update()

    def step_layout(self, dt):
        """Iterate the graph layout algorithm. `dt` is a dummy arg required for kivy's scheduler.
        """
        self._unscaled_layout = self.G.layout_graphopt(niter=1, seed=self._unscaled_layout, max_sa_movement=.1, node_charge=.00001)

        # Keep the animated node fixed:
        if self.selected_edge is not None:
            self._unscaled_layout[self.selected_node.index] = self._selected_node_x, self._selected_node_y

        self.layout = self._unscaled_layout.copy()
        self.layout.transform(self._transform_coords)

        self.update_canvas()
