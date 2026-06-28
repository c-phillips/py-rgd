from enum import Enum
from pathlib import Path


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
        State.GRAPH_DOC_HEADER : {State.GRAPH_DOC_BODY},
        State.GRAPH_DOC_BODY   : {State.NODE_DOC_HEADER},
        State.NODE_DOC_HEADER  : {State.NODE_DOC_BODY},
        State.NODE_DOC_BODY    : {State.EDGE_DOC_HEADER, State.GRAPH_DOC_HEADER},
        State.EDGE_DOC_HEADER  : {State.EDGE_DOC_BODY},
        State.EDGE_DOC_BODY    : {State.GRAPH_DOC_HEADER},
    }

    @staticmethod
    def parse(self, filepath: Path):
        graphs = []

        # Start in node-mode since graph metadata is optional
        state = self.State.NODE_DOC_HEADER

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
                else:
                    if state == self.State.GRAPH_DOC_BODY:
                        graph_meta.append(self._parse_graph_meta(line))
                    elif state == self.State.NODE_DOC_BODY:
                        nodes.append(self._parse_node(line))
                    elif state == self.State.EDGE_DOC_BODY:
                        edges.append(self._parse_edge(line))
                    else:
                        raise RGDStateError

    def _parse_key(self, substr: str):
        ...

    def _parse_key_set(self, substr: str):
        ...

    def _parse_value(self, substr: str):
        ...

    def _parse_section(self, line: str):
        ...

    def _parse_graph_meta(self, line: str) -> dict:
        ...

    def _parse_node(self, line: str):
        ...

    def _parse_edge(self, line: str):
        ...

