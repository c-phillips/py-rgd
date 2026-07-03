import pytest
import rich


def test_lark():
    from py_rgd import rgd_loads

    s = """
    {A, B, C, "😀"} hey there
    42: label = "Numeric node key"
    #
    A -> B: 12
    C <- B: 5
    D -- "what"
    E <> Z
    {B, C} -> {A}
    A B buddy boy 12

    """

    graphs = rgd_loads(s)
    rich.print(graphs)

