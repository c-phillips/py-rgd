from functools import partial
from typing import Iterable, Protocol

from rgd.graph import Graph, Edge, Hyperedge


def rgdValueEncoder(value, is_key: bool = False) -> str:
    if isinstance(value, str):
        if is_key:
            return value
        return f'"{value}"'
    elif isinstance(value, list):
        return rgdArrayEncoder(value)
    elif isinstance(value, dict):
        raise ValueError("RGD values cannot be maps. Flatten your dictionary before serializing.")

    # TODO: Validate this
    return str(value)

def rgdArrayEncoder(values) -> str:
    return "[" + ", ".join(map(rgdValueEncoder, values)) + "]"

def rgdKVEncoder(kvs) -> str:
    parts = []
    for k,v in kvs.items():
        parts.append(f"{k} = {rgdValueEncoder(v)}")
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
        return f"{edge.u} {str(edge.direction)} {edge.v}"
    elif isinstance(edge, Hyperedge):
        if edge.v is not None:
            return f"{edge.u} {str(edge.direction)} {edge.v}"
        return f"{edge.u}"
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
            out += f"{k} = {rgdValueEncoder(v)}\n"
        out += "\n"
    out += "# nodes\n"
    for node in graph.nodes:
        line = f"{node.key}"
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

