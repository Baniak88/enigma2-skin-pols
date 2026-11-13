#!/usr/bin/env python3
"""Małe autorskie PNG bez zewnętrznych bibliotek i bez logotypów operatorów."""
from pathlib import Path
import struct
import zlib
import shutil
import math
from build import VERSION
from skin_effects import FADE_TOP, BODY_ALPHA, BODY_RGB, BAR_HEIGHTS, fade_alpha, event_fade_alpha

ROOT=Path(__file__).resolve().parents[1]/'PolsQ'
BG=(13,19,34,255); PANEL=(21,29,49,255); GREEN=(245,200,66,255)
SELECTED=(38,64,127,255)
WHITE=(245,245,245,255); RED=(255,98,98,255); BLUE=(94,172,255,255)


def png(path,w,h,bg,rects=(),pixels=None):
    pixels=bytearray(bg*(w*h)) if pixels is None else pixels
    for x,y,rw,rh,c in rects:
        for yy in range(max(0,y),min(h,y+rh)):
            for xx in range(max(0,x),min(w,x+rw)):
                pixels[(yy*w+xx)*4:(yy*w+xx)*4+4]=bytes(c)
    def chunk(kind,data):
        return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data)&0xffffffff)
    raw=b''.join(b'\0'+bytes(pixels[y*w*4:(y+1)*w*4]) for y in range(h))
    data=b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',w,h,8,6,0,0,0))+chunk(b'IDAT',zlib.compress(raw,9))+chunk(b'IEND',b'')
    path=ROOT/path; path.parent.mkdir(parents=True,exist_ok=True); path.write_bytes(data)


def line_icon(path,lines,accent=()):
    pixels=bytearray(32*32*4)
    for segments,color in ((lines,(194,204,215,255)),(accent,(194,204,215,255))):
        for points in segments:
            for (ax,ay),(bx,by) in zip(points,points[1:]):
                dx,dy=bx-ax,by-ay
                for y in range(32):
                    for x in range(32):
                        t=max(0,min(1,((x-ax)*dx+(y-ay)*dy)/(dx*dx+dy*dy or 1)))
                        if (x-ax-t*dx)**2+(y-ay-t*dy)**2<=1:
                            pixels[(y*32+x)*4:(y*32+x+1)*4]=bytes(color)
    png(Path(path),32,32,(0,0,0,0),pixels=pixels)


def build():
    # Start from empty asset folders: stale PNGs from older layouts must not
    # end up in the packages.
    for folder in (ROOT/'assets',ROOT.parent/'PolsQLarge/assets'):
        shutil.rmtree(folder,ignore_errors=True)
    (ROOT/'VERSION').write_text(VERSION+'\n')
    # Przezroczyste pole dziedziczy kolor paska/ekranu, bez osobnej ramki i symbolu.
    png(Path('picon_default.png'),220,132,(0,0,0,0))
    # Explicit opaque selection prevents a glossy fallback from the base skin.
    # Native list rows clip the pixmap to their 100/116px item height.
    png(Path('assets/channel-selected.png'),1136,76,SELECTED)
    png(Path('assets/history-selected.png'),664,112,SELECTED)
    # Single-column gradients are stretched natively; no blur shader or timer.
    for name,height in BAR_HEIGHTS.items():
        total=height+FADE_TOP
        # Full width: the bar is blitted 1:1 instead of stretched from 1 px.
        pixels=bytearray(c for y in range(total) for c in (*BODY_RGB,fade_alpha(y))*1920)
        png(Path('assets')/(name.lower()+'-fade.png'),1920,total,(0,0,0,0),pixels=pixels)
    event_pixels=bytearray(c for x in range(1920) for c in (*BODY_RGB,event_fade_alpha(x)))
    png(Path('assets/eventview-fade.png'),1920,1080,(0,0,0,0),pixels=event_pixels*1080)
    width=1792
    accent=bytearray()
    glow=bytearray()
    for y in range(18):
        vertical=max(0,1-abs(y-9)/9)**2
        for x in range(width):
            envelope=min(1,x/160,(width-1-x)/160)
            glow.extend((255,255,255,0))
    for y in range(2):
        for x in range(width):
            envelope=min(1,x/160,(width-1-x)/160)
            accent.extend((255,255,255,round(56*max(0,envelope))))
    png(Path('assets/accent-fade.png'),width,2,(0,0,0,0),pixels=accent)
    png(Path('assets/accent-glow.png'),width,18,(0,0,0,0),pixels=glow)
    badge=bytearray()
    for y in range(48):
        for x in range(128):
            dx=max(8-x,0,x-119);dy=max(8-y,0,y-39)
            badge.extend((255,214,10,26 if dx*dx+dy*dy<=64 else 0))
    png(Path('assets/now-badge.png'),128,48,(0,0,0,0),pixels=badge)
    # Checkbox graphics used by the native SelectionList in the IPK installer.
    edge=[(2,2,28,2,WHITE),(2,28,28,2,WHITE),(2,2,2,28,WHITE),(28,2,2,28,WHITE)]
    png(Path('icons/lock_off.png'),32,32,(0,0,0,0),edge)
    png(Path('icons/lock_on.png'),32,32,(0,0,0,0),edge+[(7,7,18,18,GREEN)])
    # FileList resolves these through the active skin before system fallbacks.
    folder=[(8,18,48,4,WHITE),(8,50,48,4,WHITE),(8,18,4,36,WHITE),(52,18,4,36,WHITE),(12,10,20,8,GREEN)]
    for name in ('directory','current','parent'):
        png(Path('extensions')/(name+'.png'),64,64,(0,0,0,0),folder)
    png(Path('extensions/storage.png'),64,64,(0,0,0,0),[(8,12,48,4,WHITE),(8,48,48,4,WHITE),(8,12,4,40,WHITE),(52,12,4,40,WHITE),(16,38,8,4,GREEN)])
    document=[(14,6,36,4,WHITE),(14,54,36,4,WHITE),(14,6,4,52,WHITE),(46,6,4,52,WHITE),(22,20,20,4,GREEN),(22,32,20,4,WHITE)]
    for name in ('file','ipk','cfg','txt','log'):
        png(Path('extensions')/(name+'.png'),64,64,(0,0,0,0),document)
    for name,c in [('timeline',PANEL),('timeline-now',GREEN),('state',GREEN)]:
        png(Path('assets')/(name+'.png'),4,4,c)
    for name,c in [('question',GREEN),('info',BLUE),('warning',(245,206,85,255)),('error',RED),('message',WHITE)]:
        png(Path('assets')/(name+'.png'),80,80,PANEL,[(35,15,10,34,c),(35,58,10,10,c)])
    normal=['CurrentEvent','OtherEvent','CurrentService','OtherService','TimeLineDate','TimeLineTime']
    selected=['SelectedCurrentEvent','SelectedEvent','SelectedZapEvent']
    for name in normal+selected+['RecordEvent','SelectedRecordEvent','RecordingEvent','ZapEvent']:
        c=SELECTED if name in selected else RED if 'Record' in name else BLUE if name=='ZapEvent' else PANEL
        png(Path('epg')/(name+'.png'),8,8,c)
    for name in ['BorderTop','BorderBottom','BorderLeft','BorderRight','SelectedBorderTop','SelectedBorderBottom','SelectedBorderLeft','SelectedBorderRight']:
        png(Path('epg')/(name+'.png'),2,2,BG)
    for name in ['information','SelectedInformation']:
        png(Path('epg')/(name+'.png'),24,24,PANEL,[(10,4,4,3,GREEN),(10,10,4,10,GREEN)])
    names=['epgclock','epgclock_add','epgclock_pre','epgclock_post','epgclock_prepost','epgclock_selpre','epgclock_selpost','epgclock_selprepost',
        'epgclock_zap','epgclock_zaprec','epgclock_autotimer','epgclock_disabled','epgclock_icetv','epgclock_primetime',
        'timer_autotimer','timer_done','timer_failed','timer_icetv','timer_off','timer_once','timer_prep','timer_rec','timer_rep','timer_wait','timer_zap',
        'folder','trashcan','movie_play','movie_play_rec','part_new','part_unwatched']+[f'part_{i}_4' for i in range(5)]
    for name in names:
        c=RED if any(k in name for k in ('rec','failed')) else BLUE if 'zap' in name else GREEN
        if 'folder' in name:
            rects=[(3,8,26,20,c),(3,4,12,6,c)]
        elif name=='trashcan':
            rects=[(7,10,18,20,c),(4,6,24,3,c)]
        elif name.startswith('part_'):
            part=int(name.split('_')[1]) if name.split('_')[1].isdigit() else 0
            rects=[(2,22,28,6,PANEL),(2,22,int(28*part/4),6,c)]
        else:
            rects=[(2,2,28,2,c),(2,28,28,2,c),(2,2,2,28,c),(28,2,2,28,c),(15,8,2,9,c),(15,15,9,2,c)]
        png(Path('icons')/(name+'.png'),32,32,(0,0,0,0),rects)
    # OpenATV ładuje mainmenu/<key>.png i używa missing.png dla nieznanych wtyczek.
    for i,name in enumerate(['missing','mainmenu','setup','information','timermenu','timer_edit','powertimer_edit','movie_selection','plugin_selection','shutdown','standby','restart','restart_enigma','deep_standby','epg','video_menu','audio_menu','system','user_interface','scan','service_searching','rec','network','hardisk_selection']):
        if name in ('mainmenu','movie_selection','video_menu'):
            rects=[(28,42,144,8,WHITE),(28,128,144,8,WHITE),(28,42,8,94,WHITE),(164,42,8,94,WHITE),(86,148,28,8,GREEN)]
        elif name in ('timermenu','timer_edit','powertimer_edit'):
            rects=[(36,36,128,8,WHITE),(36,156,128,8,WHITE),(36,36,8,128,WHITE),(156,36,8,128,WHITE),(96,56,8,52,GREEN),(96,100,42,8,GREEN)]
        elif name=='epg':
            rects=[(24,36+i*36,152,6,WHITE) for i in range(4)]+[(60,32,6,132,GREEN)]
        else:
            rects=[(42,42,44,44,WHITE),(114,42,44,44,GREEN),(42,114,44,44,GREEN),(114,114,44,44,WHITE)]
        png(Path('mainmenu')/(name+'.png'),200,200,(0,0,0,0),rects)
    # Recording, scheduled timer, zap and disabled timer must not share a glyph.
    for name in names:
        if not name.startswith(('epgclock','timer_')):continue
        disabled='disabled' in name or name.endswith('_off')
        recording='rec' in name or 'epgclock' in name and 'zap' not in name and name=='epgclock'
        c=(150,158,165,255) if disabled else RED if recording else BLUE if 'zap' in name else GREEN
        rects=[]
        for y in range(32):
            for x in range(32):
                d=(x-15)**2+(y-15)**2
                if 110<=d<=155:rects.append((x,y,1,1,c))
                if recording and d<45:rects.append((x,y,1,1,c))
        if disabled:
            rects.extend((i,i,2,2,c) for i in range(8,24))
            rects.extend((31-i,i,2,2,c) for i in range(8,24))
        elif not recording:rects.extend([(14,7,3,10,WHITE),(14,14,9,3,WHITE)])
        png(Path('icons')/(name+'.png'),32,32,(0,0,0,0),rects)
    folder=[[(4,10),(12,10),(15,13),(28,13),(28,26),(4,26),(4,10)]]
    list_lines=[[(9,18),(23,18)],[(9,22),(19,22)]]
    line_icon('assets/line-tv.png', [[(4,7),(28,7),(28,24),(4,24),(4,7)],[(16,24),(16,28)],[(10,28),(22,28)]], [[(23,20),(25,20)]])
    line_icon('assets/line-bouquet.png',folder+list_lines)
    arc=[(16+11*math.cos(t*math.pi/180),16+11*math.sin(t*math.pi/180)) for t in range(-130,191,10)]
    line_icon('assets/line-history.png',[arc,[(16,10),(16,16),(21,19)]],[[(4,10),(4,5),(9,5)]])
    line_icon('icons/folder.png',folder+list_lines)
    line_icon('icons/marker.png',[[(8,4),(24,4),(24,28),(16,22),(8,28),(8,4)]])
    from q_assets import build as build_q_assets, build_menu_icons
    build_q_assets()
    build_menu_icons()
    # Native components also resolve icons relative to the selected skin.
    large=ROOT.parent/'PolsQLarge';large.mkdir(exist_ok=True)
    (large/'VERSION').write_text(VERSION+'\n')
    for folder in (ROOT,large):
        shutil.copyfile(ROOT.parent/'LICENSE',folder/'LICENSE')
        shutil.copyfile(ROOT.parent/'docs/SOURCE.md',folder/'SOURCE.md')
    for path in ROOT.rglob('*.png'):
        dest=large/path.relative_to(ROOT);dest.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(path,dest)
    print('Built shared assets, distinct timer icons and Large variant icons')


if __name__=='__main__':
    build()

