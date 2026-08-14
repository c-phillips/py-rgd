from collections.abc import Iterable

try:
    import networkx as nx
except ImportError:
    raise ImportError("Could not import networkx")

from rgd.graph import Edge, Graph, Node
from rgd.writer import dumps as rgd_dumps, TextWrite


def _convert_networkx_graph(graph: nx.Graph) -> Graph:
    nodes = []
    for n, props in graph.nodes(data=True):
        if isinstance(props, dict) \
           and len(props) == 1 and 'attributes' in props:
                props = props['attributes']
        nodes.append(Node(n,props))

    edges = []
    direction = (
        Edge.Direction.DIRECTED if isinstance(graph, nx.DiGraph)
        else Edge.Direction.UNDIRECTED
    )
    for u,v,props in graph.edges(data=True):
        if isinstance(props, dict) \
           and len(props) == 1 and 'attributes' in props:
                props = props['attributes']
        edges.append(Edge(u, v, direction, props))
    return Graph(nodes, edges, {})


def dumps(
    graphs: nx.Graph | Iterable[nx.Graph],
) -> str:
    if isinstance(graphs, (nx.Graph, nx.DiGraph)):
        graphs = [graphs]
    rgd_graphs = list(map(_convert_networkx_graph, graphs))
    return rgd_dumps(rgd_graphs)


def dump(
    graphs: nx.Graph | Iterable[nx.Graph],
    fp: TextWrite
):
    fp.write(dumps(graphs))

