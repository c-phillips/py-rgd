from copy import deepcopy
from typing import Protocol, TypeVar, Any
from lark import Lark, Transformer

from rgd.transformer import RGDValueTransformer
from rgd.graph import (
    Edge,
    EdgeTransformer,
    Graph,
    GraphTransformer,
    Hyperedge,
    NodeTransformer,
    Node,
    NodeReference,
)


rgd_grammar = r"""
?start: rgd | empty_doc

empty_doc: NLP*

rgd: NLP* (graph_docs | headerless_doc)

graph_docs: graph_doc+

graph_doc: GRAPH_HEADER NLP graph_prop_line* NODE_HEADER NLP node_doc_body NLP*

headerless_doc: (NODE_HEADER NLP node_doc_body | node_doc_body) NLP*

node_doc_body: node_doc edge_doc?
node_doc: node_line+

edge_doc: edge_header NLP edge_line*

edge_header: EDGE_HEADER | LEGACY_EDGE_HEADER

graph_prop_line: graph_expression NLP
node_line: node_expr NLP
edge_line: edge_expr NLP

graph_expression: keyval


// ---------------------------------------------------------------------------
// Nodes
// ---------------------------------------------------------------------------

?node_expr: node_set description?       -> node_set_decl
          | key description             -> node_decl
          | key legacy_description      -> legacy_node_decl
          | key                         -> node_decl
          | REF key description?        -> node_reference_decl
          | REF key_set description?    -> node_set_reference_decl
          | REF "*" description?        -> all_nodes_reference_decl


// ---------------------------------------------------------------------------
// Edges
// ---------------------------------------------------------------------------

?edge_expr: endpoint edge_dir endpoint edge_identity? description? -> edge_decl
          | key_set edge_identity? description?                    -> hyper_edge_decl
          | key key edge_identity? legacy_description?             -> legacy_edge_decl

edge_identity: EDGE_REF "*" -> anonymous_edge_identity
             | EDGE_REF key -> named_edge_identity

edge_dir: E_LR -> lr
        | E_RL -> rl
        | E_BI -> bi
        | E_UN -> un

?endpoint: key | key_set


// ---------------------------------------------------------------------------
// Descriptions
// ---------------------------------------------------------------------------

?description: ":" (metadata | val)

legacy_description: legacy_value+

?legacy_value: string
             | array
             | DATE_TIME    -> datetime
             | UNQUOTED_KEY -> legacy_bare
             | LEGACY_TEXT  -> legacy_bare


// ---------------------------------------------------------------------------
// Node sets / key sets
// ---------------------------------------------------------------------------

node_set: key_set

// Key sets remain non-empty, as in the ABNF.
// NLP* permits multiline formatting and comments between elements.
key_set: "{" NLP* key (NLP* "," NLP* key)* (NLP* ",")? NLP* "}"


// ---------------------------------------------------------------------------
// Metadata
// ---------------------------------------------------------------------------

// Inline metadata remains the original comma-separated form.
metadata: keyval ("," keyval)*

// A metadata block may be empty or may contain multiline key/value pairs.
// These are written as explicit alternatives to avoid adjacent nullable
// constructs and Lark's duplicate-rule expansion.
metadata_block: "{" NLP* "}"
              | "{" NLP* keyval (NLP* "," NLP* keyval)* (NLP* ",")? NLP* "}"

keyval: key "=" val


// ---------------------------------------------------------------------------
// Values
// ---------------------------------------------------------------------------

?val: metadata_block
    | array
    | string
    | BOOL      -> bool
    | NULL      -> null
    | DATE_TIME -> datetime
    | FLOAT     -> float
    | HEX_INT   -> hex_int
    | OCT_INT   -> oct_int
    | BIN_INT   -> bin_int
    | DEC_INT   -> int


// ---------------------------------------------------------------------------
// Arrays
// ---------------------------------------------------------------------------

// As with metadata blocks, the empty and non-empty cases are separate to
// avoid nullable-rule expansion problems.
array: "[" NLP* "]"
     | "[" NLP* val (NLP* "," NLP* val)* (NLP* ",")? NLP* "]"


// ---------------------------------------------------------------------------
// Strings
// ---------------------------------------------------------------------------

?string: ML_BASIC_STRING   -> ml_basic_string
       | ML_LITERAL_STRING -> ml_literal_string
       | BASIC_STRING      -> basic_string
       | LITERAL_STRING    -> literal_string

// The optional leading newline of a multiline string should be removed
// semantically by the transformer, not represented as a separate optional
// grammar production.
ML_BASIC_STRING.8: /\"\"\"(?:(?:\\(?:[\"\\bfenrt]|x[0-9A-Fa-f]{2}|u[0-9A-Fa-f]{4}|U[0-9A-Fa-f]{8}))|(?:\\[ \t]*(?:\r\n|\n)(?:[ \t]|\r\n|\n)*)|(?!\"{3})[\s\S])*\"\"\"/

ML_LITERAL_STRING.8: /'''(?:(?!''')[\s\S])*'''/

BASIC_STRING: /"(?:\\(?:["\\bfenrt]|x[0-9A-Fa-f]{2}|u[0-9A-Fa-f]{4}|U[0-9A-Fa-f]{8})|[^"\\\r\n])*"/

LITERAL_STRING: /'[^'\r\n]*'/


// ---------------------------------------------------------------------------
// Keys
// ---------------------------------------------------------------------------

// Multiline strings are deliberately not valid keys.
?key: BASIC_STRING   -> basic_string
    | LITERAL_STRING -> literal_string
    | UNQUOTED_KEY


// ---------------------------------------------------------------------------
// Section headers
// ---------------------------------------------------------------------------

GRAPH_HEADER.10: /#[ \t]*graph/
NODE_HEADER.10: /#[ \t]*nodes/
EDGE_HEADER.10: /#[ \t]*edges/
LEGACY_EDGE_HEADER.10: /#[ \t]*(?=\r?\n|$|\/\/)/


// ---------------------------------------------------------------------------
// Edge directions
// ---------------------------------------------------------------------------

// Horizontal whitespace is still globally ignored, but these lookarounds
// verify that whitespace existed on both sides in the original source.
//
// Valid:
//     A -> B
//     A   ->   B
//
// Invalid:
//     A->B
//     A ->B
//     A-> B

E_LR.10: /(?<=[ \t])->(?=[ \t])/
E_RL.10: /(?<=[ \t])<-(?=[ \t])/
E_BI.10: /(?<=[ \t])<>(?=[ \t])/
E_UN.10: /(?<=[ \t])--(?=[ \t])/


// ---------------------------------------------------------------------------
// References / edge identities
// ---------------------------------------------------------------------------

// A node reference requires '&' to be directly adjacent to its target.
//
// Valid:
//     &A
//     &{A, B}
//     &*
//
// Invalid:
//     & A
//     & {A, B}
//     & *
REF.10: /&(?=[^ \t\r\n])/

// An edge identity additionally requires whitespace immediately before '&'.
//
// Valid:
//     A -> B &e1
//     A -> B &*
//
// Invalid:
//     A -> B&e1
//     A -> B & e1
EDGE_REF.11: /(?<=[ \t])&(?=[^ \t\r\n])/


// ---------------------------------------------------------------------------
// Scalars
// ---------------------------------------------------------------------------

BOOL.6: "true" | "false"

NULL.6: "null"

DATE_TIME.5: /[0-9]{4}-[0-9]{2}-[0-9]{2}(?:[Tt ][0-9]{2}:[0-9]{2}(?::[0-9]{2}(?:\.[0-9]+)?)?(?:[Zz]|[+-][0-9]{2}:[0-9]{2})?)?|[0-9]{2}:[0-9]{2}(?::[0-9]{2}(?:\.[0-9]+)?)?/

FLOAT.4: /[+-]?(?:(?:0|[1-9](?:_?[0-9])*)\.[0-9](?:_?[0-9])*(?:[eE][+-]?[0-9](?:_?[0-9])*)?|(?:0|[1-9](?:_?[0-9])*)[eE][+-]?[0-9](?:_?[0-9])*|inf|nan)/

HEX_INT.3: /0x[0-9A-Fa-f](?:_?[0-9A-Fa-f])*/
OCT_INT.3: /0o[0-7](?:_?[0-7])*/
BIN_INT.3: /0b[01](?:_?[01])*/
DEC_INT.2: /[+-]?(?:0|[1-9](?:_?[0-9])*)/


// ---------------------------------------------------------------------------
// Unquoted / legacy text
// ---------------------------------------------------------------------------

UNQUOTED_KEY.1: /[A-Za-z0-9_][A-Za-z0-9_.-]*/

LEGACY_TEXT.-10: /(?:(?!\/\/)[^ \t\r\n:=,\[\]{}"'])+/


// ---------------------------------------------------------------------------
// Newlines and comments
// ---------------------------------------------------------------------------

NLP: NEWLINE+

// Do not consume the newline as part of COMMENT. Leaving it for NLP is
// important for comments inside multiline arrays, mappings, and key sets.
COMMENT: /[ \t]*\/\/[^\r\n]*/

%import common.NEWLINE

%ignore COMMENT
%ignore /[ \t]+/
"""

class RGDTansformer(
    RGDValueTransformer,
    EdgeTransformer,
    NodeTransformer,
    GraphTransformer,
    Transformer,
):
    ...

rgd_parser = Lark(
    rgd_grammar,
    parser='lalr',
    lexer='contextual',
    maybe_placeholders=False,
    transformer=RGDTansformer(),
)


def _lark_parse(input: str):
    if input and not input.endswith(("\n", "\r")):
        input += "\n"
    return rgd_parser.parse(input)


RefRGDTree = tuple[dict[str, Any], list[Node | NodeReference], list[Edge | Hyperedge]]
RGDTree = tuple[dict[str, Any], list[Node], list[Edge | Hyperedge]]


T_co = TypeVar("T_co", covariant=True)
class SupportsRead(Protocol[T_co]):
    def read(self) -> T_co:
        ...

RGDStream = (
    SupportsRead[str]
    | SupportsRead[bytes]
    | SupportsRead[bytearray]
)
RGDSource = str | bytes | bytearray

def load(fp: RGDStream) -> list[Graph]:
    return loads(fp.read())


def loads(source: RGDSource, validate: bool = True) -> list[Graph]:
    if isinstance(source, str):
        src = source
    elif isinstance(source, (bytes, bytearray)):
        src = bytes(source).decode("utf-8", errors="strict")
    else:
        raise TypeError("rgd.loads() expects a str, bytes, or bytearray input, not {type(source).__name__}")

    tree = _lark_parse(src)
    if tree is None:
        return [Graph([], [], {})]


    tree = dereference(tree)

    graphs = [Graph(n,e,p) for (p,n,e) in tree]

    if validate:
        for graph in graphs:
            graph.validate()

    return graphs


def dereference(tree: RefRGDTree) -> RGDTree:
    node_defs = {}
    for i, (props, nodes, edges) in enumerate(tree):
        refs = []
        for i, node in enumerate(nodes):
            if isinstance(node, NodeReference):
                refs.append(i)
                continue
            if node.key not in node_defs:
                node_defs[node.key] = node

        if refs:
            for idx in reversed(refs):
                nr = nodes.pop(idx)

                if nr.all:
                    for n in node_defs.values():
                        clone = deepcopy(n)
                        if nr.props is not None:
                            if len(clone.props.keys() & nr.props.keys()) > 0:
                                raise ValueError("Node references cannot override properties!")
                            clone.props.update(nr.props)
                        nodes.append(clone)
                    continue

                if nr.key not in node_defs:
                    raise KeyError(f"Could not find node reference for {nr.key}")

                clone = deepcopy(node_defs[nr.key])
                if nr.props is not None:
                    if len(clone.props.keys() & nr.props.keys()) > 0:
                        raise ValueError("Node references cannot override properties!")
                    clone.props.update(nr.props)

                nodes.append(clone)
    return tree
