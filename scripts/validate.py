#!/usr/bin/env python3
"""Kontrole pakietu i kontraktów OpenATV. Nie emuluje Enigma2/C++ ani tunera."""
import ast
import json
from pathlib import Path
import re
import struct
import xml.etree.ElementTree as E
import zlib

ROOT=Path(__file__).resolve().parents[1]
SOURCE_TYPES={'StaticText','List','ServiceEvent','Event','Boolean','CurrentService','Clock'}


def check_template(code):
    tree=ast.parse(code,mode='eval')
    names={'gFont','MultiContentEntryText','MultiContentEntryPixmapAlphaBlend','MultiContentEntryRectangle'}
    for node in ast.walk(tree):
        assert not isinstance(node,(ast.Attribute,ast.Subscript,ast.Lambda,ast.ListComp)), 'Niedozwolony szablon'
        if isinstance(node,ast.Call):
            assert isinstance(node.func,ast.Name) and node.func.id in names
    flags={n.id for n in ast.walk(tree) if isinstance(n,ast.Name) and n.id not in names}
    assert all(n.startswith(('RT_','BT_')) for n in flags)
    ns={n:1<<i for i,n in enumerate(sorted(flags))}
    ns.update(gFont=lambda *a:a,MultiContentEntryText=lambda **kw:('text',kw),MultiContentEntryPixmapAlphaBlend=lambda **kw:('pixmap',kw),MultiContentEntryRectangle=lambda **kw:('rect',kw))
    result=eval(compile(tree,'skin-template','eval'),{'__builtins__':{}},ns)
    assert result['fonts']
    templates=result.get('templates',{'default':(result.get('itemHeight'),result.get('template'))})
    assert 'default' in templates
    for style,(height,entries,*_) in templates.items():
        height=height[1] if isinstance(height,tuple) else height
        assert height>0
        for _,kw in entries:
            x,y=kw['pos'];w,h=kw['size']
            assert x>=0 and y>=0 and w>0 and h>0 and y+h<=height,(style,kw)
            assert kw.get('font',0)<len(result['fonts'])
    return result


def check_png(path):
    data=path.read_bytes();assert data[:8]==b'\x89PNG\r\n\x1a\n',path
    offset=8;raw=b'';size=None
    while offset<len(data):
        length=struct.unpack('>I',data[offset:offset+4])[0]
        kind=data[offset+4:offset+8];chunk=data[offset+8:offset+8+length]
        crc=struct.unpack('>I',data[offset+8+length:offset+12+length])[0]
        assert zlib.crc32(kind+chunk)&0xffffffff==crc,path
        if kind==b'IHDR':
            w,h,depth,ctype,_,_,_=struct.unpack('>IIBBBBB',chunk);assert depth==8 and ctype==6;size=(w,h)
        if kind==b'IDAT':raw+=chunk
        offset+=12+length
    assert len(zlib.decompress(raw))==size[1]*(1+size[0]*4)


def check_picon_layers(screen):
    """Enigma2 tworzy renderery przed eLabel/ePixmap niezależnie od kolejności XML.

    Przy tym samym z dekoracja znajdzie się nad rendererem. Wykrywamy pełne
    zasłonięcie prostokąta pikony, a nie tylko obecność konkretnego atrybutu.
    """
    for picon in screen.findall("widget[@render='Picon']"):
        x,y=map(int,picon.get('position').split(','));w,h=map(int,picon.get('size').split(','))
        pz=int(picon.get('zPosition','0'))
        for decoration in screen:
            if decoration.tag not in ('eLabel','ePixmap'):continue
            if decoration.tag=='eLabel' and not decoration.get('backgroundColor'):continue
            dx,dy=map(int,decoration.get('position').split(','));dw,dh=map(int,decoration.get('size').split(','))
            covers=dx<=x and dy<=y and dx+dw>=x+w and dy+dh>=y+h
            assert not covers or int(decoration.get('zPosition','0'))<pz,(screen.get('name'),'decoration covers picon',decoration.attrib)


def validate(directory='PolsQ'):
    skin=E.parse(ROOT/directory/'skin.xml').getroot()
    colors={x.get('name') for x in skin.findall('colors/color')}
    contracts=json.loads((ROOT/'scripts/openatv-contracts.json').read_text())
    names=[s.get('name') for s in skin.findall('screen')]
    assert len(names)==len(set(names))
    assert {'Menu','BouquetSelector','EPGBouquetSelector','GraphicalEPG','GraphicalEPGPIG','EPGSelectionMulti','EPGvertical','Setup','MovieSelection','RecordTimerOverview'}<=set(names)
    for s in skin.findall('screen'):
        check_picon_layers(s)
        sw,sh=map(int,s.get('size').split(','));sx,sy=map(int,s.get('position').split(','))
        assert sx>=0 and sy>=0 and sx+sw<=1920 and sy+sh<=1080,s.get('name')
        for n in s:
            x,y=map(int,n.get('position').split(','));w,h=map(int,n.get('size').split(','))
            assert x>=0 and y>=0 and w>0 and h>0 and x+w<=sw and y+h<=sh,(s.get('name'),n.attrib)
            for key,value in n.attrib.items():
                if 'color' in key.lower():
                    assert value in colors or re.fullmatch(r'#[0-9a-fA-F]{6,8}',value),(key,value)
                if key in ('pixmap','pixmaps'):
                    for path in value.split(','):
                        assert (ROOT/path).is_file(),path
            if n.tag=='widget':
                assert bool(n.get('name')) != bool(n.get('source'))
                key=n.get('name') or n.get('source')
                for version,contract in contracts.items():
                    known=contract['screens'][s.get('name')]['widgets']
                    if contract['screens'][s.get('name')].get('available') is False:
                        continue
                    if '.' not in key:
                        assert key in known or n.get('conditional')==key,(version,s.get('name'),key,'unknown widget')
                        if n.get('name'):
                            assert known.get(key) not in SOURCE_TYPES,(s.get('name'),key,'source used as GUI widget')
                for convert in n.findall('convert'):
                    if convert.get('type')=='TemplatedMultiContent':
                        result=check_template(convert.text)
                        if s.get('name')=='Menu':
                            assert {'default','text','number','image','both'}<=set(result['templates'])
                if n.get('render')=='Picon':
                    assert n.find('convert').text=='Reference'
        present={n.get('name') or n.get('source') for n in s.findall('widget')}
        for version,contract in contracts.items():
            assert set(contract['screens'][s.get('name')]['required'])<=present,(version,s.get('name'),'mandatory widgets')
    template=E.parse(ROOT/directory/'skinTemplates.xml').getroot().find('template')
    assert template.get('component')=='serviceList'
    assert {x.get('name') for x in template.findall('mode')}=={'services','bouquets','other'}
    assert template.find('.//pixmap[@index="Picon"]') is not None
    for path in (ROOT/directory).rglob('*.png'):check_png(path)
    graph=skin.find("screen[@name='GraphicalEPG']")
    assert all(graph.find(f"widget[@name='timeline{i}']") is not None for i in range(6))
    assert graph.find("widget[@name='bouquetlist']") is not None
    assert (ROOT/'PolsQ/picon_default.png').is_file()
    # SkinSelection wyszukuje prev.png w katalogu skórki (bez wpisu w XML).
    thumbnail=(ROOT/directory/'prev.png').read_bytes()
    assert struct.unpack('>II',thumbnail[16:24])==(640,360)
    print(f'OK: {directory}, {len(names)} screens, OpenATV '+('/'.join(contracts))+' widget contracts, templates, geometry, PNG assets.')


if __name__=='__main__':
    validate()
    validate('PolsQLarge')

