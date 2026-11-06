from pathlib import Path
import sys
import struct
import unittest
import xml.etree.ElementTree as E
import zlib

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from validate import check_picon_layers


class PiconLayers(unittest.TestCase):
    def test_fallback_has_no_symbol_to_bleed_through_logo(self):
        data=(ROOT/'PolsQ/picon_default.png').read_bytes();offset=8;compressed=b''
        while offset<len(data):
            size=struct.unpack('>I',data[offset:offset+4])[0]
            if data[offset+4:offset+8]==b'IDAT':compressed+=data[offset+8:offset+8+size]
            offset+=12+size
        width,height=struct.unpack('>II',data[16:24]);raw=zlib.decompress(compressed)
        pixels=set()
        for y in range(height):
            row=raw[y*(width*4+1):(y+1)*(width*4+1)]
            self.assertEqual(row[0],0)
            pixels.update(row[x:x+4] for x in range(1,len(row),4))
        self.assertEqual(pixels,{bytes((0,0,0,0))},'Fallback must be fully transparent on every screen')

    def test_original_blank_panel_regression(self):
        # Order in XML did not help: OpenATV creates the eLabel after Picon.
        original=E.fromstring('''<screen name="InfoBar">
          <eLabel position="64,34" size="220,132" backgroundColor="panel"/>
          <widget source="session.CurrentService" render="Picon" position="64,34" size="220,132"/>
        </screen>''')
        with self.assertRaisesRegex(AssertionError,'decoration covers picon'):
            check_picon_layers(original)

    def test_shipped_picons_above_fallback(self):
        screens=E.parse(ROOT/'PolsQ/skin.xml').getroot().findall('screen')
        count=0
        for screen in screens:
            check_picon_layers(screen)
            for picon in screen.findall("widget[@render='Picon']"):
                count+=1
                self.assertEqual(picon.get('transparent'),'1')
                self.assertEqual(picon.get('backgroundColor'),'transparent')
                matching=[n for n in screen.findall('ePixmap')
                    if n.get('position')==picon.get('position') and n.get('size')==picon.get('size')]
                self.assertTrue(matching,screen.get('name'))
                for fallback in matching:
                    self.assertEqual(fallback.get('pixmap'),'PolsQ/picon_default.png')
                    self.assertLess(int(fallback.get('zPosition','0')),int(picon.get('zPosition','0')))
        self.assertGreater(count,10)


if __name__=='__main__':unittest.main()

