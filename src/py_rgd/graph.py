from typing import Any
from dataclasses import dataclass
from enum import Enum, StrEnum
from itertools import chain

from lark import Token, Transformer

from .attributes import Attributes


@dataclass
class Node:
    key: Any
    props: Attributes | None = None

    def __repr__(self) -> str:
        return f"(Node) {self.key}: {self.props}"


@dataclass
class Edge:
    class Direction(StrEnum):
        UNDIRECTED = "--"
        DIRECTED = "->"
        BIDIRECTIONAL = "<>"

    class DirectionOrder(StrEnum):
        LR = "->"
        RL = "<-"
        BI = "<>"

    u: Any
    v: Any
    direction: Direction = Direction.UNDIRECTED
    props: Attributes | None = None

    def __repr__(self) -> str:
        return f"(Edge) {self.u} {self.direction} {self.v}: {self.props}"


@dataclass
class Hyperedge:
    e: set[Any]
    f: set[Any] | Any | None = None
    direction: Edge.Direction = Edge.Direction.UNDIRECTED
    props: Attributes | None = None

    def __repr__(self) -> str:
        return f"(Hyperdge) {self.e} {self.direction} {self.f}: {self.props}"


class NodeTransformer(Transformer):
    def node_decl(self, items):
        return [Node(items[0], items[1] if len(items) > 1 else None)]

    def node_set(self, items):
        return items[0]

    def node_set_decl(self, items):
        return [Node(n, items[1] if len(items) > 1 else None) for n in items[0]]

    def node_line(self, items):
        return items[0]

    def node_doc(self, items):
        nodes = list(chain.from_iterable(items))

        # Merge node redefinitions
        node_map = dict()
        for node in nodes:
            if node.key not in node_map:
                node_map[node.key] = [node]
            else:
                node_map[node.key].append(node)
        for key, nodes in node_map.items():
            if len(nodes) > 1:
                props = dict()
                for node in nodes:
                    if not isinstance(node.props, dict):
                        raise ValueError("Nodes cannot have multiple descriptions unless each uses a key-value list")
                    props |= node.props
                node_map[key] = Node(key, props)
            else:
                node_map[key] = nodes[0]
        return list(node_map.values())

    def node_doc_body(self, items):
        return items


class EdgeTransformer(Transformer):

    @staticmethod
    def __build_edge(u, v, direction = Edge.Direction.UNDIRECTED, details = None):
        if isinstance(u, set) or isinstance(v, set):
            return Hyperedge(u, v, direction, details)
        return Edge(u, v, direction, details)

    def edge_decl(self, items):
        u, d, v = items[0], items[1], items[2]
        # Normalize edge direction
        if d == Edge.DirectionOrder.RL:
            u,v = v,u
            d = Edge.DirectionOrder.LR
        props = items[3] if len(items) > 3 else None
        return self.__build_edge(u, v, d, props)

    def legacy_edge_decl(self, items):
        return self.__build_edge(items[0], items[1], details=items[2:])

    def edge_line(self, items):
        return items[0]

    def edge_doc(self, items):
        return [e for e in items if isinstance(e, (Edge, Hyperedge))]



class GraphTransformer(Transformer):
    def graph_expression(self, items):
        return {items[0][0]:items[0][1]}

    def graph_prop_line(self, items):
        return items[0]

    def headerless_doc(self, items):
        items = items[0]
        if len(items) > 1:
            return (dict(), items[0], items[1])
        return [(dict(), items[0], [])]

    def graph_doc(self, items):
        items = [item for item in items if not (isinstance(item, Token) and item.type == "NLP") ]
        node_header_index = [(isinstance(t, Token) and t.type == "NODE_HEADER") for t in items].index(True)

        graph_props = dict()
        for prop in items[1:node_header_index]:
            graph_props |= prop

        edges = []
        items = items[node_header_index+1]
        if len(items) > 1:
            nodes, edges = items
        else:
            nodes = items[0]

        return (graph_props, nodes, edges)

    def graph_docs(self, items):
        return items

    def rgd(self, items):
        items = [item for item in items if not (isinstance(item, Token) and item.type == "NLP") ]
        return items[0]

    def empty_doc(self, _items):
        return None


@dataclass(frozen=True)
class Graph:
    nodes: list[Node]
    edges: list[Edge | Hyperedge]
    props: Attributes | None = None
    _node_keys: set[Any] = None

    def __post_init__(self):
        """Doing bad things for convenience."""
        object.__setattr__(self, "_node_keys", {n.key for n in self.nodes})

    @property
    def node_keys(self) -> set[Any]:
        return self._node_keys

    def get_node(self, key: Any) -> Node | None:
        if key not in self.node_keys:
            return None
        for node in self.nodes:
            if key == node.key:
                return node 

    def validate(self):
        # Validate graph
        node_names = {n.key for n in self.nodes}
        edge_nodes = set()
        for edge in self.edges:
            if isinstance(edge, Edge):
                edge_nodes.add(edge.u)
                edge_nodes.add(edge.v)
            else:
                if isinstance(edge.e, set):
                    edge_nodes.update(edge.e)
                else:
                    edge_nodes.add(edge.e)
                if edge.f is None:
                    pass
                elif isinstance(edge.f, set):
                    edge_nodes.update(edge.f)
                else:
                    edge_nodes.add(edge.f)
        diff = edge_nodes.difference(node_names)
        assert len(diff) == 0, f"Edges contain undefined nodes! {diff}"

    def __repr__(self) -> str:
        s = "Graph:\n"
        if self.props:
            s += "\tProperties:\n"
            for k,v in self.props.items():
                s += f"\t\t{k}: {v}\n"
        s += "\tNodes:\n"
        for node in self.nodes:
            s += f"\t\t{node}\n"
        if self.edges:
            s += "\tEdges:\n"
            for edge in self.edges:
                s += f"\t\t{edge}\n"
        return s

