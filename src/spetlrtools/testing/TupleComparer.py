from functools import total_ordering


@total_ordering
class TupleComparer(object):
    """This class contains a potentially nested tuple and can be
    compared even if any of the sub-members are zero.
    The only requirements are that the tuples are of equal length,
    and that they have comparable types in non-zero fields."""

    def __init__(self, data: tuple):
        self.data = data

    def __le__(self, other: "TupleComparer"):
        if self == other:
            return True
        if len(self.data) != len(other.data):
            raise ValueError("Cannot compare tuples of unequal lengths.")

        for lhs, rhs in zip(self.data, other.data):
            if lhs is None:
                if rhs is None:
                    # Equal, check more elements.
                    continue
                else:
                    # None is less than non-none
                    return True
            else:
                # lsh is not none
                if rhs is None:
                    # nothing is less than None
                    return False
                else:
                    # both not None
                    if lhs == rhs:
                        continue

                    if isinstance(lhs, tuple) and isinstance(rhs, tuple):
                        return TupleComparer(lhs) <= TupleComparer(rhs)

                    # neither is None nor tuple and unequal
                    return lhs < rhs

        # if not element comparison could reach a conclusion
        # something broke
        raise ValueError("Inconclusive comparison between unequal tuples")

    def __eq__(self, other):
        return self.data == other.data
