from pathlib import Path
import unittest
import xml.etree.ElementTree as E

ROOT=Path(__file__).resolve().parents[1]


class FileCommanderUI(unittest.TestCase):
    def setUp(self): self.skin=E.parse(ROOT/'PolsQ/skin.xml').getroot()

    def test_panels_have_equal_width_and_complete_readable_rows(self):
        screen=self.skin.find("screen[@name='FileCommander']")
        self.assertIsNotNone(screen)
        panels=[screen.find(f"widget[@name='list{side}']") for side in ('left','right')]
        self.assertEqual(panels[0].get('size'),panels[1].get('size'))
        width,height=map(int,panels[0].get('size').split(','))
        self.assertEqual(height%64,0)
        self.assertEqual(height//64,8)
        left_x=int(panels[0].get('position').split(',')[0])
        right_x=int(panels[1].get('position').split(',')[0])
        self.assertLess(left_x+width,right_x)
        self.assertEqual(left_x,1920-right_x-width)
        # Native FileList uses aliases/parameters, not the listbox font alone.
        for alias_name,name_param in (('FileList','FileListName'),('FileListMulti','FileListMultiName')):
            alias=self.skin.find(f"fonts/alias[@name='{alias_name}']")
            self.assertGreaterEqual(int(alias.get('size')),28)
            self.assertEqual(int(alias.get('height')),64)
            param=self.skin.find(f"parameters/parameter[@name='{name_param}']")
            x,y,w,h=map(int,param.get('value').split(','))
            self.assertLessEqual(x+w,width-20)
            self.assertLessEqual(y+h,64)

    def test_status_does_not_cover_files_and_text_views_keep_monospace_font(self):
        screen=self.skin.find("screen[@name='FileCommander']")
        row=screen.find("widget[@name='listleft']")
        bottom=int(row.get('position').split(',')[1])+int(row.get('size').split(',')[1])
        status=screen.find("widget[@name='status']")
        self.assertGreaterEqual(int(status.get('position').split(',')[1]),bottom)
        self.assertEqual(screen.find("widget[@name='quickselect']").get('size'),row.get('size'))
        for name in ('FileCommanderFileViewer','FileCommanderTextEditor'):
            data=self.skin.find(f"screen[@name='{name}']/widget[@name='data']")
            self.assertTrue(data.get('font').startswith('PolsQMono;'))
        self.assertEqual(self.skin.find("fonts/font[@name='PolsQMono']").get('filename'),'andale.ttf')


if __name__=='__main__': unittest.main()

