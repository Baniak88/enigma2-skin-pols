from pathlib import Path
import unittest
import xml.etree.ElementTree as E

ROOT=Path(__file__).resolve().parents[1]


class QuickMenuUI(unittest.TestCase):
    def test_blue_menu_uses_native_two_column_sources(self):
        skin=E.parse(ROOT/'PolsQ/skin.xml').getroot()
        menu=skin.find("screen[@name='QuickMenu']")
        self.assertIsNotNone(menu)
        self.assertEqual(menu.get('size'),'1920,1080')
        left=menu.find("widget[@source='mainlist']")
        right=menu.find("widget[@source='sublist']")
        self.assertIsNotNone(left);self.assertIsNotNone(right)
        lx,ly=map(int,left.get('position').split(','));lw,lh=map(int,left.get('size').split(','))
        rx,ry=map(int,right.get('position').split(','))
        self.assertLess(lx+lw,rx);self.assertEqual(ly,ry)
        self.assertIsNotNone(menu.find("widget[@name='description']"))
        for key in ('red','green','yellow'):
            self.assertIsNotNone(menu.find(f"widget[@source='key_{key}']"))

    def test_device_choice_controls_actual_component_font_and_rows(self):
        skin=E.parse(ROOT/'PolsQ/skin.xml').getroot()
        font=skin.find("fonts/alias[@name='ChoiceList']")
        self.assertEqual(font.get('font'),'PolsQText')
        self.assertGreaterEqual(int(font.get('size')),30)
        height=int(font.get('height'))
        box=skin.find("screen[@name='ChoiceBox']/widget[@name='list']")
        self.assertEqual(int(box.get('size').split(',')[1]),8*height)
        params={p.get('name'):p.get('value') for p in skin.findall('parameters/parameter')}
        x,y,w,h=map(int,params['ChoicelistName'].split(','))
        self.assertGreaterEqual(x,48);self.assertLessEqual(y+h,height)
        self.assertGreaterEqual(h,int(font.get('size')))


if __name__=='__main__':unittest.main()

