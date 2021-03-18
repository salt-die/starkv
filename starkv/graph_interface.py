from igraph import Graph
# Need a Node and Edge canvas instructions

class GraphInterface(Graph):
    """
    An interface from an igraph Graph to the graph canvas that updates the canvas when an edge/vertex
    has been added/removed.
    """
    __slots__ = 'canvas'

    def __init__(self, canvas, *args, **kwargs):
        self.canvas = canvas
        super().__init__(*args, **kwargs)

    def add_vertex(self, *args, **kwargs):
        node = super().add_vertex(*args, **kwargs)

        with self.canvas._node_instructions:
            self.canvas.nodes[node] = Node(node, self.canvas)

        # self.vp.pos[node][:] = random(), random()   # Need to update dict of positions
        return node

    def remove_vertex(self, node, fast=True):
        for edge in set(node.all_edges()):  # Change to equivalent in igraph
            self.remove_edge(edge)

        instruction = self.canvas.nodes[node]
        canvas = self.canvas
        #
        # --- Remove the canvas instructions corresponding to node. Prepare last node to take its place. ---
        #
        if canvas.highlighted is instruction:
            canvas.highlighted = None

        if instruction in canvas._pinned:
            canvas._pinned.remove(instruction)
        elif instruction in canvas._selected:
            canvas._selected.remove(instruction)

        last = self.num_vertices() - 1
        pos = int(node)
        if pos != last:
            last_vertex = self.vertex(last)
            last_node = canvas.nodes.pop(last_vertex)
            edge_instructions = tuple(canvas.edges.pop(edge) for edge in set(last_vertex.all_edges()))
        else:
            last_vertex = None

        canvas._node_instructions.remove_group(instruction.group_name)
        del canvas.nodes[node]
        #
        # --- Prep done.
        #

        # super().remove_vertex(node, fast=True)  # Replace with igraph equivalent

        #
        # --- Swap the vertex descriptor of the last node and edge descriptors of all edges adjacent to ---
        # --- it and fix our node and edge dictionary that used these descriptors. (Node deletion       ---
        # --- invalidated these descriptors.)                                                           ---
        #
        if last_vertex is None:
            return

        last_node.vertex = self.vertex(pos)         # Update descriptor
        canvas.nodes[last_node.vertex] = last_node  # Update node dict

        for edge_instruction, edge in zip(edge_instructions, set(last_node.vertex.all_edges())):
            edge_instruction.s, edge_instruction.t = edge  # Update descriptor
            canvas.edges[edge] = edge_instruction          # Update edge dict

    def add_edge(self, *args, **kwargs):
        edge = super().add_edge(*args, **kwargs)

        # Make a new canvas instruction corresponding to edge.
        with self.canvas._edge_instructions:
            self.canvas.edges[edge] = Edge(edge, self.canvas)
        self.canvas.nodes[self.canvas.edges[edge].s].list_item.update_text()
        self.canvas.update_canvas()

        return edge

    def remove_edge(self, edge):
        # Remove canvas instruction corresponding to edge
        source = edge.source()
        instruction = self.canvas.edges.pop(edge)
        self.canvas._edge_instructions.remove_group(instruction.group_name)

        super().remove_edge(edge)

        self.canvas.update_canvas()
