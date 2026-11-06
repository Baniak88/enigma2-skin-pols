from pathlib import Path
import xml.etree.ElementTree as E
from PIL import Image, ImageDraw, ImageFont
import zipfile
ROOT=Path(__file__).resolve().parents[1]
skin=E.Element('skin')
output=E.SubElement(skin,'output',{'id':'0'}); E.SubElement(output,'resolution',{'xres':'1920','yres':'1080','bpp':'32'})
colors=E.SubElement(skin,'colors')
for n,v in {'background':'#00101938','panel':'#0018284e','foreground':'#00ffffff','muted':'#009baed2','accent':'#000078e8'}.items(): E.SubElement(colors,'color',{'name':n,'value':v})
fonts=E.SubElement(skin,'fonts'); E.SubElement(fonts,'font',{'filename':'/usr/share/fonts/nmsbd.ttf','name':'Regular','scale':'100'})
BG='#101938'; PANEL='#18284e'; BLUE='#0078e8'; WHITE='#ffffff'; MUTED='#9baed2'
def screen(name,title):
 s=E.SubElement(skin,'screen',{'name':name,'position':'0,0','size':'1920,1080','backgroundColor':BG,'flags':'wfNoBorder'})
 label(s,'POLS Q',90,55,300,65,42); label(s,title,430,62,1100,55,36); label(s,'20:15',1650,65,180,50,34)
 return s
def label(s,text,x,y,w,h,fs=30,bg=None):
 a={'text':text,'position':f'{x},{y}','size':f'{w},{h}','font':f'Regular;{fs}','foregroundColor':WHITE,'backgroundColor':bg or BG,'transparent':'0' if bg else '1'}
 return E.SubElement(s,'eLabel',a)
def widget(s,name,x,y,w,h,**kw):
 a={'position':f'{x},{y}','size':f'{w},{h}'}; a.update(kw)
 if name: a['name']=name
 return E.SubElement(s,'widget',a)
def source(s,src,conv,x,y,w,h,fs=32):
 a=widget(s,None,x,y,w,h,source=src,render='Label',font=f'Regular;{fs}',foregroundColor=WHITE,backgroundColor=BG,transparent='1')
 E.SubElement(a,'convert',{'type':conv[0]}).text=conv[1]
def footer(s): label(s,'●  Nagrywaj         ●  Ulubione         ●  Informacje         ●  Szukaj',90,985,1580,50,26); label(s,'OK  Wybierz     EXIT  Wstecz',1330,990,520,42,24)
s=screen('Menu','Menu główne')
widget(s,'menu',90,185,620,680,font='Regular;36',itemHeight='85',foregroundColor=WHITE,backgroundColor=BG,backgroundColorSelected=BLUE,foregroundColorSelected=WHITE,scrollbarMode='showOnDemand')
label(s,'Twój wieczór. Twój wybór.',810,220,1000,100,56); label(s,'Telewizja, nagrania i ustawienia',810,345,1000,65,32); label(s,'Wybierz pozycję za pomocą strzałek pilota.',810,455,1000,60,28); footer(s)
s=screen('ChannelSelection','Telewizja  /  Wszystkie kanały')
widget(s,'list',90,190,1060,700,font='Regular;32',serviceNumberFont='Regular;28',serviceNameFont='Regular;32',serviceInfoFont='Regular;26',itemHeight='76',foregroundColor=WHITE,backgroundColor=BG,backgroundColorSelected=BLUE,foregroundColorSelected=WHITE,scrollbarMode='showOnDemand')
source(s,'ServiceEvent',('ServiceName','Name'),1230,210,600,60,40)
source(s,'ServiceEvent',('EventName','Name'),1230,325,600,100,34)
source(s,'ServiceEvent',('EventName','ExtendedDescription'),1230,460,590,380,26); footer(s)
s=E.SubElement(skin,'screen',{'name':'InfoBar','position':'0,0','size':'1920,1080','backgroundColor':'#ff000000','flags':'wfNoBorder'})
label(s,'',0,765,1920,315,30,BG); label(s,'POLS Q',90,800,240,60,38)
source(s,'session.CurrentService',('ServiceName','Name'),380,800,1100,60,38)
source(s,'session.Event_Now',('EventName','Name'),380,875,1120,55,34)
source(s,'session.Event_Next',('EventName','Name'),380,970,1100,50,27)
a=widget(s,None,380,943,1120,6,source='session.Event_Now',render='Progress',foregroundColor=BLUE,backgroundColor=PANEL); E.SubElement(a,'convert',{'type':'EventTime'}).text='Progress'
a=widget(s,None,1660,805,190,55,source='global.CurrentTime',render='Label',font='Regular;34',foregroundColor=WHITE,backgroundColor=BG); E.SubElement(a,'convert',{'type':'ClockToText'}).text='Default'
s=screen('EPGSelection','Program TV')
source(s,'Service',('ServiceName','Name'),90,150,1600,60,36)
widget(s,'list',90,240,1740,650,font='Regular;30',itemHeight='72',foregroundColor=WHITE,backgroundColor=BG,backgroundColorSelected=BLUE,foregroundColorSelected=WHITE,scrollbarMode='showOnDemand'); footer(s)
s=screen('MovieSelection','Moje nagrania')
widget(s,'list',90,190,1740,700,font='Regular;32',itemHeight='76',foregroundColor=WHITE,backgroundColor=BG,backgroundColorSelected=BLUE,foregroundColorSelected=WHITE,scrollbarMode='showOnDemand'); footer(s)
s=screen('Setup','Ustawienia')
widget(s,'config',90,210,1740,650,font='Regular;32',itemHeight='72',foregroundColor=WHITE,backgroundColor=BG,backgroundColorSelected=BLUE,foregroundColorSelected=WHITE,scrollbarMode='showOnDemand')
widget(s,'key_red',90,975,500,50,font='Regular;28',foregroundColor=WHITE,backgroundColor=BG); widget(s,'key_green',650,975,600,50,font='Regular;28',foregroundColor=WHITE,backgroundColor=BG)
E.indent(skin); E.ElementTree(skin).write(ROOT/'PolsQ/skin.xml',encoding='utf-8',xml_declaration=True)
# Podgląd geometrii z rzeczywistego XML; przykładowe dane zastępują źródła Enigma2.
samples={'menu':['Telewizja','Program TV','Moje nagrania','Wtyczki','Ustawienia','Tryb czuwania'],'ChannelSelection':['001   Das Erste HD                 Wiadomości','002   ZDF HD                         Film wieczoru','003   RTL HD                          Rozrywka','004   SAT.1 HD                       Serial','005   ProSieben HD                 Kino','006   Sky Cinema                    Premiera','007   Sky Sport                       Na żywo'],'EPGSelection':['19:30 — 20:00    Wiadomości','20:00 — 20:15    Serwis sportowy','20:15 — 22:10    Film wieczoru','22:10 — 22:40    Magazyn kulturalny','22:40 — 00:15    Kino nocne'],'MovieSelection':['Film wieczoru                                  05.11.2026     1 h 55 min','Planeta Ziemia                                 04.11.2026     52 min','Mecz tygodnia                                  03.11.2026     2 h 10 min'],'config':['Rozdzielczość obrazu                              1920 × 1080','Format obrazu                                        16:9','Język menu                                             Polski','Wygląd interfejsu                                    Pols Q']}
font='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
for s in skin.findall('screen'):
 im=Image.new('RGB',(1920,1080),BG); d=ImageDraw.Draw(im)
 if s.get('name')=='InfoBar':
  for y in range(765): d.line((0,y,1920,y),fill=(18+int(y/45),35+int(y/22),54+int(y/16)))
  d.text((90,100),'PODGLĄD TELEWIZJI',font=ImageFont.truetype(font,32),fill=MUTED)
 for el in s:
  x,y=map(int,el.get('position','0,0').split(',')); w,h=map(int,el.get('size','0,0').split(',')); bg=el.get('backgroundColor',BG)
  if el.get('transparent')!='1': d.rectangle((x,y,x+w,y+h),fill=bg if bg.startswith('#') and len(bg)==7 else BG)
  fs=int(el.get('font','Regular;30').split(';')[1]); f=ImageFont.truetype(font,fs)
  text=el.get('text','')
  if el.tag=='widget':
   name=el.get('name'); src=el.get('source'); cv=el.find('convert')
   if name in ('menu','list','config'):
    rows=samples.get(name,samples.get(s.get('name'),[])); ih=int(el.get('itemHeight','76'))
    for i,row in enumerate(rows):
     if i==1: d.rectangle((x,y+i*ih,x+w,y+(i+1)*ih-4),fill=BLUE)
     d.text((x+18,y+i*ih+17),row,font=f,fill=WHITE)
   elif el.get('render')=='Progress': d.rectangle((x,y,x+w*.58,y+h),fill=BLUE)
   elif src=='global.CurrentTime': text='20:15'
   elif src in ('session.CurrentService','Service'): text='ZDF HD'
   elif src=='session.Event_Now': text='20:15  Film wieczoru'
   elif src=='session.Event_Next': text='Następnie  22:10  Magazyn kulturalny'
   elif src=='ServiceEvent':
    text='ZDF HD' if cv.get('type')=='ServiceName' else ('Film wieczoru' if cv.text=='Name' else '20:15 – 22:10\n\nNiezwykła historia, wielkie emocje.\nWieczorne pasmo filmowe.\n\nHD   •   Dolby Audio')
  if text: d.multiline_text((x+4,y+5),text,font=f,fill=WHITE,spacing=16)
 im.resize((1280,720)).save(ROOT/f'preview/{s.get("name")}.png')
 im.resize((1280,720)).save(ROOT/f'preview/{s.get("name")}.webp')
with zipfile.ZipFile(ROOT/'PolsQ-preview.zip','w',zipfile.ZIP_DEFLATED) as z:
 for p in (ROOT/'PolsQ').rglob('*'):
  if p.is_file(): z.write(p,p.relative_to(ROOT))
print('Generated 6 screens and previews')
