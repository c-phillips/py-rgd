import pytest
import rich


def test_lark():
    from py_rgd.graph import Graph
    from py_rgd.parser import _lark_parse

    s = """
    # graph
    # nodes
    {A, B, C, "😀"} hey there
    42: label = "Numeric node key"
    #
    A -> B: 12
    C <- B: 5
    D -- "what"
    E <> Z
    {B, C} -> {A}
    A B buddy boy 12

    # graph
    # nodes
    """
    # print(s)
    # result = _lark_parse(s)
    # rich.print(result)

    G = Graph.loads(s)
    rich.print(G)


