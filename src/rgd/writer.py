from functools import partial
import json
import re
from typing import Iterable, Protocol

from rgd.graph import Graph, Edge, Hyperedge


_UNQUOTED_KEY_RE = re.compile(
    r"[A-Za-z0-9_][A-Za-z0-9_.-]*\Z"
)

# Thanks AI
def rgdStringEncoder(value: str) -> str:
    if not isinstance(value, str):
        raise TypeError(
            f"expected str, got {type(value).__name__}"
        )

    # RGD documents must contain Unicode scalar values, not lone surrogates.
    if any(0xD800 <= ord(char) <= 0xDFFF for char in value):
        raise ValueError("RGD strings cannot contain surrogate code points")

    # JSON basic-string escaping is a valid subset of RGD escaping.
    encoded = json.dumps(value, ensure_ascii=False)

    # Python's JSON encoder does not necessarily escape DEL, but RGD excludes
    # it from unescaped basic-string characters.
    return encoded.replace("\x7f", r"\u007f")


def rgdValueEncoder(value) -> str:
    if isinstance(value, str):
        return rgdStringEncoder(value)
    elif isinstance(value, bool):
        return "true" if value else "false"
    elif isinstance(value, list):
        return rgdArrayEncoder(value)
    elif isinstance(value, dict):
        raise ValueError("RGD values cannot be maps. Flatten your dictionary before serializing.")

    # TODO: Validate this
    return str(value)


def rgdKeyEncoder(key) -> str:
    # TODO: Decide to enforce type(key) == str ahead of time or not
    k = str(key)
    if _UNQUOTED_KEY_RE.fullmatch(k):
        return key
    return rgdStringEncoder(k)


def rgdArrayEncoder(values) -> str:
    return "[" + ", ".join(map(rgdValueEncoder, values)) + "]"

def rgdKVEncoder(kvs) -> str:
    parts = []
    for k,v in kvs.items():
        parts.append(f"{rgdKeyEncoder(k)} = {rgdValueEncoder(v)}")
    return ", ".join(parts)

def rgdEncodeDescription(props) -> str: 
    line = ": "
    if isinstance(props, dict):
        line += rgdKVEncoder(props)
    else:
        line += rgdValueEncoder(props)
    return line

def rgdEndpointEncoder(edge) -> str:
    if isinstance(edge, Edge):
        return f"{rgdKeyEncoder(edge.u)} {str(edge.direction)} {rgdKeyEncoder(edge.v)}"
    elif isinstance(edge, Hyperedge):
        u = ', '.join(map(rgdKeyEncoder, list(edge.u)))
        if edge.v is not None:
            v = ', '.join(map(rgdKeyEncoder, list(edge.v)))
            return f"{{{u}}} {str(edge.direction)} {{{v}}}"
        return f"{{{u}}}"
    else:
        raise ValueError(f"Unknown edge type: {type(edge)}")

def rgdEncoder(graph: Graph, force_graph_header: bool = False) -> str:
    if not graph.nodes:
        return ""
    
    out = ""
    if graph.props or force_graph_header:
        out += "# graph\n"
    if graph.props:
        for k,v in graph.props.items():
            out += f"{rgdKeyEncoder(k)} = {rgdValueEncoder(v)}\n"
        out += "\n"
    out += "# nodes\n"
    for node in graph.nodes:
        line = f"{rgdKeyEncoder(node.key)}"
        if node.props:
            line += rgdEncodeDescription(node.props)

        out += line+"\n"
    out += "\n"
    if graph.edges:
        out += "# edges\n"
        for edge in graph.edges:
            line = rgdEndpointEncoder(edge)
            if edge.props:
                line += rgdEncodeDescription(edge.props)
            out += line+"\n"

    return out


class TextWrite(Protocol):
    def write(self, data: str, /) -> object:
        ...

def dump(graphs: Graph | Iterable[Graph], fp: TextWrite):
    src = dumps(graphs)
    fp.write(src)


# TODO: [Feature] Add support to specify legacy output
def dumps(graphs: Graph | Iterable[Graph]) -> str:
    if isinstance(graphs, Graph):
        graphs = [graphs]

    output = "\n".join(
        map(
            partial(
                rgdEncoder,
                force_graph_header=len(graphs) > 1
            ),
            graphs
        )
    )
    return output

