"""News-style ticker for the InfoBar red bar.

Light on the receiver: one opaque label is moved inside a clipping widget.
The timer runs only when the text is wider than the bar and the InfoBar is
visible; short text is drawn once and never animated.
"""
from enigma import eLabel, ePoint, eSize, eTimer, eWidget, gFont
from Components.Renderer.Renderer import Renderer
from skin import parseColor, parseFont

MAX_CHARS = 320
MAX_WIDTH = 8000
GAP = 160


class PolsQTicker(Renderer):
    GUI_WIDGET = eWidget

    def __init__(self):
        Renderer.__init__(self)
        self.label = None
        self.font = gFont('Regular', 28)
        self.foreground = None
        self.background = None
        self.step = 4
        self.interval = 40
        self.pause = 2500
        self.text = ''
        self.offset = 0
        self.textWidth = 0
        self.visible = True
        self.timer = eTimer()
        try:
            self.timerConnection = self.timer.timeout.connect(self.tick)
        except AttributeError:
            self.timerConnection = None
            self.timer.callback.append(self.tick)

    def applySkin(self, desktop, parent):
        attributes = []
        for attribute, value in self.skinAttributes or []:
            if attribute == 'font':
                self.font = parseFont(value)
            elif attribute == 'foregroundColor':
                self.foreground = parseColor(value)
            elif attribute in ('step', 'interval', 'pause'):
                setattr(self, attribute, max(1, int(value)))
            else:
                if attribute == 'backgroundColor':
                    self.background = parseColor(value)
                attributes.append((attribute, value))
        self.skinAttributes = attributes
        result = Renderer.applySkin(self, desktop, parent)
        self.setupLabel()
        return result

    def postWidgetCreate(self, instance):
        self.label = eLabel(instance)

    def preWidgetRemove(self, instance):
        self.timer.stop()
        self.label = None

    def setupLabel(self):
        if self.label is None or self.instance is None:
            return
        label = self.label
        label.setFont(self.font)
        if self.foreground is not None:
            label.setForegroundColor(self.foreground)
        if self.background is not None:
            # Opaque label: no alpha blending while it scrolls.
            label.setBackgroundColor(self.background)
            label.setTransparent(0)
        else:
            label.setTransparent(1)
        label.setVAlign(eLabel.alignCenter)
        for name, value in (('setNoWrap', 1), ('setWrap', 0)):
            method = getattr(label, name, None)
            if method is not None:
                try:
                    method(value)
                    break
                except Exception:
                    pass
        self.layout()

    def changed(self, what):
        if what[0] == self.CHANGED_CLEAR:
            text = ''
        else:
            text = ' '.join((self.source.text or '').split())
        if len(text) > MAX_CHARS:
            cut = text.rfind(' ', 0, MAX_CHARS)
            text = text[:cut if cut > 0 else MAX_CHARS].rstrip(' ,.;:') + '…'
        if text == self.text:
            return
        self.text = text
        self.layout()

    def layout(self):
        self.timer.stop()
        if self.label is None or self.instance is None:
            return
        size = self.instance.size()
        width, height = size.width(), size.height()
        self.label.resize(eSize(MAX_WIDTH, height))
        self.label.setText(self.text)
        self.textWidth = self.label.calculateSize().width() if self.text else 0
        self.offset = 0
        if self.textWidth <= width:
            self.label.resize(eSize(width, height))
            self.label.move(ePoint(0, 0))
            return
        self.label.resize(eSize(min(MAX_WIDTH, self.textWidth + 8), height))
        self.label.move(ePoint(0, 0))
        if self.visible:
            self.timer.start(self.pause, True)

    def tick(self):
        if self.label is None or self.instance is None or not self.visible:
            return
        self.offset -= self.step
        if self.offset + self.textWidth + GAP < 0:
            self.offset = self.instance.size().width()
        self.label.move(ePoint(self.offset, 0))
        self.timer.start(self.interval, True)

    def onShow(self):
        base = getattr(Renderer, 'onShow', None)
        if base is not None:
            base(self)
        self.visible = True
        self.layout()

    def onHide(self):
        base = getattr(Renderer, 'onHide', None)
        if base is not None:
            base(self)
        self.visible = False
        self.timer.stop()
