#!/usr/bin/env python3
"""Run pinned native history selection and template converters with C++ stubbed.

Checks real tuple indices, ordering, initial selection, OK/Cancel and empty EPG.
Does not tune a service or emulate receiver graphics.
"""
import argparse
import ast
from contextlib import redirect_stdout
import io
from pathlib import Path
import sys
from time import localtime, strftime
from types import ModuleType, SimpleNamespace as NS
from urllib.request import urlopen
import xml.etree.ElementTree as E

from check_upstream_fonts import PINS, ROOT
from check_upstream_templates import Content, Font, StringList


class Screen(dict):
    def __init__(self, session, **kwargs):
        super().__init__()
        self.onLayoutFinish=[]
        self.skinName=[type(self).__name__]
        self.result='not closed'
    def setTitle(self, title):self.title=title
    def close(self, result):self.result=result


class Listing:
    def __init__(self, rows, **kwargs):
        self.list=rows;self.style='default';self.index=0
    def __getattr__(self, name):
        if name.startswith('go'):return lambda:None
        raise AttributeError(name)
    def setIndex(self, index):self.index=index
    def getCurrent(self):return self.list[self.index] if self.list else None
    def enableAutoNavigation(self, enabled):self.auto=enabled


def converter_class(source, helper_source):
    cls=next(n for n in ast.parse(source).body if isinstance(n,ast.ClassDef) and n.name=='TemplatedMultiContent')
    enigma=ModuleType('enigma');enigma.gFont=Font;enigma.eListboxPythonMultiContent=Content
    names={a.name for n in ast.walk(cls) if isinstance(n,ast.ImportFrom) and n.module=='enigma' for a in n.names}
    for index,name in enumerate(sorted(names-{'gFont'})):setattr(enigma,name,1<<index)
    multi=ModuleType('Components.MultiContent')
    names={a.name for n in ast.walk(cls) if isinstance(n,ast.ImportFrom) and n.module=='Components.MultiContent' for a in n.names}
    for name in names:setattr(multi,name,lambda **kw:kw)
    # Execute the real helper calls as well: accepting arbitrary kwargs in a
    # stub would miss native API differences such as rectangle color names.
    helpers=[n for n in ast.parse(helper_source).body if isinstance(n,ast.FunctionDef) and n.name in (
        'MultiContentEntryText','MultiContentEntryRectangle','MultiContentEntryPixmapAlphaBlend')]
    helper_ns=dict(__resolveColor=lambda value:value,__resolvePixmap=lambda value:value,
        eListboxPythonMultiContent=NS(TYPE_TEXT=0,TYPE_RECT=1,TYPE_PIXMAP_ALPHABLEND=2))
    for name in {n.id for node in helpers for n in ast.walk(node) if isinstance(n,ast.Name) and n.id.startswith('RT_')}:
        helper_ns[name]=1
    exec(compile(ast.Module(body=helpers,type_ignores=[]),'native-history-helpers','exec'),helper_ns)
    def checked(native):
        def call(**kwargs):
            native(**kwargs)
            return kwargs
        return call
    for method in helpers:setattr(multi,method.name,checked(helper_ns[method.name]))
    skin=ModuleType('skin');skin.getSkinFactor=lambda:1.5;skin.parseFont=lambda font:Font(*font.split(';'))
    sys.modules.update({'enigma':enigma,'Components.MultiContent':multi,'skin':skin})
    ns=dict(StringList=StringList,gFont=Font,eListboxPythonMultiContent=Content)
    exec(compile(ast.Module(body=[cls],type_ignores=[]),'native-history-template','exec'),ns)
    return ns['TemplatedMultiContent']


def probe(version, history_source, template_source, helper_source):
    cls=next(n for n in ast.parse(history_source).body if isinstance(n,ast.ClassDef) and n.name=='HistoryZapSelector')
    now=10000
    event=NS(getEventName=lambda:'Długi tytuł audycji z polskimi znakami ąęłść — odcinek specjalny',
        getShortDescription=lambda:'Opis, którego nie należy wciskać między nazwę kanału a godziny.',
        getExtendedDescription=lambda:'Pełny opis',getBeginTime=lambda:9000,getDuration=lambda:3600)
    def info(reference):
        return NS(getName=lambda ref:'Kanał '+ref,getEvent=lambda ref:None if reference=='bez-epg' else event)
    ns=dict(Screen=Screen,List=Listing,StaticText=lambda text:NS(text=text),
        HelpableActionMap=lambda *args,**kwargs:None,_=lambda text:text,
        eServiceCenter=NS(getInstance=lambda:NS(info=info)),ServiceReference=lambda ref:ref,
        getPiconName=lambda ref:ref if ref!='bez-epg' else '',
        getChannelSelectionPiconName=lambda ref:ref if ref!='bez-epg' else '',loadPNG=lambda path:('picon',path),
        time=lambda:now,localtime=localtime,strftime=strftime,ngettext=lambda one,many,n:one if n==1 else many)
    sort=NS(value=0)
    ns['config']=NS(usage=NS(zapHistorySort=sort,time=NS(short=NS(value='%H:%M'))))
    exec(compile(ast.Module(body=[cls],type_ignores=[]),'native-history-selector','exec'),ns)
    selector=ns['HistoryZapSelector'];converter=converter_class(template_source,helper_source)
    for order in (0,1):
        sort.value=order
        dialog=selector(None,['pierwszy','bez-epg','trzeci'],markedItem=0,selectedItem=2)
        dialog.layoutFinished()
        self_menu=dialog['menu']
        expected=['trzeci','bez-epg','pierwszy'] if order==0 else ['pierwszy','bez-epg','trzeci']
        assert [row[7] for row in self_menu.list]==expected
        assert self_menu.index==(0 if order==0 else 2) and not self_menu.auto
        marked=next(row for row in self_menu.list if row[7]=='pierwszy')
        assert marked[1]=='»' and marked[2]=='Kanał pierwszy' and marked[3]==event.getEventName()
        assert marked[4]==event.getShortDescription() and marked[5] and marked[6]==('picon','pierwszy')
        missing=next(row for row in self_menu.list if row[7]=='bez-epg')
        assert missing[3:7]==('','','','')
        for folder in ('PolsQ','PolsQLarge'):
            skin=E.parse(ROOT/folder/'skin.xml').getroot()
            # Names follow native priority in 8.0; 7.5/7.6 use the class name.
            matched=next(name for name in dialog.skinName if skin.find(f"screen[@name='{name}']") is not None)
            assert matched==('HistoryZap' if version=='8.0' else 'HistoryZapSelector')
            for name in ('HistoryZap','HistoryZapSelector'):
                menu_widget=skin.find(f"screen[@name='{name}']/widget[@source='menu']")
                width,height=map(int,menu_widget.get('size').split(','))
                code=menu_widget.find('convert').text
                output=io.StringIO()
                with redirect_stdout(output):
                    instance=converter(code);instance.source=self_menu;instance.changed((0,))
                assert not output.getvalue(),output.getvalue()
                assert instance.content.rows==self_menu.list
                items=instance.content.template
                assert {item['text'] for item in items if 'text' in item}=={1,2,3,5}
                assert next(item['png'] for item in items if 'png' in item)==6
                for item in items:
                    x,y=item['pos'];w,h=item['size']
                    assert 0<=x and x+w<=width and 0<=y and y+h<=instance.content.height
        for index,row in enumerate(self_menu.list):
            self_menu.setIndex(index);dialog.keySelect();assert dialog.result==row[7]
        dialog.keyCancel();assert dialog.result is None
        empty=selector(None,[]);empty.layoutFinished();empty.keySelect();assert empty.result is None
    print(f'OpenATV {version}: native history aliases, eight fields, sort/selection, missing EPG/picon, OK/Cancel and both template sizes pass (C++ stubbed).')


def main():
    parser=argparse.ArgumentParser();parser.add_argument('sources',nargs='?',type=Path);parser.add_argument('--download',action='store_true');args=parser.parse_args()
    if args.sources is None and not args.download:parser.error('provide source snapshots or --download')
    for version,pin in PINS.items():
        sources=[]
        for path in ('lib/python/Screens/ChannelSelection.py','lib/python/Components/Converter/TemplatedMultiContent.py','lib/python/Components/MultiContent.py'):
            if args.sources:sources.append((args.sources/version/path).read_text())
            else:
                with urlopen(f'https://raw.githubusercontent.com/openatv/enigma2/{pin}/{path}',timeout=30) as response:sources.append(response.read().decode())
        probe(version,*sources)


if __name__=='__main__':main()

