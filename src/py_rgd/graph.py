from typing import Any
from dataclasses import dataclass
from enum import Enum
from itertools import chain

from lark import Transformer

from .attributes import Attributes


@dataclass
class Node:
    key: Any
    props: Attributes | None = None

    def __repr__(self) -> str:
        return f"(Node) {self.key}: {self.props}"


@dataclass
class Edge:
    class Direction(Enum):
        UNDIRECTED = 0
        DIRECTED = 1
        BIDIRECTIONAL = 2

        def __str__(self) -> str:
            return self.__repr__()

        def __repr__(self) -> str:
            if self.name == "UNDIRECTED":
                return "--"
            elif self.name == "DIRECTED":
                return "->"
            elif self.name == "BIDIRECTIONAL":
                return "<>"
            else:
                return "??"

    class DirectionOrder(Enum):
        LR = 0
        RL = 1
        BI = 2

    u: Node
    v: Node
    direction: Direction = Direction.UNDIRECTED
    props: Attributes | None = None

    def __repr__(self) -> str:
        return f"(Edge) {self.u} {self.direction} {self.v}: {self.props}"


@dataclass
class Hyperedge:
    e: set[Node]
    f: set[Node] | Node | None = None
    direction: Edge.Direction = Edge.Direction.UNDIRECTED
    props: Attributes | None = None

    def __repr__(self) -> str:
        return f"(Hyperdge) {self.e} {self.direction} {self.f}: {self.props}"


class KeyTransformer(Transformer):
    def DIGIT(self, args):
        print(f"DIGIT: {args}")
        return int(args)

    def ESCAPED_STRING(self, args):
        return str(args)[1:-1]

    def UNQUOTED_KEY(self, args):
        # FIXME: DIGIT keys are returned as strings...
        return str(args)

    def key(self, args):
        return args[0]

    def key_set(self, args):
        # TODO: Throw exception for repeated set values
        return set(args)

class ValueTransformer(Transformer):
    def string(self, args):
        return str(args[0])

    def number(self, args):
        return float(args[0])

    def SIGNED_NUMBER(self, args):
        # TODO: use int when appropriate
        return float(args)

    def NLP(self, _args):
        return None

    def keyval(self, args):
        return (args[0],args[1])

    def keyval_list(self, args):
        # TODO: Throw exception for repeated keys
        return {k:v for k,v in args}

    def legacy_description(self, args):
        return args

    def description(self, args):
        return args[0]

class NodeTransformer(Transformer):
    def node(self, args):
        return args[0]

    def node_expr(self, args):
        nodes = [args[0]] if not isinstance(args[0], set) else list(args[0])
        desc = args[1] if len(args) > 1 else None
        return [Node(n, desc) for n in nodes]

    def node_doc(self, args):
        a = [a for a in args if isinstance(a, list)]
        return list(chain.from_iterable(a))

class EdgeTransformer(Transformer):
    def E_LR(self, _args):
        return Edge.Direction.DIRECTED
    def lr(self, args):
        return (args[0], Edge.DirectionOrder.LR)

    def E_RL(self, _args):
        return Edge.Direction.DIRECTED
    def rl(self, args):
        return (args[0], Edge.DirectionOrder.RL)

    def E_BI(self, _args):
        return Edge.Direction.BIDIRECTIONAL
    def bi(self, args):
        return (args[0], Edge.DirectionOrder.BI)

    def E_UN(self, _args):
        return Edge.Direction.UNDIRECTED
    def un(self, args):
        return (args[0], None)

    @staticmethod
    def __build_edge(u, v, direction = Edge.Direction.UNDIRECTED, details = None):
        if isinstance(u, set):
            return Hyperedge(u, v, direction, details)
        return Edge(u, v, direction, details)

    def edge_expr(self, args):
        # Normalize edge direction order
        if args[1][0] == Edge.Direction.DIRECTED:
            if args[1][1] == Edge.DirectionOrder.RL:
                args[1] = (Edge.Direction.DIRECTED, Edge.DirectionOrder.LR)
                args[2], args[0] = args[0], args[2]

        return self.__build_edge(args[0], args[2], args[1][0], args[3] if len(args) > 3 else None)

    def legacy_edge_expr(self, args):
        args = args[:-1]
        if len(args) > 2:
            if len(args) == 3:
                details = args[2]
            else:
                details = args[2:-1]
        else:
            details = None
        return self.__build_edge(args[0], args[1], Edge.Direction.UNDIRECTED, details)

    def edge_doc(self, args):
        return [e for e in args if isinstance(e, Edge) or isinstance(e, Hyperedge)]

class GraphTransformer(Transformer):
    def graph_prop(self, args):
        return args[0]

    def graph_doc(self, args):
        return {a[0]:a[1] for a in args if isinstance(a, tuple)}

    def block(self, args):
        return args[0]

@dataclass
class Graph:
    nodes: list[Node]
    edges: list[Edge | Hyperedge]
    properties: Attributes | None = None

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
                if isinstance(edge.f, set):
                    edge_nodes.update(edge.f)
                else:
                    edge_nodes.add(edge.f)
        print(node_names)
        print(edge_nodes)
        diff = edge_nodes.difference(node_names)
        assert len(diff) == 0, f"Edges contain undefined nodes! {diff}"

    def __repr__(self) -> str:
        s = "Graph:\n"
        if self.properties is not None:
            s += "\tProperties:\n"
            for k,v in self.properties.items():
                s += f"\t\t{k}: {v}\n"
        s += "\tNodes:\n"
        for node in self.nodes:
            s += f"\t\t{node}\n"
        if self.edges:
            s += "\tEdges:\n"
            for edge in self.edges:
                s += f"\t\t{edge}\n"
        return s

