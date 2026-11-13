"""Render native PNG surfaces with blur and glow baked in.

Each surface is produced at the exact size the skin draws it, so the receiver
blits it 1:1 instead of scaling and blending in software (slow on STBs)."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter
import math
ROOT=Path(__file__).resolve().parents[1]/'PolsQ/assets'

def panel(name,w,h,top,bottom,radius=24,shine=False,glow=None,edge=(255,255,255,20),inset=(12,8,12,16)):
 # inset: transparent margin (left, top, right, bottom); the bottom one holds
 # the shadow. Every card uses the same inset, so equal layout gaps give
 # equal visible gaps.
 im=Image.new('RGBA',(w,h));pix=im.load()
 for y in range(h):
  t=y/max(1,h-1)
  for x in range(w):
   lift=max(0,1-math.hypot((x-w*.15)/w,(y-h*.05)/h))*14 if shine else 0
   pix[x,y]=tuple(min(255,round(a*(1-t)+b*t+lift)) for a,b in zip(top[:3],bottom[:3]))+(round(top[3]*(1-t)+bottom[3]*t),)
 mask=Image.new('L',(w,h));l,t,r,b=inset;box=(l,t,w-1-r,h-1-b)
 ImageDraw.Draw(mask).rounded_rectangle(box,radius=radius,fill=255)
 # Two shadow layers: a tight contact shadow and a wider ambient one.
 shadow=Image.new('RGBA',(w,h));sd=ImageDraw.Draw(shadow);sd.rounded_rectangle((l,t+8,w-1-r,h-1-b+8),radius=radius,fill=(0,0,0,150));shadow=shadow.filter(ImageFilter.GaussianBlur(7))
 ambient=Image.new('RGBA',(w,h));ImageDraw.Draw(ambient).rounded_rectangle((l+2,t+6,w-3-r,h+1-b),radius=radius,fill=(0,4,16,90));ambient=ambient.filter(ImageFilter.GaussianBlur(4))
 ambient.alpha_composite(shadow);shadow=ambient
 if glow:
  # Focus halo inside the item rectangle (native lists clip outside it).
  halo=Image.new('RGBA',(w,h));ImageDraw.Draw(halo).rounded_rectangle((l-2,t-2,w+1-r,h+1-b),radius=radius+2,outline=glow,width=4);halo=halo.filter(ImageFilter.GaussianBlur(3))
  shadow.alpha_composite(halo)
 im.putalpha(Image.composite(im.getchannel('A'),Image.new('L',(w,h)),mask));shadow.alpha_composite(im)
 d=ImageDraw.Draw(shadow);d.rounded_rectangle(box,radius=radius,outline=edge,width=1)
 # Glass highlight along the upper edge.
 d.line((l+radius,t+1,w-1-r-radius,t+1),fill=(255,255,255,14),width=1)
 # The shadow falls downwards: keep the strip above the card fully clear.
 if t:shadow.paste((0,0,0,0),(0,0,w,t))
 shadow.save(ROOT/name)

def build():
 ROOT.mkdir(exist_ok=True)
 w,h=960,540;im=Image.new('RGBA',(w,h));p=im.load()
 for y in range(h):
  for x in range(w):
   a=math.exp(-(((x-780)/460)**2+((y-80)/300)**2));b=math.exp(-(((x-250)/600)**2+((y-490)/250)**2))
   p[x,y]=(round(13+4*a),round(18+10*a),round(21+11*a),255)
 # Opaque full-HD wallpaper: drawn without scaling or alpha blending.
 im.resize((1920,1080),Image.Resampling.BICUBIC).save(ROOT/'q-wallpaper.png')
 for w,h in skin_sizes('q-hero'):panel(f'q-hero-{w}x{h}.png',w,h,(27,37,43,248),(22,30,35,248),26)
 row_focus()
 build_video_effects()
 live_badge()
 news_band()
 native_variants()


def skin_sizes(prefix):
 import re
 import xml.etree.ElementTree as E
 sizes=set()
 for folder in ('PolsQ','PolsQLarge'):
  path=ROOT.parent.parent/folder/'skin.xml'
  if path.exists():
   for n in E.parse(path).getroot().iter('ePixmap'):
    m=re.fullmatch(r'PolsQ/assets/'+prefix+r'-(\d+)x(\d+)\.png',n.get('pixmap',''))
    if m:sizes.add((int(m.group(1)),int(m.group(2))))
 return sorted(sizes)
BEZEL=(10,14,16,255)
VIDEO_PAD=40
VIDEO_RADIUS=14


def video_sizes():
 import xml.etree.ElementTree as E
 skin=E.parse(ROOT.parent/'skin.xml').getroot()
 return sorted({tuple(map(int,n.get('size').split(','))) for n in skin.iter('widget') if n.get('render')=='Pig'})


def video_shadow(w,h):
 # Floating bezel: wide soft drop shadow, blue ambient glow and a dark rim.
 p=VIDEO_PAD;W,H=w+2*p,h+2*p
 im=Image.new('RGBA',(W,H))
 shadow=Image.new('RGBA',(W,H));ImageDraw.Draw(shadow).rounded_rectangle((p-4,p+10,p+w+3,p+h+18),radius=VIDEO_RADIUS+8,fill=(0,0,0,190))
 im.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(14)))
 glow=Image.new('RGBA',(W,H));ImageDraw.Draw(glow).rounded_rectangle((p-10,p-10,p+w+9,p+h+9),radius=VIDEO_RADIUS+10,outline=(255,255,255,0),width=6)
 im.alpha_composite(glow.filter(ImageFilter.GaussianBlur(9)))
 ImageDraw.Draw(im).rounded_rectangle((p-6,p-6,p+w+5,p+h+5),radius=VIDEO_RADIUS+6,fill=BEZEL,outline=(255,255,255,30),width=1)
 # The video rectangle itself stays fully transparent: the picture shows
 # through the OSD there, so nothing may be painted on top of it.
 ImageDraw.Draw(im).rectangle((p,p,p+w-1,p+h-1),fill=(0,0,0,0))
 im.save(ROOT/f'q-video-shadow-{w}x{h}.png')


ROW_W,ROW_H=936,96
def row_focus():
 # Selected list row (menu and channel lists): a full, opaque row. No rounded
 # transparent corners, so the native selection colour never shows around it.
 im=Image.new('RGBA',(ROW_W,ROW_H));p=im.load()
 for y in range(ROW_H):
  t=y/(ROW_H-1)
  c=(round(30-4*t),round(78-8*t),round(82-8*t),255)
  for x in range(ROW_W):p[x,y]=c
 im.save(ROOT/'q-row-focus.png')


def build_video_effects():
 for w,h in video_sizes():
  video_shadow(w,h)


def live_badge():
 # Pill for the NA ŻYWO label under the preview.
 w,h=172,40;s=4
 im=Image.new('RGBA',(w*s,h*s));d=ImageDraw.Draw(im)
 d.rounded_rectangle((0,0,w*s-1,h*s-1),radius=h*s//2,fill=(10,14,16,210),outline=(255,255,255,40),width=s)
 cx,cy,r=22*s,h*s//2,7*s
 d.ellipse((cx-r-3*s,cy-r-3*s,cx+r+3*s,cy+r+3*s),fill=(255,98,98,70));d.ellipse((cx-r,cy-r,cx+r,cy+r),fill=(255,98,98,255))
 im.resize((w,h),Image.Resampling.LANCZOS).save(ROOT/'q-live-badge.png')

NEWS_W,NEWS_H=1920,226
NEWS_FADE=40
NEWS_ALPHA=238
LOGO_CARD=(64,44,300,190)
NEXT_BOX=(1512,44,1856,190)
NUMBER_BADGE=(324,46,388,82)


def news_band():
 # Navy-to-royal-blue lower third: soft fade on top so the band melts into
 # the picture, nearly opaque body for contrast behind the yellow headline.
 w,h=NEWS_W,NEWS_H
 im=Image.new('RGBA',(w,h));p=im.load()
 for y in range(h):
  t=min(1,y/NEWS_FADE);alpha=round(NEWS_ALPHA*t*t*(3-2*t))
  v=y/(h-1)
  for x in range(w):
   u=x/(w-1)
   r=27-5*v+2*u;g=37-7*v+3*u;b=43-8*v+3*u
   p[x,y]=(max(0,min(255,round(r))),max(0,min(255,round(g))),max(0,min(255,round(b))),alpha)
 # Logo card: white with a soft contact shadow; the picon is drawn on it.
 shadow=Image.new('RGBA',(w,h));x0,y0,x1,y1=LOGO_CARD
 ImageDraw.Draw(shadow).rounded_rectangle((x0+2,y0+6,x1+2,y1+6),radius=14,fill=(0,0,0,140))
 im.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(6)))
 k=4;cw,ch=x1-x0,y1-y0
 card=Image.new('RGBA',(cw*k,ch*k));cd=ImageDraw.Draw(card)
 cd.rounded_rectangle((0,0,cw*k-1,ch*k-1),radius=14*k,fill=(252,252,253,255))
 card=card.resize((cw,ch),Image.Resampling.LANCZOS)
 im.alpha_composite(card,dest=(x0,y0))
 # Next panel: a lighter glass box with a thin bright edge.
 x0,y0,x1,y1=NEXT_BOX;bw,bh=x1-x0,y1-y0
 box=Image.new('RGBA',(bw*k,bh*k));bd=ImageDraw.Draw(box)
 bd.rounded_rectangle((0,0,bw*k-1,bh*k-1),radius=16*k,fill=(255,255,255,12),outline=(255,255,255,28),width=2*k)
 box=box.resize((bw,bh),Image.Resampling.LANCZOS)
 im.alpha_composite(box,dest=(x0,y0))
 # Fixed badge for the channel number, same glass style as the panel.
 x0,y0,x1,y1=NUMBER_BADGE;bw,bh=x1-x0,y1-y0
 badge=Image.new('RGBA',(bw*k,bh*k));ImageDraw.Draw(badge).rounded_rectangle((0,0,bw*k-1,bh*k-1),radius=8*k,fill=(255,255,255,12),outline=(255,255,255,28),width=2*k)
 im.alpha_composite(badge.resize((bw,bh),Image.Resampling.LANCZOS),dest=(x0,y0))
 im.save(ROOT/'q-news-band.png')


def native_variants():
 # Native-size copies for every shared PNG that the skin would otherwise stretch.
 import re
 import xml.etree.ElementTree as E
 wanted=set()
 for folder in ('PolsQ','PolsQLarge'):
  path=ROOT.parent.parent/folder/'skin.xml'
  if not path.exists():continue
  for n in E.parse(path).getroot().iter('ePixmap'):
   m=re.fullmatch(r'PolsQ/assets/(accent-fade|line-tv|line-bouquet|line-history)-(\d+)x(\d+)\.png',n.get('pixmap',''))
   if m:wanted.add((m.group(1),int(m.group(2)),int(m.group(3))))
 for stem,w,h in sorted(wanted):
  with Image.open(ROOT/f'{stem}.png') as base:
   base.convert('RGBA').resize((w,h),Image.Resampling.LANCZOS).save(ROOT/f'{stem}-{w}x{h}.png')


if __name__=='__main__':build()


def build_menu_icons():
    c=(230,241,255,255)
    for name in ['information','setup','plugin_selection','shutdown','movie_selection','timermenu']:
        im=Image.new('RGBA',(96,96));d=ImageDraw.Draw(im)
        if name=='information':
            d.ellipse((15,15,81,81),outline=c,width=4);d.line((48,44,48,66),fill=c,width=5);d.ellipse((45,29,51,35),fill=c)
        elif name=='setup':
            pts=[]
            for i in range(32):
                a=i*math.pi/16;radius=34 if i%4 in (0,1) else 28;pts.append((48+radius*math.cos(a),48+radius*math.sin(a)))
            d.polygon(pts,outline=c,width=4);d.ellipse((36,36,60,60),outline=c,width=4)
        elif name=='plugin_selection':
            for x,y in [(18,18),(54,18),(18,54),(54,54)]:d.rounded_rectangle((x,y,x+24,y+24),radius=5,outline=c,width=3)
        elif name=='shutdown':
            d.arc((18,18,78,78),-65,245,fill=c,width=5);d.line((48,10,48,48),fill=c,width=5)
        elif name=='movie_selection':
            d.rounded_rectangle((14,21,82,72),radius=5,outline=c,width=4);d.polygon([(40,32),(40,61),(62,47)],outline=c,width=3)
        else:
            d.ellipse((16,16,80,80),outline=c,width=4);d.line([(48,28),(48,49),(63,56)],fill=c,width=4)
        im.save(ROOT.parent/'mainmenu'/(name+'.png'))
