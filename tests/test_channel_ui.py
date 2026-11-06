from pathlib import Path
import unittest
import xml.etree.ElementTree as E

ROOT=Path(__file__).resolve().parents[1]


class ChannelUI(unittest.TestCase):
    def setUp(self):self.skin=E.parse(ROOT/'PolsQ/skin.xml').getroot()

    def test_default_and_selected_styles_have_live_preview(self):
        for name in ('ChannelSelection','ChannelSelection_PIG'):
            screen=self.skin.find(f"screen[@name='{name}']")
            video=screen.find("widget[@render='Pig']")
            self.assertIsNotNone(video,name)
            w,h=map(int,video.get('size').split(','))
            self.assertGreaterEqual(w,600)
            self.assertEqual(w*9,h*16)
            self.assertEqual(video.get('source'),'session.VideoPicture')
            self.assertEqual(video.get('backgroundColor'),'transparent')
            vx,vy=map(int,video.get('position').split(','))
            # No later-created opaque decoration can cover the video aperture.
            for n in screen:
                if n.tag not in ('eLabel','ePixmap') or not n.get('backgroundColor'):continue
                x,y=map(int,n.get('position').split(','));nw,nh=map(int,n.get('size').split(','))
                overlaps=x<vx+w and x+nw>vx and y<vy+h and y+nh>vy
                self.assertFalse(overlaps,(name,n.attrib))

    def test_channel_and_event_have_separate_lines_with_room_for_long_names(self):
        for folder,rows in (('PolsQ',8),('PolsQLarge',8)):
            skin=E.parse(ROOT/folder/'skin.xml').getroot()
            screen=skin.find("screen[@name='ChannelSelection']")
            _,height=map(int,screen.find("widget[@name='list']").get('size').split(','))
            template=E.parse(ROOT/folder/'skinTemplates.xml').getroot().find('template')
            fonts=template.get('fonts').split(',')
            self.assertTrue(fonts[0].startswith('PolsQStrong;'))
            for kind in ('services','bouquets'):
                mode=template.find(f"mode[@name='{kind}']")
                self.assertEqual(height//int(mode.get('itemHeight')),rows)
                self.assertEqual(mode.get('backgroundColorSelected'),'selected')
                self.assertEqual(mode.find('rectangle').get('foregroundColorSelected'),'green')
                channel=mode.find("text[@index='ServiceName']");event=mode.find("text[@index='Title1']")
                cx,cy=map(int,channel.get('position').split(','));cw,ch=map(int,channel.get('size').split(','))
                ex,ey=map(int,event.get('position').split(','));ew,eh=map(int,event.get('size').split(','))
                px,py=map(int,mode.find("progress[@index='Progress']").get('position').split(','))
                self.assertEqual(cx,ex)
                self.assertGreaterEqual(cw,640)
                self.assertGreaterEqual(ew,560)
                self.assertGreaterEqual(ey-(cy+ch),2)
                self.assertGreaterEqual(px-(ex+ew),24)
                self.assertTrue(ey<=py<ey+eh)
                self.assertEqual(channel.get('wrap'),'ellipsis')
                self.assertEqual(event.get('wrap'),'ellipsis')
                self.assertEqual(event.get('foregroundColorSelected'),'muted')
                self.assertEqual(height,768)
                for node in (channel,event):
                    font=int(fonts[int(node.get('font'))].split(';')[1])
                    self.assertGreaterEqual(int(node.get('size').split(',')[1]),font*1.2)
            other=template.find("mode[@name='other']")
            self.assertEqual(height//int(other.get('itemHeight')),8)
            self.assertIsNotNone(other.find("pixmap[@index='FolderImage']"))
            self.assertEqual(screen.find("widget[@name='list']").get('position'),'992,192')

    def test_selection_is_an_explicit_dark_surface_instead_of_system_gradient(self):
        from PIL import Image
        for name in ('ChannelSelection','ChannelSelection_PIG','ChannelSelection_NoPIG','ChannelSelectionRadio'):
            node=self.skin.find(f"screen[@name='{name}']/widget[@name='list']")
            with Image.open(ROOT/node.get('selectionPixmap')) as image:
                self.assertEqual(image.size,(864,96))
                self.assertEqual(image.getpixel((0,0))[3],0)
                self.assertEqual(image.getpixel((100,40))[3],255)
                self.assertNotEqual(image.getpixel((100,20)),image.getpixel((100,70)))

    def test_sidebar_title_is_measured_and_does_not_collide_with_time_or_description(self):
        for folder in ('PolsQ','PolsQLarge'):
            skin=E.parse(ROOT/folder/'skin.xml').getroot()
            for name in ('ChannelSelection','ChannelSelection_PIG'):
                screen=skin.find(f"screen[@name='{name}']")
                title=next(n for n in screen.findall("widget[@source='ServiceEvent']") if n.find("convert[@type='EventName']") is not None and n.find("convert[@type='EventName']").text=='Name')
                self.assertEqual(title.get('render'),'PolsQSummary')
                bottom=int(title.get('position').split(',')[1])+int(title.get('size').split(',')[1])
                starts=[n for n in screen.findall("widget[@source='ServiceEvent']") if n.find("convert[@type='EventTime']") is not None and n.find("convert[@type='EventTime']").text=='StartTime']
                self.assertGreaterEqual(int(starts[0].get('position').split(',')[1])-bottom,8)
                hint=next(n for n in screen.findall('eLabel') if n.get('text')=='INFO — pełny opis')
                self.assertLessEqual(int(hint.get('position').split(',')[1])+int(hint.get('size').split(',')[1]),1004)

    def test_font_is_registered_regular_instead_of_default_bold(self):
        fonts={n.get('name'):n.get('filename') for n in self.skin.findall('fonts/font')}
        self.assertEqual(fonts['PolsQText'],'DejaVuSans.ttf')
        listbox=self.skin.find("screen[@name='ChannelSelection']/widget[@name='list']")
        self.assertTrue(listbox.get('serviceNameFont').startswith('PolsQText;'))
        self.assertGreaterEqual(int(listbox.get('serviceNameFont').split(';')[1]),28)

    def test_explicit_no_video_variant_remains_available(self):
        screen=self.skin.find("screen[@name='ChannelSelection_NoPIG']")
        self.assertIsNotNone(screen)
        self.assertIsNone(screen.find("widget[@render='Pig']"))

    def test_bouquet_selectors_use_ten_compact_rows_in_both_profiles(self):
        for folder in ('PolsQ','PolsQLarge'):
            skin=E.parse(ROOT/folder/'skin.xml').getroot()
            for name in ('BouquetSelector','EPGBouquetSelector'):
                menu=skin.find(f"screen[@name='{name}']/widget[@name='menu']")
                height=int(menu.get('size').split(',')[1])
                self.assertEqual(height//int(menu.get('itemHeight')),10)
                self.assertEqual(menu.get('position'),'40,168')
            for name in ('SimpleChannelSelection','SlimChannelSelection'):
                node=skin.find(f"screen[@name='{name}']/widget[@name='list']")
                self.assertEqual(node.get('size'),'1840,760')
                self.assertEqual(node.get('serviceItemHeight'),'76')

    def test_minimal_icons_are_distinct_transparent_outlines(self):
        from PIL import Image
        paths=['assets/line-tv.png','assets/line-history.png','assets/line-bouquet.png','icons/folder.png','icons/marker.png']
        images=[]
        for name in paths:
            with Image.open(ROOT/'PolsQ'/name) as image:
                self.assertEqual(image.size,(32,32))
                pixels=list(image.getdata())
                visible=[p for p in pixels if p[3]]
                self.assertGreater(len(visible),20)
                self.assertLess(len(visible),512)
                self.assertTrue(set(visible)<={(194,204,215,255),(70,186,255,255)})
                images.append(image.tobytes())
        self.assertEqual(len(set(images)),4)  # Folder matches the bouquet icon.

    def test_selected_event_description_has_room_before_info_hint(self):
        for name in ('ChannelSelection','ChannelSelection_PIG'):
            screen=self.skin.find(f"screen[@name='{name}']")
            description=next(n for n in screen.findall("widget[@source='ServiceEvent']")
                if n.find("convert[@type='EventName']") is not None and n.find("convert[@type='EventName']").text=='ExtendedDescription')
            height=int(description.get('size').split(',')[1])
            self.assertGreaterEqual(height,48)
            hint=next(n for n in screen.findall('eLabel') if n.get('text')=='INFO — pełny opis')
            bottom=int(description.get('position').split(',')[1])+height
            self.assertGreaterEqual(int(hint.get('position').split(',')[1])-bottom,8)


if __name__=='__main__':unittest.main()

