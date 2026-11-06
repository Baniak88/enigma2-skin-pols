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
    def test_svg_and_png_show_video_through_bar_and_picon_area(self):
        from PIL import Image
        self.assertEqual(rgba('#26101938'),(16,25,56,217))
        with tempfile.TemporaryDirectory() as temp:
            svg=Path(temp)/'preview.svg'
            preview.render('InfoBar',str(svg),make_png=True)
            tree=E.parse(svg).getroot()
            background=next(n for n in tree.iter() if n.tag.endswith('image') and n.get('width')=='1920' and n.get('height')=='418')
            with Image.open(io.BytesIO(base64.b64decode(background.get('href').split(',')[1]))) as mask:
                self.assertEqual(mask.getpixel((0,0)),(16,25,56,0))
                self.assertEqual(mask.getpixel((0,32)),(16,25,56,108))
                self.assertEqual(mask.getpixel((0,64)),(16,25,56,217))
            with Image.open(svg.with_suffix('.png')) as image:
                def pixel(x,y):return image.getpixel((round(x*2/3),round(y*2/3)))
                colors=[]
                for x,y in ((160,1068),(900,1068),(1640,1068),(80,780)):
                    self.assertEqual(image.getpixel((round(x*2/3),round(y*2/3)))[3],255,'Composited TV preview must remain opaque')
                    video=pixel(x,500)
                    expected=tuple(round(f*217/255+b*38/255) for f,b in zip((16,25,56),video))
                    actual=pixel(x,y)
                    self.assertTrue(all(abs(a-b)<=1 for a,b in zip(actual,expected)),(actual,expected))
                    colors.append(actual)
                self.assertEqual(len(set(colors[:3])),3,'Different TV colors must remain visible through the bar')
                # Fade above the body, away from the accent; all text stays below.
                video=pixel(900,500)
                self.assertTrue(all(abs(a-b)<=1 for a,b in zip(pixel(900,662),video)))
                # LANCZOS maps this sample between two source scanlines; check
                # the transition against its endpoints instead of rounding y.
                for middle,top,body in zip(pixel(900,694)[:3],video[:3],pixel(900,1068)[:3]):
                    self.assertGreater(middle,min(top,body))
                    self.assertLess(middle,max(top,body))

    def test_fade_never_runs_under_text_and_background_never_covers_picons(self):
        from PIL import Image
        for folder in ('PolsQ','PolsQLarge'):
            skin=E.parse(ROOT/folder/'skin.xml').getroot()
            for name in ('InfoBar','SecondInfoBar','MoviePlayer'):
                scene=skin.find(f"screen[@name='{name}']")
                background=scene.find(f"ePixmap[@pixmap='PolsQ/assets/{name.lower()}-fade.png']")
                with Image.open(ROOT/background.get('pixmap')) as mask:
                    alpha=[mask.getpixel((0,y))[3] for y in range(mask.height)]
                    self.assertEqual(alpha,sorted(alpha))
                    for node in scene:
                        if node.get('font'):
                            y=int(node.get('position').split(',')[1])
                            self.assertGreaterEqual(alpha[y],217,(folder,name,node.attrib))
                for logo in scene.findall("widget[@render='Picon']"):
                    self.assertGreater(int(logo.get('zPosition')),int(background.get('zPosition')))

    def test_separator_has_room_for_logo_name_and_now_badge_in_both_profiles(self):
        for folder in ('PolsQ','PolsQLarge'):
            scene=E.parse(ROOT/folder/'skin.xml').getroot().find("screen[@name='InfoBar']")
            logo=scene.find("widget[@render='Picon']")
            separator=next(node for node in scene.findall('eLabel') if node.get('backgroundColor')=='line')
            name=scene.find("widget[@source='session.CurrentService'][@render='Label']")
            badge=scene.find("ePixmap[@pixmap='PolsQ/assets/now-badge.png']")
            line_x=int(separator.get('position').split(',')[0])
            logo_right=int(logo.get('position').split(',')[0])+int(logo.get('size').split(',')[0])
            self.assertGreaterEqual(line_x-logo_right,32)
            self.assertGreaterEqual(int(name.get('position').split(',')[0])-line_x-1,32)
            self.assertGreaterEqual(int(badge.get('position').split(',')[0])-line_x-1,24)
            progress=scene.find("widget[@render='Progress']")
            self.assertEqual(int(progress.get('position').split(',')[0]),int(name.get('position').split(',')[0]))
            self.assertEqual(sum(int(node.split(',')[0]) for node in (progress.get('position'),progress.get('size'))),1856)

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

