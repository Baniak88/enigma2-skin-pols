import unittest
from pathlib import Path
import xml.etree.ElementTree as E

ROOT=Path(__file__).resolve().parents[1]


class SkinSelectionLayout(unittest.TestCase):
    def test_specific_names_have_full_layout_and_preview_above_placeholder(self):
        skin=E.parse(ROOT/'PolsQ/skin.xml').getroot()
        for name in ('SkinSelection','setup_Skin','SetupSkin'):
            with self.subTest(name=name):
                s=skin.find(f"screen[@name='{name}']")
                self.assertEqual(s.get('size'),'1920,1080')
                preview=s.find("widget[@name='preview']")
                w,h=map(int,preview.get('size').split(','))
                self.assertEqual(w*9,h*16)
                self.assertGreater(int(preview.get('zPosition')),0)
                config=s.find("widget[@name='config']")
                height=int(config.get('size').split(',')[1])
                self.assertEqual(height//int(config.get('itemHeight')),9)
                self.assertEqual(height%int(config.get('itemHeight')),0)
                self.assertEqual(config.get('font'),config.get('valueFont'))

    def test_preview_description_and_restart_note_do_not_overlap(self):
        s=E.parse(ROOT/'PolsQ/skin.xml').getroot().find("screen[@name='SkinSelection']")
        end=0
        for name in ('preview','description','footnote'):
            n=s.find(f"widget[@name='{name}']")
            x,y=map(int,n.get('position').split(','));w,h=map(int,n.get('size').split(','))
            self.assertGreaterEqual(y,end)
            self.assertLessEqual(x+w,1856)
            end=y+h
        self.assertLess(end,974)

