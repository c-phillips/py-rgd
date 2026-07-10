try:
    import networkx as nx
except:
    raise ImportError("Could not import networkx")

from py_rgd.graph import Edge, Hyperedge
from py_rgd.parser import loads

def networkx_loads(
    input: str,
    validate: bool = True,
) -> nx.Graph | list[nx.Graph]:
    basic_graphs = loads(input, validate)

    # Networkx has no hypergraph features.
    #   Raise error if any graphs include hyperedges.
    if any([
        any([isinstance(edge, Hyperedge) for edge in graph.edges])
        for graph in basic_graphs
    ]):
        raise NotImplementedError("Networkx does not support hyperedges")

    nx_graphs = []
    for g in basic_graphs:
        nx_type = nx.Graph
        for edge in g.edges:
            if edge.direction != Edge.Direction.UNDIRECTED:
                nx_type = nx.DiGraph
        ng = nx_type()
        for node in g.nodes:
            props = node.props if node.props is not None else dict()
            if not isinstance(node.props, dict):
                props = {"attributes": props}
            ng.add_node(node.key, **props)
        
        for edge in g.edges:
            props = edge.props if edge.props is not None else dict()
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

