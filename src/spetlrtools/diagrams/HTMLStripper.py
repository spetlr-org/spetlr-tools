from html.parser import HTMLParser
from io import StringIO


class HTMLStripper(HTMLParser):
    def __init__(self):
        super().__init__()
        self.reset()
        self.strict = False
        self.convert_charrefs = True
        self.text = StringIO()

    def handle_data(self, d):
        self.text.write(d)
        return self

    def get_data(self):
        return self.text.getvalue()

    @staticmethod
    def strip(text):
        o = HTMLStripper()
        o.feed(text)
        return o.get_data()
