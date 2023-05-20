from collections import namedtuple

_Edge = namedtuple("_Edge", "source target")


class Edge(_Edge):
    def __new__(cls, source: str, target: str, *, style=None):
        self = super().__new__(cls, source, target)
        self.style = style
        return self
