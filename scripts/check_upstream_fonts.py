#!/usr/bin/env python3
"""Probe the native valueFont setter with C++ replaced, using pinned OpenATV sources."""
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


def probe(version,source):
    skin=E.parse(ROOT/'PolsQ/skin.xml').getroot()
    registered={node.get('name') for node in skin.findall('fonts/font')}
    values=[node.get('valueFont') for node in skin.findall(".//widget[@name='config']")]
    defaults=skin.find('windowstyle/configList')
    values.append(defaults.get('valueFont'))
    cls=next(node for node in ast.parse(source).body if isinstance(node,ast.ClassDef) and node.name=='AttributeParser')
    method=next(node for node in cls.body if isinstance(node,ast.FunctionDef) and node.name=='valueFont')
    module=ast.Module(body=[method],type_ignores=[])
    recorded=[]
    def parse_font(value,scale):
        family,size=value.rsplit(';',1)
        assert family in registered and int(size)>=28
        return (family,int(size),scale)
    ns={'parseFont':parse_font}
    exec(compile(module,'upstream-skin.py','exec'),ns)
    scale=((1,1),(1,1))
    gui=SimpleNamespace(setValueFont=recorded.append)
    instance=SimpleNamespace(guiObject=gui,scaleTuple=scale)
    for value in values:
        ns['valueFont'](instance,value)
    assert len(recorded)==len(values)
    assert all(font[0]=='PolsQText' and font[1]==30 and font[2]==scale for font in recorded)
    for name in ('entryFont','valueFont','headerFont'):
        assert name in defaults.attrib and f'configList.attrib.get("{name}"' in source
    print(f'OpenATV {version}: native valueFont setter accepts 30px PolsQText for every config widget (C++/font loading stubbed).')


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('sources',nargs='?',type=Path)
    parser.add_argument('--download',action='store_true',help='Fetch only the three pinned public skin.py files')
    args=parser.parse_args()
    if args.sources is None and not args.download:
        parser.error('provide the source snapshot directory or --download')
    for version,pin in PINS.items():
        if args.sources is not None:
            source=(args.sources/version/'lib/python/skin.py').read_text()
        else:
            with urlopen(f'https://raw.githubusercontent.com/openatv/enigma2/{pin}/lib/python/skin.py',timeout=30) as response:
                source=response.read().decode('utf-8')
        probe(version,source)


if __name__=='__main__':
    main()

