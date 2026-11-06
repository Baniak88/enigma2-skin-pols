#!/usr/bin/env python3
"""Exercise pinned native skin lookup and SkinSelection preview with C++ stubbed.

No receiver preferences are loaded or changed. Only the original layoutFinished
and loadPreview methods run; createItems, keySave and GUI reload never run.
"""
import argparse
import ast
from os.path import isfile, join, split
from pathlib import Path
from types import SimpleNamespace as NS
from urllib.request import urlopen
import xml.etree.ElementTree as E

from check_upstream_fonts import PINS, ROOT


def definitions(source, names):
    return [n for n in ast.parse(source).body if isinstance(n, (ast.FunctionDef, ast.ClassDef)) and n.name in names]


def probe(version, sources):
    skin=E.parse(ROOT/'PolsQ/skin.xml').getroot()
    ns={'_':lambda text:text,'join':join,'split':split,'isfile':isfile}
    # Run native Setup's ordered name construction without its GUI/config init.
    cls=definitions(sources['Screens/Setup.py'], {'Setup'})[0]
    init=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='__init__')
    start=next(i for i,n in enumerate(init.body) if isinstance(n,ast.If) and 'self.skinName' in ast.unparse(n.test))
    receiver=NS(skinName='SkinSelection')
    exec(compile(ast.Module(body=init.body[start:start+3],type_ignores=[]),'native-Setup-names','exec'),{'self':receiver,'setup':'Skin'})
    assert receiver.skinName==['SkinSelection','setup_Skin','SetupSkin','Setup']

    # Execute readSkin's original resolution logic up to GUI attribute parsing.
    funcs=definitions(sources['skin.py'], {'findWidgets','readSkin'})
    reader=next(n for n in funcs if n.name=='readSkin')
    stop=next(i for i,n in enumerate(reader.body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Attribute) and t.attr=='skinAttributes' for t in n.targets))
    reader.body=reader.body[:stop]+[ast.Return(value=ast.Tuple(elts=[ast.Name(id='myName',ctx=ast.Load()),ast.Name(id='myScreen',ctx=ast.Load())],ctx=ast.Load()))]
    ns['domScreens']={n.get('name'):(n,None) for n in skin.findall('screen')}
    exec(compile(ast.fix_missing_locations(ast.Module(body=funcs,type_ignores=[])),'native-skin-lookup','exec'),ns)
    for names in (receiver.skinName,receiver.skinName[1:],receiver.skinName[2:]):
        name,selected=ns['readSkin'](NS(mandatoryWidgets=['config','description','footnote']),None,names,None)
        assert name==names[0] and selected.get('size')=='1920,1080'
        assert selected.find("widget[@name='preview']") is not None

    class Setup(dict):
        def layoutFinished(self):pass
    class Preview:
        visible=False
        pixmap=None
        def hide(self):self.visible=False
        def show(self):self.visible=True
    class PicLoad:
        def __init__(self):
            self.callbacks=[]
            self.PictureData=NS(get=lambda:self.callbacks)
        def setPara(self,params):self.params=params
        def getData(self):return NS(__deref__=lambda:'decoded-preview')
        def startDecode(self,path):
            self.path=Path(path)
            for callback in self.callbacks:callback()
    gui=NS(value='PolsQ/skin.xml');lcd=NS(value='skin_display.xml')
    ns.update(Setup=Setup,ePicLoad=PicLoad,config=NS(skin=NS(guiSkin=gui,lcdSkin=lcd)))
    exec(compile(ast.Module(body=definitions(sources['Screens/SkinSelection.py'],{'SkinSelection'}),type_ignores=[]),'native-SkinSelection','exec'),ns)
    selection=ns['SkinSelection'].__new__(ns['SkinSelection']);dict.__init__(selection)
    dimensions=tuple(map(int,skin.find("screen[@name='SkinSelection']/widget[@name='preview']").get('size').split(',')))
    preview=Preview();preview.instance=NS(size=lambda:NS(width=lambda:dimensions[0],height=lambda:dimensions[1]),setPixmap=lambda pixmap:setattr(preview,'pixmap',pixmap))
    selection['preview']=preview
    selection.guiRoot=str(ROOT);selection.lcdRoot=str(ROOT/'display');selection.noPreview=str(ROOT/'absent.png');selection.picLoad=None
    current=[gui];selection.getCurrentItem=lambda:current[0]
    selection.layoutFinished()
    assert selection.picLoad.params[:2]==(608,342)
    assert selection.picLoad.path==ROOT/'PolsQ/prev.png' and preview.visible and preview.pixmap=='decoded-preview'
    current[0]=NS(value='Fallback Font 1');selection.loadPreview()
    assert not preview.visible
    print(f'OpenATV {version}: native name priority, all three layouts, preview decode/show/hide pass (C++ stubbed).')


def main():
    parser=argparse.ArgumentParser();parser.add_argument('sources',nargs='?',type=Path);parser.add_argument('--download',action='store_true');args=parser.parse_args()
    if args.sources is None and not args.download:parser.error('provide snapshot directory or --download')
    for version,pin in PINS.items():
        sources={}
        for path in ('Screens/SkinSelection.py','Screens/Setup.py','skin.py'):
            if args.sources:sources[path]=(args.sources/version/'lib/python'/path).read_text()
            else:
                with urlopen(f'https://raw.githubusercontent.com/openatv/enigma2/{pin}/lib/python/{path}',timeout=30) as response:sources[path]=response.read().decode('utf-8')
        probe(version,sources)


if __name__=='__main__':main()

