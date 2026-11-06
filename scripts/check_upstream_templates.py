#!/usr/bin/env python3
"""Uruchamia oryginalny konwerter TemplatedMultiContent ze stubem warstwy C++.

Sprawdza tworzenie/switch stylów, nie renderuje ani nie emuluje całego Enigma2.
Argument: katalog z checkoutami 7.5/, 7.6/, 8.0/; kod upstream nie jest dołączany.
"""
import ast
import contextlib
import io
from pathlib import Path
import sys
import types
import xml.etree.ElementTree as E

ROOT=Path(__file__).resolve().parents[1]


class Font:
    def __init__(self,family,size):self.family=family;self.pointSize=size


class Content:
    def setFont(self,*args):pass
    def setTemplate(self,value):self.template=value
    def setItemWidth(self,value):self.width=value
    def setItemHeight(self,value):self.height=value
    def setList(self,value):self.rows=value


class Downstream(list):
    def changed(self,what):pass


class StringList:
    CHANGED_SPECIFIC=1
    def __init__(self,args):self.content=None;self.source=None;self.downstream_elements=Downstream()


def check(sources):
    enigma=types.ModuleType('enigma');enigma.gFont=Font;enigma.eListboxPythonMultiContent=Content
    multi=types.ModuleType('Components.MultiContent')
    for kind in ['Text','PixmapAlphaBlend','Pixmap','PixmapAlphaTest','Progress','ProgressPixmap','Rectangle','LinearGradient','LinearGradientAlphaBlend']:
        setattr(multi,'MultiContentEntry'+kind,lambda **kw:(0,*kw.get('pos',(0,0)),*kw.get('size',(0,0)),kw))
    multi.MultiContentTemplateColor=lambda *a:a
    skin=types.ModuleType('skin');skin.getSkinFactor=lambda:1.5;skin.parseFont=lambda s:Font(s.split(';')[0],int(s.split(';')[1]))
    sys.modules.update({'enigma':enigma,'skin':skin,'Components.MultiContent':multi})
    for version in ('7.5','7.6','8.0'):
        p=sources/version/'lib/python/Components/Converter/TemplatedMultiContent.py'
        parsed=ast.parse(p.read_text())
        cls=next(n for n in parsed.body if isinstance(n,ast.ClassDef))
        for n in ast.walk(cls):
            if isinstance(n,ast.ImportFrom) and n.module=='enigma':
                for alias in n.names:
                    if not hasattr(enigma,alias.name):setattr(enigma,alias.name,1)
        namespace={'StringList':StringList,'gFont':Font,'eListboxPythonMultiContent':Content}
        exec(compile(ast.Module(body=[cls],type_ignores=[]),str(p),'exec'),namespace)
        converter=namespace['TemplatedMultiContent'];count=0
        for screen in E.parse(ROOT/'PolsQ/skin.xml').getroot().findall('screen'):
            for xml in screen.findall(".//convert[@type='TemplatedMultiContent']"):
                errors=io.StringIO()
                with contextlib.redirect_stdout(errors):
                    instance=converter(xml.text)
                    styles=instance.template.get('templates',{'default':None})
                    for style in styles:
                        # Slot count: OpenATV Menu=8, plugins=4, audio/subtitles=6.
                        if screen.get('name')=='QuickMenu':
                            slots=3 if xml is screen.find("widget[@source='mainlist']/convert") else 2
                        elif screen.get('name') in ('PackageAction','PluginAction'):
                            slots=12
                        elif screen.get('name')=='FileCommander':
                            slots=27
                        elif screen.get('name') in ('HistoryZap','HistoryZapSelector'):
                            slots=8
                        else:
                            slots=8 if screen.get('name')=='Menu' else 4 if screen.get('name').startswith('Plugin') else 6
                        sample=tuple(range(slots))
                        instance.source=types.SimpleNamespace(style=style,list=[sample])
                        instance.changed((0,))
                        assert instance.content.height>0
                        for entry in instance.content.template:
                            kw=entry[-1]
                            for key in ('text','png'):
                                if key in kw and isinstance(kw[key],int):assert 0<=kw[key]<len(sample),(screen.get('name'),style,kw)
                        count+=1
                assert not errors.getvalue(),errors.getvalue()
        print(f'OpenATV {version}: original converter accepted {count} template/style combinations (C++ layer stubbed).')


if __name__=='__main__':check(Path(sys.argv[1]))

