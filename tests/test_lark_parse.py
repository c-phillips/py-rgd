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
"crazy$key"
#
A -> B
    """
    print(s)
    result = Parser.lark(s)
    rich.print(result)

