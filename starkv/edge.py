from .arrow import Arrow

class Edge(Arrow):
    __slots__ = 'edge', 's', 't', 'canvas', '_directed'

    def __init__(self, edge, canvas, directed=True):
        self.edge = edge
        self.s, self.t = edge.tuple
        self.canvas = canvas
        self._directed = directed

        super().__init__(width=EDGE_WIDTH, head_size=HEAD_SIZE)

    @property
    def directed(self):
        return self._directed

    @directed.setter
    def directed(self, boolean):
        self._directed = self.head.color.a = boolean

    def update(self):
        x1, y1, x2, y2 = *self.canvas.coords[int(self.s)], *self.canvas.coords[int(self.t)]
        self.points = x1, y1, x2, y2
        if self.directed:
            self.head.update(x1, y1, x2, y2)

        if self.canvas.G.vp.pinned[self.s]:
            color = HIGHLIGHTED_EDGE
        else:
            color = EDGE_COLOR

        hcolor =  tuple(min(c * 1.2, 1) for c in color)
        self.color.rgba = color
        self.head.color.rgba = hcolor
