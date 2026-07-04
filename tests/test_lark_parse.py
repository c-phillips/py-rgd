import pytest
import rich


def test_lark():
    from py_rgd.parser import rgd_loads

    s = """
    # graph
    # nodes
    {A, B, C, "😀"}: value = "hey there"
    {D, E}: label = "follower"
    42: label = "Numeric node key"
    C: label = "leader"
    D: value = 11.111
    #
    A -> B
    C -> A: label = "custom", another = 12

    # graph
    example = 42
    # nodes
    A: 2026-04-07
    """

    tree = rgd_loads(s)
    rich.print(tree)

