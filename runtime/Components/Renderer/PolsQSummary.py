"""Fit short EPG summaries to complete measured lines; INFO keeps full EPG.

Fast path: unchanged text is not measured again, text that fits is set once,
and very long EPG texts are cut before the binary search, so moving through
the channel list does not re-layout kilobytes of description.
"""
from Components.Renderer.Label import Label


class PolsQSummary(Label):
    MAX_CHARS = 1200

    def __init__(self):
        Label.__init__(self)
        self.lastText = None

    def applySkin(self, desktop, parent):
        result = Label.applySkin(self, desktop, parent)
        self.lastText = None
        self.changed((self.CHANGED_DEFAULT,))
        return result

    def changed(self, what):
        if self.instance is None:
            return
        text = '' if what[0] == self.CHANGED_CLEAR else (self.source.text or '')
        if text == self.lastText:
            return
        self.lastText = text
        if len(text) > self.MAX_CHARS:
            text = text[:self.MAX_CHARS]
        self.instance.setText(text)
        height = self.instance.size().height()
        if not text or self.instance.calculateSize().height() <= height:
            return
        low, high, best = 0, len(text), '…'
        while low <= high:
            middle = (low + high) // 2
            boundary = text.rfind(' ', 0, middle)
            candidate = text[:boundary if boundary > 0 else middle].rstrip() + '…'
            self.instance.setText(candidate)
            if self.instance.calculateSize().height() <= height:
                best = candidate
                low = middle + 1
            else:
                high = middle - 1
        self.instance.setText(best)
