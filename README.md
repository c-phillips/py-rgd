# PyRGD
An [RGD](https://github.com/c-phillips/rgd) parser for Python

This is a work in progress


## Usage
We recommend using [uv](https://docs.astral.sh/uv/getting-started/installation/) for your environment.
You can test parsing an RGD file with `uv run rgd [FILE]`.

The PyRGD package provides library functions to make working with RGD data simple.

To read an RGD file:

```python
import rgd

with open("my_graph.rgd", 'r') as fp:
    g = rgd.load(fp)
```

To write an RGD file:

```python
import rgd

def convert_to_rgd_graph(graph: MyGraphClass) -> rgd.Graph:
    ...
    return rgd.Graph(nodes, edges, props)

with open("output_path.rgd", 'w') as fp:
    rgd.dump(convert_to_rgd_graph(my_graph))
```

### NetworkX
We have also included some convenient functions for working directly with NetworkX graphs.
Start by syncing the correct extras: `uv sync --extra networkx`.

Read RGD to NetworkX:

```python
from rgd.networkx import networkx_load

with open("my_graph.rgd", 'r') as fp:
    nx_graph = networkx_load(fp)
```

Write NetworkX to RGD:

```python
from rgd.networkx import networkx_dump
import networkx as nx

my_graph = nx.Graph()
...

with open("output_path.rgd", 'w') as fp:
    networkx_dump(my_graph)
```

