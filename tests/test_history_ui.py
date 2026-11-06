from pathlib import Path
import sys
import unittest
import xml.etree.ElementTree as E

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from validate import check_template


class HistoryUI(unittest.TestCase):
    def test_both_native_aliases_use_a_narrow_left_panel(self):
        for folder,rows in (('PolsQ',6),('PolsQLarge',6)):
            skin=E.parse(ROOT/folder/'skin.xml').getroot()
            codes=[]
            for name in ('HistoryZap','HistoryZapSelector'):
                screen=skin.find(f"screen[@name='{name}']")
                self.assertIsNotNone(screen,name)
                self.assertEqual(screen.get('size'),'704,920')
                self.assertEqual(screen.get('position'),'40,80')
                self.assertEqual(screen.get('backgroundColor'),'overlay')
                menu=screen.find("widget[@source='menu'][@render='Listbox']")
                code=menu.find('convert').text;codes.append(code)
                template=check_template(code)
                height=int(menu.get('size').split(',')[1])
                self.assertEqual(height,rows*template['itemHeight'])
                self.assertIsNotNone(screen.find("widget[@source='key_red']"))
                self.assertIsNotNone(screen.find("widget[@source='key_green']"))
                self.assertIsNone(screen.find("widget[@source='key_blue']"))
            self.assertEqual(codes[0],codes[1])

    def test_native_indices_and_non_overlapping_text_and_picons(self):
        for folder in ('PolsQ','PolsQLarge'):
            skin=E.parse(ROOT/folder/'skin.xml').getroot()
            node=skin.find("screen[@name='HistoryZap']/widget[@source='menu']/convert")
            template=check_template(node.text);items=template['template']
            texts={kw['text']:kw for kind,kw in items if kind=='text'}
            self.assertEqual(set(texts),{1,2,3,5},'Full description and service reference must not be printed in a row')
            picon=next(kw for kind,kw in items if kind=='pixmap')
            self.assertEqual(picon['png'],6)
            channel,event,times=texts[2],texts[3],texts[5]
            self.assertTrue(template['fonts'][channel['font']][0]=='PolsQStrong')
            self.assertGreaterEqual(channel['pos'][0]-(picon['pos'][0]+picon['size'][0]),16)
            self.assertGreaterEqual(event['pos'][1]-(channel['pos'][1]+channel['size'][1]),2)
            self.assertGreaterEqual(times['pos'][1]-(event['pos'][1]+event['size'][1]),2)
            for kind,kw in items:
                self.assertLessEqual(kw['pos'][0]+kw['size'][0],664)
            for key in (2,3,5):
                self.assertIn('RT_ELLIPSIS',node.text)
                self.assertGreaterEqual(texts[key]['size'][1],template['fonts'][texts[key]['font']][1]*1.2)


if __name__=='__main__':unittest.main()

