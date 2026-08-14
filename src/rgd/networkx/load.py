import warnings

try:
    import networkx as nx
except ImportError:
    raise ImportError("Could not import networkx")

from rgd.graph import Edge, Hyperedge
from rgd.parser import loads as rgd_loads, RGDStream, RGDSource


def loads(
    source: RGDSource,
    validate: bool = True,
) -> nx.Graph | list[nx.Graph]:
    basic_graphs = rgd_loads(source, validate)

    # Networkx has no hypergraph features.
    #   Raise error if any graphs include hyperedges.
    if any([
        any([isinstance(edge, Hyperedge) for edge in graph.edges])
        for graph in basic_graphs
    ]):
        raise NotImplementedError("Networkx does not support hyperedges")

    nx_graphs = []
    for g in basic_graphs:

        # TODO: Figure out if we want to support a secondary output containing
        #       these properties, e.g. 
        #       `graphs, props = rgd.networkx_loads(..., retain_props=True)`
        if g.props:
            warnings.warn("""\
            Loaded RGD graph contains graph-level properties;\
            these are not supported by NetworkX, so these properties will be dropped!\
            """)

        nx_type = nx.Graph
        for edge in g.edges:
            if edge.direction != Edge.Direction.UNDIRECTED:
                nx_type = nx.DiGraph
        ng = nx_type()

        for node in g.nodes:
            props = node.props if node.props is not None else {}
            if not isinstance(node.props, dict):
                props = {"attributes": props}
            ng.add_node(node.key, **props)
        
        for edge in g.edges:
            props = edge.props if edge.props is not None else {}
            if not isinstance(edge.props, dict):
                props = {"attributes": props}
            ng.add_edge(edge.u, edge.v, **props)
            if edge.direction == Edge.Direction.BIDIRECTIONAL  \
            or edge.direction == Edge.Direction.UNDIRECTED:
                ng.add_edge(edge.v, edge.u, **props)

        nx_graphs.append(ng)

    if len(nx_graphs) == 1:
        return nx_graphs[0]
    return nx_graphs


def load(
    fp: RGDStream,
) -> nx.Graph | list[nx.Graph]:
    return loads(fp.read())

