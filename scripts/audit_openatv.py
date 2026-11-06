#!/usr/bin/env python3
"""Odczytuje AST źródeł OpenATV, bez importowania/wykonywania ich kodu.

Użycie: python3 scripts/audit_openatv.py /tmp/polsq-openatv --write
Wymaga checkoutów 7.5, 7.6 i 8.0 w podkatalogach argumentu.
Zapisany kontrakt pozwala ponawiać kontrolę bez sieci i bez odbiornika.
"""
import argparse
import ast
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
VERSIONS=('7.5','7.6','8.0')


def callname(node):
    if isinstance(node,ast.IfExp):
        return callname(node.body) or callname(node.orelse)
    if isinstance(node,ast.Call):
        if isinstance(node.func,ast.Name):
            return node.func.id
        if isinstance(node.func,ast.Attribute):
            return node.func.attr
    return None


def subkey(node):
    if isinstance(node,ast.Subscript) and isinstance(node.value,ast.Name) and node.value.id=='self':
        if isinstance(node.slice,ast.Constant) and isinstance(node.slice.value,str):
            return node.slice.value
    return None


def loop_value(node,env):
    if isinstance(node,ast.Constant):return node.value
    if isinstance(node,ast.Name) and node.id in env:return env[node.id]
    if isinstance(node,(ast.Tuple,ast.List)):return [loop_value(x,env) for x in node.elts]
    if isinstance(node,ast.JoinedStr):
        return ''.join(str(loop_value(x.value,env)) if isinstance(x,ast.FormattedValue) else x.value for x in node.values)
    if isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id=='range':
        return list(range(*[loop_value(x,env) for x in node.args]))
    raise ValueError('Non-static loop')


def extract(directory):
    classes={}; fingerprints={}
    for path in sorted((directory/'lib/python').rglob('*.py')):
        fingerprints[str(path.relative_to(directory))]=hashlib.sha256(path.read_bytes()).hexdigest()
        tree=ast.parse(path.read_text(),filename=str(path))
        for cls in [c for c in tree.body if isinstance(c,ast.ClassDef)]:
            entries={}; mandatory=[]
            attributes={}
            for node in ast.walk(cls):
                if isinstance(node,ast.Assign) and callname(node.value):
                    for target in node.targets:
                        if isinstance(target,ast.Attribute) and isinstance(target.value,ast.Name) and target.value.id=='self':
                            attributes[target.attr]=callname(node.value)
            for node in ast.walk(cls):
                if isinstance(node,ast.Assign):
                    kind=callname(node.value)
                    if isinstance(node.value,ast.Attribute) and isinstance(node.value.value,ast.Name) and node.value.value.id=='self':
                        kind=attributes.get(node.value.attr)
                    if kind:
                        for target in node.targets:
                            key=subkey(target)
                            if key:
                                entries.setdefault(key,kind)
                if isinstance(node,ast.For) and isinstance(node.target,ast.Name):
                    try: values=loop_value(node.iter,{})
                    except (ValueError,TypeError):continue
                    for value in values:
                        for child in ast.walk(node):
                            if not isinstance(child,ast.Assign):continue
                            kind=callname(child.value)
                            if not kind:continue
                            for target in child.targets:
                                if isinstance(target,ast.Subscript) and isinstance(target.value,ast.Name) and target.value.id=='self':
                                    try:key=loop_value(target.slice,{node.target.id:value})
                                    except (ValueError,TypeError):continue
                                    if isinstance(key,str):entries.setdefault(key,kind)
                if isinstance(node,ast.Call):
                    for kw in node.keywords:
                        if kw.arg=='mandatoryWidgets' and isinstance(kw.value,ast.List):
                            mandatory += [x.value for x in kw.value.elts if isinstance(x,ast.Constant)]
            data={'module':path.name,'bases':[b.id for b in cls.bases if isinstance(b,ast.Name)],'widgets':entries,'required':mandatory}
            classes[cls.name]=data
            classes[path.name+':'+cls.name]=data
    def inherited(name,seen=None):
        seen=set() if seen is None else seen
        if name not in classes and ':' in name:
            name=name.split(':')[-1]
        if name in seen or name not in classes:
            return {},[]
        seen.add(name); c=classes[name]; result={}; required=[]
        for base in c['bases']:
            w,r=inherited(c['module']+':'+base,seen);result.update(w);required+=r
        result.update(c['widgets']);required+=c['required']
        return result,required
    mapping={
        'Menu':'Menu','QuickMenu':'QuickMenu','ChannelSelection':'ChannelSelection','ChannelSelection_PIG':'ChannelSelection','ChannelSelection_NoPIG':'ChannelSelection',
        'ChannelSelectionRadio':'ChannelSelectionRadio','SimpleChannelSelection':'SimpleChannelSelection','SlimChannelSelection':'SimpleChannelSelection',
        'HistoryZap':'HistoryZapSelector','HistoryZapSelector':'HistoryZapSelector',
        'BouquetSelector':'BouquetSelector','EPGBouquetSelector':'EPGBouquetSelector',
        **{x:'EPGSelection' for x in ['EPGSelection','QuickEPG','EPGSelectionMulti','GraphicalEPG','GraphicalEPGPIG','GraphicalInfoBarEPG','EPGvertical','EPGverticalPIG']},
        'EventView':'EventViewEPGSelect','InfoBarEventView':'EventViewSimple','Setup':'Setup',
        **{name:'SkinSelection' for name in ('SkinSelection','setup_Skin','SetupSkin')},
        'ChoiceBox':'ChoiceBoxNew','ChannelContextMenu':'ChannelContextMenu','MessageBox':'MessageBox','MessageBoxSimple':'MessageBox','MessageBoxModal':'MessageBox',
        'IpkgInstaller':'IpkgInstaller','Opkg':'Opkg','Console':'Console','Processing':'ProcessingScreen',
        'PackageAction':'PackageAction','PluginAction':'PackageAction','PackageActionLog':'PackageActionLog','PluginActionLog':'PackageActionLog',
        'FileCommander':'FileCommander','FileCommanderContextMenu':'FileCommanderContextMenu','FileCommanderData':'FileCommanderData',
        'FileCommanderFileViewer':'FileCommanderFileViewer','FileCommanderTextEditor':'FileCommanderTextEditor',
        'MovieSelection':'MovieSelection','MovieSelectionSlim':'MovieSelection',
        'TimerOverview':'RecordTimerOverview','RecordTimerOverview':'RecordTimerOverview','TimerEditList':'RecordTimerOverview',
        'ConflictTimerOverview':'ConflictTimerOverview','TimerSanityConflict':'ConflictTimerOverview',
        'PluginBrowserList':'PluginBrowser','PluginBrowserGrid':'PluginBrowser','InfoBar':'InfoBar','SecondInfoBar':'SecondInfoBar',
        'MoviePlayer':'MoviePlayer','PVRState':'PVRState','TimeshiftState':'TimeshiftState','NumberZap':'NumberZap'
        ,'AudioSelection':'AudioSelection','QuickSubtitlesConfigMenu':'QuickSubtitlesConfigMenu'
    }
    if directory.name=='8.0':
        mapping.update(EPGSelection='EPGSelectionSingle',QuickEPG='EPGSelectionInfobarSingle',
            EPGSelectionMulti='EPGSelectionMulti',GraphicalEPG='EPGSelectionGrid',
            GraphicalEPGPIG='EPGSelectionGrid',GraphicalInfoBarEPG='EPGSelectionInfobarGrid',
            EPGvertical='EPGSelectionVertical',EPGverticalPIG='EPGSelectionVertical')
    screens={}
    for screen,cls in mapping.items():
        if cls=='IpkgInstaller' and cls not in classes:
            # This installer moved into Enigma2 core in OpenATV 8.0. Do not
            # invent a widget contract for external installers on older images.
            screens[screen]={'class':cls,'available':False,'widgets':{},'required':[]}
            continue
        widgets,required=inherited(cls)
        widgets.update(inherited('Screen')[0])
        if cls=='SkinSelection':
            # layoutFinished unconditionally uses preview.instance.size().
            required.append('preview')
        if cls=='HistoryZapSelector':
            required.append('menu')
        if cls=='PluginBrowser':
            widgets.update(pluginList='List',pluginGrid='List')  # self[self.layout]
        if cls in ('EPGSelection','EPGSelectionGrid','EPGSelectionInfobarGrid'):
            widgets.update({f'timeline{i}':'Pixmap' for i in range(6)})  # f-string loop
        screens[screen]={'class':cls,'widgets':widgets,'required':sorted(set(required))}
    # Volume/Mute to core Enigma2 screens (C++), only these fixed widgets.
    screens['Volume']={'class':'C++ Volume','widgets':{'Volume':'ProgressBar'},'required':['Volume']}
    screens['Mute']={'class':'C++ Mute','widgets':{},'required':[]}
    # Our passive settings plugin owns these controls on every OpenATV version.
    screens['PolsQSettings']={'class':'PolsQSettings (bundled plugin)','widgets':{'Title':'StaticText','config':'ConfigList','description':'Label','footnote':'Label','key_red':'StaticText','key_green':'StaticText'},'required':['config','description','footnote']}
    return {'source_sha256':fingerprints,'screens':screens}


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('sources',type=Path);parser.add_argument('--write',action='store_true')
    args=parser.parse_args()
    result={version:extract(args.sources/version) for version in VERSIONS}
    if args.write:
        target=ROOT/'scripts/openatv-contracts.json'
        target.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
        print(target)
    else:
        known=json.loads((ROOT/'scripts/openatv-contracts.json').read_text())
        assert result==known,'Kontrakt różni się od zapisanych źródeł'
        print('OpenATV source contracts match')

