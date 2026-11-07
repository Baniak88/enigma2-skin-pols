"""Short reveal animation over the native TV preview (Pig).

The video plane cannot be animated from Python, so the OSD layer above it is:
when the screen opens or the playing service starts, a navy veil with a light
sweep covers the preview and fades out frame by frame. The timer runs only for
the length of the sequence (about 0.6 s) and the widget is hidden afterwards,
so no animation loop remains active while the screen is idle.
"""
from enigma import ePixmap, eTimer, iPlayableService

from Components.Renderer.Renderer import Renderer
from Tools.Directories import SCOPE_GUISKIN, resolveFilename
from Tools.LoadPixmap import LoadPixmap


class PolsQVideoFade(Renderer):
    GUI_WIDGET = ePixmap
    TRIGGERS = (iPlayableService.evStart,)

    def __init__(self):
        Renderer.__init__(self)
        self.frames = []
        self.interval = 40
        self.index = 0
        self.timer = eTimer()
        self.timer.callback.append(self.step)

    def applySkin(self, desktop, parent):
        attributes = []
        for attrib, value in self.skinAttributes or []:
            if attrib == 'pixmaps':
                frames = (LoadPixmap(resolveFilename(SCOPE_GUISKIN, path.strip())) for path in value.split(','))
                self.frames = [frame for frame in frames if frame is not None]
            elif attrib == 'interval':
                self.interval = max(20, int(value))
            else:
                attributes.append((attrib, value))
        self.skinAttributes = attributes
        result = Renderer.applySkin(self, desktop, parent)
        self.rest()
        return result

    def rest(self):
        self.timer.stop()
        if self.instance:
            self.instance.hide()

    def play(self):
        if not self.instance or not self.frames:
            return
        self.index = 0
        self.instance.setPixmap(self.frames[0])
        self.instance.show()
        self.timer.start(self.interval, False)

    def step(self):
        self.index += 1
        if not self.instance or self.index >= len(self.frames):
            self.rest()
            return
        self.instance.setPixmap(self.frames[self.index])

    def changed(self, what):
        # Only a newly started service (zap, preview on OK) replays the reveal;
        # EPG or info updates of the same channel keep the picture untouched.
        if what[0] == self.CHANGED_SPECIFIC and len(what) > 1 and what[1] in self.TRIGGERS and not self.suspended:
            self.play()

    def onShow(self):
        Renderer.onShow(self)
        self.play()

    def onHide(self):
        Renderer.onHide(self)
        self.rest()

    def preWidgetRemove(self, instance):
        self.timer.stop()
