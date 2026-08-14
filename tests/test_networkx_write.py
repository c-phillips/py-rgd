from pathlib import Path
from textwrap import dedent

try:
    import networkx as nx
except ImportError:
    raise ImportError("Could not import networkx")

from rgd.networkx import dumps as networkx_dumps


TEST_DATA = Path(__file__).parent/"data"


def test_networkx_write_digraph():
    digraph = nx.DiGraph()
    digraph.add_nodes_from(["A", "B", "C", "D", "E"])
    digraph.add_edges_from([
        ("A", "C"),
        ("B", "D"),
        ("E", "D"),
        ("E", "A", {"label":"custom", "value": 1.0}),
        ("A", "B", {"attributes":[1,2,3]}),
        ("B", "A", {"attributes": [1,2,3]})
    ])

    ans = dedent("""\
    # nodes
    A
    B
    C
    D
    E

    # edges
    A -> C
    A -> B: [1, 2, 3]
    B -> D
    B -> A: [1, 2, 3]
    E -> D
    E -> A: label = "custom", value = 1.0
    """)

    out = networkx_dumps(digraph)
    assert out == ans


def test_networkx_write_undir_graph():
    digraph = nx.Graph()
    digraph.add_nodes_from(["A", "B", "C", "D", "E"])
    digraph.add_edges_from([
        ("A", "C"),
        ("B", "D"),
        ("E", "D"),
        ("E", "A", {"label":"custom", "value": 1.0}),
        ("A", "B", {"attributes":[1,2,3]}),
    ])

    ans = dedent("""\
    # nodes
    A
    B
    C
    D
    E

    # edges
    A -- C
    A -- E: label = "custom", value = 1.0
    A -- B: [1, 2, 3]
    B -- D
    D -- E
    """)

    out = networkx_dumps(digraph)
    assert out == ans


def test_football():
    import rgd

    # Football GML file from http://www-personal.umich.edu/~mejn/netdata/football.zip
    with open(TEST_DATA/"football.gml", 'r') as fp:
        gml = fp.read()
    gml = gml.split("\n")[1:]
    k = nx.parse_gml(gml)  # parse gml data
    
    rgd_str = rgd.networkx.dumps(k)
    g = rgd.networkx.loads(rgd_str)
    assert len(g.nodes) == len(k.nodes)
    for node in g.nodes:
        assert node in k.nodes
    for edge in g.edges:
        assert edge in k.edges

