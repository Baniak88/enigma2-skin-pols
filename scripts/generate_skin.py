#!/usr/bin/env python3
"""Autorskie układy, nazwy widgetów sprawdzone w OpenATV 7.5/7.6/8.0.

Źródło API opisane w docs/COMPATIBILITY.md. Nie kopiuje kodu Python Enigma2.
"""
from pathlib import Path
import xml.etree.ElementTree as E
from skin_effects import EVENT_MARGIN

ROOT = Path(__file__).resolve().parents[1]
# Pols Q: navy surfaces and blue/cyan accents inspired by SKY DE.
PALETTE = dict(bg='101938', panel='18284e', selected='0759ad', now='123b68', white='f3f6fa', muted='b1c4e5',
               green='46baff', nativeGreen='00e676', line='304a72', track='647181', red='ff6262', yellow='f5ce55', blue='5eacff')
skin = E.Element('skin')


def add(parent, tag, **attrs):
    return E.SubElement(parent, tag, {k: str(v) for k, v in attrs.items() if v is not None})


def box(s, x, y, w, h, color='line', **kw):
    return add(s, 'eLabel', position=f'{x},{y}', size=f'{w},{h}', backgroundColor=color, **kw)


def label(s, text, x, y, w, h, font=28, color='white', family='PolsQText', **kw):
    return add(s, 'eLabel', text=text, position=f'{x},{y}', size=f'{w},{h}',
               font=f'{family};{font}', foregroundColor=color, transparent='1', **kw)


def widget(s, name, x, y, w, h, font=None, **kw):
    if kw.pop('noWrap',None)=='1':kw['wrap']='ellipsis'
    if name=='config':
        kw.setdefault('valueFont', f'PolsQText;{font or 30}')
    return add(s, 'widget', name=name, position=f'{x},{y}', size=f'{w},{h}',
               font=f'PolsQText;{font}' if font else None, **kw)


def source(s, name, x, y, w, h, font=28, color='white', render='Label', converts=(), **kw):
    if render=='Label' and ('EventName','ExtendedDescription') in converts:
        render='PolsQSummary'
    if kw.pop('noWrap',None)=='1':kw['wrap']='ellipsis'
    if render != 'Picon':
        kw.setdefault('foregroundColor', color)
    if render in ('Label', 'FixedLabel', 'PolsQSummary'):
        kw.setdefault('transparent', '1')
    n = add(s, 'widget', source=name, render=render, position=f'{x},{y}', size=f'{w},{h}',
            font=f'PolsQText;{font}' if render in ('Label', 'FixedLabel', 'PolsQSummary') else None,
            **kw)
    for kind, arg in converts:
        add(n, 'convert', type=kind).text = arg
    return n


def screen(name, pos=(0, 0), size=(1920, 1080), bg='bg'):
    return add(skin, 'screen', name=name, position=f'{pos[0]},{pos[1]}',
               size=f'{size[0]},{size[1]}', flags='wfNoBorder', backgroundColor=bg)


def header(s, section, margin=64):
    delta=margin-64
    width=1920-2*margin
    box(s,margin,54,5,28,'green')
    label(s, 'POLS Q', margin+20, 38, 300, 60, 40, family='PolsQStrong')
    label(s, section, 420+delta, 48, 1110-2*delta, 44, 25, 'muted')
    source(s, 'global.CurrentTime', 1920-margin-256, 40, 256, 58, 36, halign='right', converts=[('ClockToText', 'Default')])
    add(s,'ePixmap',position=f'{margin},126',size=f'{width},2',pixmap='PolsQ/assets/accent-fade.png',alphatest='blend',scale='1')
    source(s, 'Title', margin, 150, width, 48, 27, 'muted', noWrap='1')


def footer(s, keys=('red', 'green', 'yellow', 'blue'), margin=64):
    width=1920-2*margin
    column=width//4
    box(s, margin, 974, width, 2)
    for i, key in enumerate(keys):
        x = margin + ('red','green','yellow','blue').index(key) * column
        source(s, f'key_{key}', x, 1012, 6, 24, render='FixedLabel', text=' ',
               backgroundColor="nativeGreen" if key=="green" else key, transparent='0', conditional=f'key_{key}', converts=[('ConditionalShowHide',None)])
        source(s, f'key_{key}', x + 22, 998, column-34, 50, 25, noWrap='1', valign='center',
               conditional=f'key_{key}', converts=[('ConditionalShowHide',None)])


def compact_header(s,section):
    box(s,40,32,4,26,'green')
    label(s,'POLS Q',60,20,220,48,36,family='PolsQStrong')
    add(s,'ePixmap',position='304,30',size='28,28',pixmap='PolsQ/assets/line-tv.png',alphatest='blend',scale='1')
    label(s,section,348,28,1100,40,24,'muted')
    source(s,'global.CurrentTime',1624,20,256,48,32,halign='right',converts=[('ClockToText','Default')])
    add(s,'ePixmap',position='40,88',size='1840,2',pixmap='PolsQ/assets/accent-fade.png',alphatest='blend',scale='1')
    source(s,'Title',40,112,1840,40,25,'muted',noWrap='1')


LIST = dict(backgroundColor='bg', foregroundColor='white',
            backgroundColorSelected='selected', foregroundColorSelected='white', scrollbarMode='showOnDemand',
            scrollbarWidth='6', scrollbarBorderWidth='0', scrollbarOffset='8',
            scrollbarForegroundColor='muted', scrollbarBackgroundColor='line')


def picon(s, src, x, y, w=220, h=132):
    # Screen.createGUIScreen tworzy additionalWidgets PO rendererach.
    # Jawne warstwy są konieczne: dekoracja z tym samym z zasłoniłaby Picon.
    add(s,'ePixmap',position=f'{x},{y}',size=f'{w},{h}',pixmap='PolsQ/picon_default.png',
        scale='1',alphatest='blend',zPosition='0')
    return source(s, src, x, y, w, h, render='Picon', converts=[('ServiceName', 'Reference')],
        alphatest='blend',zPosition='1',backgroundColor='transparent',transparent='1')


def event(s, src, x, y, w, desc=True):
    source(s, src, x, y, w, 54, 34, converts=[('EventName', 'Name')], noWrap='1')
    source(s, src, x, y+66, 140, 42, 26, 'green', converts=[('EventTime', 'StartTime'), ('ClockToText', 'Default')])
    source(s, src, x+144, y+66, 160, 42, 26, 'muted', converts=[('EventTime', 'EndTime'), ('ClockToText', 'Format:– %H:%M')])
    if desc:
        source(s, src, x, y+132, w, 186, 26, 'muted', converts=[('EventName', 'ExtendedDescription')])


def templated(n, template):
    add(n, 'convert', type='TemplatedMultiContent').text = template


def build():
    add(add(skin, 'output', id='0'), 'resolution', xres='1920', yres='1080', bpp='32')
    colors = add(skin, 'colors')
    for name, value in PALETTE.items():
        add(colors, 'color', name=name, value='#00'+value)
    # Enigma2 ARGB uses inverse alpha: 00 is opaque, ff is transparent.
    # 26 = 38/255 (~15%) transparency, ~85% opacity.
    add(colors, 'color', name='overlay', value='#26101938')
    add(colors, 'color', name='transparent', value='#ff000000')
    style = add(skin, 'windowstyle', type='skinned', id='0')
    add(style, 'title', offset='24,12', font='PolsQText;30')
    for name, color in dict(Background='bg', LabelForeground='white', ListboxBackground='bg', ListboxForeground='white',
        ListboxSelectedBackground='selected', ListboxSelectedForeground='white', ListboxMarkedBackground='panel',
        ListboxMarkedForeground='green', ListboxMarkedAndSelectedBackground='green',
        ListboxMarkedAndSelectedForeground='bg', WindowTitleForeground='white', WindowTitleBackground='bg').items():
        add(style, 'color', name=name, color=color)
    add(style, 'configList', entryFont='PolsQText;30', valueFont='PolsQText;30', headerFont='PolsQText;30')
    add(style, 'label', font='PolsQText;30')
    add(style, 'listbox', font='PolsQText;30', scrollbarWidth='6', scrollbarBorderWidth='0', scrollbarMode='showOnDemand')
    fonts = add(skin, 'fonts')
    add(fonts,'font',filename='DejaVuSans.ttf',name='PolsQText',scale='100')
    add(fonts,'font',filename='LiberationSans-Bold.ttf',name='PolsQStrong',scale='100')
    add(fonts,'font',filename='andale.ttf',name='PolsQMono',scale='100')
    for name, size, height in [('TextNormal',30,40), ('ChoiceBoxDescription',26,36), ('ChoiceList',30,72), ('SelectionList',30,72), ('FileList',28,64), ('FileListMulti',28,64), ('MenuFont',32,64)]:
        add(fonts, 'alias', name=name, font='PolsQText', size=size, height=height)
    parameters=add(skin,'parameters')
    for name,value in {
        'ChoicelistName':'64,16,1712,40',
        'ChoicelistNameSingle':'24,16,1744,40',
        'ChoicelistIcon':'12,20,36,32',
        'ChoicelistDash':'0,16,1792,40',
        'SelectionListDescr':'64,16,1656,40',
        'SelectionListLock':'12,20,32,32',
        'FileListIcon':'12,16,32,32',
        'FileListName':'60,12,776,40',
        'FileListMultiLock':'12,20,24,24',
        'FileListMultiIcon':'48,16,32,32',
        'FileListMultiName':'96,12,740,40',
    }.items():
        add(parameters,'parameter',name=name,value=value)

    s = screen('Menu'); header(s, 'MENU'); footer(s)
    n = source(s, 'menu', 64, 240, 1080, 640, render='Listbox', **LIST)
    common = 'MultiContentEntryText(pos=(92,0),size=(950,80),font=0,flags=RT_HALIGN_LEFT|RT_VALIGN_CENTER,text=3)'
    icon = 'MultiContentEntryPixmapAlphaBlend(pos=(16,12),size=(56,56),png=1,flags=BT_SCALE|BT_KEEP_ASPECT_RATIO)'
    number = 'MultiContentEntryText(pos=(12,0),size=(60,80),font=1,flags=RT_HALIGN_CENTER|RT_VALIGN_CENTER,text=2)'
    templated(n, '{"fonts":[gFont("PolsQText",32),gFont("PolsQText",26)],"templates":{' +
        ','.join('"%s":(80,[%s])' % (k, v) for k,v in {
            'default': 'MultiContentEntryText(pos=(24,0),size=(1030,80),font=0,flags=RT_HALIGN_LEFT|RT_VALIGN_CENTER,text=0)',
            'text':common, 'number':number+','+common, 'image':icon+','+common,
            'both':icon+','+'MultiContentEntryText(pos=(92,0),size=(60,80),font=1,flags=RT_HALIGN_CENTER|RT_VALIGN_CENTER,text=2),MultiContentEntryText(pos=(168,0),size=(870,80),font=0,flags=RT_HALIGN_LEFT|RT_VALIGN_CENTER,text=3)'
        }.items()) + '}}')
    box(s, 1200, 240, 2, 640)
    widget(s, 'menuimage', 1390, 248, 240, 240, alphatest='blend', scale='1')
    source(s, 'description', 1264, 540, 592, 266, 32, 'muted')
    label(s, 'OK  Wybierz     EXIT  Powrót', 64, 906, 1080, 42, 24, 'muted')

    s=screen('QuickMenu');header(s,'SZYBKIE MENU');footer(s,('red','green','yellow'))
    label(s,'KATEGORIE  ·  ← → zmień kolumnę',64,214,608,34,20,'muted')
    label(s,'DOSTĘPNE DZIAŁANIA  ·  OK wybierz',736,214,1120,34,20,'muted')
    box(s,704,260,2,608)
    n=source(s,'mainlist',64,260,608,608,render='Listbox',**LIST)
    templated(n,'{"fonts":[gFont("PolsQText",30),gFont("PolsQText",22)],"itemHeight":76,"template":['
        'MultiContentEntryPixmapAlphaBlend(pos=(12,14),size=(52,48),png=2,flags=BT_SCALE|BT_KEEP_ASPECT_RATIO),'
        'MultiContentEntryText(pos=(88,4),size=(496,40),font=0,flags=RT_HALIGN_LEFT|RT_VALIGN_CENTER|RT_ELLIPSIS,text=0),'
        'MultiContentEntryText(pos=(88,44),size=(496,28),font=1,flags=RT_HALIGN_LEFT|RT_VALIGN_CENTER|RT_ELLIPSIS,text=1,color=0x00b1c4e5,color_sel=0x00f3f6fa)]}')
    n=source(s,'sublist',736,260,1120,608,render='Listbox',**LIST)
    templated(n,'{"fonts":[gFont("PolsQText",30),gFont("PolsQText",23)],"itemHeight":76,"template":['
        'MultiContentEntryText(pos=(20,4),size=(1080,40),font=0,flags=RT_HALIGN_LEFT|RT_VALIGN_CENTER|RT_ELLIPSIS,text=0),'
        'MultiContentEntryText(pos=(20,44),size=(1080,28),font=1,flags=RT_HALIGN_LEFT|RT_VALIGN_CENTER|RT_ELLIPSIS,text=1,color=0x00b1c4e5,color_sel=0x00f3f6fa)]}')
    widget(s,'description',64,888,1792,72,25,foregroundColor='muted',transparent='1')

    for name in ('ChannelSelection','ChannelSelection_PIG','ChannelSelection_NoPIG','ChannelSelectionRadio'):
        s = screen(name); compact_header(s, 'TELEWIZJA' if name != 'ChannelSelectionRadio' else 'RADIO'); footer(s,margin=40)
        if name != 'ChannelSelectionRadio':
            s.set('base','ChannelSelection')
            s.set('label',{'ChannelSelection':'PolsQ — 10 kanałów z TV','ChannelSelection_PIG':'PolsQ — podgląd TV','ChannelSelection_NoPIG':'PolsQ — bez podglądu'}[name])
        widget(s,'list',40,168,1136,760,serviceNameFont='PolsQText;28',serviceInfoFont='PolsQText;23',
            serviceNumberFont='PolsQText;24',serviceItemHeight='76',foregroundColorEvent='muted',
            fieldMargins='16',itemsDistances='16',listMarginLeft='8',listMarginRight='16',
            selectionPixmap='PolsQ/assets/channel-selected.png',selectionZoom='0',
            progressBarWidth='96',progressbarHeight='6',progressbarBorderWidth='0',
            foregroundColorEventSelected='muted',colorEventProgressbar='green',colorEventProgressbarSelected='green',
            colorEventProgressbarBorder='line',colorEventProgressbarBorderSelected='line',
            colorServiceRecorded='red',colorServiceRecording='red',**LIST)
        label(s,'OK — kanał     INFO — opis     EXIT — powrót',40,940,1136,28,21,'muted')
        box(s,1200,168,2,760)
        video = name in ('ChannelSelection','ChannelSelection_PIG')
        if video:
            source(s,'session.VideoPicture',1272,168,608,342,render='Pig',backgroundColor='transparent',zPosition='2')
            label(s,'ZAZNACZONA POZYCJA',1232,526,648,28,20,'muted')
            source(s,'ServiceEvent',1232,558,648,38,26,'green',converts=[('ServiceName','Name')],noWrap='1')
            box(s,1232,606,648,1)
            source(s,'ServiceEvent',1232,620,648,88,30,render='PolsQSummary',converts=[('EventName','Name')])
            source(s,'ServiceEvent',1232,724,130,36,25,'green',converts=[('EventTime','StartTime'),('ClockToText','Default')])
            source(s,'ServiceEvent',1372,724,170,36,25,'muted',converts=[('EventTime','EndTime'),('ClockToText','Format:– %H:%M')])
            source(s,'ServiceEvent',1552,724,328,36,23,'muted',halign='right',converts=[('PolsQEventRemaining','')])
            source(s,'ServiceEvent',1232,774,648,4,render='Progress',color='green',backgroundColor='line',borderWidth='0',converts=[('EventTime','Progress')])
            source(s,'ServiceEvent',1232,790,648,128,25,'muted',converts=[('EventName','ExtendedDescription')])
            label(s,'INFO — pełny opis',1232,940,648,28,20,'muted')
        else:
            picon(s,'ServiceEvent',1232,168)
            source(s,'ServiceEvent',1232,352,648,48,30,'green',converts=[('ServiceName','Name')],noWrap='1')
            event(s,'ServiceEvent',1232,432,648)
            label(s,'INFO — pełny opis audycji',1232,878,648,44,24,'muted')

    from ui_profiles import history_template
    for name in ('HistoryZap','HistoryZapSelector'):
        s=screen(name,pos=(40,80),size=(704,920),bg='overlay')
        add(s,'ePixmap',position='24,28',size='28,28',pixmap='PolsQ/assets/line-history.png',alphatest='blend',scale='1')
        label(s,'OSTATNIE KANAŁY',68,22,612,44,28,family='PolsQStrong')
        box(s,20,84,664,2,'green')
        label(s,'» Oglądany kanał',24,100,656,28,20,'muted')
        n=source(s,'menu',20,144,664,672,render='Listbox',selectionPixmap='PolsQ/assets/history-selected.png',selectionZoom='0',**LIST)
        templated(n,history_template())
        for key,x in (('red',24),('green',352)):
            source(s,f'key_{key}',x,836,4,18,render='FixedLabel',text=' ',backgroundColor="nativeGreen" if key=="green" else key,transparent='0',
                conditional=f'key_{key}',converts=[('ConditionalShowHide',None)])
            source(s,f'key_{key}',x+16,826,296,36,22,noWrap='1',valign='center',conditional=f'key_{key}',converts=[('ConditionalShowHide',None)])
        label(s,'↑ ↓ — wybierz     OK — przełącz',24,876,656,28,22,'muted')

    for name in ('SimpleChannelSelection','SlimChannelSelection'):
        s=screen(name); compact_header(s,'WYBIERZ KANAŁ / BUKIET'); footer(s,margin=40)
        widget(s,'list',40,168,1840,760,serviceNameFont='PolsQText;28',serviceInfoFont='PolsQText;23',serviceNumberFont='PolsQText;24',serviceItemHeight='76',**LIST)

    for name in ('BouquetSelector','EPGBouquetSelector'):
        s=screen(name); compact_header(s,'WYBÓR BUKIETU'); footer(s,('red','green'),margin=40)
        widget(s,'menu',40,168,1136,760,30,itemHeight='76',**LIST)
        box(s,1200,168,2,760)
        add(s,'ePixmap',position='1264,196',size='40,40',pixmap='PolsQ/assets/line-bouquet.png',alphatest='blend',scale='1')
        label(s,'TWOJE KANAŁY',1324,190,556,56,32,'green')
        label(s,'Wybierz bukiet z listy.\n\nOK — otwórz\nEXIT — wróć',1264,288,616,300,28,'muted')

    epg_attrs=dict(ServiceFontGraphical='PolsQText;26',EntryFontGraphical='PolsQText;26',ServiceFontInfobar='PolsQText;26',
        EventFontInfobar='PolsQText;28',EventFontSingle='PolsQText;30',EventFontMulti='PolsQText;29',EventFontVertical='PolsQText;26',
        TimeFontVertical='PolsQText;23',ServiceForegroundColor='white',ServiceForegroundColorNow='green',ServiceBackgroundColor='panel',
        ServiceBackgroundColorNow='panel',EntryForegroundColor='white',EntryForegroundColorSelected='white',EntryBackgroundColor='panel',
        EntryBackgroundColorSelected='selected',EntryBackgroundColorNow='now',EntryBackgroundColorNowSelected='selected',
        EntryForegroundColorNow='white',EntryForegroundColorNowSelected='white',EntryBackgroundColorPast='bg',
        EntryBackgroundColorPastSelected='selected',EntryForegroundColorPast='muted',EntryForegroundColorPastSelected='white',
        EntryBorderColor='bg',ServiceBorderColor='bg',ServiceBorderWidth='2',EventBorderWidth='2',EventNamePadding='12',
        ServiceNamePadding='12',RecordForegroundColor='bg',RecordForegroundColorSelected='bg',RecordBackgroundColor='red',
        RecordBackgroundColorSelected='red',ZapForegroundColor='bg',ZapBackgroundColor='blue',ZapForegroundColorSelected='bg',ZapBackgroundColorSelected='green')
    for name in ('EPGSelection','QuickEPG','EPGSelectionMulti','GraphicalEPG','GraphicalEPGPIG','GraphicalInfoBarEPG'):
        s=screen(name); header(s,'PROGRAM TV'); footer(s)
        graph=name.startswith('Graphical')
        pig=name=='GraphicalEPGPIG'
        multi=name=='EPGSelectionMulti'
        if graph:
            event(s,'Event',64,218,1200 if pig else 1792,desc=False)
            if pig:
                source(s,'session.VideoPicture',1376,208,480,270,render='Pig',backgroundColor='transparent',zPosition='2')
            y=506 if pig else 366
            height=420 if pig else 560
            widget(s,'timeline_text',64,y-46,1792,46,TimelineFont='PolsQText;26',itemHeight='46',foregroundColor='muted',backgroundColor='bg')
            widget(s,'list',64,y,1792,height,NumberOfRows='6' if pig else '8',**epg_attrs,**LIST)
            widget(s,'lab1',64,y,1792,height,32,halign='center',valign='center',backgroundColor='bg',zPosition='5')
            for i in range(6):
                widget(s,f'timeline{i}',64,y,2,height,pixmap='PolsQ/assets/timeline.png',scale='1',zPosition='2')
            widget(s,'timeline_now',64,y,4,height,pixmap='PolsQ/assets/timeline-now.png',scale='1',zPosition='3')
            widget(s,'bouquetlist',64,y,720,height,30,itemHeight='70',zPosition='4',**LIST)
        else:
            if multi:
                for i,part in enumerate(('now','next','more')):
                    widget(s,part+'_button',64+i*240,216,224,48,pixmap='PolsQ/epg/OtherEvent.png')
                    widget(s,part+'_button_sel',64+i*240,216,224,48,pixmap='PolsQ/epg/SelectedEvent.png',zPosition='1')
                    widget(s,part+'_text',76+i*240,222,200,40,25,transparent='1',zPosition='2',halign='center')
                widget(s,'date',1440,216,416,48,26,halign='right',transparent='1')
            else:
                source(s,'Service',64,216,1792,54,32,'green',converts=[('ServiceName','Name')],noWrap='1')
            widget(s,'list',64,300,1160,616,NumberOfRows='8',**epg_attrs,**LIST)
            widget(s,'lab1',64,300,1160,616,30,backgroundColor='bg',halign='center',valign='center',zPosition='5')
            picon(s,'Service',1312,280)
            event(s,'Event',1312,456,544)
            if multi:
                widget(s,'bouquetlist',64,300,720,616,30,itemHeight='70',zPosition='4',**LIST)
        widget(s,'number',1660,214,196,48,30,foregroundColor='green',halign='right',transparent='1',zPosition='6',conditional='number')
        label(s,'Zielona linia — teraz   •   Zegar — timer   •   Czerwony — timer nagrania',64,936,1792,30,22,'muted')

    for name in ('EPGvertical','EPGverticalPIG'):
        s=screen(name); header(s,'PROGRAM TV / UKŁAD PIONOWY'); footer(s)
        pig=name.endswith('PIG'); count=3 if pig else 5
        width=416 if pig else 344
        for i in range(1,count+1):
            x=64+(i-1)*(width+16)
            picon(s,f'piconCh{i}',x,230,132,80)
            widget(s,f'currCh{i}',x+144,240,width-144,54,24,transparent='1')
            widget(s,f'Active{i}',x,322,width,4,backgroundColor='green')
            widget(s,f'list{i}',x,344,width,434,NumberOfRows='6',**epg_attrs,**LIST)
        widget(s,'list',64,212,1,1,scrollbarMode='showNever')
        widget(s,'bouquetlist',64,344,720,434,30,itemHeight='62',zPosition='4',**LIST)
        widget(s,'lab1',64,344,1280 if pig else 1792,434,32,backgroundColor='bg',zPosition='5',halign='center',valign='center')
        source(s,'Event',64,814,1792,50,30,converts=[('EventName','Name')],noWrap='1')
        source(s,'Event',64,878,1792,72,25,'muted',converts=[('EventName','ExtendedDescription')])
        if pig:
            source(s,'session.VideoPicture',1440,230,416,234,render='Pig',backgroundColor='transparent',zPosition='2')

    for name in ('EventView','InfoBarEventView'):
        margin=EVENT_MARGIN; width=1920-2*margin
        s=screen(name); header(s,'INFORMACJE O AUDYCJI',margin=margin); footer(s,margin=margin)
        widget(s,'channel',margin,224,width,54,32,foregroundColor='green',transparent='1')
        widget(s,'datetime',margin,298,width-448,44,26,foregroundColor='muted',transparent='1')
        widget(s,'duration',1920-margin-416,298,416,44,26,foregroundColor='muted',transparent='1',halign='right')
        widget(s,'epg_description',margin,388,width,550,32,transparent='1')

    s=screen('Setup'); header(s,'USTAWIENIA'); footer(s)
    widget(s,'config',64,236,1248,640,30,itemHeight='64',**LIST)
    box(s,1344,236,2,640)
    widget(s,'description',1392,246,464,550,28,foregroundColor='muted',transparent='1')
    widget(s,'footnote',1392,818,464,108,26,foregroundColor='yellow',transparent='1')
    label(s,'← →  Zmień wartość     OK  Wybierz     EXIT  Powrót',64,916,1248,42,24,'muted')
    widget(s,'HelpWindow',64,240,1,1,conditional='HelpWindow',transparent='1')

    s=screen('PolsQSettings');header(s,'WYGLĄD I CZYTELNOŚĆ');footer(s,('red','green'))
    widget(s,'config',64,236,1120,560,30,itemHeight='80',**LIST)
    box(s,1216,236,2,688)
    widget(s,'description',1256,246,600,420,28,foregroundColor='muted',transparent='1')
    widget(s,'footnote',1256,716,600,172,26,foregroundColor='yellow',transparent='1')
    label(s,'← →  Zmień wariant     Zielony — zapisz     EXIT — anuluj',64,916,1120,42,24,'muted')
    widget(s,'HelpWindow',64,240,1,1,conditional='HelpWindow',transparent='1')

    # Setup derives its preferred name from the subclass before trying generic
    # Setup. SkinSelection.layoutFinished also requires a real preview instance.
    for name in ('SkinSelection','setup_Skin','SetupSkin'):
        s=screen(name); header(s,'SKÓRKI / INTERFEJS'); footer(s,('red','green'))
        widget(s,'config',64,236,1120,576,30,itemHeight='64',**LIST)
        box(s,1216,236,2,716)
        label(s,'PODGLĄD SKÓRKI',1248,214,608,30,20,'muted')
        box(s,1248,260,608,342,'panel',zPosition='0')
        label(s,'Podgląd skórki\nWybierz pozycję Skórka GUI',1280,382,544,100,26,'muted',halign='center',zPosition='0')
        widget(s,'preview',1248,260,608,342,conditional='preview',alphatest='blend',scale='1',zPosition='1')
        widget(s,'description',1248,628,608,198,26,foregroundColor='muted',transparent='1')
        widget(s,'footnote',1248,848,608,104,24,foregroundColor='yellow',transparent='1')
        label(s,'← →  Zmień wartość     OK  Wybierz\nZielony — zapisz. Restart GUI, jeśli system o niego poprosi.',64,864,1120,88,24,'muted')
        widget(s,'HelpWindow',64,240,1,1,conditional='HelpWindow',transparent='1')

    for name in ('ChoiceBox','ChannelContextMenu'):
        s=screen(name); header(s,'WYBÓR' if name=='ChoiceBox' else 'OPCJE')
        if name=='ChoiceBox':
            widget(s,'text',64,216,1792,64,30,transparent='1')
            widget(s,'list',64,304,1792,576,30,itemHeight='72',**LIST)
            box(s,64,974,1792,2)
            label(s,'↑ ↓  Wybierz     OK  Zatwierdź     EXIT  Powrót',64,1000,1792,48,25,'muted')
        else:
            footer(s)
            widget(s,'menu',64,236,1792,648,30,itemHeight='72',**LIST)

    for name in ('MessageBox','MessageBoxSimple','MessageBoxModal'):
        s=screen(name,pos=(320,200),size=(1280,680))
        box(s,0,0,1280,4,'green')
        source(s,'Title',40,32,1200,58,36)
        widget(s,'icon',40,132,80,80,pixmaps=','.join('PolsQ/assets/'+x+'.png' for x in ('question','info','warning','error','message')),conditional='icon',alphatest='blend',scale='1')
        widget(s,'text',160,132,1080,344,30,transparent='1')
        widget(s,'list',40,508,1200,128,30,itemHeight='64',**LIST)

    for name in ('MovieSelection','MovieSelectionSlim'):
        s=screen(name); header(s,'NAGRANIA'); footer(s)
        widget(s,'list',64,236,1160,650,30,**LIST)
        widget(s,'waitingtext',64,236,1160,650,32,halign='center',valign='center',backgroundColor='bg',zPosition='5')
        widget(s,'chosenletter',64,236,1160,650,80,halign='center',valign='center',foregroundColor='green',transparent='1',zPosition='6')
        # OpenATV odwołuje się do instance DescriptionBorder przy zmianie trybu opisu.
        # Wąska niewidoczna ramka zachowuje wymagany obiekt bez panelu pod listą.
        widget(s,'DescriptionBorder',64,236,1,1,pixmap='PolsQ/assets/state.png',alphatest='blend')
        source(s,'Service',1312,236,544,140,32,converts=[('MovieInfo','ShortDescription')])
        source(s,'Service',1312,412,544,50,26,'green',converts=[('MovieInfo','RecordServiceName')])
        source(s,'Service',1312,508,544,340,27,'muted',converts=[('EventName','ExtendedDescription')])
        widget(s,'freeDiskSpace',64,916,1792,40,25,foregroundColor='muted',transparent='1',halign='right')
        for i,key in enumerate(('movie_sort','movie_off')):
            widget(s,key,64+i*48,916,32,32,pixmaps=','.join(['PolsQ/assets/state.png']*10),alphatest='blend')

    for name in ('TimerOverview','RecordTimerOverview','TimerEditList','ConflictTimerOverview','TimerSanityConflict'):
        conflict='Conflict' in name
        s=screen(name); header(s,'KONFLIKT NAGRAŃ' if conflict else 'ZAPLANOWANE NAGRANIA'); footer(s)
        if conflict:label(s,'Nagrania nakładają się. Wybierz timer, aby zmienić czas lub go wyłączyć.',64,214,1792,58,28,'yellow')
        widget(s,'timerlist',64,292 if conflict else 236,1792,384 if conflict else 512,itemHeight='128',topHeight='44',bottomHeight='36',timerNameFont='PolsQText;32',detailFont='PolsQText;25',statusFont='PolsQText;25',**LIST)
        widget(s,'description',64,830,1792,116,28,foregroundColor='muted',transparent='1')

    for name in ('PluginBrowserList','PluginBrowserGrid'):
        s=screen(name); header(s,'WTYCZKI'); footer(s)
        grid=name.endswith('Grid'); key='pluginGrid' if grid else 'pluginList'
        y,height=(232,684) if grid else (236,600)
        n=source(s,key,64,y,1792,height,render='Listbox',listOrientation='grid' if grid else 'vertical',**LIST)
        tpl='[MultiContentEntryPixmapAlphaBlend(pos=(24,12),size=(100,60),png=3,flags=BT_SCALE|BT_KEEP_ASPECT_RATIO),MultiContentEntryText(pos=(156,4),size=(1580,42),font=0,flags=RT_HALIGN_LEFT|RT_VALIGN_CENTER,text=1),MultiContentEntryText(pos=(156,48),size=(1580,40),font=1,text=2)]'
        if grid:
            tpl='[MultiContentEntryRectangle(pos=(8,8),size=(432,212),backgroundColor=0x0018284e,backgroundColorSelected=0x000759ad,borderWidth=2,borderColor=0x00304a72,borderColorSelected=0x0046baff),MultiContentEntryPixmapAlphaBlend(pos=(148,24),size=(152,84),png=3,flags=BT_SCALE|BT_KEEP_ASPECT_RATIO),MultiContentEntryText(pos=(24,130),size=(400,76),font=0,flags=RT_HALIGN_CENTER|RT_VALIGN_CENTER|RT_WRAP,text=1)]'
        templated(n,'{"template":'+tpl+',"fonts":[gFont("PolsQText",30),gFont("PolsQText",24)],"itemHeight":'+('228,"itemWidth":448}' if grid else '100}'))
        widget(s,'quickselect',64,y,1792,height,80,halign='center',valign='center',transparent='1',foregroundColor='green',zPosition='5')
        if grid:
            widget(s,'description',64,928,1792,36,24,foregroundColor='muted',transparent='1',noWrap='1')
        else:
            widget(s,'description',64,860,1792,90,27,foregroundColor='muted',transparent='1')

    s=screen('AudioSelection'); header(s,'DŹWIĘK I NAPISY')
    widget(s,'config',112,236,1744,224,30,itemHeight='56',**LIST)
    widget(s,'switchdescription',64,484,1792,50,27,foregroundColor='muted',transparent='1')
    for i,key in enumerate(('red','green','yellow','blue')):
        source(s,'key_'+key,64,244+i*56,30,40,24,key,render='FixedLabel',text='●',converts=[('ConditionalShowHide',None)])
    entries='[MultiContentEntryText(pos=(20,0),size=(90,64),font=0,flags=RT_VALIGN_CENTER,text=2),MultiContentEntryText(pos=(130,0),size=(560,64),font=0,flags=RT_VALIGN_CENTER,text=3),MultiContentEntryText(pos=(720,0),size=(860,64),font=0,flags=RT_VALIGN_CENTER,text=4),MultiContentEntryText(pos=(1640,0),size=(100,64),font=0,flags=RT_VALIGN_CENTER,text=5)]'
    n=source(s,'streams',64,560,1792,384,render='Listbox',**LIST)
    templated(n,'{"fonts":[gFont("PolsQText",30)],"templates":{"default":(64,'+entries+',True,"showOnDemand"),"notselected":(64,'+entries+',False,"showOnDemand")}}')
    for i,key in enumerate(('key_left','key_right')):
        widget(s,key,64+i*40,484,24,24,pixmap='PolsQ/assets/state.png',alphatest='blend')
    s=screen('QuickSubtitlesConfigMenu'); header(s,'USTAWIENIA NAPISÓW')
    widget(s,'config',64,236,1792,616,30,itemHeight='56',**LIST)
    widget(s,'videofps',64,890,1792,48,26,foregroundColor='muted',transparent='1')

    s=screen('FileCommander');header(s,'MENEDŻER PLIKÓW');footer(s)
    box(s,960,216,2,700)
    for side,x,title in (('left',64,'LEWY PANEL'),('right',992,'PRAWY PANEL')):
        label(s,title,x,216,864,32,22,'muted')
        heading=dict(LIST);heading['backgroundColor']='panel'
        n=source(s,'head'+side,x,252,864,96,render='Listbox',selection='0',**heading)
        templated(n,'{"fonts":[gFont("PolsQText",28),gFont("PolsQText",22)],"itemHeight":96,"selectionEnabled":False,"template":['
            'MultiContentEntryText(pos=(16,0),size=(832,44),font=0,flags=RT_HALIGN_LEFT|RT_VALIGN_CENTER|RT_ELLIPSIS,text=17),'
            'MultiContentEntryText(pos=(16,60),size=(176,32),font=1,flags=RT_HALIGN_LEFT|RT_VALIGN_CENTER,text=1,color=0x00b1c4e5),'
            'MultiContentEntryText(pos=(212,60),size=(156,32),font=1,flags=RT_HALIGN_RIGHT|RT_VALIGN_CENTER|RT_ELLIPSIS,text=11,color=0x00b1c4e5),'
            'MultiContentEntryText(pos=(396,60),size=(452,32),font=1,flags=RT_HALIGN_RIGHT|RT_VALIGN_CENTER|RT_ELLIPSIS,text=13,color=0x00b1c4e5)]}')
        widget(s,'list'+side,x,368,864,512,28,itemHeight='64',**LIST)
        widget(s,'sort'+side,x,888,864,28,21,foregroundColor='muted',transparent='1',noWrap='1')
    widget(s,'quickselect',64,368,864,512,64,halign='center',valign='center',foregroundColor='green',transparent='1',zPosition='5')
    # Native FileCommander moves QuickSelect to whichever panel has focus.
    widget(s,'status',64,884,1792,40,25,foregroundColor='white',backgroundColor='panel',valign='center',halign='center',zPosition='6')
    label(s,'← →  Zmień panel     OK  Otwórz',64,932,864,32,22,'muted')
    for key,x,w,text in (('menu',1056,256,'MENU  Operacje'),('info',1336,240,'INFO  Zadania'),('help',1600,256,'HELP  Pomoc')):
        source(s,'key_'+key,x,928,w,36,22,'muted',render='FixedLabel',text=text,conditional='key_'+key,converts=[('ConditionalShowHide',None)])

    s=screen('FileCommanderContextMenu');header(s,'OPERACJE NA PLIKACH');footer(s,())
    widget(s,'menu',64,236,1792,504,30,itemHeight='72',**LIST)
    widget(s,'description',64,776,1792,140,28,foregroundColor='muted',transparent='1')
    label(s,'↑ ↓  Wybierz     OK  Zatwierdź     EXIT  Powrót',64,1000,1420,48,25,'muted')
    source(s,'key_menu',1600,1000,256,48,25,'muted',conditional='key_menu',converts=[('ConditionalShowHide',None)])

    s=screen('FileCommanderData');header(s,'INFORMACJE O PLIKU');footer(s)
    widget(s,'data',64,236,1792,680,28,transparent='1',splitPosition='560')
    label(s,'↑ ↓  Przewiń     EXIT  Powrót',64,930,1792,32,22,'muted')

    for name in ('FileCommanderFileViewer','FileCommanderTextEditor'):
        s=screen(name);header(s,'PODGLĄD PLIKU' if name.endswith('Viewer') else 'EDYTOR TEKSTU');footer(s)
        widget(s,'path',64,224,1456,48,26,foregroundColor='muted',transparent='1',noWrap='1')
        if name.endswith('Editor'):
            widget(s,'location',1550,224,306,48,24,foregroundColor='muted',transparent='1',halign='right')
            data=widget(s,'data',64,292,1792,640,26,itemHeight='40',**LIST)
        else:
            data=widget(s,'data',64,292,1792,640,26,transparent='1')
        data.set('font','PolsQMono;26')

    s=screen('IpkgInstaller');header(s,'PAKIETY LOKALNE');footer(s)
    label(s,'WYBIERZ PAKIETY DO INSTALACJI',64,216,1792,38,22,'muted')
    widget(s,'list',64,276,1792,576,30,itemHeight='72',**LIST)
    source(s,'introduction',64,884,1792,64,27,'muted')

    s=screen('Opkg');header(s,'INSTALACJA OPROGRAMOWANIA');footer(s,('red','blue'))
    widget(s,'status',64,236,1792,110,32,foregroundColor='white',transparent='1')
    widget(s,'package',64,378,1792,86,28,foregroundColor='muted',transparent='1')
    widget(s,'activityslider',64,506,1792,6,foregroundColor='green',backgroundColor='line',borderWidth='0')
    widget(s,'slider',64,546,1792,12,foregroundColor='green',backgroundColor='line',borderWidth='0')
    # Native Opkg toggles status/package/sliders off before showing this log.
    # Its initially empty, transparent text must not cover the status widgets.
    widget(s,'log',64,236,1792,680,26,transparent='1')
    label(s,'Po zakończeniu: czerwony — zamknij, niebieski — dziennik. Błąd: sprawdź szczegóły w dzienniku.',64,930,1792,32,22,'muted')

    for name in ('PackageAction','PluginAction'):
        s=screen(name);header(s,'WTYCZKI I PAKIETY');footer(s)
        n=source(s,'plugins',64,236,1792,616,render='Listbox',**LIST)
        templated(n,'{"fonts":[gFont("PolsQText",32),gFont("PolsQText",30),gFont("PolsQText",24)],"itemHeight":88,"template":['
            'MultiContentEntryPixmapAlphaBlend(pos=(12,20),size=(56,48),png=6,flags=BT_SCALE|BT_KEEP_ASPECT_RATIO),'
            'MultiContentEntryText(pos=(92,0),size=(1608,88),font=0,flags=RT_HALIGN_LEFT|RT_VALIGN_CENTER|RT_ELLIPSIS,text=2),'
            'MultiContentEntryText(pos=(92,6),size=(1232,40),font=1,flags=RT_HALIGN_LEFT|RT_VALIGN_CENTER|RT_ELLIPSIS,text=3),'
            'MultiContentEntryText(pos=(1360,8),size=(312,36),font=2,flags=RT_HALIGN_RIGHT|RT_VALIGN_CENTER|RT_ELLIPSIS,text=5),'
            'MultiContentEntryText(pos=(92,48),size=(1580,32),font=2,flags=RT_HALIGN_LEFT|RT_VALIGN_CENTER|RT_ELLIPSIS,text=4,color=0x00b1c4e5,color_sel=0x00f3f6fa),'
            'MultiContentEntryPixmapAlphaBlend(pos=(1720,20),size=(48,48),png=7,flags=BT_SCALE|BT_KEEP_ASPECT_RATIO)]}')
        widget(s,'description',64,880,1792,72,27,foregroundColor='muted',transparent='1')
        widget(s,'quickselect',64,236,1792,616,70,halign='center',valign='center',transparent='1',foregroundColor='green',zPosition='5')

    for name in ('Console','PackageActionLog','PluginActionLog'):
        s=screen(name);header(s,'DZIENNIK OPERACJI');footer(s,('red','green','yellow') if name=='Console' else ('red',))
        widget(s,'text' if name=='Console' else 'log',64,236,1792,680,26,transparent='1')
        label(s,'↑ ↓  Przewiń     EXIT  Powrót',64,930,1792,32,22,'muted')

    # ProcessingScreen resizes the description and dialog at runtime. Keep all
    # fixed content above the description; no decoration follows the growing text.
    s=screen('Processing',pos=(464,438),size=(992,204),bg='panel');s.set('zPosition','99')
    label(s,'POLS Q',32,22,180,34,24,family='PolsQStrong')
    source(s,'Title',230,22,730,34,23,'muted',noWrap='1')
    widget(s,'progress',32,76,928,6,foregroundColor='green',backgroundColor='line',borderWidth='0')
    widget(s,'description',32,110,928,48,28,transparent='1')

    s=screen('InfoBar',pos=(0,726),size=(1920,354),bg='overlay')
    box(s,64,0,1792,4,'green'); picon(s,'session.CurrentService',64,34)
    source(s,'session.CurrentService',320,30,1190,60,36,converts=[('ServiceName','Name')],noWrap='1')
    source(s,'global.CurrentTime',1570,30,286,60,36,halign='right',converts=[('ClockToText','Default')])
    label(s,'TERAZ',320,112,104,40,24,'green')
    source(s,'session.Event_Now',440,108,140,44,28,converts=[('EventTime','StartTime'),('ClockToText','Default')])
    source(s,'session.Event_Now',600,104,1256,52,32,converts=[('EventName','Name')],noWrap='1')
    source(s,'session.Event_Now',320,174,1536,6,render='Progress',color='green',converts=[('EventTime','Progress')],backgroundColor='track',borderWidth='0')
    label(s,'POTEM',320,216,104,40,24,'muted')
    source(s,'session.Event_Next',440,212,140,44,28,'muted',converts=[('EventTime','StartTime'),('ClockToText','Default')])
    source(s,'session.Event_Next',600,210,1256,50,30,'muted',converts=[('EventName','Name')],noWrap='1')
    source(s,'session.RecordState',64,290,240,38,24,'red',render='FixedLabel',text='● REC',converts=[('ConditionalShowHide',None)])
    source(s,'session.Event_Now',1396,290,460,38,24,'muted',halign='right',converts=[('PolsQEventRemaining','')])

    s=screen('SecondInfoBar',pos=(0,576),size=(1920,504),bg='overlay')
    box(s,64,0,1792,4,'green'); picon(s,'session.CurrentService',64,34)
    source(s,'session.CurrentService',320,34,1536,56,36,'green',converts=[('ServiceName','Name')])
    event(s,'session.Event_Now',320,120,1536)

    s=screen('MoviePlayer',pos=(0,786),size=(1920,294),bg='overlay')
    box(s,64,0,1792,4,'green'); label(s,'ODTWARZANIE NAGRANIA',64,30,1792,42,26,'green')
    source(s,'session.CurrentService',64,100,1792,64,38,converts=[('ServiceName','Name')],noWrap='1')
    source(s,'session.CurrentService',64,208,230,48,28,converts=[('ServicePosition','Position')])
    source(s,'session.CurrentService',330,230,1180,6,render='Progress',color='green',backgroundColor='track',borderWidth='0',converts=[('ServicePosition','Position')])
    source(s,'session.CurrentService',1550,208,306,48,28,'muted',halign='right',converts=[('ServicePosition','Remaining,Negate')])
    widget(s,'state',1200,30,400,42,26,foregroundColor='green',transparent='1')
    widget(s,'speed',1640,30,216,42,26,transparent='1',halign='right')
    widget(s,'statusicon',0,0,1,1,pixmaps=','.join(['PolsQ/assets/state.png']*7),alphatest='blend')

    for name in ('PVRState','TimeshiftState'):
        s=screen(name,pos=(64,62),size=(540,212) if name=='TimeshiftState' else (540,176))
        widget(s,'state',24,18,320,62,34,foregroundColor='green',transparent='1')
        widget(s,'speed',366,18,150,62,30,transparent='1',halign='right')
        widget(s,'statusicon',0,0,1,1,pixmaps=','.join(['PolsQ/assets/state.png']*7),alphatest='blend')
        widget(s,'eventname',24,120,492,44,24,foregroundColor='muted',transparent='1')
        if name=='TimeshiftState':
            label(s,'TIMESHIFT',24,10,492,30,22,'muted')
            s.find("widget[@name='state']").set('position','24,44')
            s.find("widget[@name='speed']").set('position','366,44')
            s.find("widget[@name='eventname']").set('position','24,160')
            widget(s,'PTSSeekBack',24,138,492,6,pixmap='PolsQ/assets/timeline.png',scale='1')
            widget(s,'PTSSeekPointer',24,132,4,18,pixmap='PolsQ/assets/timeline-now.png',scale='1',zPosition='2')

    s=screen('NumberZap',pos=(1200,70),size=(656,164))
    box(s,0,0,6,164,'green')
    widget(s,'number',30,14,160,58,40,foregroundColor='green',transparent='1')
    widget(s,'servicename',30,88,596,50,28,transparent='1')
    s=screen('Volume',pos=(1356,70),size=(500,110))
    label(s,'GŁOŚNOŚĆ',28,16,444,36,24)
    widget(s,'Volume',28,74,444,8,foregroundColor='green',backgroundColor='line',borderWidth='0')
    s=screen('Mute',pos=(1496,70),size=(360,86))
    box(s,0,0,6,86,'green'); label(s,'WYCISZONO',30,22,300,44,28)
    from skin_effects import modernize_bars
    modernize_bars(skin)
    E.indent(skin,space='  ')
    (ROOT/'PolsQ/skin.xml').write_bytes(b'<?xml version="1.0" encoding="UTF-8"?>\n'+E.tostring(skin,encoding='utf-8')+b'\n')
    from ui_profiles import write_variants
    write_variants(ROOT,skin)
    print(f'Generated {len(skin.findall("screen"))} OpenATV screens')


if __name__=='__main__':
    build()

