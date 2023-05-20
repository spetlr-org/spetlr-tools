import xml.etree.ElementTree as ET
from itertools import chain
from typing import Dict, List, Optional

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

    def parse(self):
        with open(self.path, "r", encoding="utf-8") as f:
            conts = f.read()
            diagram = ET.fromstring(conts)
        _edges = []

        for cell in chain(diagram.iter("mxCell"), diagram.iter("object")):
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
