import re
from html.parser import HTMLParser
from io import StringIO


class HTMLStripper(HTMLParser):
    """removes all HTML markup, leaving only normal letters and characters."""

    # Drawio nodes use HTML markup. I want this markup to not affect comparisons.
    def __init__(self):
        super().__init__()
        self.reset()
        self.strict = False
        self.convert_charrefs = True
        self.text = StringIO()

    def handle_data(self, d):
        # needed for the internal working of HTMLParser
        # not to be used directly
        self.text.write(d)
        return self

    def get_data(self) -> str:
        return self.text.getvalue()

    @staticmethod
    def strip(text: str) -> str:
        """Return the input minus any markup."""
        o = HTMLStripper()
        o.feed(text)
        return o.get_data()


def condense_whitespace(input: str) -> str:
    """The output has all whitespace sequences replaces with a single space.
    Leading and trailing whitespaces are stripped."""
    return re.sub(r"\s+", " ", input).strip()
