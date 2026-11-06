"""Remaining event minutes independent of OpenATV elapsed/remaining preferences."""
from time import time
from Components.Converter.Converter import Converter
from Components.Converter.Poll import Poll
from Components.Element import cached


class PolsQEventRemaining(Converter, Poll):
    def __init__(self, argument):
        Converter.__init__(self, argument)
        Poll.__init__(self)
        self.poll_interval = 30000
        self.poll_enabled = True

    @cached
    def getText(self):
        event = self.source.event
        if event is None or event.getDuration() <= 0:
            return ''
        now = int(time())
        if now < event.getBeginTime():
            return ''
        remaining = max(0, event.getBeginTime() + event.getDuration() - now)
        if not remaining:
            return ''
        return 'Do końca: %d min' % ((remaining + 59) // 60)

    text = property(getText)

