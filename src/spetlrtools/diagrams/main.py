import argparse

from spetlrtools.diagrams.DiagramParser import DiagramParser
from spetlrtools.diagrams.LibraryParser import LibraryParser


def process_diagram(diagram_path: str, code_path: str, start_tag: str, stop_tag: str, include_files:str):
    diagram_edges = set(e.get_Edge() for e in DiagramParser(diagram_path).parse())

    lib_parser = LibraryParser(code_path)
    lib_parser.yaml_block_start_tag = start_tag
    lib_parser.yaml_block_end_tag = stop_tag
    lib_parser.include_files = include_files
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

    parser.add_argument("--code-path", help="Root of the codebase to parse.", required=True)
    parser.add_argument("--diagram", help="Path to the diagram to process.", required=True)
    parser.add_argument(
        "--start-tag",
        help="Tag name for use in docstrings.",
        default="```diagram",
    )
    parser.add_argument(
        "--stop-tag", help="Tag name for use in docstrings.", default="```"
    )

    parser.add_argument(
        "--include-files", help="Regex to determine which files to read.", default=".py$"
    )
    args = parser.parse_args()

    ret = process_diagram(
        diagram_path= args.diagram,
        code_path= args.code_path,
        start_tag= args.start_tag,
        stop_tag= args.stop_tag,
        include_files= args.include_files)
    if ret:
        exit(ret)
