from collections.abc import Iterable
from functools import partial

try:
    from torch_geometric.data import Data
except ImportError:
    raise ImportError("Could not import necessary Pytorch Geometric dependencies")

from rgd.graph import Graph
from rgd.writer import dumps as rgd_dumps, TextWrite
from rgd.pyg.encoders import NodeEncoder, EdgeEncoder, GraphEncoder


def _convert_data(
    data: Data,
    node_encoder:  NodeEncoder,
    edge_encoder:  EdgeEncoder  | None = None,
    graph_encoder: GraphEncoder | None = None,
) -> Graph:
    nodes = node_encoder.decode(data)
    edges = edge_encoder.decode(data)  if edge_encoder  is not None else []
    props = graph_encoder.decode(data) if graph_encoder is not None else []
    return Graph(nodes, edges, props)


def dumps(
    graphs: Data | Iterable[Data],
    node_encoder:  NodeEncoder,
    edge_encoder:  EdgeEncoder  | None = None,
    graph_encoder: GraphEncoder | None = None,
) -> str:
    if isinstance(graphs, Data):
        graphs = [graphs]
    rgd_graphs = list(map(
        partial(_convert_data,
            node_encoder=node_encoder,
            edge_encoder=edge_encoder,
            graph_encoder=graph_encoder,
        ),
        graphs
    ))
    return rgd_dumps(rgd_graphs)


def dump(
    graphs: Data | Iterable[Data],
    fp: TextWrite,
    node_encoder:  NodeEncoder,
    edge_encoder:  EdgeEncoder  | None = None,
    graph_encoder: GraphEncoder | None = None,
):
    fp.write(dumps(graphs, node_encoder, edge_encoder, graph_encoder))
