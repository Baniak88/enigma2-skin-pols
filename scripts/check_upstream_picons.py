#!/usr/bin/env python3
"""Próba logiki natywnego Picon; warstwa C++ i ustawienia zastąpione stubami.

Argument: katalog checkoutów 7.5/, 7.6/, 8.0/. Nie jest to test dekodera.
"""
import ast
from os.path import exists,getmtime,getsize,join
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[1]


class Renderer:
    CHANGED_DEFAULT=0
    def __init__(self):self.instance=None
    def applySkin(self,desktop,parent):return True


class Pixmap:
    def setScale(self,value):self.scale=value
    def setPixmapFromFile(self,value):self.path=value
    def show(self):self.visible=True
    def hide(self):self.visible=False


def check(sources):
    fallback=ROOT/'PolsQ/picon_default.png'
    for version in ('7.5','7.6','8.0'):
        path=sources/version/'lib/python/Components/Renderer/Picon.py'
        cls=next(n for n in ast.parse(path.read_text()).body if isinstance(n,ast.ClassDef) and n.name=='Picon')
        with tempfile.TemporaryDirectory() as tmp:
            logo=Path(tmp)/'tvnhd.png';logo.write_bytes((ROOT/'PolsQ/icons/folder.png').read_bytes())
            settings=SimpleNamespace(usage=SimpleNamespace(showpicon=SimpleNamespace(value=True)))
            found=[str(logo)]
            ns=dict(Renderer=Renderer,ePixmap=Pixmap,exists=exists,getmtime=getmtime,getsize=getsize,join=join,
                findPicon=lambda *a:'',resolveFilename=lambda *a:str(fallback),SCOPE_GUISKIN=1,SCOPE_SKINS=2,
                config=settings,getDABImage=lambda *a:'',getPiconName=lambda *a:found[0],searchPaths=[])
            exec(compile(ast.Module(body=[cls],type_ignores=[]),str(path),'exec'),ns)
            renderer=ns['Picon']();renderer.source=SimpleNamespace(text='1:0:1:1234:1:1:C00000:0:0:0:')
            renderer.instance=Pixmap()
            renderer.changed((1,));assert renderer.instance.path==str(logo) and renderer.instance.visible
            found[0]='';renderer.changed((1,));assert renderer.instance.path==str(fallback) and renderer.instance.visible
            found[0]=str(logo);settings.usage.showpicon.value=False
            renderer.changed((1,));assert renderer.instance.path==str(fallback) and renderer.instance.visible
            renderer.changed((2,));assert not renderer.instance.visible
            print(f'OpenATV {version}: found logo / missing logo / disabled picons / cleared source OK (C++ stubbed).')


if __name__=='__main__':check(Path(sys.argv[1]))

