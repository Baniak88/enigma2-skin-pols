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

def shell(s,section):
 wallpaper(s)
 image(s,'q-rail.png',0,0,112,1080,-20)
 text(s,'Q',34,40,60,68,48,bold=True)
 for i,path in enumerate(['line-tv.png','line-bouquet.png','line-history.png']):image(s,path,38,234+i*112,36,36,0,scale=True)
 text(s,'POLS',28,960,80,44,20)
 lift(text(s,section,152,48,1350,68,40,bold=True))
 src(s,'global.CurrentTime',1616,52,240,54,32,converts=[('ClockToText','Default')],halign='right')

def menu(s,large):
 saved={n.get('name') or n.get('source'):deepcopy(n) for n in s.findall('widget')}
 s[:]=[];shell(s,'Twój wieczór')
 hero(s,144,164,1712,384)
 text(s,'NA ŻYWO',192,202,800,40,21,'green')
 src(s,'session.CurrentService',192,252,850,46,28,converts=[('ServiceName','Name')])
 lift(src(s,'session.Event_Now',192,310,896,114,46,render='PolsQSummary',converts=[('EventName','Name')]))
 src(s,'session.Event_Now',192,444,850,70,25,render='PolsQSummary',converts=[('EventName','ExtendedDescription')],foregroundColor='muted')
 src(s,'session.VideoPicture',1200,194,576,324,render='Pig',backgroundColor='transparent',zPosition='2')
 n=saved['menu'];place(n,144,584,1712,352)
 n.set('listOrientation','grid');n.set('itemWidth','570');n.set('itemHeight','176');n.set('transparent','1');n.set('selectionPixmap','PolsQ/assets/q-tile-focus.png');n.set('selectionZoom','0');n.set('scrollbarMode','showOnDemand')
 icon='MultiContentEntryPixmapAlphaBlend(pos=(32,28),size=(64,64),png=1,flags=BT_SCALE|BT_KEEP_ASPECT_RATIO)'
 def title(index,x=32):return f'MultiContentEntryText(pos=({x},108),size=({530-x},54),font=0,flags=RT_HALIGN_LEFT|RT_VALIGN_CENTER|RT_ELLIPSIS,text={index})'
 styles={k:icon+','+title(0 if k=='default' else 3) for k in ('default','text','number','image','both')}
 n.find('convert').text='{"itemHeight":176,"itemWidth":570,"template":['+styles['default']+'],"fonts":[gFont("PolsQStrong",'+str(32 if large else 28)+')],"templates":{'+','.join('"'+k+'":((570,176),['+v+'])' for k,v in styles.items())+'}}'
 for i in range(6):image(s,'q-tile.png',144+(i%3)*570,584+(i//3)*176,570,176,-10)
 s.append(n)
 # The native menu also expects a menuimage GUI component.
 m=saved['menuimage'];place(m,1080,212,64,64);s.append(m)
 d=saved['description'];place(d,160,952,1650,44);d.set('font','PolsQText;24');s.append(d)
 for key in ('key_red','key_green','key_yellow','key_blue'):
  for original in [n for n in saved.values() if n.get('source')==key]:
   # Captions remain native; empty actions are hidden by the original converter.
   i=('key_red','key_green','key_yellow','key_blue').index(key)
   place(original,184+i*424,1010,374,44);s.append(original)
   src(s,key,160+i*424,1020,6,20,render='FixedLabel',text=' ',backgroundColor='nativeGreen' if key=='key_green' else key[4:],transparent='0',conditional=key,converts=[('ConditionalShowHide',None)])

def channels(s,large):
 old=s.get('name');saved={n.get('source'):deepcopy(n) for n in s.findall('widget') if n.get('source','').startswith('key_') and n.get('render')=='Label'}
 s[:]=[];shell(s,'Telewizja' if old!='ChannelSelectionRadio' else 'Radio')
 src(s,'Title',152,128,1660,44,24,foregroundColor='muted',wrap='ellipsis')
 hero(s,144,192,800,760)
 video=old in ('ChannelSelection','ChannelSelection_PIG')
 if video:src(s,'session.VideoPicture',160,208,768,432,render='Pig',backgroundColor='transparent',zPosition='2')
 else:
  src(s,'ServiceEvent',392,260,304,172,render='Picon',converts=[('ServiceName','Reference')],alphatest='blend',zPosition='2')
  text(s,'TWÓJ KANAŁ',192,470,680,50,32,'green')
 src(s,'ServiceEvent',192,660,500 if video else 704,44,28,converts=[('ServiceName','Name')],foregroundColor='green',wrap='ellipsis')
 lift(src(s,'ServiceEvent',192,706,704,88,34,render='PolsQSummary',converts=[('EventName','Name')]))
 src(s,'ServiceEvent',192,808,128,38,24,converts=[('EventTime','StartTime'),('ClockToText','Default')])
 src(s,'ServiceEvent',340,808,168,38,24,converts=[('EventTime','EndTime'),('ClockToText','Format:– %H:%M')],foregroundColor='muted')
 src(s,'ServiceEvent',544,808,352,38,23,converts=[('PolsQEventRemaining','')],halign='right',foregroundColor='muted')
 src(s,'ServiceEvent',192,858,704,6,render='Progress',backgroundColor='line',foregroundColor='green',borderWidth='0',converts=[('EventTime','Progress')])
 src(s,'ServiceEvent',192,872,704,52,23,render='PolsQSummary',converts=[('EventName','ExtendedDescription')],foregroundColor='muted')
 n=node(s,'widget',name='list',position='992,192',size='864,768',serviceItemHeight='96',serviceNameFont='PolsQText;'+str(32 if large else 28),serviceInfoFont='PolsQText;'+str(28 if large else 24),serviceNumberFont='PolsQText;24',foregroundColor='white',backgroundColor='bg',foregroundColorSelected='white',backgroundColorSelected='selected',foregroundColorEvent='muted',foregroundColorEventSelected='muted',selectionPixmap='PolsQ/assets/q-channel-focus.png',scrollbarMode='showOnDemand',scrollbarWidth='4',progressBarWidth='64',colorEventProgressbar='green',colorEventProgressbarSelected='green')
 if s.get('label'):s.set('label',s.get('label').replace('10 kanałów','8 kanałów'))
 text(s,'INFO — pełny opis',160,966,750,30,22,'muted')
 for i,key in enumerate(('key_red','key_green','key_yellow','key_blue')):
  if key in saved:
   n=saved[key];place(n,184+i*424,1010,374,42);s.append(n)
   src(s,key,160+i*424,1020,6,20,render='FixedLabel',text=' ',backgroundColor='nativeGreen' if key=='key_green' else key[4:],transparent='0',conditional=key,converts=[('ConditionalShowHide',None)])

# News-style InfoBar (lower third): white logo card with the clock under it,
# a yellow upper-case headline on a navy-blue band and a red ticker bar.
NEWS_TOP=754
NEWS_BAND=226
NEWS_BAR=60
def infobar(s,large):
 s[:]=[];s.set('position',f'0,{NEWS_TOP}');s.set('size',f'1920,{NEWS_BAND+NEWS_BAR+4}');s.set('backgroundColor','transparent')
 # One native-size PNG holds the band, the logo card and the Next panel:
 # a single 1:1 blit instead of several blended layers.
 image(s,'q-news-band.png',0,0,1920,NEWS_BAND,-10)
 # Picons are 220x132: drawn at native size, no scaling on the receiver.
 src(s,'session.CurrentService',56,51,220,132,render='Picon',converts=[('ServiceName','Reference')],alphatest='blend',zPosition='2')
 lift(src(s,'global.CurrentTime',48,190,236,36,30,converts=[('ClockToText','Default')],halign='center',font='PolsQStrong;30'))
 src(s,'session.CurrentService',310,46,1178,36,26,converts=[('ServiceName','Name')],foregroundColor='newsSky',wrap='ellipsis',font='PolsQStrong;26')
 lift(src(s,'session.Event_Now',310,84,1178,104,40,render='PolsQSummary',converts=[('EventName','Name'),('PolsQUpper','')],foregroundColor='newsYellow',font='PolsQStrong;40'))
 src(s,'session.Event_Now',310,192,92,32,24,converts=[('EventTime','StartTime'),('ClockToText','Default')])
 src(s,'session.Event_Now',402,192,112,32,24,converts=[('EventTime','EndTime'),('ClockToText','Format:– %H:%M')])
 src(s,'session.Event_Now',530,205,600,6,render='Progress',foregroundColor='newsYellow',backgroundColor='line',borderWidth='0',converts=[('EventTime','Progress')])
 src(s,'session.Event_Now',1148,192,340,32,24,converts=[('PolsQEventRemaining','')],foregroundColor='newsSky',halign='right')
 text(s,'POTEM',1544,56,150,30,22,'newsSky',bold=True)
 src(s,'session.Event_Next',1700,56,140,30,24,converts=[('EventTime','StartTime'),('ClockToText','Default')],halign='right')
 src(s,'session.Event_Next',1544,92,296,84,28,render='PolsQSummary',converts=[('EventName','Name')],font='PolsQStrong;28')
 src(s,'session.RecordState',1520,188,344,34,24,render='FixedLabel',text='● NAGRYWANIE',foregroundColor='red',halign='right',converts=[('ConditionalShowHide',None)])
 # Opaque red bar: plain fills, no alpha blending, cheap while the text scrolls.
 node(s,'eLabel',position=f'0,{NEWS_BAND}',size=f'1920,{NEWS_BAR}',backgroundColor='newsRed')
 node(s,'eLabel',position=f'0,{NEWS_BAND}',size='1920,2',backgroundColor='newsRedLight',zPosition=1)
 node(s,'eLabel',position=f'0,{NEWS_BAND+2}',size=f'292,{NEWS_BAR-2}',backgroundColor='newsRedDark',zPosition=1)
 node(s,'eLabel',text='W SKRÓCIE',position=f'40,{NEWS_BAND+2}',size=f'232,{NEWS_BAR-2}',font='PolsQStrong;26',foregroundColor='white',transparent='1',halign='center',valign='center',zPosition=2)
 src(s,'session.Event_Now',308,NEWS_BAND+2,1572,NEWS_BAR-2,render='PolsQTicker',converts=[('EventName','ExtendedDescription'),('PolsQUpper','')],font='PolsQStrong;30',backgroundColor='newsRed',transparent='0',zPosition='2')

def graph(s,large):
 # Details form a wide top feature; the guide occupies the lower half.
 for n in s:
  key=n.get('name') or n.get('source','')
  if key=='list':place(n,144,480,1712,480);n.set('NumberOfRows','5' if large else '6')
  elif key in ('lab1','bouquetlist'):place(n,144,480,1712 if key=='lab1' else 720,480)
  elif key=='timeline_text':place(n,144,430,1712,46)
  elif key.startswith('timeline'):place(n,144,480,int(n.get('size').split(',')[0]),480)
  elif key=='Event':
   c=n.find('convert');arg=c.text if c is not None else ''
   if arg=='Name':place(n,192,240,1100,94);n.set('font','PolsQStrong;'+str(42 if large else 38))
   elif arg=='StartTime':place(n,192,352,140,44)
   elif arg=='EndTime':place(n,350,352,180,44)
  elif n.get('render')=='Pig':place(n,1376,160,480,270)
 src(s,'Event',600,342,660 if s.get('name')=='GraphicalEPGPIG' else 1120,66,24,render='PolsQSummary',converts=[('EventName','ExtendedDescription')],foregroundColor='muted')
 # Remove the inherited header and replace it without touching dynamic widgets.
 s[:]=[n for n in s if not (n.tag in ('eLabel','ePixmap') and int(n.get('position').split(',')[1])<200) and n.get('source') not in ('Title','global.CurrentTime')]
 hero(s,144,188,1712,230,-15)
 shell(s,'Program TV')
 for n in s.findall('eLabel'):
  if 'Zielona linia' in n.get('text',''):n.set('text','Niebieska linia — teraz   •   Zegar — timer');place(n,144,966,1712,30)

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
