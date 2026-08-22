import math
from textwrap import dedent

import pytest

from rgd import loads



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
    src = dedent(r'''
    A
    B: label = "leader"
    {C, D, "node with spaces"}: group = "followers"
    E: [1, 2, "three"]
    ''')

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
    src = dedent(r'''
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
    nothing = null
    # nodes
    A 😉
    "🫣"
    ''')

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
    assert props["nothing"] is None

    # Accept either Python date/time objects or strings, depending on transformer policy.
    assert "when" in props
    assert "local_date" in props
    assert "local_time" in props

    assert graph.node_keys == {"A", "🫣"}
    assert graph.get_node("A").props == ["😉"]
    assert graph.edges == []


def test_ordinary_edges_directions_descriptions_and_normalization() -> None:
    src = dedent(r'''
    # nodes
    A
    B
    C
    D
    # edges
    A -> B: weight = 5.0
    C <- B: label = "reverse normalized"
    A -- C
    B <> D: active = true
    ''')

    graph = loads(src)[0]

    assert graph.props == {}
    assert graph.node_keys == {"A", "B", "C", "D"}
    assert len(graph.edges) == 4

    e1 = graph.get_edge("A", "B", "->")
    assert e1.props["weight"] == pytest.approx(5.0)

    # C <- B should normalize to B -> C in your EdgeTransformer.
    e2 = graph.get_edge("B", "C", "->")
    assert e2.props["label"] == "reverse normalized"

    e3 = graph.get_edge("A", "C")
    assert e3 is not None

    e4 = graph.get_edge("B", "D", "<>")
    assert e4.props["active"] is True


def test_hyperedges_and_directed_hyperedges() -> None:
    src = dedent(r'''
    # nodes
    {A, B, C, D, E, F, G}
    # edges
    {A, B, C}: hyperproperty = 42.0
    {B, C} -> {E, F, G}: directed-hyperedge = true
    D -- A
    ''')

    graph = loads(src)[0]

    assert graph.node_keys == {"A", "B", "C", "D", "E", "F", "G"}
    assert len(graph.edges) == 3

    h1 = graph.get_hyperedge({"A", "B", "C"})
    assert h1.props["hyperproperty"] == pytest.approx(42.0)

    h2 = graph.get_hyperedge({"B", "C"}, {"E", "F", "G"}, "->")
    assert h2.props["directed-hyperedge"] is True

    e1 = graph.get_edge("D", "A", "--")
    assert e1 is not None


def test_tgf_style_legacy_nodes_and_edges() -> None:
    src = dedent(r'''
    A leader
    B follower
    C follower
    #
    C A at 1979-05-27T07:33Z
    B A at 1979-05-30T12:05Z
    ''')

    graph = loads(src)[0]

    assert graph.props == {}
    assert graph.node_keys == {"A", "B", "C"}
    assert len(graph.edges) == 2

    # Exact legacy description representation may be list[str], list[list[str]], etc.,
    # depending on how your legacy_description transformer flattens values.
    assert graph.get_node("A").props is not None
    assert graph.edges[0].props is not None

    assert graph.get_edge("C", "A") is not None
    assert graph.get_edge("B", "A") is not None


def test_numeric_node_keys_are_keys_not_numbers() -> None:
    src = dedent(r'''
    # nodes
    42: label = "Numeric node key"
    7
    # edges
    42 -- 7
    ''')
    graph = loads(src)[0]

    assert len(graph.nodes) == 2
    assert len(graph.edges) == 1
    assert graph.node_keys == {"42", "7"}
    assert graph.get_node("42").props["label"] == "Numeric node key"
    assert graph.get_edge("42", "7") is not None


def test_multiple_graphs() -> None:
    src = dedent(r'''
    # graph
    name = "g1"
    # nodes
    A

    # graph
    name = "g2"
    # nodes
    B
    C
    # edges
    B -- C
    ''')

    graphs = loads(src)
    assert len(graphs) == 2

    assert graphs[0].props["name"] == "g1"
    assert graphs[0].node_keys == {"A"}
    assert graphs[0].edges == []

    assert graphs[1].props["name"] == "g2"
    assert graphs[1].node_keys == {"B", "C"}
    assert graphs[1].get_edge("B", "C") is not None


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
        loads(dedent(src))


def test_undefined_edge_endpoint_is_invalid() -> None:
    with pytest.raises(Exception):
        loads(dedent(r'''
        # nodes
        A
        # edges
        A -- B
        '''))


@pytest.mark.parametrize(("name", "src"), [
(
    "duplicate_keyvalue_node_properties",
    r'''
    A: property = "first"
    A: property = "second"
    '''
),
(
    "duplicate_value_only_node_properties",
    r'''
    A: "first"
    A: "second"
    '''
),
])
def test_duplicate_node_property_is_invalid(name, src) -> None:
    with pytest.raises(Exception):
        loads(dedent(src))

def test_combine_node_properties() -> None:
    graph = loads(dedent(r'''
    A: property = "first"
    A: another  = "second"
    '''))[0]
    
    assert graph.get_node("A").props['property'] == "first"
    assert graph.get_node("A").props['another']  == "second"


@pytest.mark.parametrize(("name", "src"), [
(
    "duplicate_keyvalue_edge_properties",
    r'''
    {A, B}
    #
    A -> B: property = "first"
    A -> B: property = "second"
    '''
),
(
    "duplicate_value_only_edge_properties",
    r'''
    {A, B}
    #
    A -> B: "first"
    A -> B: "second"
    '''
),
])
def test_duplicate_edge_property_is_invalid(name, src) -> None:
    with pytest.raises(Exception):
        loads(dedent(src))

def test_combine_edge_properties() -> None:
    graph = loads(dedent(r'''
    {A, B}
    #
    A -- B: property = "first"
    A -- B: another  = "second"
    '''))[0]
    
    assert graph.get_edge("A", "B").props['property'] == "first"
    assert graph.get_edge("A", "B").props['another']  == "second"


def test_node_reference() -> None:
    graphs = loads(dedent(r'''
    # graph
    # nodes
    {A, B}: prop = true

    # graph
    # nodes
    &A

    # graph
    # nodes
    &B

    # graph
    # nodes
    &{A,B}

    # graph
    # nodes
    &*

    # graph
    # nodes
    &A: new = 1
    C

    # graph
    # nodes
    &*
    '''))
    
    assert len(graphs) == 7

    # Check the first graph
    g0_A = graphs[0].get_node("A")
    assert g0_A is not None
    assert g0_A.props["prop"] == True
    g0_B = graphs[0].get_node("B")
    assert g0_B is not None
    assert g0_B.props["prop"] == True

    # Check referencing A from g0
    assert len(graphs[1].nodes) == 1
    g1_A = graphs[1].get_node("A")
    assert g1_A is not None
    assert g1_A.props["prop"] == True

    # Check referencing B from g0
    assert len(graphs[2].nodes) == 1
    g2_B = graphs[2].get_node("B")
    assert g2_B is not None
    assert g2_B.props["prop"] == True

    # Check referencing A and B from g0
    assert len(graphs[3].nodes) == 2
    g3_A = graphs[3].get_node("A")
    assert g3_A is not None
    assert g3_A.props["prop"] == True
    g3_B = graphs[3].get_node("B")
    assert g3_B is not None
    assert g3_B.props["prop"] == True

    # Check referencing all from g0
    assert len(graphs[4].nodes) == 2
    g4_A = graphs[4].get_node("A")
    assert g4_A is not None
    assert g4_A.props["prop"] == True
    g4_B = graphs[4].get_node("B")
    assert g4_B is not None
    assert g4_B.props["prop"] == True

    # Check referencing A from g0
    assert len(graphs[5].nodes) == 2
    g5_A = graphs[5].get_node("A")
    assert g5_A is not None
    assert g5_A.props["prop"] == True
    assert g5_A.props["new"] == 1
    assert graphs[5].get_node("C") is not None

    # Check referencing all from all previous
    assert len(graphs[6].nodes) == 3
    g6_A = graphs[6].get_node("A")
    assert g6_A is not None
    assert g6_A.props["prop"] == True
    assert g5_A.props["new"] == 1
    g6_B = graphs[6].get_node("B")
    assert g6_B is not None
    assert g6_B.props["prop"] == True
    assert graphs[6].get_node("C") is not None


@pytest.mark.parametrize(("name", "src", "answer"),
[
(
    "bms_single_line",
    r'''
    # nodes
    A: """single line multiline string"""
    ''',
    "single line multiline string"
),
(
    "bms_next_line",
    r'''
    # nodes
    A: """
    next line multiline string"""
    ''',
    "next line multiline string"
),
(
    "bms_next_line_newline",
    r'''
    # nodes
    A: """
    next line multiline string newline
    """
    ''',
    "next line multiline string newline\n"
),
(
    "bms_next_line_newline_indent",
    r'''
    # nodes
    A:  """
        next line multiline string newline
        """
    ''',
    "next line multiline string newline\n"
),
(
    "bms_newline_next_line_newline_indent",
    r'''
    # nodes
    A:  """

        next line multiline string newline
        """
    ''',
    "\nnext line multiline string newline\n"
),
(
    "bms_newline_next_line_newline_indent_extra",
    r'''
    # nodes
    A:  """

            next line multiline string newline
        """
    ''',
    "\nnext line multiline string newline\n"
),
(
    "bms_newline_next_line_newline_indent_extra",
    r'''
    # nodes
    A:  """
    ┌─────────────────┐
    │ Line One Text   │
    │ Line Two Text   │
    └─────────────────┘
    """
    ''',
    "┌─────────────────┐\n│ Line One Text   │\n│ Line Two Text   │\n└─────────────────┘\n"
),
])
def test_basic_multiline_string(name, src, answer):
    g = loads(dedent(src))[0]
    assert g.get_node("A").props == answer


@pytest.mark.parametrize(("name", "src", "answer"),
[
(
    "lms_single_line",
    r"""
    # nodes
    A: '''single line multiline string'''
    """,
    "single line multiline string"
),
(
    "lms_next_line",
    r"""
    # nodes
    A: '''
    next line multiline string'''
    """,
    "next line multiline string"
),
(
    "lms_next_line_newline",
    r"""
    # nodes
    A: '''
    next line multiline string newline
    '''
    """,
    "next line multiline string newline\n"
),
(
    "lms_next_line_newline_indent",
    r"""
    # nodes
    A:  '''
        next line multiline string newline
        '''
    """,
    "next line multiline string newline\n"
),
(
    "lms_newline_next_line_newline_indent",
    r"""
    # nodes
    A:  '''

        next line multiline string newline
        '''
    """,
    "\nnext line multiline string newline\n"
),
(
    "lms_newline_next_line_newline_indent_extra",
    r"""
    # nodes
    A:  '''

            next line multiline string newline
        '''
    """,
    "\nnext line multiline string newline\n"
),
(
    "lms_newline_next_line_newline_indent_extra",
    r"""
    # nodes
    A:  '''
    ┌─────────────────┐
    │ Line One Text   │
    │ Line Two Text   │
    └─────────────────┘
    '''
    """,
    "┌─────────────────┐\n│ Line One Text   │\n│ Line Two Text   │\n└─────────────────┘\n"
),
(
    "lms_with_newline_escaped",
    r"""
    # nodes
    A:  '''

            next line multiline string newline\n\n
        '''
    """,
    "\nnext line multiline string newline\\n\\n\n"
),
])
def test_literal_multiline_string(name, src, answer):
    g = loads(dedent(src))[0]
    assert g.get_node("A").props == answer


def test_edge_identity():
    graph = loads(dedent(r"""
    # nodes
    {A,B}
    # edges
    A -> B &1
    A -> B &2: tag = "exists"
    A -> B &*
    A -> B &*: tag = "another one"
    """))[0]
    assert len(graph.nodes) == 2
    assert len(graph.edges) == 4

