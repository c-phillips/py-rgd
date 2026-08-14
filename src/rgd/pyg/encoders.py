from collections.abc import Iterable
from typing import Protocol

try:
    import torch
    from torch_geometric.data import Data
except ImportError:
    raise ImportError("Could not import necessary Pytorch Geometric dependencies")

from rgd.attributes import Attributes
from rgd.graph import Node, Edge, Hyperedge


class NodeEncoder(Protocol):
    def encode(self, node: Node) -> dict[str, torch.Tensor]:
        ...

    def decode(self, data: Data) -> Iterable[Node]:
        ...


class EdgeEncoder(Protocol):
    def encode(self, edge: Edge, u: Node, v: Node) -> dict[str, torch.Tensor]:
        ...

    def encode_empty(self) -> dict[str, torch.Tensor]:
        ...

    def decode(self, data: Data) -> Iterable[Edge | Hyperedge]:
        ...


class GraphEncoder(Protocol):
    def encode(self, props: Attributes) -> dict[str, torch.Tensor]:
        ...

    def decode(self, data: Data) -> Attributes:
        ...

