import gzip
import io
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from build import PACKAGE, VERSION, build
from validate import validate


def read_ar(data):
    assert data[:8]==b'!<arch>\n'
    result={};offset=8
    while offset<len(data):
        h=data[offset:offset+60];assert h[58:]==b'`\n'
        name=h[:16].decode().strip().rstrip('/');size=int(h[48:58])
        result[name]=data[offset+60:offset+60+size]
        offset+=60+size+size%2
    assert offset==len(data)
    return result


class Packages(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        build()

    def test_skin_contracts_and_assets(self):
        validate()

    def test_ipk_complete_payload(self):
        files=read_ar((ROOT/'dist'/PACKAGE).read_bytes())
        self.assertEqual(set(files),{'debian-binary','control.tar.gz','data.tar.gz'})
        self.assertEqual(files['debian-binary'],b'2.0\n')
        with tarfile.open(fileobj=io.BytesIO(files['control.tar.gz'])) as t:
            control=t.extractfile('./control').read().decode()
            self.assertTrue(t.getmember('.').isdir())
        self.assertIn('Architecture: all\n',control)
        self.assertIn('Depends: enigma2\n',control)
        self.assertIn(f'Version: {VERSION}\n',control)
        with tarfile.open(fileobj=io.BytesIO(files['data.tar.gz'])) as t:
            names={m.name.removeprefix('./') for m in t if m.isfile()}
            expected={'usr/share/enigma2/'+str(p.relative_to(ROOT)) for folder in ('PolsQ','PolsQLarge') for p in (ROOT/folder).rglob('*') if p.is_file()}
            expected.update('usr/lib/enigma2/python/'+str(p.relative_to(ROOT/'runtime')) for p in (ROOT/'runtime').rglob('*.py') if '__pycache__' not in p.parts)
            self.assertEqual(names,expected)
            self.assertEqual(t.extractfile('./usr/share/enigma2/PolsQ/VERSION').read().decode().strip(),VERSION)
            for p in (ROOT/'PolsQ').rglob('*'):
                if p.is_file():
                    name='./usr/share/enigma2/'+str(p.relative_to(ROOT))
                    self.assertEqual(t.extractfile(name).read(),p.read_bytes())
                    self.assertEqual(t.getmember(name).mode,0o644)
                    self.assertTrue(t.getmember('./'+str(Path(name).parent)).isdir())

    def test_manual_install_backup_and_symlink_refusal(self):
        with tempfile.TemporaryDirectory() as temp:
            temp=Path(temp);source=temp/'package'
            with tarfile.open(ROOT/'dist'/f'PolsQ-{VERSION}.tar.gz') as t:
                for m in t:
                    self.assertFalse(Path(m.name).is_absolute())
                    self.assertNotIn('..',Path(m.name).parts)
                t.extractall(source,filter='data')
            env=dict(os.environ,DESTDIR=str(temp/'receiver'))
            target=temp/'receiver/usr/share/enigma2/PolsQ'
            def install():
                return subprocess.run(['sh',str(source/'install.sh')],env=env,capture_output=True,text=True)
            first=install();self.assertEqual(first.returncode,0,first.stderr)
            self.assertIn('INSTALACJA ZAKOŃCZONA POMYŚLNIE',first.stdout)
            self.assertIn('GUI',first.stdout)
            self.assertIn(f'Wersja: {VERSION}',first.stdout)
            self.assertTrue((target.parent/'PolsQLarge/skin.xml').is_file())
            self.assertTrue((temp/'receiver/usr/lib/enigma2/python/Components/Converter/PolsQEventRemaining.py').is_file())
            self.assertTrue((temp/'receiver/usr/lib/enigma2/python/Plugins/Extensions/PolsQSettings/plugin.py').is_file())
            for p in (ROOT/'PolsQ').rglob('*'):
                if p.is_file():self.assertEqual((target/p.relative_to(ROOT/'PolsQ')).read_bytes(),p.read_bytes())
            (target/'skin.xml').write_text('old skin')
            (target/'user-note').write_text('keep in backup')
            second=install();self.assertEqual(second.returncode,0,second.stderr)
            backups=list(target.parent.glob('PolsQ.backup-*'));self.assertEqual(len(backups),1)
            self.assertEqual((backups[0]/'skin.xml').read_text(),'old skin')
            self.assertEqual((backups[0]/'user-note').read_text(),'keep in backup')
            self.assertFalse((target/'user-note').exists())
            import shutil
            shutil.rmtree(target);outside=temp/'outside';outside.mkdir();target.symlink_to(outside,target_is_directory=True)
            failed=install();self.assertNotEqual(failed.returncode,0)
            self.assertNotIn('INSTALACJA ZAKOŃCZONA POMYŚLNIE',failed.stdout)
            self.assertFalse(list(outside.iterdir()))

    def test_packaged_postinst_reports_success_only_after_files_exist(self):
        files=read_ar((ROOT/'dist'/PACKAGE).read_bytes())
        with tempfile.TemporaryDirectory() as temp:
            temp=Path(temp)
            with tarfile.open(fileobj=io.BytesIO(files['control.tar.gz'])) as archive:
                member=archive.getmember('./postinst')
                self.assertEqual(member.mode,0o755)
                hook=temp/'postinst';hook.write_bytes(archive.extractfile(member).read())
            receiver=temp/'receiver';receiver.mkdir()
            env=dict(os.environ,IPKG_INSTROOT=str(receiver))
            def run_hook():
                return subprocess.run(['sh',str(hook),'configure'],env=env,capture_output=True,text=True)
            missing=run_hook()
            self.assertNotEqual(missing.returncode,0)
            self.assertNotIn('INSTALACJA ZAKOŃCZONA POMYŚLNIE',missing.stdout)
            with tarfile.open(fileobj=io.BytesIO(files['data.tar.gz'])) as archive:
                archive.extractall(receiver,filter='data')
            success=run_hook()
            self.assertEqual(success.returncode,0,success.stderr)
            self.assertIn('INSTALACJA ZAKOŃCZONA POMYŚLNIE',success.stdout)
            self.assertIn('GUI',success.stdout)
            self.assertIn(f'Wersja: {VERSION}',success.stdout)

    def test_reproducible_archives(self):
        before={p.name:p.read_bytes() for p in (ROOT/'dist').glob(f'*{VERSION}*')}
        build()
        self.assertEqual(before,{p.name:p.read_bytes() for p in (ROOT/'dist').glob(f'*{VERSION}*')})


if __name__=='__main__':
    unittest.main()

