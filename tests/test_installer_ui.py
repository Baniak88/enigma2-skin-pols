from pathlib import Path
import unittest
import xml.etree.ElementTree as E

ROOT=Path(__file__).resolve().parents[1]


class InstallerUI(unittest.TestCase):
    def setUp(self):
        self.skin=E.parse(ROOT/'PolsQ/skin.xml').getroot()

    def test_native_installer_and_operation_screens_are_present(self):
        for name in ('IpkgInstaller','Opkg','PackageAction','PluginAction','PackageActionLog','PluginActionLog','Console'):
            screen=self.skin.find(f"screen[@name='{name}']")
            self.assertIsNotNone(screen,name)
            self.assertEqual(screen.get('size'),'1920,1080')
        installer=self.skin.find("screen[@name='IpkgInstaller']")
        self.assertIsNotNone(installer.find("widget[@source='introduction']"))
        alias=self.skin.find("fonts/alias[@name='SelectionList']")
        height=int(alias.get('height'))
        area=installer.find("widget[@name='list']")
        self.assertEqual(int(area.get('size').split(',')[1])%height,0)
        self.assertGreaterEqual(int(alias.get('size')),30)

    def test_processing_text_is_below_thin_progress_and_has_room_to_grow(self):
        screen=self.skin.find("screen[@name='Processing']")
        progress=screen.find("widget[@name='progress']")
        text=screen.find("widget[@name='description']")
        self.assertLessEqual(int(progress.get('size').split(',')[1]),8)
        progress_bottom=int(progress.get('position').split(',')[1])+int(progress.get('size').split(',')[1])
        self.assertLess(progress_bottom,int(text.get('position').split(',')[1]))
        self.assertEqual(int(screen.get('zPosition')),99)
        self.assertEqual(list(screen)[-1],text,'No fixed decoration may overlap dynamically growing text')

    def test_empty_footer_actions_hide_both_marker_and_caption(self):
        for screen in self.skin.findall('screen'):
            markers=screen.findall("widget[@render='FixedLabel'][@text=' ']")
            for marker in markers:
                key=marker.get('source')
                caption=screen.find(f"widget[@source='{key}'][@render='Label']")
                self.assertIsNotNone(caption)
                for widget in (marker,caption):
                    self.assertIsNotNone(widget.find("convert[@type='ConditionalShowHide']"))
                if key=='key_blue':
                    expected='1376' if screen.get('name') in ('EventView','InfoBarEventView') else '1408'
                    if screen.get('name') in ('ChannelSelection','ChannelSelection_PIG','ChannelSelection_NoPIG','ChannelSelectionRadio','SimpleChannelSelection','SlimChannelSelection'):
                        expected='1420'
                    self.assertEqual(marker.get('position').split(',')[0],expected)

    def test_opkg_status_and_log_remain_native_dynamic_widgets(self):
        screen=self.skin.find("screen[@name='Opkg']")
        for name in ('status','package','slider','activityslider','log'):
            self.assertIsNotNone(screen.find(f"widget[@name='{name}']"))
        self.assertEqual(screen.find("widget[@name='log']").get('transparent'),'1')
        self.assertFalse(any('POMYŚLNIE' in n.get('text','') for n in screen),'The skin must not replace actual errors with a success label')


if __name__=='__main__':
    unittest.main()

