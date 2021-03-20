from kivy.graphics import Color, Line


class Node(Line):
    __slots__ = 'color', 'vertex', 'canvas', 'group_name', 'list_item'

    def __init__(self, vertex, canvas):
        self.group_name = str(id(self))

        self.vertex = vertex
        self.canvas = canvas

        self.color = Color(*color, group=self.group_name)
        super().__init__(width=NODE_WIDTH, group=self.group_name)

    def update_out_edges(self):
        for edge in self.vertex.out_edges():
            self.canvas.edges[edge].update()

    def freeze(self, color=None):
        self.canvas.G.vp.pinned[self.vertex] = 1
        if color is not None:
            self.color.rgba = color

        self.update_out_edges()

    def unfreeze(self):
        canvas = self.canvas
        canvas.G.vp.pinned[self.vertex] = 0
        self.color.rgba = canvas.node_colormap[canvas.node_colors[self.vertex]]
        self.update_out_edges()

    def collides(self, mx, my):
        x, y = self.canvas.coords[int(self.vertex)]
        return abs(x - mx) <= BOUNDS and abs(y - my) <= BOUNDS

    def update(self):
        canvas = self.canvas
        if not canvas.G.vp.pinned[self.vertex]:
            self.color.rgba = canvas.node_colormap[canvas.node_colors[self.vertex]]
        self.circle = *canvas.coords[int(self.vertex)], NODE_RADIUS
