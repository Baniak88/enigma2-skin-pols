#!/usr/bin/env python3
"""Sprawdza rzeczywisty ChoiceList i ChoiceEntryComponent ze stubami warstwy C++."""
import ast
from pathlib import Path
import sys
import xml.etree.ElementTree as E

ROOT=Path(__file__).resolve().parents[1]


class Content:
    TYPE_TEXT=0
    TYPE_PIXMAP_ALPHABLEND=1
    def setFont(self,index,font):self.font=font
    def setItemHeight(self,height):self.height=height


class MenuList:
    def __init__(self,rows,wrap,content):self.l=content()


def check(sources):
    skin=E.parse(ROOT/'PolsQ/skin.xml').getroot()
    f=skin.find("fonts/alias[@name='ChoiceList']")
    fonts={'ChoiceList':(f.get('font'),int(f.get('size')),int(f.get('height')))}
    parameters={p.get('name'):list(map(int,p.get('value').split(','))) for p in skin.findall('parameters/parameter')}
    for version in ('7.5','7.6','8.0'):
        path=sources/version/'lib/python/Components/ChoiceList.py'
        tree=ast.parse(path.read_text())
        nodes=[n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))]
        ns=dict(MenuList=MenuList,eListboxPythonMultiContent=Content,gFont=lambda *a:a,fonts=fonts,parameters=parameters,
            parseVerticalAlignment=lambda value:0,RT_HALIGN_LEFT=1,RT_HALIGN_CENTER=2,RT_VALIGN_CENTER=4,RT_BLEND=8,
            SCOPE_GUISKIN=0,resolveFilename=lambda *a:'',LoadPixmap=lambda *a:None,MultiContentEntryText=lambda **kw:kw)
        exec(compile(ast.Module(body=nodes,type_ignores=[]),str(path),'exec'),ns)
        entry=ns['ChoiceEntryComponent']('1',['Back USB: Elements 25A2 (DISK_1)  /media/hdd/'])
        text=entry[1]
        assert text[1:5]==(64,16,1712,40)
        choice=ns['ChoiceList']([entry]);assert choice.l.font==('PolsQText',30) and choice.getItemHeight()==72
        print(f'OpenATV {version}: native device-choice row uses PolsQText 30 and 72px height (C++ stubbed).')


if __name__=='__main__':check(Path(sys.argv[1]))

