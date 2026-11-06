"""Procedural fictional film frame, used only in documentation previews."""
from pathlib import Path
from PIL import Image, ImageDraw
import math,random

def render():
 path=Path(__file__).resolve().parents[1]/'docs/tv-demo.png'
 im=Image.new('RGB',(1920,1080));p=im.load()
 for y in range(1080):
  t=y/1080
  for x in range(1920):
   glow=math.exp(-(((x-1390)/590)**2+((y-410)/290)**2))
   p[x,y]=(int(9+40*t+88*glow),int(17+25*t+22*glow),int(43+36*t+65*glow))
 d=ImageDraw.Draw(im);rng=random.Random(18)
 for i in range(160):
  x=rng.randrange(1920);y=rng.randrange(480);d.ellipse((x,y,x+1,y+1),fill=(142,167,205))
 d.ellipse((1270,280,1510,520),fill=(219,170,175))
 d.polygon([(0,680),(180,500),(420,690),(670,410),(960,650),(1170,510),(1500,750),(1720,600),(1920,780),(1920,1080),(0,1080)],fill=(36,49,79))
 d.polygon([(0,850),(350,670),(510,820),(890,560),(1100,800),(1340,620),(1680,880),(1920,720),(1920,1080),(0,1080)],fill=(16,31,52))
 d.polygon([(0,1040),(400,880),(750,990),(1200,810),(1700,1040),(1920,930),(1920,1080),(0,1080)],fill=(8,21,39))
 path.parent.mkdir(exist_ok=True);im.save(path)
 return path
