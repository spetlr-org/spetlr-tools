import argparse

from spetlrtools.diagrams.DiagramParser import DiagramParser
from spetlrtools.diagrams.LibraryParser import LibraryParser


def process_diagram(diagram_path: str, module_name: str, start_tag: str, stop_tag: str):
    diagram_edges = set(e.get_Edge() for e in DiagramParser(diagram_path).parse())

    lib_parser = LibraryParser(module_name)
    lib_parser.yaml_block_start_tag = start_tag
    lib_parser.yaml_block_end_tag = stop_tag
    code_edges = set(lib_parser.get_relations())
    if diagram_edges == code_edges:
        return 0

    print("in both:", len(code_edges.intersection(diagram_edges)))
    print("only in diagram:", len(diagram_edges - code_edges))
    for edge in diagram_edges - code_edges:
        print(edge)
    print("only in code:", len(code_edges - diagram_edges))
    for edge in code_edges - diagram_edges:
        print(edge)

    return -1


def main():
    parser = argparse.ArgumentParser(
        description="Compare DrawIO digram edges to docstrings."
    )

    parser.add_argument("module", help="Python module to use.")
    parser.add_argument("diagram", help="Path to the diagram to process.")
    parser.add_argument(
        "--start-tag",
        help="Tag name for use in docstrings.",
        default="```spetlr diagram",
    )
    parser.add_argument(
        "--stop-tag", help="Tag name for use in docstrings.", default="```"
    )

    args = parser.parse_args()

    ret = process_diagram(args.diagram, args.module, args.start_tag, args.stop_tag)
    if ret:
        exit(ret)
