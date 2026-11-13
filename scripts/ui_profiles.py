"""Build complete Standard/Large skins, sharing graphics through PolsQ paths."""
import ast
from copy import deepcopy
import xml.etree.ElementTree as E


def write_xml(path,root):
    path.parent.mkdir(parents=True,exist_ok=True)
    E.indent(root,space='  ')
    path.write_bytes(b'<?xml version="1.0" encoding="UTF-8"?>\n'+E.tostring(root,encoding='utf-8')+b'\n')


def service_templates(large=False):
    root=E.Element('templates')
    name='PolsQLarge' if large else 'PolsQ'
    height=96
    template=E.SubElement(root,'template',name=name,component='serviceList',fonts='PolsQStrong;30,PolsQText;25,PolsQText;26' if large else 'PolsQStrong;28,PolsQText;23,PolsQText;24')
    def item(mode,tag,**attrs):
        return E.SubElement(mode,tag,{k:str(v) for k,v in attrs.items()})
    for kind in ('services','bouquets','other'):
        mode=E.SubElement(template,'mode',name=kind,itemHeight=str(height),itemWidth='936',foregroundColor='white',foregroundColorSelected='white',backgroundColor='bg',backgroundColorSelected='selected')
        item(mode,'rectangle',position='0,0',size=f'4,{height}',foregroundColor='bg',foregroundColorSelected='green')
        item(mode,'rectangle',position=f'0,{height-1}',size='936,1',foregroundColor='line',foregroundColorSelected='selected')
        if kind=='other':
            for index in ('FolderImage','MarkerImage'):
                item(mode,'pixmap',index=index,position='16,22',size='32,32',alpha='blend',scale='scaleCenter')
            item(mode,'text',index='EntryName',position='64,0',size=f'856,{height}',font='0',verticalAlignment='center',wrap='ellipsis')
            continue
        item(mode,'text',index='Number',position='4,0',size=f'52,{height}',font='2',horizontalAlignment='right',verticalAlignment='center',foregroundColor='muted',foregroundColorSelected='white')
        item(mode,'pixmap',index='Picon',position='60,20',size='80,46',alpha='blend',scale='scaleCenter')
        # Both sizes use two distinct text lines. Channel names can use the full
        # upper line; programme titles end before the separate progress slot.
        item(mode,'text',index='ServiceName',position='160,6',size='760,40',font='0',verticalAlignment='center',wrap='ellipsis')
        item(mode,'text',index='Title1',position='160,50',size='672,38',font='1',verticalAlignment='center',foregroundColor='muted',foregroundColorSelected='muted',wrap='ellipsis')
        item(mode,'progress',index='Progress',position='856,68',size='64,6',foregroundColor='green',foregroundColorSelected='green',backgroundColor='line',backgroundColorSelected='line',borderWidth='0')
    return root


def history_template(large=False):
    return ('{"fonts":[gFont("PolsQStrong",%d),gFont("PolsQText",%d),gFont("PolsQText",%d)],"itemHeight":112,"itemWidth":664,"template":[' % ((32,25,22) if large else (30,24,21))+
        'MultiContentEntryRectangle(pos=(0,0),size=(3,112),backgroundColor=0x000d1322,backgroundColorSelected=0x00f5c842),'
        'MultiContentEntryRectangle(pos=(8,111),size=(648,1),backgroundColor=0x0026304a,backgroundColorSelected=0x0026407f),'
        'MultiContentEntryText(pos=(4,0),size=(16,112),font=2,flags=RT_HALIGN_CENTER|RT_VALIGN_CENTER,text=1,color=0x00f5c842,color_sel=0x00f5c842),'
        'MultiContentEntryPixmapAlphaBlend(pos=(24,30),size=(88,50),png=6,flags=BT_SCALE|BT_KEEP_ASPECT_RATIO),'
        'MultiContentEntryText(pos=(128,4),size=(512,40),font=0,flags=RT_HALIGN_LEFT|RT_VALIGN_CENTER|RT_ELLIPSIS,text=2),'
        'MultiContentEntryText(pos=(128,46),size=(512,32),font=1,flags=RT_HALIGN_LEFT|RT_VALIGN_CENTER|RT_ELLIPSIS,text=3,color=0x00a9b4c9,color_sel=0x00a9b4c9),'
        'MultiContentEntryText(pos=(128,80),size=(512,28),font=2,flags=RT_HALIGN_LEFT|RT_VALIGN_CENTER|RT_ELLIPSIS,text=5,color=0x00a9b4c9,color_sel=0x00a9b4c9)]}')


def bigger_height(value):
    return ((int(value)*6//5+7)//8)*8


def enlarge_template(code):
    tree=ast.parse(code,mode='eval')
    for node in ast.walk(tree):
        if isinstance(node,ast.Call) and isinstance(node.func,ast.Name):
            if node.func.id=='gFont':node.args[1].value+=4
            elif node.func.id.startswith('MultiContentEntry'):
                for kw in node.keywords:
                    if kw.arg=='pos':kw.value.elts[1].value=round(kw.value.elts[1].value*1.2)
                    elif kw.arg=='size':
                        height=kw.value.elts[1].value
                        kw.value.elts[1].value=max(1,round(height*1.2)) if height<=4 else bigger_height(height)
        if isinstance(node,ast.Dict):
            for key,val in zip(node.keys,node.values):
                if isinstance(key,ast.Constant) and key.value=='itemHeight':val.value=bigger_height(val.value)
                if isinstance(key,ast.Constant) and key.value=='templates':
                    for style in val.values:style.elts[0].value=bigger_height(style.elts[0].value)
    return ast.unparse(tree)


def large_skin(skin):
    large=deepcopy(skin)
    history_screens=[large.find(f"screen[@name='{name}']") for name in ('HistoryZap','HistoryZapSelector')]
    history_nodes={id(n) for scene in history_screens for n in scene.iter()}
    for node in large.iter():
        if id(node) in history_nodes:continue
        for key,value in list(node.attrib.items()):
            if key.lower().endswith('font') and ';' in value:
                family,size=value.rsplit(';',1)
                node.set(key,f'{family};{int(size)+4}')
        if node.tag=='alias':
            node.set('size',str(int(node.get('size'))+4))
            node.set('height',str(bigger_height(node.get('height'))))
        if node.tag=='widget':
            if node.get('itemHeight'):
                node.set('itemHeight',str(bigger_height(node.get('itemHeight'))))
                width,height=map(int,node.get('size').split(','))
                row=int(node.get('itemHeight'))
                if height>=row:node.set('size',f'{width},{height//row*row}')
            if node.get('NumberOfRows'):
                node.set('NumberOfRows',str(max(3,int(node.get('NumberOfRows'))-2)))
            converter=node.find("convert[@type='TemplatedMultiContent']")
            if converter is not None:
                converter.text=enlarge_template(converter.text)
                from validate import check_template
                template=check_template(converter.text)
                row=template.get('itemHeight') or template['templates']['default'][0]
                width,height=map(int,node.get('size').split(','))
                if height>=row:node.set('size',f'{width},{height//row*row}')
    for name in ('ChannelSelection','ChannelSelection_PIG','ChannelSelection_NoPIG','ChannelSelectionRadio'):
        screen=large.find(f"screen[@name='{name}']")
        if screen.get('label'):screen.set('label',screen.get('label').replace('PolsQ','PolsQ Large'))
        widget=screen.find("widget[@name='list']")
        widget.set('size','1136,760');widget.set('serviceItemHeight','76')
        widget.set('serviceNameFont','PolsQText;30');widget.set('serviceInfoFont','PolsQText;25')
    for name in ('SimpleChannelSelection','SlimChannelSelection'):
        widget=large.find(f"screen[@name='{name}']/widget[@name='list']")
        widget.set('size','1840,760');widget.set('serviceItemHeight','76')
        widget.set('serviceNameFont','PolsQText;30');widget.set('serviceInfoFont','PolsQText;25')
    for name in ('BouquetSelector','EPGBouquetSelector'):
        widget=large.find(f"screen[@name='{name}']/widget[@name='menu']")
        widget.set('itemHeight','76');widget.set('size','1136,760')
    for scene in history_screens:
        scene.find("widget[@source='menu']/convert").text=history_template(True)
        for node in scene:
            if node.get('font'):
                family,size=node.get('font').rsplit(';',1)
                node.set('font',f'{family};{int(size)+2}')
    # Keep short labels tall enough for the enlarged baseline/descenders.
    for scene in large.findall('screen'):
        screen_height=int(scene.get('size').split(',')[1])
        for node in scene:
            if node.get('font'):
                font=int(node.get('font').rsplit(';',1)[1])
                width,height=map(int,node.get('size').split(','))
                y=int(node.get('position').split(',')[1])
                minimum=(font*6+4)//5
                if height<minimum and y+minimum<=screen_height:node.set('size',f'{width},{minimum}')
    # 8 full file rows become 6 full 80px rows; keep native aliases in sync.
    for side in ('left','right'):
        node=large.find(f"screen[@name='FileCommander']/widget[@name='list{side}']")
        node.set('itemHeight','80');node.set('size','864,480')
    for alias in large.findall('fonts/alias'):
        if alias.get('name') in ('FileList','FileListMulti'):alias.set('height','80')
    # Keep generic settings at eight 80px rows, and skin settings at seven.
    for node in large.findall(".//widget[@name='config']"):
        width,height=map(int,node.get('size').split(','));row=int(node.get('itemHeight'))
        if height>=row:node.set('size',f'{width},{height//row*row}')
    return large


def write_variants(root,skin):
    from q_layout import apply
    large=large_skin(skin)
    write_xml(root/'PolsQ/skin.xml',apply(skin))
    write_xml(root/'PolsQLarge/skin.xml',apply(large,True))
    write_xml(root/'PolsQ/skinTemplates.xml',service_templates())
    write_xml(root/'PolsQLarge/skinTemplates.xml',service_templates(True))
