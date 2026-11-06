"""Render lightweight native PNG surfaces; no runtime blur or animation loop."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter
import math
ROOT=Path(__file__).resolve().parents[1]/'PolsQ/assets'

def panel(name,w,h,top,bottom,radius=24,shine=True):
 im=Image.new('RGBA',(w,h));pix=im.load()
 for y in range(h):
  t=y/max(1,h-1)
  for x in range(w):
   glow=max(0,1-math.hypot((x-w*.15)/w,(y-h*.05)/h))*14 if shine else 0
   pix[x,y]=tuple(min(255,round(a*(1-t)+b*t+glow)) for a,b in zip(top[:3],bottom[:3]))+(round(top[3]*(1-t)+bottom[3]*t),)
 mask=Image.new('L',(w,h));ImageDraw.Draw(mask).rounded_rectangle((8,4,w-9,h-13),radius=radius,fill=255)
 shadow=Image.new('RGBA',(w,h));sd=ImageDraw.Draw(shadow);sd.rounded_rectangle((8,12,w-9,h-5),radius=radius,fill=(0,0,0,150));shadow=shadow.filter(ImageFilter.GaussianBlur(7))
 im.putalpha(Image.composite(im.getchannel('A'),Image.new('L',(w,h)),mask));shadow.alpha_composite(im)
 d=ImageDraw.Draw(shadow);d.rounded_rectangle((8,4,w-9,h-13),radius=radius,outline=(141,200,255,42),width=1)
 shadow.save(ROOT/name)

def build():
 ROOT.mkdir(exist_ok=True)
 w,h=960,540;im=Image.new('RGBA',(w,h));p=im.load()
 for y in range(h):
  for x in range(w):
   a=math.exp(-(((x-780)/460)**2+((y-80)/300)**2));b=math.exp(-(((x-250)/600)**2+((y-490)/250)**2))
   p[x,y]=(round(7+10*a+12*b),round(12+27*a+7*b),round(29+65*a+39*b),255)
 im.save(ROOT/'q-wallpaper.png')
 panel('q-hero.png',856,380,(24,47,88,248),(11,22,47,246),26)
 panel('q-tile.png',570,176,(25,47,80,245),(15,29,53,250),20)
 panel('q-tile-focus.png',570,176,(23,139,229,255),(12,67,143,255),20)
 panel('q-channel-focus.png',864,96,(19,115,201,255),(13,67,125,255),16)
 panel('q-logo-card.png',280,256,(37,78,126,241),(13,28,53,238),24)
 panel('q-info-card.png',1492,256,(22,43,78,241),(10,21,45,238),24)
 rail=Image.new('RGBA',(112,1080),(7,13,30,230));d=ImageDraw.Draw(rail);d.line((111,0,111,1080),fill=(96,153,220,45),width=1);rail.save(ROOT/'q-rail.png')

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
