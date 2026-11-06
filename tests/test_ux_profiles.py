import ast
import importlib.util
from pathlib import Path
from types import SimpleNamespace as NS
import tempfile
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as E
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from validate import validate
from install_payload import install


def load_profiles():
    spec=importlib.util.spec_from_file_location('polsq_profiles',ROOT/'runtime/Plugins/Extensions/PolsQSettings/profiles.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


class Field:
    def __init__(self,value,choices=None):
        self.value=value;self.saved=0;self.choices=NS(choices=choices or [])
    def setChoices(self,choices):self.choices.choices=choices
    def save(self):self.saved+=1


class Profiles(unittest.TestCase):
    def test_explicit_activation_sets_both_native_list_engines_and_supported_values(self):
        profiles=load_profiles()
        for name in ('standard','large'):
            usage=NS(**{k:Field(v) for k,v in {'serviceitems_per_page':18,'serviceitems_per_page_twolines':12,'servicelist_twolines':False,'servicelist_column':'-1','service_icon_enable':False,'show_event_progress_in_servicelist':'no'}.items()})
            selection=NS(screenStyle=Field('old',[('old','Old')]),widgetStyle=Field('Legacy',[('Legacy','Old')]),showPicon=Field(False))
            config=NS(skin=NS(primary_skin=Field('Other/skin.xml')),usage=usage,channelSelection=selection)
            profile=profiles.apply_profile(config,name)
            self.assertEqual(config.skin.primary_skin.value,profile['skin'])
            self.assertEqual(selection.widgetStyle.value,profile['template'])
            self.assertTrue(selection.showPicon.value)
            self.assertEqual(usage.serviceitems_per_page.value,8)
            self.assertEqual(usage.serviceitems_per_page_twolines.value,profile['rows'])
            self.assertTrue(usage.servicelist_twolines.value)
            self.assertIn(int(usage.servicelist_column.value),range(100,1325,25))
            self.assertEqual(usage.show_event_progress_in_servicelist.value,'barright')
            self.assertEqual(config.skin.primary_skin.saved,1)

    def test_large_has_larger_fonts_ten_rows_and_complete_layout_contracts(self):
        validate('PolsQLarge')
        skins=[E.parse(ROOT/folder/'skin.xml').getroot() for folder in ('PolsQ','PolsQLarge')]
        for name in ('InfoBar','Setup','PolsQSettings'):
            normal=skins[0].find(f"screen[@name='{name}']");large=skins[1].find(f"screen[@name='{name}']")
            for a,b in zip(normal,large):
                if a.get('font'):self.assertGreater(int(b.get('font').split(';')[1]),int(a.get('font').split(';')[1]))
        for folder,rows in (('PolsQ',8),('PolsQLarge',8)):
            skin=E.parse(ROOT/folder/'skin.xml').getroot()
            height=int(skin.find("screen[@name='ChannelSelection']/widget[@name='list']").get('size').split(',')[1])
            template=E.parse(ROOT/folder/'skinTemplates.xml').getroot().find('template')
            for kind in ('services','bouquets'):
                mode=template.find(f"mode[@name='{kind}']")
                self.assertEqual(height//int(mode.get('itemHeight')),rows)
                self.assertIsNotNone(mode.find("text[@index='Title1']"))
                self.assertIsNotNone(mode.find("progress[@index='Progress']"))

    def test_timer_and_epg_states_are_distinguishable(self):
        skin=E.parse(ROOT/'PolsQ/skin.xml').getroot()
        epg=skin.find("screen[@name='GraphicalEPG']/widget[@name='list']")
        self.assertNotEqual(epg.get('EntryBackgroundColorNow'),epg.get('EntryBackgroundColor'))
        self.assertIsNotNone(skin.find("screen[@name='ConflictTimerOverview']/widget[@name='timerlist']"))
        self.assertNotEqual((ROOT/'PolsQ/icons/epgclock.png').read_bytes(),(ROOT/'PolsQ/icons/epgclock_disabled.png').read_bytes())
        self.assertNotEqual((ROOT/'PolsQ/icons/epgclock.png').read_bytes(),(ROOT/'PolsQ/icons/epgclock_zap.png').read_bytes())

    def test_manual_installer_rolls_back_every_replaced_unit_after_failure(self):
        with tempfile.TemporaryDirectory() as temp:
            destination=Path(temp)
            install(ROOT,destination)
            targets=[destination/'usr/share/enigma2/PolsQ/VERSION',destination/'usr/share/enigma2/PolsQLarge/VERSION',destination/'usr/lib/enigma2/python/Plugins/Extensions/PolsQSettings/plugin.py']
            for target in targets:target.write_text('previous')
            rename=Path.rename
            def fail_late(path,target):
                if path.name=='PolsQEventRemaining.py' and path.parent.name.startswith('.PolsQ-stage-'):raise OSError('injected write failure')
                return rename(path,target)
            with patch.object(Path,'rename',fail_late):
                with self.assertRaises(OSError):install(ROOT,destination)
            self.assertTrue(all(target.read_text()=='previous' for target in targets))

    def test_settings_plugin_has_no_autostart_and_cancel_does_not_apply(self):
        tree=ast.parse((ROOT/'runtime/Plugins/Extensions/PolsQSettings/plugin.py').read_text())
        descriptor=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='Plugins')
        places=[n.attr for n in ast.walk(descriptor) if isinstance(n,ast.Attribute) and n.attr.startswith('WHERE_')]
        self.assertEqual(places,['WHERE_PLUGINMENU'])
        cls=next(n for n in tree.body if isinstance(n,ast.ClassDef))
        cancel=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='keyCancel')
        calls=[ast.unparse(n.func) for n in ast.walk(cancel) if isinstance(n,ast.Call)]
        self.assertEqual(calls,['self.close'])

    def test_restart_keeps_settings_dialog_under_native_quit_confirmation(self):
        tree=ast.parse((ROOT/'runtime/Plugins/Extensions/PolsQSettings/plugin.py').read_text())
        cls=next(n for n in tree.body if isinstance(n,ast.ClassDef))
        method=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='restartAnswer')
        namespace={'TryQuitMainloop':'native-quit','QUIT_RESTART':3}
        exec(compile(ast.Module(body=[method],type_ignores=[]),'restart-answer','exec'),namespace)
        events=[]
        screen=NS(session=NS(open=lambda *args:events.append(('open',args))),close=lambda:events.append(('close',)))
        namespace['restartAnswer'](screen,True)
        self.assertEqual(events,[('open',('native-quit',3))])
        events.clear();namespace['restartAnswer'](screen,False)
        self.assertEqual(events,[('close',)])


class RemainingTime(unittest.TestCase):
    def test_summary_fits_complete_lines_and_keeps_full_source_for_info(self):
        path=ROOT/'runtime/Components/Renderer/PolsQSummary.py'
        cls=next(n for n in ast.parse(path.read_text()).body if isinstance(n,ast.ClassDef))
        class Label:
            CHANGED_CLEAR=2
        class Display:
            text=''
            def setText(self,text):self.text=text
            def size(self):return NS(height=lambda:60)
            def calculateSize(self):return NS(height=lambda:((len(self.text)+29)//30)*30)
        namespace={'Label':Label}
        exec(compile(ast.Module(body=[cls],type_ignores=[]),str(path),'exec'),namespace)
        renderer=namespace['PolsQSummary']()
        renderer.instance=Display();full='Opis audycji z pełnymi informacjami. '*20;renderer.source=NS(text=full)
        renderer.changed((0,))
        self.assertLessEqual(renderer.instance.calculateSize().height(),60)
        self.assertTrue(renderer.instance.text.endswith('…'))
        self.assertEqual(renderer.source.text,full)
        renderer.source.text='Krótki opis';renderer.changed((0,))
        self.assertEqual(renderer.instance.text,'Krótki opis')
        renderer.changed((2,));self.assertEqual(renderer.instance.text,'')

    def test_real_event_times_missing_epg_future_and_finished_events(self):
        path=ROOT/'runtime/Components/Converter/PolsQEventRemaining.py'
        cls=next(n for n in ast.parse(path.read_text()).body if isinstance(n,ast.ClassDef))
        class Converter:
            def __init__(self,argument):pass
        class Poll:
            def __init__(self):pass
        namespace={'Converter':Converter,'Poll':Poll,'cached':lambda method:method,'time':lambda:1000}
        exec(compile(ast.Module(body=[cls],type_ignores=[]),str(path),'exec'),namespace)
        converter=namespace['PolsQEventRemaining']('')
        self.assertEqual(converter.poll_interval,30000)
        for begin,duration,expected in ((900,221,'Do końca: 3 min'),(900,100,''),(1100,300,''),(900,0,'')):
            converter.source=NS(event=NS(getBeginTime=lambda:begin,getDuration=lambda:duration))
            self.assertEqual(converter.text,expected)
        converter.source=NS(event=None)
        self.assertEqual(converter.text,'')

