"""Render native PNG surfaces with blur and glow baked in.

Each surface is produced at the exact size the skin draws it, so the receiver
blits it 1:1 instead of scaling and blending in software (slow on STBs)."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter
import math
ROOT=Path(__file__).resolve().parents[1]/'PolsQ/assets'

def panel(name,w,h,top,bottom,radius=24,shine=True,glow=None):
 im=Image.new('RGBA',(w,h));pix=im.load()
 for y in range(h):
  t=y/max(1,h-1)
  for x in range(w):
   lift=max(0,1-math.hypot((x-w*.15)/w,(y-h*.05)/h))*14 if shine else 0
   pix[x,y]=tuple(min(255,round(a*(1-t)+b*t+lift)) for a,b in zip(top[:3],bottom[:3]))+(round(top[3]*(1-t)+bottom[3]*t),)
 mask=Image.new('L',(w,h));ImageDraw.Draw(mask).rounded_rectangle((8,4,w-9,h-13),radius=radius,fill=255)
 # Two shadow layers: a tight contact shadow and a wider ambient one.
 shadow=Image.new('RGBA',(w,h));sd=ImageDraw.Draw(shadow);sd.rounded_rectangle((8,12,w-9,h-5),radius=radius,fill=(0,0,0,150));shadow=shadow.filter(ImageFilter.GaussianBlur(7))
 ambient=Image.new('RGBA',(w,h));ImageDraw.Draw(ambient).rounded_rectangle((10,10,w-11,h-3),radius=radius,fill=(0,4,16,90));ambient=ambient.filter(ImageFilter.GaussianBlur(4))
 ambient.alpha_composite(shadow);shadow=ambient
 if glow:
  # Focus halo inside the item rectangle (native lists clip outside it).
  halo=Image.new('RGBA',(w,h));ImageDraw.Draw(halo).rounded_rectangle((6,2,w-7,h-11),radius=radius+2,outline=glow,width=4);halo=halo.filter(ImageFilter.GaussianBlur(3))
  shadow.alpha_composite(halo)
 im.putalpha(Image.composite(im.getchannel('A'),Image.new('L',(w,h)),mask));shadow.alpha_composite(im)
 d=ImageDraw.Draw(shadow);d.rounded_rectangle((8,4,w-9,h-13),radius=radius,outline=(141,200,255,42) if not glow else (190,228,255,120),width=1)
 # Glass highlight along the upper edge.
 d.line((8+radius,5,w-9-radius,5),fill=(255,255,255,46 if glow else 22),width=1)
 shadow.save(ROOT/name)

def build():
 ROOT.mkdir(exist_ok=True)
 w,h=960,540;im=Image.new('RGBA',(w,h));p=im.load()
 for y in range(h):
  for x in range(w):
   a=math.exp(-(((x-780)/460)**2+((y-80)/300)**2));b=math.exp(-(((x-250)/600)**2+((y-490)/250)**2))
   p[x,y]=(round(7+10*a+12*b),round(12+27*a+7*b),round(29+65*a+39*b),255)
 # Opaque full-HD wallpaper: drawn without scaling or alpha blending.
 im.resize((1920,1080),Image.Resampling.BICUBIC).save(ROOT/'q-wallpaper.png')
 for w,h in HERO_SIZES:panel(f'q-hero-{w}x{h}.png',w,h,(24,47,88,248),(11,22,47,246),26)
 panel('q-tile.png',570,176,(25,47,80,245),(15,29,53,250),20)
 panel('q-tile-focus.png',570,176,(23,139,229,255),(12,67,143,255),20,glow=(110,200,255,150))
 panel('q-channel-focus.png',864,96,(19,115,201,255),(13,67,125,255),16,glow=(110,200,255,130))
 panel('q-logo-card.png',280,256,(37,78,126,241),(13,28,53,238),24)
 panel('q-info-card.png',1492,256,(22,43,78,241),(10,21,45,238),24)
 rail=Image.new('RGBA',(112,1080),(7,13,30,230));d=ImageDraw.Draw(rail);d.line((111,0,111,1080),fill=(96,153,220,45),width=1);rail.save(ROOT/'q-rail.png')
 build_video_effects()
 live_badge()


HERO_SIZES=((1712,384),(800,760),(1712,230))
BEZEL=(6,12,30,255)
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
 glow=Image.new('RGBA',(W,H));ImageDraw.Draw(glow).rounded_rectangle((p-10,p-10,p+w+9,p+h+9),radius=VIDEO_RADIUS+10,outline=(70,170,255,70),width=6)
 im.alpha_composite(glow.filter(ImageFilter.GaussianBlur(9)))
 ImageDraw.Draw(im).rounded_rectangle((p-6,p-6,p+w+5,p+h+5),radius=VIDEO_RADIUS+6,fill=BEZEL,outline=(120,190,255,70),width=1)
 # The video rectangle itself stays fully transparent: the picture shows
 # through the OSD there, so nothing may be painted on top of it.
 ImageDraw.Draw(im).rectangle((p,p,p+w-1,p+h-1),fill=(0,0,0,0))
 im.save(ROOT/f'q-video-shadow-{w}x{h}.png')


def build_video_effects():
 for w,h in video_sizes():
  video_shadow(w,h)


def live_badge():
 # Pill for the NA ŻYWO label under the preview.
 w,h=172,40;s=4
 im=Image.new('RGBA',(w*s,h*s));d=ImageDraw.Draw(im)
 d.rounded_rectangle((0,0,w*s-1,h*s-1),radius=h*s//2,fill=(6,12,30,200),outline=(255,255,255,40),width=s)
 cx,cy,r=22*s,h*s//2,7*s
 d.ellipse((cx-r-3*s,cy-r-3*s,cx+r+3*s,cy+r+3*s),fill=(255,98,98,70));d.ellipse((cx-r,cy-r,cx+r,cy+r),fill=(255,98,98,255))
 im.resize((w,h),Image.Resampling.LANCZOS).save(ROOT/'q-live-badge.png')

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
