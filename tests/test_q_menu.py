from pathlib import Path
import sys
import unittest
import xml.etree.ElementTree as E
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from validate import check_template

class QMenu(unittest.TestCase):
    def test_native_grid_has_scalar_initial_size_and_all_native_menu_styles(self):
        for profile in ('PolsQ','PolsQLarge'):
            menu=E.parse(ROOT/profile/'skin.xml').getroot().find("screen[@name='Menu']/widget[@source='menu']")
            self.assertEqual(menu.get('listOrientation'),'grid')
            data=check_template(menu.find('convert').text)
            # OpenATV's initial style may be None. A direct template plus scalar
            # dimensions avoids its tuple itemSize fallback in that state.
            self.assertIsInstance(data['itemWidth'],int)
            self.assertIsInstance(data['itemHeight'],int)
            self.assertIn('template',data)
            self.assertEqual(set(data['templates']),{'default','text','number','image','both'})
            w,h=map(int,menu.get('size').split(','))
            self.assertEqual((w//data['itemWidth'],h//data['itemHeight']),(3,2))

    def test_live_video_and_menu_grid_do_not_overlap(self):
        for profile in ('PolsQ','PolsQLarge'):
            screen=E.parse(ROOT/profile/'skin.xml').getroot().find("screen[@name='Menu']")
            video=screen.find("widget[@render='Pig']");menu=screen.find("widget[@source='menu']")
            vx,vy=map(int,video.get('position').split(','));vw,vh=map(int,video.get('size').split(','))
            self.assertEqual(vw*9,vh*16)
            self.assertLess(vy+vh,int(menu.get('position').split(',')[1]))
