import logging
from enum import Enum
from pathlib import Path
import re

from lark import Lark


class RGDSectionError(Exception):
    ...

class RGDStateError(Exception):
    ...

class RGDKeyValueError(Exception):
    ...


class Parser:
    class State(Enum):
        GRAPH_DOC_HEADER = 0
        GRAPH_DOC_BODY   = 1
        NODE_DOC_HEADER  = 2
        NODE_DOC_BODY    = 3
        EDGE_DOC_HEADER  = 4
        EDGE_DOC_BODY    = 5

    state_transitions = {
        State.GRAPH_DOC_HEADER : [State.GRAPH_DOC_BODY],
        State.GRAPH_DOC_BODY   : [State.NODE_DOC_HEADER],
        State.NODE_DOC_HEADER  : [State.NODE_DOC_BODY],
        State.NODE_DOC_BODY    : [State.EDGE_DOC_HEADER, State.GRAPH_DOC_HEADER],
        State.EDGE_DOC_HEADER  : [State.EDGE_DOC_BODY],
        State.EDGE_DOC_BODY    : [State.GRAPH_DOC_HEADER],
    }

    @staticmethod
    def lark(s: str):
        grammar = r"""
        rgd:  NLP* (node_doc | graph_doc+)

        graph_doc:  (graph_header NLP)? graph_prop* node_doc
        node_doc:   (node_header NLP)?  node_expr*  edge_doc*
        edge_doc:   (edge_header NLP)?  edge_expr* 

        graph_header: "# graph"
        node_header:  "# nodes"
        edge_header:  "#" "edges"?

        graph_prop: key NLP
        node_expr:  key NLP
        edge_expr:  key edge_dir key NLP

        edge_dir: E_LR | E_RL | E_BI | E_UN
        E_LR: "->"
        E_RL: "<-"
        E_BI: "<>"
        E_UN: "--"

        key: ESCAPED_STRING | unquoted_key
        unquoted_key: KEY_START KEY_FINAL*
        KEY_START: LETTER | DIGIT
        KEY_FINAL: LETTER | DIGIT | "." | "_"

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
        %import common.ESCAPED_STRING
        %import common.LETTER
        %import common.DIGIT


        %ignore COMMENT
        %ignore WS_INLINE
        """

        lark = Lark(grammar, start='rgd')
        return lark.parse(s)

    def parse(self, filepath: Path):
        logger = logging.getLogger("rgd.Parser")

        graphs = []

        # Start in node-mode since graph metadata is optional
        state = self.State.NODE_DOC_HEADER
        logger.debug(f"State: {state}")

        graph_meta = []
        nodes = []
        edges = []
        with open(filepath, 'r') as fp:
            acc = []
            for line_num, line in enumerate(fp.readlines()):
                # Handle blank lines and comments
                if not line or line.startswith("//"):
                    continue

                # Check for a new section
                if line.startswith('#'):
                    next_section = self._parse_section(line)
                    # Check if this is a valid section transition
                    if next_section not in self.state_transitions[state]:
                        raise RGDSectionError

                    state = next_section
                    logger.debug(f"State: {state}")
                else:
                    if state.name.lower().endswith("header"):
                        state = self.state_transitions[state][0]
                        logger.debug(f"State: {state}")

                    if state == self.State.GRAPH_DOC_BODY:
                        graph_meta.append(self._parse_graph_meta(line))
                    elif state == self.State.NODE_DOC_BODY:
                        nodes.append(self._parse_node(line))
                    elif state == self.State.EDGE_DOC_BODY:
                        edges.append(self._parse_edge(line))
                    else:
                        logger.error(f"{state}")
                        raise RGDStateError

    def _parse_key(self, substr: str):
        # Check if quoted key
        if substr[0] == '"' or substr[0] == "'":
            quote_regex = r'"(?:\\.|[^"\\])*"' if substr[0] == '"' else r"'(?:\\.|[^'\\])*'"
            # Find matching quote
            if (m := re.search(quote_regex, substr)) is not None:
                span = m.span()
                key = substr[span[0]+1:span[1]-1]
                if len(key) < 1:
                    raise RGDKeyValueError
                line = substr[span[1]:]
                return key, line
            else:
                raise RGDKeyValueError

        # TODO: Is there a better way to do this?
        invalid_chars = ['=', '<', '>']
        if any([c in substr for c in invalid_chars]):
            raise RGDKeyValueError

        unquote_regex = r'^[A-Za-z0-9_][A-Za-z0-9_.-]*'
        if (m := re.search(unquote_regex, substr)) is not None:
            print(m)
            span = m.span()
            key = substr[span[0]:span[1]]
            line = substr[span[1]:]
            return key, line
        else:
            raise RGDKeyValueError

    def _parse_key_set(self, substr: str):
        ...

    def _parse_value(self, substr: str):
        ...

    def _parse_section(self, line: str):
        ...

    def _parse_graph_meta(self, line: str) -> dict:
        key, line = self._parse_key(line)
        value, line = self._parse_value(line)

    def _parse_node(self, line: str):
        parts = line.strip().split()
        for part in parts:
            key, _= self._parse_key(line.strip())
            print(key, line)

    def _parse_edge(self, line: str):
        ...

