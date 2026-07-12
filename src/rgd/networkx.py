from typing import Iterable
import warnings

try:
    import networkx as nx
except:
    raise ImportError("Could not import networkx")

from rgd.graph import Graph, Node, Edge, Hyperedge
from rgd.parser import loads, RGDStream, RGDSource
from rgd.writer import dumps, TextWrite



def _convert_networkx_graph(graph: nx.Graph) -> Graph:
    nodes = []
    for n, props in graph.nodes(data=True):
        if isinstance(props, dict):
            if len(props) == 1 and 'attributes' in props:
                props = props['attributes']
        nodes.append(Node(n,props))

    edges = []
    direction = Edge.Direction.DIRECTED if isinstance(graph, nx.DiGraph) else Edge.Direction.UNDIRECTED
    for u,v,props in graph.edges(data=True):
        if isinstance(props, dict):
            if len(props) == 1 and 'attributes' in props:
                props = props['attributes']
        edges.append(Edge(u, v, direction, props))
    return Graph(nodes, edges, {})


def networkx_dumps(
    graphs: nx.Graph | Iterable[nx.Graph],
) -> str:
    if isinstance(graphs, (nx.Graph, nx.DiGraph)):
        graphs = [graphs]
    rgd_graphs = list(map(_convert_networkx_graph, graphs))
    return dumps(rgd_graphs)


def networkx_dump(
    graphs: nx.Graph | Iterable[nx.Graph],
    fp: TextWrite
):
    fp.write(networkx_dumps(graphs))


def networkx_loads(
    source: RGDSource,
    validate: bool = True,
) -> nx.Graph | list[nx.Graph]:
    basic_graphs = loads(source, validate)

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


def networkx_load(
    fp: RGDStream,
) -> nx.Graph | list[nx.Graph]:
    return networkx_loads(fp.read())

