import warnings
from collections import defaultdict

try:
    import torch
    from torch_geometric.data import Data
except ImportError:
    raise ImportError("Could not import necessary Pytorch Geometric dependencies")

from rgd.graph import Hyperedge
from rgd.parser import loads as rgd_loads, RGDStream, RGDSource
from rgd.pyg.encoders import NodeEncoder, EdgeEncoder, GraphEncoder


def loads(
    source: RGDSource,
    node_encoder:  NodeEncoder,
    edge_encoder:  EdgeEncoder  | None = None,
    graph_encoder: GraphEncoder | None = None,
    validate: bool = True,
) -> Data | list[Data]:
    basic_graphs = rgd_loads(source, validate)

    # Pytorch Geometric does support hypergraphs, but we haven't implemented it.
    #   Raise error if any graphs include hyperedges.
    if any([
        any([isinstance(edge, Hyperedge) for edge in graph.edges])
        for graph in basic_graphs
    ]):
        raise NotImplementedError("py-rgd does not support pyg hyperedges yet")

    pyg_graphs = []
    for g in basic_graphs:
        graph_props = {}
        if g.props:
            if graph_encoder is not None:
                graph_props = graph_encoder.encode(g.props)
            else:
                warnings.warn("""\
                Loaded RGD graph contains graph-level properties;\
                these are not supported by NetworkX, so these properties will be dropped!\
                """)

        node_idx = {n.key:i for i,n in enumerate(g.nodes)}
        node_props = defaultdict(list)
        for node in node_idx:
            for k,v in node_encoder.encode(g.get_node(node)).items():
                node_props[k].append(v)
        stacked_node_props = {k: torch.stack(v, dim=0).contiguous() for k,v in node_props.items()}

        if 'x' not in stacked_node_props:
            raise KeyError("You must return an entry for `x` from `node_encoder`")

        graph_y = graph_props.pop('y', None)
        if graph_y is not None and 'y' in stacked_node_props:
                warnings.warn("""\
                Loaded RGD graph contains graph-level label `y` AND node labels `y`;\
                node labels will override `y` in the returned `Data` object!\
                """)
        y = stacked_node_props.pop('y', graph_y)
        if y is None:
            raise KeyError("You must return a `y` label for the graph from either `node_encoder` or `graph_features`")

        edge_idx = torch.tensor([
            [node_idx[e.u], node_idx[e.v]]
            for e in g.edges
        ], dtype=torch.long).reshape(-1,2).t().contiguous()

        if edge_encoder is not None:
            edge_props = defaultdict(list)
            if g.edges:
                for edge in g.edges:
                    props = edge_encoder.encode(edge, g.get_node(edge.u), g.get_node(edge.v))
                    for k,v in props.items():
                        edge_props[k].append(v)
                stacked_edge_props = {k:torch.stack(v, dim=0).contiguous() for k,v in edge_props.items()}
            else:
                stacked_edge_props = edge_encoder.encode_empty()
        else:
            stacked_edge_props = {}

        pyg_graphs.append(Data(
            x=stacked_node_props.pop('x'),
            y=y,
            edge_index=edge_idx,
            **stacked_node_props,
            **stacked_edge_props,
            **graph_props,
        ))

    if len(pyg_graphs) == 1:
        return pyg_graphs[0]
    return pyg_graphs


def load(
    fp: RGDStream,
    node_encoder:  NodeEncoder,
    edge_encoder:  EdgeEncoder  | None = None,
    graph_encoder: GraphEncoder | None = None,
) -> Data | list[Data]:
    return loads(fp.read(), node_encoder, edge_encoder, graph_encoder)

