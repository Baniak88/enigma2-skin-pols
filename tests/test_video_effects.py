"""Reveal transition, shadow and frame around every native TV preview."""
from pathlib import Path
import sys
import types
import unittest
import xml.etree.ElementTree as E

ROOT=Path(__file__).resolve().parents[1]


class Timer:
    def __init__(self):self.callback=[];self.active=False
    def start(self,interval,single):self.active=True;self.interval=interval
    def stop(self):self.active=False


class Widget:
    def __init__(self):self.visible=True;self.pixmap=None
    def hide(self):self.visible=False
    def show(self):self.visible=True
    def setPixmap(self,pixmap):self.pixmap=pixmap


def load_renderer():
    """Import the runtime module against minimal Enigma2 stubs."""
    class Renderer:
        CHANGED_DEFAULT,CHANGED_SPECIFIC=0,3
        def __init__(self):self.instance=None;self.skinAttributes=None;self.suspended=True
        def applySkin(self,desktop,parent):return True
        def onShow(self):self.suspended=False
        def onHide(self):self.suspended=True
    stubs={
        'enigma':types.SimpleNamespace(ePixmap=Widget,eTimer=Timer,iPlayableService=types.SimpleNamespace(evStart=1)),
        'Components':types.ModuleType('Components'),
        'Components.Renderer':types.ModuleType('Components.Renderer'),
        'Components.Renderer.Renderer':types.SimpleNamespace(Renderer=Renderer),
        'Tools':types.ModuleType('Tools'),
        'Tools.Directories':types.SimpleNamespace(SCOPE_GUISKIN=5,resolveFilename=lambda scope,path:str(ROOT/path)),
        'Tools.LoadPixmap':types.SimpleNamespace(LoadPixmap=lambda path:path if Path(path).is_file() else None),
    }
    saved={k:sys.modules.get(k) for k in stubs}
    sys.modules.update(stubs)
    try:
        code=(ROOT/'runtime/Components/Renderer/PolsQVideoFade.py').read_text()
        namespace={'__name__':'PolsQVideoFade'};exec(compile(code,'PolsQVideoFade.py','exec'),namespace)
        return namespace['PolsQVideoFade']
    finally:
        for k,v in saved.items():
            if v is None:sys.modules.pop(k,None)
            else:sys.modules[k]=v


class VideoEffects(unittest.TestCase):
    def test_every_preview_has_shadow_fade_and_frame_in_order(self):
        for folder in ('PolsQ','PolsQLarge'):
            skin=E.parse(ROOT/folder/'skin.xml').getroot()
            pigs=[s for s in skin.findall('screen') if s.find("widget[@render='Pig']") is not None]
            self.assertGreaterEqual(len(pigs),5)
            for s in pigs:
                pig=s.find("widget[@render='Pig']");w,h=pig.get('size').split(',')
                fade=s.find("widget[@render='PolsQVideoFade']")
                self.assertIsNotNone(fade,s.get('name'))
                self.assertEqual((fade.get('position'),fade.get('size')),(pig.get('position'),pig.get('size')))
                self.assertEqual(fade.get('source'),'session.CurrentService')
                shadow=s.find(f"ePixmap[@pixmap='PolsQ/assets/q-video-shadow-{w}x{h}.png']")
                frame=s.find(f"ePixmap[@pixmap='PolsQ/assets/q-video-frame-{w}x{h}.png']")
                z=lambda n:int(n.get('zPosition','0'))
                self.assertLess(z(shadow),z(pig));self.assertLess(z(pig),z(fade));self.assertLess(z(fade),z(frame))
                for path in fade.get('pixmaps').split(','):self.assertTrue((ROOT/path).is_file(),path)

    def test_headlines_have_text_shadow(self):
        skin=E.parse(ROOT/'PolsQ/skin.xml').getroot()
        for name in ('Menu','ChannelSelection','InfoBar'):
            shadows=[n for n in skin.find(f"screen[@name='{name}']") if n.get('shadowColor')]
            self.assertTrue(shadows,name)
            for n in shadows:self.assertEqual(n.get('shadowOffset'),'2,2')

    def test_reveal_runs_once_and_hides_itself(self):
        cls=load_renderer();r=cls()
        r.skinAttributes=[('pixmaps',','.join(f'PolsQ/assets/q-video-fade-{i:02d}.png' for i in range(14))),('interval','40'),('scale','1')]
        r.instance=Widget();r.applySkin(None,None)
        self.assertEqual(len(r.frames),14);self.assertEqual(r.skinAttributes,[('scale','1')])
        self.assertFalse(r.instance.visible)
        r.onShow();self.assertTrue(r.instance.visible and r.timer.active)
        self.assertEqual(r.instance.pixmap,r.frames[0])
        for _ in range(13):r.timer.callback[0]()
        self.assertEqual(r.instance.pixmap,r.frames[-1])
        r.timer.callback[0]()
        self.assertFalse(r.instance.visible or r.timer.active)
        # Info updates do not replay; a new service does.
        r.changed((r.CHANGED_SPECIFIC,99));self.assertFalse(r.timer.active)
        r.changed((r.CHANGED_SPECIFIC,1));self.assertTrue(r.timer.active)
        r.onHide();self.assertFalse(r.instance.visible or r.timer.active)
        r.changed((r.CHANGED_SPECIFIC,1));self.assertFalse(r.timer.active)


if __name__=='__main__':unittest.main()
