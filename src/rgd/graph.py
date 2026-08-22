from copy import deepcopy
from dataclasses import dataclass
from enum import StrEnum
from itertools import chain
from typing import Any

from lark import Token, Transformer

from .attributes import Attributes


@dataclass
class Node:
    key: Any
    props: Attributes | None = None

    def __repr__(self) -> str:
        return f"(Node) {self.key}: {self.props}"

@dataclass
class NodeReference(Node):
    """Should not appear in the final graph."""
    all: bool = False
    def __repr__(self) -> str:
        return f"&(Node) {self.key}: {self.props}"


@dataclass
class Edge:
    class Direction(StrEnum):
        UNDIRECTED = "--"
        DIRECTED = "->"
        BIDIRECTIONAL = "<>"

    class DirectionOrder(StrEnum):
        LR = "->"
        RL = "<-"
        BI = "<>"

    u: Any
    v: Any
    direction: Direction = Direction.UNDIRECTED
    props: Attributes | None = None
    edge_id: Any | None = None

    def __hash__(self):
        return hash((self.u, self.v, self.direction))

    def __repr__(self) -> str:
        eid_str = ''
        if self.edge_id is not None:
            eid_str = f" &{self.edge_id}"
        return f"(Edge) {self.u} {self.direction} {self.v}: {self.props}" + eid_str


@dataclass
class Hyperedge:
    u: set[Any]
    v: set[Any] | Any | None = None
    direction: Edge.Direction = Edge.Direction.UNDIRECTED
    props: Attributes | None = None
    edge_id: Any | None = None

    def __hash__(self):
        return hash((frozenset(self.u), frozenset(self.v) if self.v is not None else None, self.direction))

    def __repr__(self) -> str:
        eid_str = ''
        if self.edge_id is not None:
            eid_str = f" &{self.edge_id}"
        return f"(Hyperdge) {self.u} {self.direction} {self.v}: {self.props}" + eid_str


class NodeTransformer(Transformer):
    def legacy_node_decl(self, items):
        return [Node(items[0], items[1] if len(items) > 1 else None)]

    def node_decl(self, items):
        return [Node(items[0], items[1] if len(items) > 1 else None)]

    def node_set(self, items):
        return items[0]

    def node_set_decl(self, items):
        return [Node(n, items[1] if len(items) > 1 else None) for n in items[0]]

    def node_line(self, items):
        return items[0]

    def node_doc(self, items):
        refs  = []
        nodes = []
        for n in list(chain.from_iterable(items)):
            if isinstance(n, NodeReference):
                refs.append(n)
                continue
            nodes.append(n)

        # Merge node redefinitions
        node_map = dict()
        for node in nodes:
            node_map.setdefault(node.key, []).append(node)

        results = []
        for key, nodes in node_map.items():
            if len(nodes) == 1:
                results.append(nodes[0])
                continue

            props = dict()
            for node in nodes:
                if not isinstance(node.props, dict):
                    raise ValueError("Nodes cannot have multiple descriptions unless each uses a key-value list")
                overlap = props.keys() & node.props.keys()
                if overlap:
                    raise ValueError(f"Duplicate node properties for {key!r}: {sorted(overlap)!r}")
                props.update(node.props)

            results.append(Node(key, props))

        return results + refs

    def node_doc_body(self, items):
        return items[0], items[1] if len(items) > 1 else []

    def node_reference_decl(self, items):
        items = items[1:]  # pop the REF token
        return [NodeReference(items[0], items[1] if len(items) > 1 else None)]

    def node_set_reference_decl(self, items):
        items = items[1:]  # pop the REF token
        return [NodeReference(n, items[1] if len(items) > 1 else None) for n in items[0]]

    def all_nodes_reference_decl(self, items):
        return [NodeReference(None, None, True)]


class EdgeTransformer(Transformer):

    # TODO: Evaluate if this is the best way to be handling this sort of thing?
    #       -> Fixes the type checking issue when testing for edge properties
    #          with multi-edges, but feels a little messy
    @dataclass
    class EdgeIdentity:
        eid: Any

    @dataclass
    class AnonymousEID(EdgeIdentity):
        ...

    @dataclass
    class NamedEID(EdgeIdentity):
        ...


    @staticmethod
    def __build_edge(u, v, direction = Edge.Direction.UNDIRECTED, details = None, eid = None):
        if isinstance(u, set) or isinstance(v, set):
            return Hyperedge(u, v, direction, details, eid)
        return Edge(u, v, direction, details, eid)

    def hyper_edge_decl(self, items):
        return Hyperedge(items[0], None, Edge.Direction.UNDIRECTED, props=items[1] if len(items) > 1 else None)

    def edge_decl(self, items):
        u, d, v = items[0], items[1], items[2]
        # Normalize edge direction
        if d == Edge.DirectionOrder.RL:
            u,v = v,u
            d = Edge.DirectionOrder.LR
        
        eid   = None
        props = None
        if len(items) == 5:
            eid   = items[3]
            props = items[4]
        elif len(items) == 4:
            if isinstance(items[3], dict):
                props = items[3]
            else:
                if isinstance(items[3], EdgeTransformer.EdgeIdentity):
                    eid = items[3].eid
                else:
                    props = items[3]
        return self.__build_edge(u, v, d, props, eid)

    def legacy_edge_decl(self, items):
        return self.__build_edge(items[0], items[1], details=items[2:])

    def edge_line(self, items):
        return items[0]

    def named_edge_identity(self, items):
        # return str(items[1])
        return self.NamedEID(str(items[1]))

    def anonymous_edge_identity(self, items):
        # return True
        return self.AnonymousEID(True)

    def edge_doc(self, items):
        all_decls = [e for e in items if isinstance(e, (Edge, Hyperedge))]

        # Merge node redefinitions
        decl_map = dict()
        for decl in all_decls:
            decl_map.setdefault(hash(decl), []).append(decl)

        results = []
        for hsh, decls in decl_map.items():
            if len(decls) == 1:
                results.append(decls[0])
                continue

            have_ids = [decl.edge_id is not None for decl in decls]
            if any(have_ids):
                if not all(have_ids):
                    raise ValueError(f"If any (u,v) edge is labeled, all (u,v) edges must be labeled: {decls}")
                results.extend([
                    self.__build_edge(decl.u, decl.v, decl.direction, decl.props, decl.edge_id)
                    for decl in decls
                ])
            else:
                props = dict()
                for decl in decls:
                    if not isinstance(decl.props, dict):
                        raise ValueError("Edges cannot have multiple descriptions unless each uses a key-value list")
                    overlap = props.keys() & decl.props.keys()
                    if overlap:
                        raise ValueError(f"Duplicate edge properties for {decl!r}: {sorted(overlap)!r}")
                    props.update(decl.props)

                results.append(self.__build_edge(decl.u, decl.v, decl.direction, props))

        return results


class GraphTransformer(Transformer):
    def graph_expression(self, items):
        return {items[0][0]:items[0][1]}

    def graph_prop_line(self, items):
        return items[0]

    def headerless_doc(self, items):
        semantic = [item for item in items if not isinstance(item, Token)]
        if len(semantic) != 1:
            raise ValueError("Unexpected headerless document contents: {items!r}")

        return [({}, semantic[0][0], semantic[0][1])]

    def graph_doc(self, items):
        items = [item for item in items if not (isinstance(item, Token) and item.type == "NLP") ]
        node_header_index = [(isinstance(t, Token) and t.type == "NODE_HEADER") for t in items].index(True)

        graph_props = dict()
        for prop in items[1:node_header_index]:
            graph_props |= prop

        edges = []
        items = items[node_header_index+1]
        if len(items) > 1:
            nodes, edges = items
        else:
            nodes = items[0]

        return (graph_props, nodes, edges)

    def graph_docs(self, items):
        return items

    def rgd(self, items):
        semantic = [item for item in items if not isinstance(item, Token)]
        if len(semantic) != 1:
            raise ValueError("Unexpected RGD contents: {items!r}")
        return semantic[0]

    def empty_doc(self, _items):
        return None


@dataclass(frozen=True)
class Graph:
    nodes: list[Node]
    edges: list[Edge | Hyperedge]
    props: Attributes | None = None
    _node_keys: set[Any] = None

    def __eq__(self, other):
        # TODO: Improve this wildly naive implementation
        if not len(self.nodes) == len(other.nodes):
            print("node len not the same")
            return False
        if not len(self.edges) == len(other.edges):
            print("edge len not the same")
            return False
        if not self.props == other.props:
            print("props not the same")
            return False
        
        has_match = set()
        for u in self.nodes:
            for v in other.nodes:
                if u.key == v.key\
                and u.props == v.props:
                    has_match.add(u.key)
                    break
        if not has_match == self.node_keys:
            print("unmatched nodes")
            return False

        has_match = set()
        for e in self.edges:
            for f in other.edges:
                if type(e) is type(f):
                    if e.u == f.u  \
                    and e.v == f.v \
                    and e.direction == f.direction\
                    and e.props == f.props:
                        has_match.add(frozenset([e.u, e.direction, e.v]))
                        break
        if not len(has_match) == len(self.edges):
            print("unmatched edges")
            return False

        return True
                    

    def __post_init__(self):
        """Doing bad things for convenience."""
        object.__setattr__(self, "_node_keys", {n.key for n in self.nodes})

    @staticmethod
    def deref(graphs: list["Graph"]):
        for ref_idx in self.__node_refs:
            nr = self.nodes[ref_idx]
            for graph in graphs:
                query_node = graph.get_node(nr.key)
                if query_node is not None:
                    clone = deepcopy(query_node)
                    if len(clone.props.keys() & nr.props.keys()) > 0:
                        raise ValueError("Node references cannot override properties!")
                    clone.props.update(nr.props)
                    self.nodes[ref_idx] = clone
                    break

    @property
    def node_keys(self) -> set[Any]:
        return self._node_keys

    def get_node(self, key: Any) -> Node | None:
        if key not in self.node_keys:
            return None
        for node in self.nodes:
            if key == node.key:
                return node 

    def get_edge(self, u: Any, v: Any, dir: Edge.Direction = Edge.Direction.UNDIRECTED) -> Edge | None:
        for edge in self.edges:
            if isinstance(edge, Hyperedge):
                continue
            if edge.u == u and edge.v == v and edge.direction == dir:
                return edge

    def get_hyperedge(self, u: Any, v: Any | None = None, dir: Edge.Direction = Edge.Direction.DIRECTED) -> Hyperedge | None:
        for edge in self.edges:
            if isinstance(edge, Hyperedge):
                if edge.u == u:
                    if v is not None:
                        if edge.v != v or edge.direction != dir:
                            continue
                    return edge

    def validate(self):
        # Validate graph
        node_names = {n.key for n in self.nodes}
        edge_nodes = set()
        for edge in self.edges:
            if isinstance(edge, Edge):
                edge_nodes.add(edge.u)
                edge_nodes.add(edge.v)
            else:
                if isinstance(edge.u, set):
                    edge_nodes.update(edge.u)
                else:
                    edge_nodes.add(edge.u)
                if edge.v is None:
                    pass
                elif isinstance(edge.v, set):
                    edge_nodes.update(edge.v)
                else:
                    edge_nodes.add(edge.v)
        diff = edge_nodes.difference(node_names)
        assert len(diff) == 0, f"Edges contain undefined nodes! {diff}"

    def __repr__(self) -> str:
        s = "Graph:\n"
        if self.props:
            s += "\tProperties:\n"
            for k,v in self.props.items():
                s += f"\t\t{k}: {v}\n"
        s += "\tNodes:\n"
        for node in self.nodes:
            s += f"\t\t{node}\n"
        if self.edges:
            s += "\tEdges:\n"
            for edge in self.edges:
                s += f"\t\t{edge}\n"
        return s

