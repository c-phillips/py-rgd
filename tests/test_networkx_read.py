from textwrap import dedent

import pytest

try:
    import networkx as nx
except ImportError:
    raise ImportError("Could not import networkx")

from rgd.networkx import loads as networkx_loads


def test_networkx_parse_digraph():
    rgd_str = """
    # graph
    sample = 12.0
    # nodes
    {A, B, C, D, E}
    #
    A -> C
    B -> D
    D <- E
    E -> A: label = "custom", value = 1.0
    A <> B: [1,2,3]
    """

    graph = networkx_loads(rgd_str)
    assert isinstance(graph, nx.DiGraph)

    nodes_truth = {'A', 'B', 'C', 'D', 'E'}
    for node in graph.nodes:
        assert node in nodes_truth

    edges_truth = {
        ('A', 'C'),
        ('B', 'D'),
        ('E', 'D'),
        ('E', 'A'),
        ('A', 'B'),
        ('B', 'A'),
    }
    for edge in graph.edges:
        assert edge in edges_truth

    attrs = graph.edges[('E', 'A')]
    assert attrs['label'] == 'custom'
    assert attrs['value'] == 1.0

    attrs = graph.edges[('A', 'B')]
    assert attrs['attributes'] == [1.0, 2.0, 3.0]
    attrs = graph.edges[('B', 'A')]
    assert attrs['attributes'] == [1.0, 2.0, 3.0]


def test_networkx_parse_undir_graph():
    rgd_str = """
    # graph
    sample = 12.0
    # nodes
    {A, B, C, D, E}
    #
    A -- C
    B -- D
    D -- E
    E -- A: label = "custom", value = 1.0
    A <> B: [1,2,3]
    """

    graph = networkx_loads(rgd_str)
    assert isinstance(graph, nx.Graph)

    nodes_truth = {'A', 'B', 'C', 'D', 'E'}
    for node in graph.nodes:
        assert node in nodes_truth

    edges_truth = {
        ('A', 'C'),
        ('B', 'D'),
        ('E', 'D'),
        ('E', 'A'),
        ('A', 'B'),
        ('B', 'A'),
    }
    for edge in graph.edges:
        assert edge in edges_truth or edge[::-1] in edges_truth

    attrs = graph.edges[('E', 'A')]
    assert attrs['label'] == 'custom'
    assert attrs['value'] == 1.0

    attrs = graph.edges[('A', 'B')]
    assert attrs['attributes'] == [1.0, 2.0, 3.0]
    attrs = graph.edges[('B', 'A')]
    assert attrs['attributes'] == [1.0, 2.0, 3.0]


def test_networkx_parse_mixedgraph():
    rgd_str = """
    # graph
    sample = 12.0
    # nodes
    {A, B, C, D, E}
    #
    A -> C
    B -- D
    D -- E
    E -- A: label = "custom", value = 1.0
    A <> B: [1,2,3]
    """

    graph = networkx_loads(rgd_str)
    assert isinstance(graph, nx.DiGraph)

    nodes_truth = {'A', 'B', 'C', 'D', 'E'}
    for node in graph.nodes:
        assert node in nodes_truth

    edges_truth = {
        ('A', 'C'),
        ('B', 'D'),
        ('D', 'B'),
        ('E', 'D'),
        ('D', 'E'),
        ('E', 'A'),
        ('A', 'E'),
        ('A', 'B'),
        ('B', 'A'),
    }
    for edge in graph.edges:
        assert edge in edges_truth

    attrs = graph.edges[('E', 'A')]
    assert attrs['label'] == 'custom'
    assert attrs['value'] == 1.0

    attrs = graph.edges[('A', 'B')]
    assert attrs['attributes'] == [1.0, 2.0, 3.0]
    attrs = graph.edges[('B', 'A')]
    assert attrs['attributes'] == [1.0, 2.0, 3.0]


@pytest.mark.parametrize(("name", "src"), [
(
    "invalid_newtorkx_hyperedge",
    r"""
    # graph
    sample = 12.0
    # nodes
    {A, B, C, D, E}
    #
    {A, B, C}
    """
),
(
    "invalid_newtorkx_directed_hyperedge",
    r"""
    # graph
    sample = 12.0
    # nodes
    {A, B, C, D, E}
    #
    {A, B, C} -> {D, E}
    """
),
])
def test_networkx_no_hyperedges(name, src):
    with pytest.raises(Exception):
        networkx_loads(dedent(src))


def test_karate_club():
    src = dedent("""\
    // W. W. Zachary, An information flow model for conflict and fission in small groups, Journal of Anthropological Research 33, 452-473 (1977).
    # nodes
    {2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33}
    1:  label = "instructor"
    34: label = "president"

    # edges
    2 -- 1
    3 -- 1
    3 -- 2
    4 -- 1
    4 -- 2
    4 -- 3
    5 -- 1
    6 -- 1
    7 -- 1
    7 -- 5
    7 -- 6
    8 -- 1
    8 -- 2
    8 -- 3
    8 -- 4
    9 -- 1
    9 -- 3
    10 -- 3
    11 -- 1
    11 -- 5
    11 -- 6
    12 -- 1
    13 -- 1
    13 -- 4
    14 -- 1
    14 -- 2
    14 -- 3
    14 -- 4
    17 -- 6
    17 -- 7
    18 -- 1
    18 -- 2
    20 -- 1
    20 -- 2
    22 -- 1
    22 -- 2
    26 -- 24
    26 -- 25
    28 -- 3
    28 -- 24
    28 -- 25
    29 -- 3
    30 -- 24
    30 -- 27
    31 -- 2
    31 -- 9
    32 -- 1
    32 -- 25
    32 -- 26
    32 -- 29
    33 -- 3
    33 -- 9
    33 -- 15
    33 -- 16
    33 -- 19
    33 -- 21
    33 -- 23
    33 -- 24
    33 -- 30
    33 -- 31
    33 -- 32
    34 -- 9
    34 -- 10
    34 -- 14
    34 -- 15
    34 -- 16
    34 -- 19
    34 -- 20
    34 -- 21
    34 -- 23
    34 -- 24
    34 -- 27
    34 -- 28
    34 -- 29
    34 -- 30
    34 -- 31
    34 -- 32
    34 -- 33
    """)
    g = networkx_loads(src)
    k = nx.karate_club_graph()
    assert len(g.nodes) == len(k.nodes)
    for node in g.nodes:
        assert int(node)-1 in k.nodes
    for edge in g.edges:
        assert (int(edge[0])-1, int(edge[1])-1) in k.edges

