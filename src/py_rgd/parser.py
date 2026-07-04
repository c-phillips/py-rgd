from lark import Lark

from py_rgd.transformer import RGDValueTransformer
from py_rgd.graph import (
    NodeTransformer,
    EdgeTransformer,
    GraphTransformer,
    Node,
    Graph,
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

?node_expr: node_set description?   -> node_set_decl
          | key description         -> node_decl
          | key legacy_description  -> legacy_node_decl
          | key                     -> node_decl

?edge_expr: endpoint edge_dir endpoint description? -> edge_decl
          | key_set description?                    -> hyper_edge_decl
          | key key legacy_description?             -> legacy_edge_decl

edge_dir: E_LR -> lr
        | E_RL -> rl
        | E_BI -> bi
        | E_UN -> un

?endpoint: key | key_set

?description: ":" (metadata | val)

legacy_description: legacy_value+

?legacy_value: string
             | array
             | DATE_TIME    -> datetime
             | UNQUOTED_KEY -> legacy_bare
             | LEGACY_BARE  -> legacy_bare

node_set: key_set

key_set: "{" key ("," key)* "}"

metadata: keyval ("," keyval)*

keyval: key "=" val

?val: array
    | string
    | BOOL      -> bool
    | DATE_TIME -> datetime
    | FLOAT     -> float
    | HEX_INT   -> hex_int
    | OCT_INT   -> oct_int
    | BIN_INT   -> bin_int
    | DEC_INT   -> int

array: "[" [val ("," val)* ","?] "]"

?string: BASIC_STRING   -> basic_string
       | LITERAL_STRING -> literal_string

?key: string | UNQUOTED_KEY

GRAPH_HEADER.10: /#[ \t]*graph/
NODE_HEADER.10: /#[ \t]*nodes/
EDGE_HEADER.10: /#[ \t]*edges/
LEGACY_EDGE_HEADER.10: /#[ \t]*(?=\r?\n|$|\/\/)/

E_LR.10: "->"
E_RL.10: "<-"
E_BI.10: "<>"
E_UN.10: "--"

BOOL.6: "true" | "false"

DATE_TIME.5: /[0-9]{4}-[0-9]{2}-[0-9]{2}(?:[Tt ][0-9]{2}:[0-9]{2}(?::[0-9]{2}(?:\.[0-9]+)?)?(?:[Zz]|[+-][0-9]{2}:[0-9]{2})?)?|[0-9]{2}:[0-9]{2}(?::[0-9]{2}(?:\.[0-9]+)?)?/

FLOAT.4: /[+-]?(?:(?:0|[1-9](?:_?[0-9])*)\.[0-9](?:_?[0-9])*(?:[eE][+-]?[0-9](?:_?[0-9])*)?|(?:0|[1-9](?:_?[0-9])*)[eE][+-]?[0-9](?:_?[0-9])*|inf|nan)/

HEX_INT.3: /0x[0-9A-Fa-f](?:_?[0-9A-Fa-f])*/
OCT_INT.3: /0o[0-7](?:_?[0-7])*/
BIN_INT.3: /0b[01](?:_?[01])*/
DEC_INT.2: /[+-]?(?:0|[1-9](?:_?[0-9])*)/

UNQUOTED_KEY.1: /[A-Za-z0-9_][A-Za-z0-9_.-]*/
LEGACY_BARE.0: /[A-Za-z0-9_.+-]+/

BASIC_STRING: /"(?:\\(?:["\\bfenrt]|x[0-9A-Fa-f]{2}|u[0-9A-Fa-f]{4}|U[0-9A-Fa-f]{8})|[^"\\\r\n])*"/
LITERAL_STRING: /'[^'\r\n]*'/

NLP: NEWLINE+

COMMENT: /[ \t]*\/\/[^\r\n]*(\r\n)?/

%import common.NEWLINE

%ignore COMMENT
%ignore /[ \t]+/
"""


def _lark_parse(input: str):
    lark = Lark(
        rgd_grammar,
        parser='lalr',
        lexer='contextual',
        maybe_placeholders=False,
    )
    if input and not input.endswith(("\n", "\r")):
        input += "\n"
    return lark.parse(input)



def rgd_loads(input: str, validate: bool = True):
    tree = _lark_parse(input)
    xform = (
        RGDValueTransformer()
        * EdgeTransformer()
        * NodeTransformer()
        * GraphTransformer()
    )
    tree = xform.transform(tree)

    graphs = [Graph(n,e,p) for (p,n,e) in tree]

    if validate:
        for graph in graphs:
            graph.validate()

    return graphs

