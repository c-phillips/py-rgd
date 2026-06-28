from dataclasses import dataclass
from enum import Enum


from .attributes import Attributes


@dataclass
class Node[T]:
    key: T
    props: Attributes


class EdgeDirection(Enum):
    UNDIRECTED = 0
    DIRECTED = 1
    BIDIRECTIONAL = 2


@dataclass
class Edge:
    u: Node
    v: Node
    direction: EdgeDirection
    props: Attributes


@dataclass
class Hyperedge:
    e: set[Node]
    props: Attributes
    f: set[Node] | Node | None = None
    direction: EdgeDirection = EdgeDirection.UNDIRECTED


@dataclass
class Graph:
    nodes: list[Node]

