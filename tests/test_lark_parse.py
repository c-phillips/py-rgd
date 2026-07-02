import pytest
import rich


def test_lark():
    from py_rgd.parser import Parser

    s = """
# graph
test = "prop"
another = ["list", "of", 12]
# nodes
// Comment test
A: label = "leader", value = 12
B: [1,2,3]
"crazy$key"
"😀"
#
A -> B
B C 12
    """
    print(s)
    result = Parser.lark(s)
    rich.print(result)

