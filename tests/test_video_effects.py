"""TV preview stays visible and screens avoid slow scaled blits."""
from pathlib import Path
import unittest
import xml.etree.ElementTree as E
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]


def box(n):
    x,y=map(int,n.get('position').split(','));w,h=map(int,n.get('size').split(','))
    return x,y,w,h


class VideoEffects(unittest.TestCase):
    def test_nothing_is_drawn_over_the_video_hole(self):
        for folder in ('PolsQ','PolsQLarge'):
            skin=E.parse(ROOT/folder/'skin.xml').getroot()
            pigs=[s for s in skin.findall('screen') if s.find("widget[@render='Pig']") is not None]
            self.assertGreaterEqual(len(pigs),5)
            for s in pigs:
                pig=s.find("widget[@render='Pig']");vx,vy,vw,vh=box(pig)
                self.assertIsNone(s.find("widget[@render='PolsQVideoFade']"))
                hole=[n for n in s.findall('eLabel') if n.get('backgroundColor')=='transparent' and box(n)==(vx,vy,vw,vh)]
                self.assertEqual(len(hole),1,s.get('name'))
                for n in s.findall('ePixmap'):
                    if int(n.get('zPosition','0'))<=int(pig.get('zPosition','0')):continue
                    x,y,w,h=box(n)
                    overlaps=x<vx+vw and x+w>vx and y<vy+vh and y+h>vy
                    self.assertFalse(overlaps,(s.get('name'),n.attrib))
                shadow=s.find(f"ePixmap[@pixmap='PolsQ/assets/q-video-shadow-{vw}x{vh}.png']")
                sx,sy,_,_=box(shadow)
                with Image.open(ROOT/shadow.get('pixmap')) as im:
                    alpha=im.getchannel('A').crop((vx-sx,vy-sy,vx-sx+vw,vy-sy+vh))
                    self.assertEqual(alpha.getextrema(),(0,0),'shadow must be cut out under the video')

    def test_menu_list_does_not_punch_a_hole_over_tiles(self):
        menu=E.parse(ROOT/'PolsQ/skin.xml').getroot().find("screen[@name='Menu']/widget[@source='menu']")
        self.assertNotEqual(menu.get('backgroundColor'),'transparent')
        self.assertEqual(menu.get('transparent'),'1')

    def test_large_surfaces_are_drawn_at_native_size(self):
        for folder in ('PolsQ','PolsQLarge'):
            for n in E.parse(ROOT/folder/'skin.xml').getroot().iter('ePixmap'):
                _,_,w,h=box(n)
                if w*h<200*200 or 'eventview-fade' in n.get('pixmap') or 'picon_default' in n.get('pixmap'):continue
                with Image.open(ROOT/n.get('pixmap')) as im:
                    self.assertEqual(im.size,(w,h),n.attrib)
                self.assertIsNone(n.get('scale'),n.attrib)
            wall=E.parse(ROOT/folder/'skin.xml').getroot().find(".//ePixmap[@pixmap='PolsQ/assets/q-wallpaper.png']")
            self.assertIsNone(wall.get('alphatest'),'opaque wallpaper needs no blending')

    def test_headlines_have_text_shadow(self):
        skin=E.parse(ROOT/'PolsQ/skin.xml').getroot()
        for name in ('Menu','ChannelSelection','InfoBar'):
            shadows=[n for n in skin.find(f"screen[@name='{name}']") if n.get('shadowColor')]
            self.assertTrue(shadows,name)


if __name__=='__main__':unittest.main()
