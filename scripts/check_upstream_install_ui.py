#!/usr/bin/env python3
"""Exercise native SelectionList, Processing and footer visibility with C++ stubbed."""
import argparse
import ast
from pathlib import Path
from types import SimpleNamespace
from urllib.request import urlopen
import xml.etree.ElementTree as E

ROOT=Path(__file__).resolve().parents[1]
PINS={'7.5':'29c41504a2bdecd764d54373109e3c692810b189',
      '7.6':'e42a0ffb0064962321bf500999ac2bc48cadec34',
      '8.0':'39f548521c4c3a667348139720ebe3bf3ac3cf22'}


def definitions(source):
    return ast.Module(body=[n for n in ast.parse(source).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))],type_ignores=[])


class Content:
    TYPE_TEXT=0
    TYPE_PIXMAP_ALPHABLEND=1
    def setFont(self,index,font): self.font=font
    def setItemHeight(self,height): self.height=height


class MenuList:
    def __init__(self,rows,enableWrapAround=False,content=Content):
        self.list=rows;self.l=content()
    def setList(self,rows): self.list=rows
    def getSelectedIndex(self): return 0


class Size:
    def __init__(self,w,h): self.w=w;self.h=h
    def width(self): return self.w
    def height(self): return self.h


class Window:
    def __init__(self,w,h): self.dim=Size(w,h);self.pos=Size(0,0)
    def size(self): return self.dim
    def csize(self): return self.dim
    def resize(self,dim): self.dim=dim
    def move(self,pos): self.pos=pos
    def getFont(self): return ('PolsQText',28)
    def setText(self,text): self.text=text


def check_selection(source,skin):
    alias=skin.find("fonts/alias[@name='SelectionList']")
    fonts={'SelectionList':(alias.get('font'),int(alias.get('size')),int(alias.get('height')))}
    parameters={n.get('name'):tuple(map(int,n.get('value').split(','))) for n in skin.findall('parameters/parameter')}
    ns=dict(MenuList=MenuList,eListboxPythonMultiContent=Content,fonts=fonts,parameters=parameters,
        gFont=lambda *a:a,RT_HALIGN_LEFT=1,RT_VALIGN_CENTER=2,BT_SCALE=4,BT_KEEP_ASPECT_RATIO=8,
        SCOPE_GUISKIN=0,resolveFilename=lambda scope,path:str(ROOT/'PolsQ'/path),LoadPixmap=lambda **kw:kw['path'],icons=None)
    exec(compile(definitions(source),'upstream-SelectionList.py','exec'),ns)
    listing=ns['SelectionList']()
    listing.addSelection('PolsQ.ipk','/tmp/PolsQ.ipk',0,False)
    listing.addSelection('Other.ipk','/tmp/Other.ipk',1,False)
    assert listing.l.font==('PolsQText',30) and listing.l.height==72
    assert listing.getSelectionsList()==[]
    listing.toggleSelection()
    assert listing.getSelectionsList()==[('PolsQ.ipk','/tmp/PolsQ.ipk',0)]
    listing.toggleAllSelection()
    assert listing.getSelectionsList()==[('Other.ipk','/tmp/Other.ipk',1)]
    area=skin.find("screen[@name='IpkgInstaller']/widget[@name='list']")
    width=int(area.get('size').split(',')[0])
    for entry in listing.list:
        for item in entry[1:]:
            _,x,y,w,h,*_=item
            assert 0<=x and x+w<=width and 0<=y and y+h<=listing.l.height
    assert all(Path(path).is_file() for path in ns['icons'])


def check_processing(source,skin):
    cls=next(n for n in ast.parse(source).body if isinstance(n,ast.ClassDef) and n.name=='ProcessingScreen')
    method=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='setDescription')
    screen=skin.find("screen[@name='Processing']")
    width,height=map(int,screen.get('size').split(','))
    label=screen.find("widget[@name='description']")
    x,y=map(int,label.get('position').split(','));w,h=map(int,label.get('size').split(','))
    class State:
        def __init__(self):
            self.instance=Window(width,height);self.description=''
            self.label=Window(w,h)
            self.widget=SimpleNamespace(instance=self.label,setText=self.label.setText)
        def __getitem__(self,key):
            assert key=='description'
            return self.widget
    text_height=[36]
    ns=dict(eSize=Size,ePoint=Size,getDesktop=lambda _:SimpleNamespace(size=lambda:Size(1920,1080)),
        eLabel=SimpleNamespace(calculateTextSize=lambda *args:Size(w,text_height[0])))
    exec(compile(ast.Module(body=[method],type_ignores=[]),'upstream-Processing.py','exec'),ns)
    state=State()
    for new_height,text in ((36,'Instalowanie rozszerzeń.'),(72,'Dłuższy opis operacji w dwóch liniach.')):
        text_height[0]=new_height
        ns['setDescription'](state,text)
        assert state.label.text==text and state.label.dim.height()==new_height
        assert y+new_height<state.instance.dim.height()
        assert 0<=state.instance.pos.width() and state.instance.pos.width()+state.instance.dim.width()<=1920
        assert 0<=state.instance.pos.height() and state.instance.pos.height()+state.instance.dim.height()<=1080


def check_footer(source_text,source_converter):
    class Element:
        CHANGED_ALL=0
        def __init__(self,*args): pass
        def changed(self,*args): pass
    class Converter(Element):
        def __init__(self,*args): self.downstream_elements=[];self.source=None
        def connectDownstream(self,downstream): self.downstream_elements.append(downstream)
    ns=dict(Source=Element,Converter=Converter,eTimer=None)
    exec(compile(definitions(source_text),'upstream-StaticText.py','exec'),ns)
    exec(compile(definitions(source_converter),'upstream-ConditionalShowHide.py','exec'),ns)
    text=ns['StaticText']('')
    converter=ns['ConditionalShowHide']('');converter.source=text
    marker=SimpleNamespace(visible=True);caption=SimpleNamespace(visible=True)
    converter.connectDownstream(marker);converter.connectDownstream(caption)
    assert not marker.visible and not caption.visible
    text.setText('Instaluj');converter.changed((0,))
    assert marker.visible and caption.visible
    text.setText('');converter.changed((0,))
    assert not marker.visible and not caption.visible


def main():
    parser=argparse.ArgumentParser();parser.add_argument('sources',nargs='?',type=Path);parser.add_argument('--download',action='store_true')
    args=parser.parse_args()
    if args.sources is None and not args.download: parser.error('provide snapshots or --download')
    skin=E.parse(ROOT/'PolsQ/skin.xml').getroot()
    for version,pin in PINS.items():
        def read(path):
            if args.sources is not None: return (args.sources/version/path).read_text()
            with urlopen(f'https://raw.githubusercontent.com/openatv/enigma2/{pin}/{path}',timeout=30) as response:
                return response.read().decode('utf-8')
        check_selection(read('lib/python/Components/SelectionList.py'),skin)
        check_processing(read('lib/python/Screens/Processing.py'),skin)
        check_footer(read('lib/python/Components/Sources/StaticText.py'),read('lib/python/Components/Converter/ConditionalShowHide.py'))
        print(f'OpenATV {version}: native package selection, Processing resize and empty footer visibility passed (C++ stubbed).')


if __name__=='__main__': main()

