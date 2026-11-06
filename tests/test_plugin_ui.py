from pathlib import Path
import sys
import unittest
import xml.etree.ElementTree as E

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from validate import check_template


class PluginUI(unittest.TestCase):
    def setUp(self):self.screen=E.parse(ROOT/'PolsQ/skin.xml').getroot().find("screen[@name='PluginBrowserGrid']")

    def test_four_columns_and_three_complete_rows(self):
        grid=self.screen.find("widget[@source='pluginGrid']")
        width,height=map(int,grid.get('size').split(','))
        template=check_template(grid.find('convert').text)
        self.assertEqual(width,4*template['itemWidth'])
        self.assertEqual(height,3*template['itemHeight'])
        for _,entry in template['template']:
            self.assertLessEqual(entry['pos'][0]+entry['size'][0],template['itemWidth'])
        image=next(entry for kind,entry in template['template'] if kind=='pixmap')
        self.assertGreaterEqual(image['size'][0],150)

    def test_cards_and_description_have_separate_space(self):
        grid=self.screen.find("widget[@source='pluginGrid']")
        template=check_template(grid.find('convert').text)
        card=next(entry for kind,entry in template['template'] if kind=='rect')
        self.assertNotEqual(card['backgroundColorSelected'],card['borderColorSelected'])
        description=self.screen.find("widget[@name='description']")
        bottom=int(grid.get('position').split(',')[1])+int(grid.get('size').split(',')[1])
        self.assertGreaterEqual(int(description.get('position').split(',')[1])-bottom,10)


if __name__=='__main__':unittest.main()

