from textwrap import dedent

import pytest

try:
    import networkx as nx
except:
    raise ImportError("Could not import networkx")


def test_networkx_parse_digraph():
    from py_rgd.networkx import networkx_loads

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
    from py_rgd.networkx import networkx_loads

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
    from py_rgd.networkx import networkx_loads

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
    from py_rgd.networkx import networkx_loads

    with pytest.raises(Exception):
        networkx_loads(dedent(src))

