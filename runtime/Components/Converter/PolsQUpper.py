"""Upper-case text for news-style InfoBar titles (Polish letters included)."""
from Components.Converter.Converter import Converter
from Components.Element import cached


class PolsQUpper(Converter):
    def __init__(self, argument):
        Converter.__init__(self, argument)

    @cached
    def getText(self):
        return (self.source.text or '').upper()

    text = property(getText)
