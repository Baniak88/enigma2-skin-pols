#!/usr/bin/env python3
"""Próba cyklu natywnego Pig w OpenATV 8.0 ze stubem eVideoWidget.

Nie sprawdza dekodowania ani sterownika wideo. Argument: katalog checkoutów.
"""
import ast
from pathlib import Path
import sys
from types import SimpleNamespace
import xml.etree.ElementTree as E

ROOT=Path(__file__).resolve().parents[1]


class Video:
    def __init__(self,pos,size):self.pos=pos;self.dim=size;self.restored=False
    def position(self):return self.pos
    def size(self):return self.dim
    def resize(self,size):self.dim=size
    def move(self,pos):self.pos=pos
    def setDecoder(self,decoder):self.decoder=decoder
    def setFBSize(self,size):self.fb=size
    def restoreFullsize(self):self.restored=True


class Renderer:
    def __init__(self):self.instance=None
    def applySkin(self,desktop,parent):return True


def check(sources):
    path=sources/'8.0/lib/python/Components/Renderer/Pig.py'
    node=next(c for c in ast.parse(path.read_text()).body if isinstance(c,ast.ClassDef) and c.name=='Pig')
    calls=[]
    ns={'Renderer':Renderer,'eVideoWidget':Video,'getDesktop':lambda index:SimpleNamespace(size=lambda:(1920,1080)),'PipPigMode':calls.append}
    exec(compile(ast.Module(body=[node],type_ignores=[]),str(path),'exec'),ns)
    for name in ('ChannelSelection','ChannelSelection_PIG'):
        xml=E.parse(ROOT/'PolsQ/skin.xml').getroot().find(f"screen[@name='{name}']/widget[@render='Pig']")
        pos=tuple(map(int,xml.get('position').split(',')));size=tuple(map(int,xml.get('size').split(',')))
        renderer=ns['Pig']();renderer.skinAttributes=list(xml.attrib.items());renderer.instance=Video(pos,size)
        renderer.postWidgetCreate(renderer.instance)
        assert renderer.instance.decoder==0 and renderer.instance.fb==(1920,1080)
        renderer.applySkin(None,None);renderer.onShow()
        assert renderer.instance.pos==pos and renderer.instance.dim==size and calls[-1] is True
        renderer.onHide();assert renderer.instance.restored and calls[-1] is False
        print(f'OpenATV 8.0 {name}: decoder 0, 16:9 rectangle and restore lifecycle OK (video driver stubbed).')


if __name__=='__main__':check(Path(sys.argv[1]))

