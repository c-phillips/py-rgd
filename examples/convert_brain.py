from pathlib import Path
import math

import rgd
from rgd.graph import Graph, Node, Edge


# The GB file format is similar-ish to RGD, but with fewer batteries and more confusion
# A description of this graph can be found at: https://www-cs-faculty.stanford.edu/~knuth/brain83.html
brain_gb = Path(__file__).parent/"brain83.gb"
with open(brain_gb, 'r') as fp:
    lines = fp.readlines()

# First line is a description header
graph_desc = lines.pop(0)

# Second is the graph name, num nodes, num edges
name, nodes, edges = lines.pop(0).strip().split(",")
num_nodes = int(nodes)
num_edges = int(edges)

# Third line is the vertex header
_ = lines.pop(0)

# Next `nodes` lines are node descriptions
region_map = {
    'B': 'brain-stem',
    'l': 'l-cROI',
    'r': 'r-cROI',
    'L': 'l-sROI',
    'R': 'r-sROI',
}
nodes = []
line = lines.pop(0)
while not line.startswith("*"):
    name, _, x,y,z = line.strip().split(",")
    if name == '""':
        line = lines.pop(0)
        continue
    region = name[1]
    name = name.replace('"', '')[2:]
    nodes.append(
        Node(name, props={
            "coord": list(map(int, [x,y,z])),
            "region": region_map[region],
        })
    )
    line = lines.pop(0)

assert len(nodes) == num_nodes

# Remove the Arc section header
_ = lines.pop(0)

edges = []
current = 0
line = lines.pop(0)
while not line.startswith("*"):
    if line.startswith("0"):
        break
    vert, _, weight = line.strip().split(",")
    vert = int(vert[1:])
    weight = float(weight)

    edges.append(
        Edge(nodes[current].key, nodes[vert].key, props={
            "weight": math.exp(-weight/1_000.0)
        })
    )

    line = lines.pop(0)
    current = (current + 1) % num_nodes

g = Graph(nodes, edges, props={"name": "brain83"})
with open(brain_gb.parent/"brain83.rgd", 'w') as fp:
    rgd.dump(g, fp)

