import argparse

from spetlrtools.diagrams.DiagramMarkupLibraryParser import DiagramMarkupLibraryParser
from spetlrtools.diagrams.DrawioDiagramParser import DrawioDiagramParser


def process_diagram(
    diagram_path: str,
    code_path: str,
    start_tag: str = DiagramMarkupLibraryParser.yaml_block_start_tag,
    stop_tag: str = DiagramMarkupLibraryParser.yaml_block_end_tag,
    include_files: str = DiagramMarkupLibraryParser.include_files,
) -> int:
    """Collect the set of edges from the diagram and from the code.
    Compare for equality, return the exit code."""
    diagram_edges = set(e.get_Edge() for e in DrawioDiagramParser(diagram_path).parse())

    lib_parser = DiagramMarkupLibraryParser(code_path)
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
        description="Compare DrawIO diagram edges to docstrings."
    )

    parser.add_argument(
        "--code-path", help="Root of the codebase to parse.", required=True
    )
    parser.add_argument(
        "--diagram", help="Path to the diagram to process.", required=True
    )
    parser.add_argument(
        "--start-tag",
        help="Tag name for use in docstrings.",
        default=DiagramMarkupLibraryParser.yaml_block_start_tag,
    )
    parser.add_argument(
        "--stop-tag",
        help="Tag name for use in docstrings.",
        default=DiagramMarkupLibraryParser.yaml_block_end_tag,
    )

    parser.add_argument(
        "--include-files",
        help="Regex to determine which files to read.",
        default=DiagramMarkupLibraryParser.include_files,
    )
    args = parser.parse_args()

    ret = process_diagram(
        diagram_path=args.diagram,
        code_path=args.code_path,
        start_tag=args.start_tag,
        stop_tag=args.stop_tag,
        include_files=args.include_files,
    )
    if ret:
        exit(ret)
