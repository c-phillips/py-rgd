import pytest
import rich


def test_lark():
    from py_rgd.parser import Parser

    s = """
    # graph
    hey = "there"
    # nodes
    {A, B, C, "😀"} 12
    #
    A -> B
    {B, C} -> {A}
    """
    print(s)
    result = Parser.lark(s)
    rich.print(result)

