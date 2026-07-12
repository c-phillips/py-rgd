from textwrap import dedent

import pytest

try:
    import networkx as nx
except:
    raise ImportError("Could not import networkx")

from rgd.networkx import networkx_dumps

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

