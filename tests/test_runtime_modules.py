"""Runtime modules run against small Enigma2 stand-ins (no receiver needed)."""
from pathlib import Path
import importlib.util
import sys
import types
import unittest

ROOT=Path(__file__).resolve().parents[1]


class Size:
    def __init__(self,w,h):self.w,self.h=w,h
    def width(self):return self.w
    def height(self):return self.h


class Widget:
    def __init__(self,parent=None):self._size=Size(1572,58);self.pos=(0,0)
    def size(self):return self._size
    def resize(self,size):self._size=size
    def move(self,point):self.pos=(point.x,point.y)


class Label(Widget):
    alignCenter=1
    def __init__(self,parent=None):
        super().__init__(parent);self.text='';self.calls=0
    def setText(self,text):self.text=text
    def calculateSize(self):
        self.calls+=1
        chars_per_line=max(1,self._size.w//20)
        lines=sum(max(1,-(-len(part)//chars_per_line)) for part in self.text.split('\n')) if self.text else 0
        return Size(len(self.text)*20,lines*40)
    def __getattr__(self,name):
        if name.startswith('set'):return lambda *a:None
        raise AttributeError(name)


class Timer:
    def __init__(self):self.timeout=types.SimpleNamespace(connect=lambda f:object());self.running=None
    def start(self,ms,single=False):self.running=ms
    def stop(self):self.running=None


def install_stubs():
    enigma=types.ModuleType('enigma')
    enigma.eLabel=Label;enigma.eWidget=Widget;enigma.eTimer=Timer
    enigma.eSize=Size;enigma.ePoint=lambda x,y:types.SimpleNamespace(x=x,y=y)
    enigma.gFont=lambda *a:a
    sys.modules['enigma']=enigma
    skin=types.ModuleType('skin');skin.parseColor=lambda v:v;skin.parseFont=lambda v,*a:v
    sys.modules['skin']=skin

    class Element:
        CHANGED_DEFAULT,CHANGED_ALL,CHANGED_CLEAR=0,1,2
        def __init__(self,*a):self.source=None
    class Renderer(Element):
        def __init__(self):Element.__init__(self);self.instance=None;self.skinAttributes=[]
        def applySkin(self,desktop,parent):return True
        def onShow(self):pass
        def onHide(self):pass
    class LabelRenderer(Renderer):
        def applySkin(self,desktop,parent):return True
    class Converter(Element):
        def __init__(self,arg):Element.__init__(self)
    for name,attrs in {'Components':{},'Components.Renderer':{},'Components.Converter':{},
            'Components.Renderer.Renderer':{'Renderer':Renderer},'Components.Renderer.Label':{'Label':LabelRenderer},
            'Components.Converter.Converter':{'Converter':Converter},'Components.Element':{'cached':lambda f:f}}.items():
        module=types.ModuleType(name);module.__dict__.update(attrs);sys.modules[name]=module


def load(path):
    spec=importlib.util.spec_from_file_location(path.stem,path);module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module);return module


class RuntimeModules(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.saved={k:sys.modules.get(k) for k in ('enigma','skin','Components','Components.Renderer','Components.Converter','Components.Renderer.Renderer','Components.Renderer.Label','Components.Converter.Converter','Components.Element')}
        install_stubs()
        cls.upper=load(ROOT/'runtime/Components/Converter/PolsQUpper.py')
        cls.number=load(ROOT/'runtime/Components/Converter/PolsQChannelNumber.py')
        cls.summary=load(ROOT/'runtime/Components/Renderer/PolsQSummary.py')

    @classmethod
    def tearDownClass(cls):
        for k,v in cls.saved.items():
            if v is None:sys.modules.pop(k,None)
            else:sys.modules[k]=v

    def test_upper_handles_polish_and_empty(self):
        c=self.upper.PolsQUpper('');c.source=types.SimpleNamespace(text='zażółć gęślą jaźń')
        self.assertEqual(c.text,'ZAŻÓŁĆ GĘŚLĄ JAŹŃ')
        c.source=types.SimpleNamespace(text=None);self.assertEqual(c.text,'')

    def test_channel_number_from_service_reference(self):
        c=self.number.PolsQChannelNumber('')
        c.source=types.SimpleNamespace(serviceref=types.SimpleNamespace(getChannelNum=lambda:4))
        self.assertEqual(c.text,'4')
        c.source=types.SimpleNamespace(serviceref=types.SimpleNamespace(getChannelNum=lambda:0));self.assertEqual(c.text,'')
        c.source=types.SimpleNamespace(serviceref=None);self.assertEqual(c.text,'')
        c.source=types.SimpleNamespace();self.assertEqual(c.text,'')

    def test_summary_fits_and_skips_unchanged_text(self):
        r=self.summary.PolsQSummary();r.instance=Label();r.instance.resize(Size(400,80))
        r.source=types.SimpleNamespace(text='słowo '*3000)
        r.changed((0,))
        self.assertTrue(r.instance.text.endswith('…'))
        self.assertLessEqual(r.instance.calculateSize().height(),80)
        calls=r.instance.calls;r.changed((0,))
        self.assertEqual(r.instance.calls,calls,'unchanged text is not measured again')


if __name__=='__main__':unittest.main()
