"""Pols Q 0.3: original spatial composition over native OpenATV contracts."""
from copy import deepcopy
import xml.etree.ElementTree as E


def node(s,tag,**a):return E.SubElement(s,tag,{k:str(v) for k,v in a.items()})
# Every PNG is rendered at its exact on-screen size: on set-top boxes a scaled,
# alpha-blended blit is done in software and made screens visibly slow.
def image(s,path,x,y,w,h,z=-10,scale=False,blend=True):
 a=dict(position=f'{x},{y}',size=f'{w},{h}',pixmap='PolsQ/assets/'+path,zPosition=z)
 if scale:a['scale']='1'
 if blend:a['alphatest']='blend'
 return node(s,'ePixmap',**a)
def hero(s,x,y,w,h,z=-10):return image(s,f'q-hero-{w}x{h}.png',x,y,w,h,z)
def wallpaper(s):return image(s,'q-wallpaper.png',0,0,1920,1080,-30,blend=False)
def text(s,value,x,y,w,h,size=28,color='white',bold=False):return node(s,'eLabel',text=value,position=f'{x},{y}',size=f'{w},{h}',font=f'PolsQ{"Strong" if bold else "Text"};{size}',foregroundColor=color,transparent='1')
def src(s,name,x,y,w,h,size=28,converts=(),render='Label',**kw):
 a=dict(source=name,render=render,position=f'{x},{y}',size=f'{w},{h}',foregroundColor='white',transparent='1')
 if render=='Picon':a['backgroundColor']='transparent'
 if render in ('Label','PolsQSummary','FixedLabel'):a['font']=f'PolsQText;{size}'
 a.update(kw)
 if render=='Picon':node(s,'ePixmap',position=a['position'],size=a['size'],pixmap='PolsQ/picon_default.png',scale='1',alphatest='blend',zPosition='0')
 n=node(s,'widget',**a)
 for kind,arg in converts:node(n,'convert',type=kind).text=arg
 return n

# Soft text shadow (#AARRGGBB, 00 = opaque) lifts headlines off glass cards
# and keeps InfoBar titles legible over bright video.
SHADOW=dict(shadowColor='#00030814',shadowOffset='2,2')
def lift(n):
 for k,v in SHADOW.items():n.set(k,v)
 return n

VIDEO_PAD=40
def video_effects(s):
 # Native Pig shows video only through a transparent hole in the OSD. Nothing
 # may be drawn over that rectangle: the shadow ring is cut out in the middle
 # and an explicit transparent label keeps the hole open on every driver.
 for pig in s.findall("widget[@render='Pig']"):
  x,y=map(int,pig.get('position').split(','));w,h=map(int,pig.get('size').split(','))
  image(s,f'q-video-shadow-{w}x{h}.png',x-VIDEO_PAD,y-VIDEO_PAD,w+2*VIDEO_PAD,h+2*VIDEO_PAD,-5)
  node(s,'eLabel',position=f'{x},{y}',size=f'{w},{h}',backgroundColor='transparent',zPosition=1)
  if s.get('name').startswith('ChannelSelection'):
   # Badge sits in the card right under the picture, never on the video.
   bx,by=x+w-172,y+h+20
   image(s,'q-live-badge.png',bx,by,172,40,5)
   lift(text(s,'NA ŻYWO',bx+44,by+5,120,30,19,bold=True)).set('valign','center')
   s[-1].set('zPosition','6')

def place(n,x,y,w,h):n.set('position',f'{x},{y}');n.set('size',f'{w},{h}');return n

# One grid for every full-screen layout: the same 64 px margins as all other
# screens, 24 px between cards, 32 px inside cards. Margins and gaps are
# measured on visible card edges: each card PNG has the same transparent inset
# (12 px left/right, 8 px top, 16 px bottom for the shadow).
M=64;L=M;R=1920-M;W=R-L
G=24;P=32
TITLE_Y,TITLE_H=32,60
TOP=140
KEYS_Y,KEYS_H=1000,40
INSET=(12,8,12,16)
def card(s,x,y,w,h,z=-10):
 # x,y,w,h: the visible card; the PNG includes the transparent inset.
 return hero(s,x-INSET[0],y-INSET[1],w+INSET[0]+INSET[2],h+INSET[1]+INSET[3],z)

KEYS=('key_red','key_green','key_yellow','key_blue')
def keys_row(s,saved=None):
 # Four equal columns across the content width (as on all other screens).
 column=W//4
 nodes=saved if saved is not None else [n for n in s.findall('widget') if n.get('source','').startswith('key_')]
 for n in nodes:
  key=n.get('source');i=KEYS.index(key)
  if n.get('render')=='FixedLabel' and n.get('text')==' ':place(n,L+i*column,KEYS_Y+10,6,20)
  else:
   place(n,L+i*column+22,KEYS_Y,column-34,KEYS_H);n.set('valign','center')
   if n.get('font'):n.set('font','PolsQText;25')
  if saved is not None:s.append(n)
 if saved is not None:
  for key in sorted({n.get('source') for n in saved},key=KEYS.index):
   i=KEYS.index(key)
   src(s,key,L+i*column,KEYS_Y+10,6,20,render='FixedLabel',text=' ',backgroundColor='nativeGreen' if key=='key_green' else key[4:],transparent='0',conditional=key,converts=[('ConditionalShowHide',None)])

def shell(s,section):
 wallpaper(s)
 if section is None:
  # Native screen title, e.g. "Menu główne" or the name of a submenu.
  n=lift(src(s,'Title',L,TITLE_Y,1300,TITLE_H,40,font='PolsQStrong;40',wrap='ellipsis'))
 else:n=lift(text(s,section,L,TITLE_Y,1300,TITLE_H,40,bold=True))
 n.set('valign','center')
 src(s,'global.CurrentTime',R-240,TITLE_Y,240,TITLE_H,32,converts=[('ClockToText','Default')],halign='right',valign='center')

# Shared two-column body for Menu and channel lists: a card with the live
# picture and the programme on the left, a full-height list on the right.
CARD_W=832;CARD_H=768;LIST_W=W-G-CARD_W;ROW=96
def live_card(s,source,name_source,video=True,channel_list=False):
 card(s,L,TOP,CARD_W,CARD_H)
 tx=L+P;tw=CARD_W-2*P;vh=round(tw*9/16)
 if video:src(s,'session.VideoPicture',tx,TOP+P,tw,vh,render='Pig',backgroundColor='transparent',zPosition='2')
 else:
  src(s,source,L+(CARD_W-304)//2,TOP+P+(vh-172)//2-24,304,172,render='Picon',converts=[('ServiceName','Reference')],alphatest='blend',zPosition='2')
  text(s,'TWÓJ KANAŁ',tx,TOP+P+vh-60,tw,50,32,'green').set('halign','center')
 y=TOP+P+vh+20
 src(s,name_source,tx,y+4,tw-196 if video else tw,40,28,converts=[('ServiceName','Name')],foregroundColor='green',wrap='ellipsis')
 lift(src(s,source,tx,y+48,tw,84,34,render='PolsQSummary',converts=[('EventName','Name')]))
 src(s,source,tx,y+140,128,36,24,converts=[('EventTime','StartTime'),('ClockToText','Default')])
 src(s,source,tx+132,y+140,168,36,24,converts=[('EventTime','EndTime'),('ClockToText','Format:– %H:%M')],foregroundColor='muted')
 src(s,source,tx+tw-352,y+140,352,36,23,converts=[('PolsQEventRemaining','')],halign='right',foregroundColor='muted')
 src(s,source,tx,y+186,tw,6,render='Progress',backgroundColor='line',foregroundColor='green',borderWidth='0',converts=[('EventTime','Progress')])
 src(s,source,tx,y+202,tw,TOP+CARD_H-P-(y+202),23,render='PolsQSummary',converts=[('EventName','ExtendedDescription')],foregroundColor='muted')
 if video and not channel_list:
  # Same badge as on the channel list, under the picture.
  bx,by=tx+tw-172,TOP+P+vh+20
  image(s,'q-live-badge.png',bx,by,172,40,5)
  lift(text(s,'NA ŻYWO',bx+44,by+5,120,30,19,bold=True)).set('valign','center')
  s[-1].set('zPosition','6')

def menu(s,large):
 # A vertical list: the standard OpenATV Menu only moves up/down, so a grid
 # left items in other columns (e.g. Plugins) unreachable with the remote.
 saved={n.get('name') or n.get('source'):deepcopy(n) for n in s.findall('widget')}
 s[:]=[];shell(s,None)
 live_card(s,'session.Event_Now','session.CurrentService')
 n=saved['menu'];place(n,R-LIST_W,TOP,LIST_W,CARD_H)
 for k in ('listOrientation','itemWidth','selectionZoom'):n.attrib.pop(k,None)
 n.set('itemHeight',str(ROW));n.set('transparent','1');n.set('selectionPixmap','PolsQ/assets/q-row-focus.png');n.set('scrollbarMode','showOnDemand')
 n.set('backgroundColorSelected','selected')
 rows=('MultiContentEntryRectangle(pos=(0,0),size=(4,%d),backgroundColor=0x000f1417,backgroundColorSelected=0x00f4b860),'%ROW+
  'MultiContentEntryRectangle(pos=(0,%d),size=(%d,1),backgroundColor=0x00263338,backgroundColorSelected=0x00184246),'%(ROW-1,LIST_W)+
  'MultiContentEntryPixmapAlphaBlend(pos=(32,24),size=(48,48),png=1,flags=BT_SCALE|BT_KEEP_ASPECT_RATIO)')
 def title(index):return f'MultiContentEntryText(pos=(104,0),size=({LIST_W-136},{ROW}),font=0,flags=RT_HALIGN_LEFT|RT_VALIGN_CENTER|RT_ELLIPSIS,text={index})'
 styles={k:rows+','+title(0 if k=='default' else 3) for k in ('default','text','number','image','both')}
 n.find('convert').text='{"itemHeight":%d,"template":['%ROW+styles['default']+'],"fonts":[gFont("PolsQStrong",'+str(32 if large else 28)+')],"templates":{'+','.join('"'+k+'":((%d,%d),['%(LIST_W,ROW)+v+'])' for k,v in styles.items())+'}}'
 s.append(n)
 # The native menu also expects a menuimage GUI component: shown in the header.
 m=saved['menuimage'];place(m,R-240-G-48,TITLE_Y+6,48,48);s.append(m)
 d=saved['description'];place(d,L,TOP+CARD_H+G,W,32);d.set('font','PolsQText;22');d.set('foregroundColor','muted');s.append(d)
 keys_row(s,[n for n in saved.values() if n.get('source','').startswith('key_') and n.get('render')=='Label'])

def channels(s,large):
 old=s.get('name');saved=[deepcopy(n) for n in s.findall('widget') if n.get('source','').startswith('key_') and n.get('render')=='Label']
 s[:]=[];shell(s,'Telewizja' if old!='ChannelSelectionRadio' else 'Radio')
 src(s,'Title',L,TITLE_Y+TITLE_H,1300,32,22,foregroundColor='muted',wrap='ellipsis')
 live_card(s,'ServiceEvent','ServiceEvent',video=old in ('ChannelSelection','ChannelSelection_PIG'),channel_list=True)
 n=node(s,'widget',name='list',position=f'{R-LIST_W},{TOP}',size=f'{LIST_W},{CARD_H}',serviceItemHeight=str(ROW),serviceNameFont='PolsQText;'+str(32 if large else 28),serviceInfoFont='PolsQText;'+str(28 if large else 24),serviceNumberFont='PolsQText;24',foregroundColor='white',backgroundColor='bg',foregroundColorSelected='white',backgroundColorSelected='selected',foregroundColorEvent='muted',foregroundColorEventSelected='muted',selectionPixmap='PolsQ/assets/q-row-focus.png',scrollbarMode='showOnDemand',scrollbarWidth='4',progressBarWidth='64',colorEventProgressbar='green',colorEventProgressbarSelected='green')
 if s.get('label'):s.set('label',s.get('label').replace('10 kanałów','8 kanałów'))
 text(s,'INFO — pełny opis',L,TOP+CARD_H+G,750,32,22,'muted')
 keys_row(s,saved)

# InfoBar in the style of a TV lower third: white logo card with the clock
# under it, a yellow upper-case programme title on the band and a red bar with
# the next programme. Same 64 px margins left and right, 24 px gaps.
# Everything is static: no timers, no scrolling.
NEWS_TOP=754
NEWS_BAND=226
NEWS_BAR=60
NEWS_CARD=(M,44,M+236,190)
NEWS_PANEL=(R-344,44,R,190)
NEWS_BADGE=(M+236+G,46,M+236+G+64,82)
def infobar(s,large):
 s[:]=[];s.set('position',f'0,{NEWS_TOP}');s.set('size',f'1920,{NEWS_BAND+NEWS_BAR+4}');s.set('backgroundColor','transparent')
 # One native-size PNG holds the band, logo card, number badge and info panel:
 # a single 1:1 blit instead of several blended layers.
 image(s,'q-news-band.png',0,0,1920,NEWS_BAND,-10)
 cx0,cy0,cx1,cy1=NEWS_CARD;px0,py0,px1,py1=NEWS_PANEL;bx0,by0,bx1,by1=NEWS_BADGE
 tx=bx0;tr=px0-G;tw=tr-tx
 # Picons are 220x132: drawn at native size, no scaling on the receiver.
 src(s,'session.CurrentService',cx0+8,cy0+7,220,132,render='Picon',converts=[('ServiceName','Reference')],alphatest='blend',zPosition='2')
 lift(src(s,'global.CurrentTime',cx0,cy1,cx1-cx0,36,30,converts=[('ClockToText','Default')],halign='center',font='PolsQStrong;30'))
 # Channel number centred in a fixed badge aligned with the title; NameOnly
 # avoids a second number when OpenATV's "channel number in InfoBar" is on.
 src(s,'session.CurrentService',bx0,by0,bx1-bx0,by1-by0,26,converts=[('PolsQChannelNumber','')],foregroundColor='newsYellow',font='PolsQStrong;26',halign='center',valign='center')
 src(s,'session.CurrentService',bx1+16,by0,tr-bx1-16,by1-by0,26,converts=[('ServiceName','NameOnly')],foregroundColor='muted',wrap='ellipsis',font='PolsQStrong;26',valign='center')
 lift(src(s,'session.Event_Now',tx,84,tw,104,40,render='PolsQSummary',converts=[('EventName','Name'),('PolsQUpper','')],foregroundColor='newsYellow',font='PolsQStrong;40'))
 src(s,'session.Event_Now',tx,192,92,32,24,converts=[('EventTime','StartTime'),('ClockToText','Default')])
 src(s,'session.Event_Now',tx+92,192,112,32,24,converts=[('EventTime','EndTime'),('ClockToText','Format:– %H:%M')])
 src(s,'session.Event_Now',tx+220,205,tr-tx-220,6,render='Progress',foregroundColor='newsYellow',backgroundColor='line',borderWidth='0',converts=[('EventTime','Progress')])
 # Info panel: date, remaining time and the recording state.
 ix=px0+G;iw=px1-px0-2*G
 src(s,'global.CurrentTime',ix,py0+16,iw,32,22,converts=[('ClockToText','Format:%d.%m.%Y')],foregroundColor='muted',font='PolsQStrong;22')
 src(s,'session.Event_Now',ix,py0+56,iw,36,26,converts=[('PolsQEventRemaining','')],font='PolsQStrong;26')
 src(s,'session.RecordState',ix,py0+100,iw,32,24,render='FixedLabel',text='● NAGRYWANIE',foregroundColor='red',converts=[('ConditionalShowHide',None)])
 # Opaque red bar with the next programme: plain fills, no alpha blending.
 node(s,'eLabel',position=f'0,{NEWS_BAND}',size=f'1920,{NEWS_BAR}',backgroundColor='newsRed')
 node(s,'eLabel',position=f'0,{NEWS_BAND}',size=f'{cx1},{NEWS_BAR}',backgroundColor='newsRedDark',zPosition=1)
 node(s,'eLabel',text='POTEM',position=f'{cx0},{NEWS_BAND}',size=f'{cx1-cx0},{NEWS_BAR}',font='PolsQStrong;28',foregroundColor='white',transparent='1',halign='center',valign='center',zPosition=2)
 src(s,'session.Event_Next',tx,NEWS_BAND,110,NEWS_BAR,30,converts=[('EventTime','StartTime'),('ClockToText','Default')],font='PolsQStrong;30',foregroundColor='white',valign='center',zPosition='2')
 src(s,'session.Event_Next',tx+120,NEWS_BAND,R-tx-120,NEWS_BAR,30,converts=[('EventName','Name'),('PolsQUpper','')],font='PolsQStrong;30',valign='center',wrap='ellipsis',zPosition='2')

EPG_H=270
def graph(s,large):
 # Details form a wide top card; the guide occupies the lower half.
 pig=s.get('name')=='GraphicalEPGPIG'
 hw=W-480-G if pig else W
 gy=TOP+EPG_H+G
 for n in s:
  key=n.get('name') or n.get('source','')
  if key=='list':place(n,L,gy+44,W,456);n.set('NumberOfRows','5' if large else '6')
  elif key in ('lab1','bouquetlist'):place(n,L,gy+44,W if key=='lab1' else 720,456)
  elif key=='timeline_text':place(n,L,gy,W,40)
  elif key.startswith('timeline'):place(n,L,gy+44,min(W,int(n.get('size').split(',')[0])),456)
  elif key=='Event':
   c=n.find('convert');arg=c.text if c is not None else ''
   if arg=='Name':place(n,L+P,TOP+P,hw-2*P,94);n.set('font','PolsQStrong;'+str(42 if large else 38))
   elif arg=='StartTime':place(n,L+P,TOP+EPG_H-P-44,140,44)
   elif arg=='EndTime':place(n,L+P+156,TOP+EPG_H-P-44,180,44)
  elif n.get('render')=='Pig':place(n,R-480,TOP,480,EPG_H)
 src(s,'Event',L+P+384,TOP+EPG_H-P-88,hw-2*P-384,88,24,render='PolsQSummary',converts=[('EventName','ExtendedDescription')],foregroundColor='muted')
 # Remove the inherited header and replace it without touching dynamic widgets.
 s[:]=[n for n in s if not (n.tag in ('eLabel','ePixmap') and int(n.get('position').split(',')[1])<200) and n.get('source') not in ('Title','global.CurrentTime')]
 # The old footer rule ran under the rail; the grid has no rule above the keys.
 s[:]=[n for n in s if not (n.tag=='eLabel' and not n.get('text') and n.get('size','').endswith(',2') and int(n.get('position').split(',')[1])>900)]
 card(s,L,TOP,hw,EPG_H,-15)
 shell(s,'Program TV')
 keys_row(s)
 for n in s.findall('eLabel'):
  if 'Zielona linia' in n.get('text',''):n.set('text','Żółta linia — teraz   •   Zegar — timer');place(n,L,gy+44+456+12,W,32)

# Small shared PNGs were stretched with scale="1" on many screens. Scaled
# alpha blits are done in software on most receivers, so every such use gets
# its own native-size file (generated by q_assets.native_variants).
NATIVE={'accent-fade':(1792,2),'line-tv':(32,32),'line-bouquet':(32,32),'line-history':(32,32)}
def native_pixmaps(s):
 for n in s.iter('ePixmap'):
  path=n.get('pixmap','');stem=path.rsplit('/',1)[-1][:-4]
  if n.get('scale')!='1' or not path.startswith('PolsQ/assets/') or stem not in NATIVE:continue
  w,h=map(int,n.get('size').split(','))
  if (w,h)!=NATIVE[stem]:n.set('pixmap',f'PolsQ/assets/{stem}-{w}x{h}.png')
  del n.attrib['scale']

def apply(skin,large=False):
 for s in skin.findall('screen'):
  name=s.get('name')
  if name=='Menu':menu(s,large)
  elif name.startswith('ChannelSelection'):channels(s,large)
  elif name=='InfoBar':infobar(s,large)
  elif name.startswith('Graphical'):graph(s,large)
  elif s.get('size')=='1920,1080' and s.get('backgroundColor')!='transparent':
   wallpaper(s)
  video_effects(s)
  if large and (name in ('Menu','InfoBar') or name.startswith('ChannelSelection')):
   for n in s:
    if n.get('font'):
     family,size=n.get('font').split(';');n.set('font',family+';'+str(int(size)+4))
     w,h=map(int,n.get('size').split(','));minimum=round((int(size)+4)*1.2)
     if h<minimum:n.set('size',f'{w},{minimum}')
  native_pixmaps(s)
 return skin
