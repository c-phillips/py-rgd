from typing import Any
from dataclasses import dataclass
from enum import Enum

from lark import Transformer, Visitor

from .attributes import Attributes
from .parser import _lark_parse


@dataclass
class Node:
    key: Any
    props: Attributes


@dataclass
class Edge:
    class Direction(Enum):
        UNDIRECTED = 0
        DIRECTED = 1
        BIDIRECTIONAL = 2

    class DirectionOrder(Enum):
        LR = 0
        RL = 1
        BI = 2

    u: Node
    v: Node
    direction: Direction
    props: Attributes


@dataclass
class Hyperedge:
    e: set[Node]
    props: Attributes
    f: set[Node] | Node | None = None
    direction: Edge.Direction = Edge.Direction.UNDIRECTED


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

    def NLP(self, args):
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
        if len(args) > 1:
            return (args[0], args[1])
        return args[0]

class EdgeTransformer(Transformer):
    def E_LR(self, args):
        return Edge.Direction.DIRECTED
    def lr(self, args):
        return (args[0], Edge.DirectionOrder.LR)

    def E_RL(self, args):
        return Edge.Direction.DIRECTED
    def rl(self, args):
        return (args[0], Edge.DirectionOrder.RL)

    def E_BI(self, args):
        return Edge.Direction.BIDIRECTIONAL
    def bi(self, args):
        return (args[0], Edge.DirectionOrder.BI)

    def E_UN(self, args):
        return Edge.Direction.UNDIRECTED
    def un(self, args):
        return (args[0], None)

    def edge_expr(self, args):
        if args[1][0] == Edge.Direction.DIRECTED:
            # Normalize edge direction order
            if args[1][1] == Edge.DirectionOrder.RL:
                args[1] = (Edge.Direction.DIRECTED, Edge.DirectionOrder.LR)
                args[2], args[0] = args[0], args[2]
        args[1] = args[1][0]
        return tuple(args[:-1])

    def legacy_edge_expr(self, args):
        return tuple([args[0], (Edge.Direction.UNDIRECTED, None), args[1]] + args[2:-1])

@dataclass
class Graph:
    nodes: list[Node]
    edges: list[Edge | Hyperedge]

    @classmethod
    def loads(cls, input: str) -> 'Graph':
        tree = _lark_parse(input)
        tree = KeyTransformer().transform(tree)
        tree = ValueTransformer().transform(tree)
        tree = NodeTransformer().transform(tree)
        tree = EdgeTransformer().transform(tree)
        return tree


