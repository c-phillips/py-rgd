from lark import Lark


rgd_grammar = r"""
rgd: NLP* block*

block: graph_doc | explicit_node_doc | edge_doc | implicit_node_doc

graph_doc:         graph_header NLP graph_prop*
explicit_node_doc: node_header NLP node_expr*   -> node_doc
implicit_node_doc: node_expr+                   -> node_doc
edge_doc:          edge_header NLP edge_expr*

graph_header: "# graph"
node_header:  "# nodes"
edge_header:  "#" "edges"?

graph_prop: keyval NLP

node_expr: node (description | legacy_description)? NLP
edge_expr: node edge_dir? node (description | legacy_description)? NLP

description: ":" (val* | keyval_list)
legacy_description: legacy_value+
legacy_value: SIGNED_NUMBER       -> number
              | UNQUOTED_KEY      -> string
              | ESCAPED_STRING    -> string

edge_dir: E_LR  -> lr
        | E_RL  -> rl 
        | E_BI  -> bi 
        | E_UN  -> un 
E_LR: "->"
E_RL: "<-"
E_BI: "<>"
E_UN: "--"

node: key | key_set
key_set: "{" key ("," key)* "}"
keyval_list: keyval ("," keyval)*
keyval: key "=" val
val: array
    | ESCAPED_STRING    -> string
    | SIGNED_NUMBER     -> number 
    | BOOL              -> bool

BOOL: "true" | "false"
array: "[" [val ("," val)*] "]"

key: ESCAPED_STRING | UNQUOTED_KEY
UNQUOTED_KEY: (LETTER | DIGIT) (WORD | DIGIT | "." | "_")*

NLP: NEWLINE+
COMMENT: /\/\/[^\n]*\n?/

%import common.WS
%import common.WS_INLINE
%import common.NEWLINE
%import common.SIGNED_FLOAT
%import common.SIGNED_INT
%import common.HEXDIGIT
%import common.NUMBER
%import common.SIGNED_NUMBER
%import common._STRING_ESC_INNER -> UNQUOTE_STRING
%import common.ESCAPED_STRING
%import common.LETTER
%import common.WORD
%import common.DIGIT

%ignore COMMENT
%ignore WS_INLINE
"""

def _lark_parse(input: str):
    lark = Lark(rgd_grammar, start='rgd', parser='lalr')
    return lark.parse(input)

