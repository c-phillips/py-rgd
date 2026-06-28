from enum import Enum
from pathlib import Path


class RGDSectionError(Exception):
    ...


class Parser:
    class Section(Enum):
        GRAPH_DOC = 0
        NODE_DOC  = 1
        EDGE_DOC  = 2

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
        State.NODE_DOC_BODY    : {State.EDGE_DOC_HEADER, State.GRAPH_DOC_BODY},
        State.EDGE_DOC_HEADER  : {State.EDGE_DOC_BODY},
        State.EDGE_DOC_BODY    : {State.GRAPH_DOC_HEADER},
    }

    @staticmethod
    def parse(self, filepath: Path):
        graphs = []

        section = self.Section.GRAPH_DOC
        state = self.Section.GRAPH_DOC_HEADER

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
                    if next_section not in self.state_transitions[section]:
                        raise RGDSectionError


