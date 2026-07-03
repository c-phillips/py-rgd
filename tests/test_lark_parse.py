import pytest
import rich


def test_lark():
    from py_rgd.parser import _lark_parse

    s = """
    # graph
    # nodes
    {A, B, C, "😀"} hey there
    #
    A -> B: 12
    {B, C} -> {A}
    A B buddy boy 12

    # graph
    # nodes
    """
    print(s)
    result = _lark_parse(s)
    rich.print(result)

