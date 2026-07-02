import pytest
import rich


def test_lark():
    from py_rgd.parser import Parser

    s = """
# graph
# nodes
// Comment test
A
B
#
A -> B
    """
    print(s)
    result = Parser.lark(s)
    rich.print(result)

