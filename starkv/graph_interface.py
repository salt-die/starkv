from igraph import Graph

from .node import Node
from .edge import Edge

class GraphInterface(Graph):
    """
    An interface from an igraph Graph to the graph canvas that updates the canvas when an edge
    has been added/removed.
    """
    __slots__ = 'canvas'

    def __init__(self, canvas, *args, **kwargs):
        self.canvas = canvas
        super().__init__(*args, **kwargs)

    def add_edge(self, source, target, **kwargs):
        edge = super().add_edge(source, target, **kwargs)

        with self.canvas._edge_instructions:
            self.canvas.edges[edge] = Edge(edge, self.canvas)
        self.canvas.nodes[self.canvas.edges[edge].s].list_item.update_text()
        self.canvas.update_canvas()

        return edge

    def delete_edge(self, edge):
        instruction = self.canvas.edges.pop(edge)
        self.canvas._edge_instructions.remove_group(instruction.group_name)
        edge.delete()

        self.canvas.update_canvas()
