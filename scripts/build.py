#!/usr/bin/env python3
"""Buduje .tar.gz oraz prawdziwe .ipk (ar + control/data.tar.gz), bez narzędzi SDK."""
import gzip
import io
from pathlib import Path
import tarfile
from validate import validate

ROOT=Path(__file__).resolve().parents[1]
VERSION='0.4.1'
PACKAGE=f'enigma2-plugin-skins-polsq_{VERSION}_all.ipk'


def tar_gz(files, ipk=False):
    buffer=io.BytesIO()
    with tarfile.open(fileobj=buffer,mode='w',format=tarfile.GNU_FORMAT) as archive:
        if ipk:
            # Match opkg-build: explicit directories precede ./relative file names.
            dirs={'.'}
            for name,_,_ in files:
                parent=Path(name).parent
                while str(parent)!='.':
                    dirs.add('./'+str(parent));parent=parent.parent
            for name in sorted(dirs,key=lambda n:(n.count('/'),n)):
                info=tarfile.TarInfo(name+'/');info.type=tarfile.DIRTYPE;info.mode=0o755;info.mtime=0
                archive.addfile(info)
        for name,data,mode in files:
            info=tarfile.TarInfo('./'+name if ipk else name);info.size=len(data);info.mode=mode;info.mtime=0
            archive.addfile(info,io.BytesIO(data))
    return gzip.compress(buffer.getvalue(),mtime=0)


def ar(files):
    result=bytearray(b'!<arch>\n')
    for name,data in files:
        header=f'{name+"/":<16}{0:<12}{0:<6}{0:<6}{"100644":<8}{len(data):<10}`\n'.encode('ascii')
        assert len(header)==60
        result+=header+data
        if len(data)%2:result+=b'\n'
    return bytes(result)


def build():
    (ROOT/'PolsQ/VERSION').write_text(VERSION+'\n')
    (ROOT/'PolsQLarge/VERSION').write_text(VERSION+'\n')
    validate()
    validate('PolsQLarge')
    out=ROOT/'dist';out.mkdir(exist_ok=True)
    skinfiles=sorted(p for folder in ('PolsQ','PolsQLarge') for p in (ROOT/folder).rglob('*') if p.is_file())
    payload=[(str(p.relative_to(ROOT)),p.read_bytes(),0o644) for p in skinfiles]
    runtime=sorted(p for p in (ROOT/'runtime').rglob('*.py') if '__pycache__' not in p.parts)
    docs=['README.md','LICENSE','docs/COMPATIBILITY.md']
    manual=payload+[(str(p.relative_to(ROOT)),p.read_bytes(),0o644) for p in runtime]+[(p,(ROOT/p).read_bytes(),0o644) for p in docs+['scripts/install_payload.py']]+[('install.sh',(ROOT/'install.sh').read_bytes(),0o755)]
    (out/f'PolsQ-{VERSION}.tar.gz').write_bytes(tar_gz(manual))
    control=(f'Package: enigma2-plugin-skins-polsq\nVersion: {VERSION}\nArchitecture: all\n'
             f'Maintainer: PolsQ contributors\nSection: skins\nPriority: optional\nDepends: enigma2\n'
             f'Installed-Size: {(sum(len(data) for _,data,_ in payload)+sum(p.stat().st_size for p in runtime)+1023)//1024}\n'
             'Description: PolsQ Full HD skin for OpenATV 7.5, 7.6 and 8.0\n')
    data=tar_gz([('usr/share/enigma2/'+name,content,mode) for name,content,mode in payload]+[('usr/lib/enigma2/python/'+str(p.relative_to(ROOT/'runtime')),p.read_bytes(),0o644) for p in runtime],ipk=True)
    controltar=tar_gz([('control',control.encode(),0o644),
        ('postinst',(ROOT/'packaging/postinst').read_bytes(),0o755)],ipk=True)
    (out/PACKAGE).write_bytes(ar([('debian-binary',b'2.0\n'),('control.tar.gz',controltar),('data.tar.gz',data)]))
    print(out/f'PolsQ-{VERSION}.tar.gz');print(out/PACKAGE)


if __name__=='__main__':
    build()

