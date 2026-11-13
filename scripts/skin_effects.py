"""Native static gradients for bars and programme details."""
import xml.etree.ElementTree as E

FADE_TOP=64
BODY_ALPHA=217  # ~85% opacity, retaining the requested ~15% transparency.
BODY_RGB=(16,25,56)
BAR_HEIGHTS={'InfoBar':354,'SecondInfoBar':504,'MoviePlayer':294}
EVENT_MARGIN=128
EVENT_FADE_END=1824
EVENT_ALPHA_LEFT=240
EVENT_ALPHA_RIGHT=217


def fade_alpha(y):
    t=min(1,max(0,y/FADE_TOP))
    return round(BODY_ALPHA*t*t*(3-2*t))


def event_fade_alpha(x):
    t=min(1,max(0,x/EVENT_FADE_END))
    smooth=t*t*(3-2*t)
    return round(EVENT_ALPHA_LEFT+(EVENT_ALPHA_RIGHT-EVENT_ALPHA_LEFT)*smooth)


def pixmap(parent,path,x,y,w,h,z,scale=False):
    # Native-size PNGs avoid slow software scaling on the receiver.
    node=E.Element('ePixmap',position=f'{x},{y}',size=f'{w},{h}',pixmap=f'PolsQ/assets/{path}',alphatest='blend',zPosition=str(z))
    if scale:node.set('scale','1')
    parent.insert(0,node)
    return node


def modernize_bars(skin):
    for name,height in BAR_HEIGHTS.items():
        scene=skin.find(f"screen[@name='{name}']")
        scene.set('position',f'0,{1080-height-FADE_TOP}')
        scene.set('size',f'1920,{height+FADE_TOP}')
        scene.set('backgroundColor','transparent')
        for node in list(scene):
            x,y=map(int,node.get('position').split(','))
            if node.tag=='eLabel' and (x,y)==(64,0) and node.get('backgroundColor')=='green':
                scene.remove(node)
                continue
            node.set('position',f'{x},{y+FADE_TOP}')
        # Native Screen creates decorations after renderers: explicit negative
        # z puts the surface behind text/Picon regardless of creation order.
        pixmap(scene,'accent-fade.png',64,FADE_TOP,1792,2,-5)
        pixmap(scene,'accent-glow.png',64,FADE_TOP-8,1792,18,-6)
        pixmap(scene,f'{name.lower()}-fade.png',0,0,1920,height+FADE_TOP,-10)
        if name=='InfoBar':
            # Shift the whole text grid, including the badge/progress origins;
            # keeping only the name away from the separator left TERAZ crowded.
            for node in scene:
                x,y=map(int,node.get('position').split(','))
                if x in (320,440,600):
                    node.set('position',f'{x+40},{y}')
                    w,h=map(int,node.get('size').split(','))
                    if w>1000:node.set('size',f'{w-40},{h}')
            pixmap(scene,'now-badge.png',348,FADE_TOP+104,128,48,-4)
            E.SubElement(scene,'eLabel',position=f'320,{FADE_TOP+34}',size='1,142',backgroundColor='line')
            for widget in scene.findall("widget[@source='session.CurrentService']"):
                if widget.get('render')=='Label':widget.set('font','PolsQStrong;38')
    for name in ('EventView','InfoBarEventView'):
        scene=skin.find(f"screen[@name='{name}']")
        scene.set('backgroundColor','transparent')
        # Fade gradually across 95% of the screen. The opacity floor protects
        # text contrast even when the video behind a paragraph turns white.
        # Full-size PNG: blitted 1:1, never stretched from a single row.
        pixmap(scene,'eventview-fade.png',0,0,1920,1080,-10)

