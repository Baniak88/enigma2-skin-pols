"""Channel number of the current service for OpenATV 7.5, 7.6 and 8.0.

ServiceName "Number" exists only in OpenATV 8.0; getChannelNum() is available
in all supported images. Empty when the service has no number (e.g. a recording).
"""
from Components.Converter.Converter import Converter
from Components.Element import cached


class PolsQChannelNumber(Converter):
    def __init__(self, argument):
        Converter.__init__(self, argument)

    @cached
    def getText(self):
        reference = getattr(self.source, 'serviceref', None)
        try:
            number = reference and reference.getChannelNum() or None
        except Exception:
            number = None
        return str(number) if number else ''

    text = property(getText)
