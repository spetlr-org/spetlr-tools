import importlib
import inspect
import pkgutil
import re
from textwrap import dedent

import yaml

from spetlrtools.diagrams.Edge import Edge


class LibraryParser:
    yaml_block_start_tag = "```spetlr diagram"
    yaml_block_end_tag = "```"

    def __init__(self, package_name):
        self.package_name = package_name

    def import_submodules(self, package_name):
        package = importlib.import_module(package_name)

        results = {}
        for loader, name, is_pkg in pkgutil.walk_packages(package.__path__):
            if "." in name:
                # I experienced unexpected package names popping up here that were not in
                # my code module.
                continue
            full_name = package.__name__ + "." + name
            results[full_name] = importlib.import_module(full_name)
            if is_pkg:
                results.update(self.import_submodules(full_name))
        return results

    def get_class_docstrings_in_module(self):
        modules = self.import_submodules(self.package_name)
        for mod_name, mod in modules.items():
            for name, obj in inspect.getmembers(mod):
                if inspect.isclass(obj):
                    if not str(obj.__module__).startswith(mod.__name__):
                        continue
                    name = f"{mod_name}.{name}"
                    doc = obj.__doc__
                    if not doc:
                        continue
                    yield name, doc

    def get_relations(self):
        """Returns all edges as a tuple of (source, target, style)"""
        for name, doc in self.get_class_docstrings_in_module():
            for match in re.findall(
                f"(?<={self.yaml_block_start_tag})"  # lookbehind assertion
                ".*?"  # any code whatsoever, but never include the end tag.
                f"(?={self.yaml_block_end_tag})",  # lookahead assertion
                doc,
                flags=re.DOTALL,
            ):
                try:
                    obj = yaml.safe_load(dedent(str(match)))
                except yaml.YAMLError:
                    print(f"WARNING: Skipping unparsable yaml in docstring of {name}")
                    continue
                if not isinstance(obj, dict):
                    print(f"WARNING: in docstring of {name} is not a dict")
                    continue
                for key, node in obj.items():
                    try:
                        nodename = node["name"]
                    except KeyError:
                        print(f"WARNING: Missing name in node {key} of {name}")
                        continue
                    for source in node.get("incoming", []):
                        if isinstance(source, str):
                            yield Edge(source, nodename)
                        else:
                            raise NotImplementedError("styles not supported yet")
                    for target in node.get("outgoing", []):
                        if isinstance(target, str):
                            yield Edge(nodename, target)
                        else:
                            raise NotImplementedError("styles not supported yet")
