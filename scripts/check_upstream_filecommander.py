#!/usr/bin/env python3
"""Probe real FileList rows and FileCommander focus/headings with C++ stubbed."""
import argparse
import ast
from os import lstat
from os.path import basename,dirname,exists,join,normpath,splitext
from pathlib import Path
from stat import S_IMODE,S_ISBLK,S_ISCHR,filemode
import tempfile
from types import SimpleNamespace
from urllib.request import urlopen
import xml.etree.ElementTree as E
from check_upstream_fonts import PINS
from validate import check_template

ROOT=Path(__file__).resolve().parents[1]


class Content:
    TYPE_TEXT=0
    TYPE_PIXMAP_ALPHABLEND=1
    def setFont(self,index,font): self.font=font
    def setItemHeight(self,height): self.height=height


class SkinIcon: pass
class ServiceReference: pass
class MenuList: pass


def check_file_rows(source,skin,path):
    tree=ast.parse(source)
    cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='FileListBase')
    constants={}
    for node in tree.body:
        if isinstance(node,ast.Assign):
            for target in node.targets:
                if isinstance(target,ast.Name) and (target.id.startswith(('FILE_','SELECT_','ICON_')) or target.id=='EXTENSIONS'):
                    constants[target.id]=ast.literal_eval(node.value)
    fonts={n.get('name'):(n.get('font'),int(n.get('size')),int(n.get('height'))) for n in skin.findall('fonts/alias')}
    parameters={n.get('name'):tuple(map(int,n.get('value').split(','))) for n in skin.findall('parameters/parameter')}
    ns=dict(constants,MenuList=MenuList,fonts=fonts,parameters=parameters,gFont=lambda *a:a,
        eListboxPythonMultiContent=Content,SkinIcon=SkinIcon,eServiceReference=ServiceReference,
        BT_SCALE=1,BT_VALIGN_CENTER=2,RT_HALIGN_LEFT=4,RT_VALIGN_CENTER=8,
        splitext=splitext,exists=exists,normpath=normpath,join=join)
    exec(compile(ast.Module(body=[cls],type_ignores=[]),'upstream-FileList.py','exec'),ns)
    listing=ns['FileListBase'].__new__(ns['FileListBase'])
    listing.l=Content();listing.refresh=lambda:None
    listing.extensionIcons={key:object() for key in ('lock_on','lock_off','directory','file','storage','parent','current','ipk')}
    listing.currentDirectory=str(path.parent);listing.selectedItems=[]
    width=int(skin.find("screen[@name='FileCommander']/widget[@name='listleft']").get('size').split(',')[0])
    for multi in (False,True):
        (listing.setMultiSelectMode if multi else listing.setSingleSelectMode)()
        assert listing.l.font==('PolsQText',28) and listing.itemHeight==64
        row=listing.fileListComponent(name=path.name,path=str(path),isDir=False,isLink=False,selected=False if multi else None,dirIcon=None)
        for _,x,y,w,h,*_ in row[1:]:
            assert 0<=x and x+w<=width and 0<=y and y+h<=64,(multi,(x,y,w,h))
        if multi:
            row=listing.assignSelection(row,constants['SELECT_ALL'],True)
            assert listing.selectedItems==[str(path)] and row[0][constants['FILE_SELECTED']] is True
            row=listing.assignSelection(row,constants['SELECT_ALL'],False)
            assert listing.selectedItems==[] and row[0][constants['FILE_SELECTED']] is False


class Pane:
    def __init__(self,path): self.path=path;self.active=False
    def selectionEnabled(self,value): self.active=value
    def getSortBy(self): return '0.0,0.0'
    def getPath(self): return str(self.path)
    def getCurrentDirectory(self): return str(self.path.parent)
    def getIsSpecialFolder(self): return False


class Heading:
    def updateList(self,rows): self.rows=rows


def check_focus_and_headings(source,skin,path):
    tree=ast.parse(source)
    cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='FileCommander')
    names={'keyGoLeftColumn','keyGoRightColumn','goColumn','updateHeading'}
    methods=[n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name in names]
    assert len(methods)==len(names)
    class NumberScaler:
        def scale(self,value,**kwargs): return str(value)+' B'
    ns=dict(lstat=lstat,normpath=normpath,dirname=dirname,basename=basename,filemode=filemode,S_IMODE=S_IMODE,
        S_ISCHR=S_ISCHR,S_ISBLK=S_ISBLK,NumberScaler=NumberScaler,STORAGE_DEVICES_NAME='Storage',_=lambda value:value)
    exec(compile(ast.Module(body=methods,type_ignores=[]),'upstream-FileCommander.py','exec'),ns)
    class Commander(dict):
        def updateTitle(self): pass
        def updateButtons(self): pass
        def username(self,value): return str(value)
        def groupname(self,value): return str(value)
        def formatTime(self,value): return '2026-11-04 13:40'
    for name in names: setattr(Commander,name,ns[name])
    left,right=Pane(path),Pane(path)
    state=Commander(listleft=left,listright=right,headleft=Heading(),headright=Heading())
    state.keyGoLeftColumn();assert left.active and not right.active and state.leftActive
    state.keyGoRightColumn();assert not left.active and right.active and not state.leftActive
    for side in ('left','right'):
        row=state['head'+side].rows[0]
        assert len(row)==27 and row[17]==str(path) and row[1] and row[11] and row[13]
        widget=skin.find(f"screen[@name='FileCommander']/widget[@source='head{side}']")
        width=int(widget.get('size').split(',')[0])
        template=check_template(widget.find('convert').text)
        assert template['selectionEnabled'] is False
        for _,item in template['template']:
            assert item['text']<len(row) and item['pos'][0]+item['size'][0]<=width


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
        assert 'andale.ttf' in read('data/fonts/Makefile.am'), 'OpenATV must supply the registered monospace font'
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'PolsQ.ipk';path.write_text('probe')
            check_file_rows(read('lib/python/Components/FileList.py'),skin,path)
            module='ui.py' if version=='8.0' else 'plugin.py'
            check_focus_and_headings(read('lib/python/Plugins/Extensions/FileCommander/'+module),skin,path)
        print(f'OpenATV {version}: native FileList row fonts/selection and FileCommander focus/headings passed (C++ stubbed).')


if __name__=='__main__': main()

