import os
import re
from textwrap import dedent
from typing import List

import yaml

from spetlrtools.diagrams.Edge import Edge
from spetlrtools.diagrams.HTMLStripper import condense_whitespace


class DiagramDefinitionError(Exception):
    pass


class DiagramMarkupLibraryParser:
    """Go through a library of files, look for tagged blocks
    and extract the configuration. Based on the configuration,
    return the desired set of diagram edges."""

    yaml_block_start_tag = "```diagram"
    yaml_block_end_tag = "```"
    include_files = ".py$"

    def __init__(self, package_path: str):
        self.package_path = package_path

    def _get_all_blocks(self):
        """generator to get all blocks of code enclosed by tags"""
        pattern = re.compile(
            f"(?<={self.yaml_block_start_tag})"  # lookbehind assertion
            ".*?"  # any code whatsoever, but never include the end tag.
            f"(?={self.yaml_block_end_tag})",  # lookahead assertion
            flags=re.DOTALL,
        )
        for root, dirs, files in os.walk(self.package_path):
            for file in files:
                if re.search(self.include_files, file):
                    file_path = os.path.join(root, file)
                    with open(file_path, encoding="utf-8") as f:
                        # match the tag sequence absolutely anywhere in the file
                        # this is usually in docstrings.
                        for match in pattern.findall(f.read()):
                            yield file_path, str(match)

    def _build_config(self):
        """Parse all the code blocks to build the aggregated
        YAML configuration across the library"""
        config = {}
        for file_path, block in self._get_all_blocks():
            try:
                obj = yaml.safe_load(dedent(block))
            except yaml.YAMLError:
                print(f"WARNING: Skipping unparsable yaml in {file_path}")
                continue
            if not isinstance(obj, dict):
                print(f"WARNING: block in {file_path} is not a dict")
                continue
            for key, node in obj.items():
                if not isinstance(node, dict):
                    print(f"WARNING: The contents of {key} are not a dict: {node}.")
                    print("         If you want a simple alias use:")
                    print(f"           {key}:")
                    print(f"           name: {node}")
                    continue

                try:
                    node["name"] = condense_whitespace(node["name"])
                except KeyError:
                    print(f"WARNING: Missing name in node {key} of {file_path}")
                    continue

                if key in config:
                    if config[key] != node:
                        raise DiagramDefinitionError(
                            f"Node {key} in {file_path} "
                            "conflicts with earlier definitions"
                        )
                config[key] = node
        return config

    def get_relations(self) -> List[Edge]:
        """Returns all edges as requested in the library configuration."""
        config = self._build_config()

        def resolve_name(key):
            if key in config:
                return config[key]["name"]
            else:
                return key

        for key, node in config.items():
            nodename = node["name"]  # presenece already ensured.
            for source in node.get("incoming", []):
                if isinstance(source, str):
                    # incoming edges go *to* the nodename
                    yield Edge(resolve_name(source), nodename)
                else:
                    raise NotImplementedError("styles not supported yet")
            for target in node.get("outgoing", []):
                if isinstance(target, str):
                    # outgoing edges go *from* the nodename
                    yield Edge(nodename, resolve_name(target))
                else:
                    raise NotImplementedError("styles not supported yet")
