import pytest
import math

from py_rgd import loads



@pytest.mark.parametrize(
    "src",
    [
        "",
        "\n\n",
        "// comment only\n",
        "\n// comment\n\n// another comment\n",
    ],
)
def test_empty_documents_parse(src: str) -> None:
    """
    Validate that an empty document, or document containing only
    comments/blank lines returns an empty graph.
    """
    graph = loads(src)[0]
    assert graph.nodes == []
    assert graph.edges == []
    assert graph.props == {}



def test_headerless_nodes_node_sets_and_descriptions() -> None:
    src = r'''
A
B: label = "leader"
{C, D, "node with spaces"}: group = "followers"
E: [1, 2, "three"]
'''

    graph = loads(src)[0]

    assert graph.props == {}
    assert graph.edges == []
    assert graph.node_keys == {"A", "B", "C", "D", "node with spaces", "E"}

    assert graph.get_node("B").props["label"] == "leader"
    assert graph.get_node("C").props["group"] == "followers"
    assert graph.get_node("D").props["group"] == "followers"
    assert graph.get_node("node with spaces").props["group"] == "followers"

    assert graph.get_node("E").props == [1, 2, "three"]


def test_explicit_graph_properties_and_value_types() -> None:
    src = r'''
# graph
name = "value coverage"
dec = -17
pos = +99
hex = 0xDEAD_BEEF
oct = 0o755
bin = 0b1101
flt = 6.626e-34
flt2 = 224_617.445_991_228
inf = -inf
truth = true
literal = 'no escapes here'
basic = "Jos\xE9"
arr = [1, 2.0, true, "x", [3, 4]]
when = 1979-05-27T07:32Z
local_date = 1979-05-27
local_time = 07:32
# nodes
A
'''

    graph = loads(src)[0]
    props = graph.props
    assert props["name"] == "value coverage"
    assert props["dec"] == -17
    assert props["pos"] == 99
    assert props["hex"] == 0xDEADBEEF
    assert props["oct"] == 0o755
    assert props["bin"] == 0b1101
    assert props["flt"] == pytest.approx(6.626e-34)
    assert props["flt2"] == pytest.approx(224_617.445_991_228)
    assert math.isinf(props["inf"]) and props["inf"] < 0
    assert props["truth"] is True
    assert props["literal"] == "no escapes here"
    assert props["basic"] == "José"
    assert props["arr"] == [1, 2.0, True, "x", [3, 4]]

    # Accept either Python date/time objects or strings, depending on transformer policy.
    assert "when" in props
    assert "local_date" in props
    assert "local_time" in props

    assert graph.node_keys == {"A"}
    assert graph.edges == []


@pytest.mark.parametrize(("name", "src"),
[
## VALUES
(
"repeated_value_in_key_set",
r"""
{A, B, C, D, A}
"""
),
(
"float_missing_integer_part",
r"""
funny: .24
"""
),
(
"float_missing_fraction_part",
r"""
funnier: 25.
"""
),
(
"invalid_integer_leading_zero",
r"""
schmitty_werbenjägermanjensen: 01
"""
),
(
"invalid_string_escape",
r"""
itsa: "joke\s"
"""
),
## SECTIONS
(
"invalid_section",
r"""
# kiwi
A: 42
"""
),
(
"graph_doc_empty_nodes",
r"""
# graph
phaser.setting = "STUN"
# nodes
"""
),
(
"explicit_empty_nodes_section",
r"""
# nodes
"""
),
(
"explicit_empty_nodes_section_with_comment",
r"""
# nodes
// Han shot first
"""
),
(
"edge_section_without_nodes",
r"""
# nodes
{A, B, C}
# graph
key = "value"
# edges
A -> B
"""
),
(
"edge_section_with_undefined_nodes",
r"""
{A, B, C}
# edges
A -> B
C <- B
A -> D
"""
),
(
"legacy_edge_section_without_nodes",
r"""
#
a b
"""
),
## GRAPH
(
"invalid_graph_property",
r"""
# graph
12
# nodes
{A, B, C}
"""
),

## MULTIPLE GRAPHS
(
"multiple_graphs_without_first_graph_header",
r"""
{A, B, C}

# graph
# nodes
{A, B, C, D}
"""
),
(
"multiple_graphs_without_graph_headers",
r"""
# nodes
{A, B, C}
# edges
A -> B

# nodes
{A, B, C, D}
# edges
B -> C
C -> D
"""
),

## NODES
(
"node_set_with_legacy_description",
r"""
{A, B} 12
"""
),

## LEGACY NODES
(
"legacy_nodes_with_keyvalue_description",
r"""
A key = "value"
"""
),

## EDGES
(
"edge_with_legacy_description",
r"""
{A, B, C}
#
A -> B nope
"""
),

## LEGACY EDGES
(
"legacy_edge_with_keyvalue_description",
r"""
A
B
#
A B: key = "value"
"""
),
])
def test_reject_invalid_rgd(name, src):
    with pytest.raises(Exception):
        loads(src)

