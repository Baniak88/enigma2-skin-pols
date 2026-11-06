from pathlib import Path
import sys
import tempfile
import unittest
import xml.etree.ElementTree as E
import base64
import io

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from skin_colors import rgba
import preview


class TransparencyPreview(unittest.TestCase):
    def test_floating_cards_retain_video_in_gap_and_composite_correctly(self):
        from PIL import Image
        with tempfile.TemporaryDirectory() as temp:
            svg=Path(temp)/'preview.svg';preview.render('InfoBar',str(svg),make_png=True)
            with Image.open(svg.with_suffix('.png')) as actual, Image.open(preview.DEMO) as video, Image.open(ROOT/'PolsQ/assets/q-info-card.png') as card:
                # Work away from text and edges; PNG preview is rendered at 2/3 scale.
                for x,y in ((900,1000),(1580,1000)):
                    local=(x-64-300,y-772);rgba=card.getpixel(local);alpha=rgba[3]/255
                    base=video.getpixel((x,y));expected=tuple(round(f*alpha+b*(1-alpha)) for f,b in zip(rgba[:3],base))
                    pixel=actual.getpixel((round(x*2/3),round(y*2/3)))
                    self.assertTrue(all(abs(a-b)<=3 for a,b in zip(pixel,expected)),(pixel,expected))
                # The gap between logo and programme cards must expose TV.
                x,y=354,890
                self.assertTrue(all(abs(a-b)<=3 for a,b in zip(actual.getpixel((round(x*2/3),round(y*2/3)))[:3],video.getpixel((x,y)))))

    def test_floating_cards_have_clear_edges_and_do_not_cover_picons(self):
        from PIL import Image
        for folder in ('PolsQ','PolsQLarge'):
            scene=E.parse(ROOT/folder/'skin.xml').getroot().find("screen[@name='InfoBar']")
            self.assertEqual(scene.get('backgroundColor'),'transparent')
            cards=[n for n in scene.findall('ePixmap') if '-card.png' in n.get('pixmap','')]
            self.assertEqual(len(cards),2)
            logo=scene.find("widget[@render='Picon']")
            for n in cards:
                self.assertLess(int(n.get('zPosition')),int(logo.get('zPosition')))
                with Image.open(ROOT/n.get('pixmap')) as card:
                    self.assertEqual(card.getpixel((0,0))[3],0)
                    self.assertGreater(card.getpixel((100,60))[3],230)
                    self.assertLess(card.getpixel((100,60))[3],255)
            positions=[tuple(map(int,n.get('position').split(','))) for n in cards]
            self.assertGreater(positions[1][0],280)

    def test_now_next_and_logo_occupy_distinct_columns(self):
        for folder in ('PolsQ','PolsQLarge'):
            scene=E.parse(ROOT/folder/'skin.xml').getroot().find("screen[@name='InfoBar']")
            now=scene.find("widget[@source='session.Event_Now'][@render='Label']")
            nxt=scene.find("widget[@source='session.Event_Next']")
            logo=scene.find("widget[@render='Picon']")
            def right(n):return int(n.get('position').split(',')[0])+int(n.get('size').split(',')[0])
            self.assertLess(right(logo),int(now.get('position').split(',')[0]))
            self.assertLess(right(now),int(nxt.get('position').split(',')[0]))
            progress=scene.find("widget[@render='Progress']")
            self.assertGreaterEqual(int(progress.get('position').split(',')[1]),max(int(n.get('position').split(',')[1])+int(n.get('size').split(',')[1]) for n in (now,nxt)))
            self.assertIsNotNone(scene.find("widget[@source='session.RecordState']"))

    def test_event_view_fade_protects_all_text_and_keeps_description_scrollable(self):
        from PIL import Image
        for folder in ('PolsQ','PolsQLarge'):
            skin=E.parse(ROOT/folder/'skin.xml').getroot()
            for name in ('EventView','InfoBarEventView'):
                scene=skin.find(f"screen[@name='{name}']")
                self.assertEqual(scene.get('backgroundColor'),'transparent')
                background=scene.find("ePixmap[@pixmap='PolsQ/assets/eventview-fade.png']")
                self.assertLess(int(background.get('zPosition')),0)
                with Image.open(ROOT/background.get('pixmap')) as mask:
                    alpha=[mask.getpixel((x,0))[3] for x in range(mask.width)]
                    self.assertEqual(alpha[0],240)
                    self.assertEqual(alpha[-1],217)
                    self.assertEqual(alpha,sorted(alpha,reverse=True))
                    samples=[alpha[x] for x in (128,640,1280,1600,1824)]
                    self.assertTrue(all(a>b for a,b in zip(samples,samples[1:])),samples)
                    self.assertTrue(all(a==217 for a in alpha[1824:]))
                    for node in scene:
                        if node.get('font'):
                            x=int(node.get('position').split(',')[0]);width=int(node.get('size').split(',')[0])
                            self.assertGreaterEqual(x,128,(folder,name,node.attrib))
                            self.assertLessEqual(x+width,1792,(folder,name,node.attrib))
                            self.assertTrue(all(mask.getpixel((px,0))[3]>=217 for px in range(x,x+width)),(folder,name,node.attrib))
                    colors={node.get('name'):node.get('value') for node in skin.findall('colors/color')}
                    def luminance(rgb):
                        channels=[v/255 for v in rgb]
                        linear=[v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in channels]
                        return sum(v*w for v,w in zip(linear,(.2126,.7152,.0722)))
                    backdrop=tuple(round(c*217/255+255*38/255) for c in (16,25,56))
                    for color_name in ('white','muted','green'):
                        foreground=rgba(colors[color_name])[:3]
                        self.assertGreaterEqual((luminance(foreground)+.05)/(luminance(backdrop)+.05),4.5)
                description=scene.find("widget[@name='epg_description']")
                self.assertEqual(description.get('transparent'),'1')
                self.assertIsNone(description.get('source'))
                self.assertGreaterEqual(int(description.get('size').split(',')[1]),500)
                x=int(description.get('position').split(',')[0]);width=int(description.get('size').split(',')[0])
                self.assertEqual(x,1920-x-width,'Description must have equal left/right margins')
                self.assertEqual(x,128)
                for node in scene.findall("widget[@source='global.CurrentTime']")+scene.findall("widget[@name='duration']"):
                    self.assertEqual(int(node.get('position').split(',')[0])+int(node.get('size').split(',')[0]),1792)


if __name__=='__main__':unittest.main()

