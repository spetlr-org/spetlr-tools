import os
import re
from textwrap import dedent

import yaml

from spetlrtools.diagrams.Edge import Edge


class DiagramDefinitionError(Exception):
    pass


class LibraryParser:
    yaml_block_start_tag = "```spetlr diagram"
    yaml_block_end_tag = "```"

    def _get_all_blocks(self):
        pattern = re.compile(
            f"(?<={self.yaml_block_start_tag})"  # lookbehind assertion
            ".*?"  # any code whatsoever, but never include the end tag.
            f"(?={self.yaml_block_end_tag})",  # lookahead assertion
            flags=re.DOTALL,
        )
        for root, dirs, files in os.walk(self.package_path):
            for file in files:
                if file.endswith(".py"):
                    file_path = os.path.join(root, file)
                    with open(file_path, encoding="utf-8") as f:
                        for match in pattern.findall(f.read()):
                            yield file_path, str(match)

    def __init__(self, package_path: str):
        self.package_path = package_path

    def _build_config(self):
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
                try:
                    _ = node["name"]
                except KeyError:
                    print(f"WARNING: Missing name in node {key} of {file_path}")
                    continue

                if key in config:
                    if config[key] != node:
                        raise DiagramDefinitionError(
                            f"Node {key} conflicts with earlier definitions"
                        )
                config[key] = node
        return config

    def get_relations(self):
        """Returns all edges as a tuple of (source, target, style)"""
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
                    yield Edge(resolve_name(source), nodename)
                else:
                    raise NotImplementedError("styles not supported yet")
            for target in node.get("outgoing", []):
                if isinstance(target, str):
                    yield Edge(nodename, resolve_name(target))
                else:
                    raise NotImplementedError("styles not supported yet")
