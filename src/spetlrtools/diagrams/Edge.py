from collections import namedtuple

_Edge = namedtuple("_Edge", "source target")


class Edge(_Edge):
    """An edge going from source to target.
    Additional details can be added, but will not be considered in equality tests."""

    # The complicated heritage with __new__ and namedtuple ensure that I have to write
    # no further comparison code, I can simply say
    # set(list(Edges from code)) == set(list(Edges from diagram))

    def __new__(cls, source: str, target: str, *, style=None):
        self = super().__new__(cls, source, target)
        self.style = style
        return self
