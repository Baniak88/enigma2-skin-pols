from pathlib import Path
import sys
import unittest
import xml.etree.ElementTree as E
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from validate import check_template

class QMenu(unittest.TestCase):
    def test_menu_is_a_vertical_list_reachable_with_up_down(self):
        # OpenATV's standard Menu has only up/down navigation; a grid made
        # items in other columns (e.g. Plugins) unreachable on the receiver.
        for profile in ('PolsQ','PolsQLarge'):
            menu=E.parse(ROOT/profile/'skin.xml').getroot().find("screen[@name='Menu']/widget[@source='menu']")
            self.assertIsNone(menu.get('listOrientation'))
            data=check_template(menu.find('convert').text)
            self.assertIsInstance(data['itemHeight'],int)
            self.assertIn('template',data)
            self.assertEqual(set(data['templates']),{'default','text','number','image','both'})
            w,h=map(int,menu.get('size').split(','))
            self.assertEqual(h%data['itemHeight'],0)
            self.assertGreaterEqual(h//data['itemHeight'],7)

    def test_live_video_and_menu_grid_do_not_overlap(self):
        for profile in ('PolsQ','PolsQLarge'):
            screen=E.parse(ROOT/profile/'skin.xml').getroot().find("screen[@name='Menu']")
            video=screen.find("widget[@render='Pig']");menu=screen.find("widget[@source='menu']")
            vx,vy=map(int,video.get('position').split(','));vw,vh=map(int,video.get('size').split(','))
            self.assertEqual(vw*9,vh*16)
            self.assertLess(vx+vw,int(menu.get('position').split(',')[0]))
            mx,my=map(int,menu.get('position').split(','));mw,mh=map(int,menu.get('size').split(','))
            self.assertEqual(mx+mw,1920-64,'same right margin as the left one')
