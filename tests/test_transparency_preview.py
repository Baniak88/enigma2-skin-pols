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
    def test_news_band_composites_over_video(self):
        from PIL import Image
        with tempfile.TemporaryDirectory() as temp:
            svg=Path(temp)/'preview.svg';preview.render('InfoBar',str(svg),make_png=True)
            scene=E.parse(ROOT/'PolsQ/skin.xml').getroot().find("screen[@name='InfoBar']")
            ox,oy=map(int,scene.get('position').split(','))
            with Image.open(svg.with_suffix('.png')) as actual, Image.open(preview.DEMO) as video, Image.open(ROOT/'PolsQ/assets/q-news-band.png') as band:
                # Points away from text: gap right of the logo card and the faded top edge.
                for x,y in ((296,oy+120),(1000,oy+20),(1500,oy+30)):
                    rgba=band.getpixel((x-ox,y-oy));alpha=rgba[3]/255
                    base=video.getpixel((x,y));expected=tuple(round(f*alpha+b*(1-alpha)) for f,b in zip(rgba[:3],base))
                    pixel=actual.getpixel((round(x*2/3),round(y*2/3)))
                    self.assertTrue(all(abs(a-b)<=4 for a,b in zip(pixel,expected)),(x,y,pixel,expected))
                # Above the band the picture is untouched.
                x,y=900,oy-40
                self.assertTrue(all(abs(a-b)<=3 for a,b in zip(actual.getpixel((round(x*2/3),round(y*2/3)))[:3],video.getpixel((x,y)))))

    def test_news_bar_layout_like_tv_lower_third(self):
        from PIL import Image
        for folder in ('PolsQ','PolsQLarge'):
            skin=E.parse(ROOT/folder/'skin.xml').getroot();scene=skin.find("screen[@name='InfoBar']")
            colors={c.get('name'):c.get('value') for c in skin.findall('colors/color')}
            self.assertEqual(scene.get('backgroundColor'),'transparent')
            band=scene.find("ePixmap[@pixmap='PolsQ/assets/q-news-band.png']")
            logo=scene.find("widget[@render='Picon']")
            self.assertLess(int(band.get('zPosition')),int(logo.get('zPosition')))
            self.assertEqual(logo.get('size'),'220,132','picon at native size, no scaling')
            with Image.open(ROOT/band.get('pixmap')) as im:
                self.assertEqual(im.size,tuple(map(int,band.get('size').split(','))))
                self.assertEqual(im.getpixel((960,0))[3],0,'band fades into the picture')
                self.assertGreater(im.getpixel((960,150))[3],230)
                lx,ly=map(int,logo.get('position').split(','))
                card=im.getpixel((lx+110,ly+66))
                self.assertTrue(all(c>=245 for c in card),'white logo card behind the picon')
            # Clock directly under the logo card.
            clock=scene.find("widget[@source='global.CurrentTime']")
            cx,cy=map(int,clock.get('position').split(','))
            self.assertLessEqual(abs(cx+int(clock.get('size').split(',')[0])//2-(lx+110)),2)
            self.assertGreaterEqual(cy,ly+132)
            # Yellow upper-case headline with a shadow.
            title=[n for n in scene.findall("widget[@source='session.Event_Now']") if n.find("convert[@type='PolsQUpper']") is not None and n.get('render')=='PolsQSummary']
            self.assertEqual(len(title),1)
            self.assertEqual(title[0].get('foregroundColor'),'newsYellow')
            self.assertTrue(title[0].get('font').startswith('PolsQStrong;'))
            self.assertTrue(title[0].get('shadowColor'))
            r,g,b,_=rgba(colors['newsYellow']);self.assertTrue(r>240 and g>200 and b<40)
            # Red ticker bar along the bottom, opaque (no blending while scrolling).
            ticker=scene.find("widget[@render='PolsQTicker']")
            self.assertEqual(ticker.get('backgroundColor'),'newsRed');self.assertEqual(ticker.get('transparent'),'0')
            self.assertEqual([c.get('type') for c in ticker.findall('convert')],['EventName','PolsQUpper'])
            self.assertIsNone(ticker.get('wrap'))
            bar=[n for n in scene.findall('eLabel') if n.get('backgroundColor')=='newsRed']
            self.assertEqual(len(bar),1);self.assertEqual(bar[0].get('size').split(',')[0],'1920')
            r,g,b,a=rgba(colors['newsRed']);self.assertTrue(r>200 and g<40 and b<40 and a==255)
            tx,ty=map(int,ticker.get('position').split(','));bx,by=map(int,bar[0].get('position').split(','))
            self.assertGreaterEqual(ty,by);self.assertLessEqual(ty+int(ticker.get('size').split(',')[1]),by+int(bar[0].get('size').split(',')[1]))
            self.assertIsNotNone(scene.find("eLabel[@text='W SKRÓCIE']"))
            self.assertIsNotNone(scene.find("widget[@source='session.Event_Next']"))
            self.assertIsNotNone(scene.find("widget[@source='session.RecordState']"))
            progress=scene.find("widget[@render='Progress']")
            self.assertGreaterEqual(int(progress.get('position').split(',')[1]),int(title[0].get('position').split(',')[1])+int(title[0].get('size').split(',')[1]))
            sy=int(scene.get('position').split(',')[1]);self.assertLessEqual(sy+by+int(bar[0].get('size').split(',')[1]),1044,'bar inside the TV safe area')

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

