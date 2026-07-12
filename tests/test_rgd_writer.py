from textwrap import dedent

import pytest

from rgd import dumps, loads
from rgd.graph import Graph, Node, Edge, Hyperedge


def test_write_basic():
    graph = Graph(
        nodes=[
            Node("A"),
            Node("B"),
        ],
        edges=[
            Edge("A", "B")
        ],
        props={"property": "test"}
    )
    ans = dedent(
    """\
    # graph
    property = "test"

    # nodes
    A
    B
    
    # edges
    A -- B
    """)
    out = dumps(graph)
    assert out == ans
    regraph = loads(out)[0]
    assert regraph == graph


def test_write_descriptions():
    # TODO: Test for efficient node-set definitions
    graph = Graph(
        nodes = [
            Node("A", {"label": "leader"}),
            Node("B", {"label": "follower"}),
            Node("C", {"label": "follower", "another": "something else"}),
        ],
        edges=[
            Edge("A","B", props={"weight": 1.0, "another": "hey"}),
            Edge("B","C", props={"weight": 2.0}),
            Edge("C","A", "->", props={"weight": 3.0}),
        ],
        props={},
    )
    ans = dedent(
    """\
    # nodes
    A: label = "leader"
    B: label = "follower"
    C: label = "follower", another = "something else"

    # edges
    A -- B: weight = 1.0, another = "hey"
    B -- C: weight = 2.0
    C -> A: weight = 3.0
    """)
    out = dumps(graph)
    assert out == ans
    regraph = loads(out)[0]
    assert regraph == graph

def test_write_multiple_graphs():
    graphs = [
        Graph(
            nodes = [Node("A"), Node("B"), Node("C")],
            edges = [Edge("A","B"), Edge("B","C", props={"weight": 1.0})],
            props = {},
        ),
        Graph( 
            nodes = [Node("X"), Node("Y"), Node("Z")],
            edges = [Edge("X","Y"), Edge("Y","Z", props={"weight": 2.0})],
            props = {"something": "value"},
        )
    ]
    ans = dedent(
    """\
    # graph
    # nodes
    A
    B
    C

    # edges
    A -- B
    B -- C: weight = 1.0

    # graph
    something = "value"
    
    # nodes
    X
    Y
    Z

    # edges
    X -- Y
    Y -- Z: weight = 2.0
    """)

    out = dumps(graphs)
    assert out == ans
    regraphs = loads(out)
    assert len(regraphs) == len(graphs)
    for idx, (i,o) in enumerate(zip(graphs, regraphs)):
        assert i == o

