from pathlib import Path
import unittest
import xml.etree.ElementTree as E

ROOT=Path(__file__).resolve().parents[1]


class SettingsUI(unittest.TestCase):
    def test_setting_names_and_values_share_a_readable_font(self):
        skin=E.parse(ROOT/'PolsQ/skin.xml').getroot()
        fonts={n.get('name') for n in skin.findall('fonts/font')}
        defaults=skin.find('windowstyle/configList')
        self.assertEqual(defaults.get('entryFont'),defaults.get('valueFont'))
        for widget in skin.findall(".//widget[@name='config']"):
            with self.subTest(screen_font=widget.get('font')):
                family,size=widget.get('valueFont').split(';')
                self.assertIn(family,fonts)
                self.assertGreaterEqual(int(size),28)
                self.assertEqual(widget.get('font'),widget.get('valueFont'))
                self.assertGreaterEqual(int(widget.get('itemHeight')),int(size)+20)
        setup=skin.find("screen[@name='Setup']/widget[@name='config']")
        self.assertEqual(int(setup.get('size').split(',')[1])%int(setup.get('itemHeight')),0)

    def test_infobar_has_one_dark_transparent_surface(self):
        from PIL import Image
        skin=E.parse(ROOT/'PolsQ/skin.xml').getroot()
        colors={n.get('name'):n.get('value') for n in skin.findall('colors/color')}
        for name in ('SecondInfoBar','MoviePlayer'):
            screen=skin.find(f"screen[@name='{name}']")
            self.assertEqual(screen.get('backgroundColor'),'transparent')
            mask=screen.find(f"ePixmap[@pixmap='PolsQ/assets/{name.lower()}-fade.png']")
            self.assertIsNotNone(mask)
            self.assertLess(int(mask.get('zPosition')),0)
            with Image.open(ROOT/mask.get('pixmap')) as image:
                self.assertEqual(image.getpixel((0,64)),(15,20,23,217))
            surface=colors['overlay'].lstrip('#')
            transparency=int(surface[:2],16)/255
            self.assertAlmostEqual(transparency,38/255)
            rgb=[int(surface[i:i+2],16) for i in (2,4,6)]
            background=colors['bg'].lstrip('#')
            self.assertEqual(rgb,[15,20,23])
            self.assertEqual(surface[2:],background[2:])
            self.assertEqual(colors['panel'],'#00182126')
            def luminance(value):
                channels=[int(value[-6:][i:i+2],16)/255 for i in (0,2,4)]
                linear=[x/12.92 if x<=0.04045 else ((x+0.055)/1.055)**2.4 for x in channels]
                return sum(a*b for a,b in zip(linear,(0.2126,0.7152,0.0722)))
            # Even a white TV frame must leave readable white text after mixing.
            for video in ((0,0,0),(255,255,255),(255,0,0),(0,0,255)):
                mixed=[round(c*(1-transparency)+v*transparency) for c,v in zip(rgb,video)]
                mixed_hex=''.join(f'{c:02x}' for c in mixed)
                self.assertGreater((luminance(colors['white'])+0.05)/(luminance(mixed_hex)+0.05),4.5)
            for icon in screen.findall("widget[@render='Picon']"):
                self.assertEqual(icon.get('backgroundColor'),'transparent')
                self.assertEqual(icon.get('transparent'),'1')


if __name__=='__main__':
    unittest.main()

