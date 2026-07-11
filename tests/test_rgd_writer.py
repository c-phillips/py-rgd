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
        props={}
    )
    ans = dedent(
    """\
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

