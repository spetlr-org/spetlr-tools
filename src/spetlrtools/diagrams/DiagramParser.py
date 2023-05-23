import base64
import xml.etree.ElementTree as ET
import zlib
from itertools import chain
from typing import Dict, List, Optional
from urllib.parse import unquote

from spetlrtools.diagrams.Edge import Edge
from spetlrtools.diagrams.HTMLStripper import HTMLStripper


class DiagramNode:
    def __init__(self, details):
        self.id = details["id"]
        for key in ["value", "label"]:
            try:
                self.label = HTMLStripper.strip(details[key])
                break
            except KeyError:
                continue
        else:
            self.label = ""


class DiagramEdge(DiagramNode):
    def __init__(self, details):
        super().__init__(details)

        self.source_id = details["source"]
        self.target_id = details["target"]
        self.source_node: Optional[DiagramNode] = None
        self.target_node: Optional[DiagramNode] = None

    @property
    def source_label(self):
        return self.source_node.label if self.source_node else self.source_id

    @property
    def target_label(self):
        return self.target_node.label if self.target_node else self.target_id

    def __str__(self):
        return f"< {self.source_label} -- {self.target_label} >"

    def get_Edge(self) -> Edge:
        return Edge(self.source_label, self.target_label)


class DiagramParser:
    def __init__(self, path):
        self.path = path
        self.edges: List[DiagramEdge] = []
        self.nodes: Dict[str, DiagramNode] = {}

    def _get_contents(self, path: str):
        if path.endswith("png"):
            try:
                from PIL import Image
            except ImportError:
                raise Exception("You need to install 'pillow' to work with png files.")

            im = Image.open(path)
            im.load()
            conts = unquote(im.info["mxfile"])
            return conts
        elif path.endswith(".svg"):
            with open(path, "r", encoding="utf-8") as f:
                conts = f.read()
                svg = ET.fromstring(conts)

            return svg.attrib["content"]
        else:
            # both .drawio and .xml fall into this case
            with open(path, "r", encoding="utf-8") as f:
                return f.read()

    def _deflate_nodes(self, et: ET) -> ET:
        for diagram in et.iter("diagram"):
            if len(diagram):
                # d has nested xml nodes
                continue
            b64 = base64.b64decode(diagram.text)
            full = unquote(zlib.decompress(b64, -15).decode("utf-8"))
            diagram.text = ""
            diagram.insert(0, ET.fromstring(full))
        return et

    def parse(self):
        conts = self._get_contents(self.path)
        et = ET.fromstring(conts)
        et = self._deflate_nodes(et)

        _edges = []

        for cell in chain(et.iter("mxCell"), et.iter("object")):
            try:
                node = DiagramNode(cell.attrib)
            except KeyError:
                continue
            self.nodes[node.id] = node

            try:
                _edges.append(DiagramEdge(cell.attrib))
            except KeyError:
                # the node is not a useful edge
                continue

        for e in _edges:
            e.source_node = self.nodes[e.source_id]
            e.target_node = self.nodes[e.target_id]
            if e.source_node.label and e.target_node.label:
                self.edges.append(e)

        return self.edges
