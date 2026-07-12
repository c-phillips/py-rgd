import io
from pathlib import Path
import tempfile
import urllib.request
import zipfile

import rgd
from rgd.graph import Graph, Node, Edge


CORA_URL = "https://linqs-data.soe.ucsc.edu/public/datasets/cora/cora.zip"

nodes = []
edges = []
with tempfile.TemporaryDirectory() as tmp_dir:
    tmppath = Path(tmp_dir)
    urllib.request.urlretrieve(CORA_URL, tmppath/"cora.zip")
    with zipfile.ZipFile(tmppath/"cora.zip") as zf:

        # Read node information
        with zf.open("cora/cora.content", 'r') as bf:
            with io.TextIOWrapper(bf, encoding="utf-8") as fp:
                for line in fp.readlines():
                    parts = line.strip().split()
                    if len(parts) < 2:
                        break
                    paper_id, *vec_parts, paper_class = parts

                    # Sparse vector indices
                    vec = [i for i,v in enumerate(vec_parts) if v == "1"]

                    nodes.append(Node(paper_id, props={
                        "vec": vec,
                        "class": paper_class,
                    }))

        # Read edge information
        # NOTE: Edges are directed, and listed in right-left order
        with zf.open("cora/cora.cites", 'r') as bf:
            with io.TextIOWrapper(bf, encoding="utf-8") as fp:
                for line in fp.readlines():
                    parts = line.strip().split()
                    if len(parts) < 2:
                        break
                    v, u = parts
                    edges.append(Edge(u,v, Edge.Direction.DIRECTED))

g = Graph(nodes, edges, props={"url": CORA_URL, "vocab_size": 1433})
with open(Path(__file__).parent/"cora.rgd", 'w') as fp:
    rgd.dump(g, fp)

