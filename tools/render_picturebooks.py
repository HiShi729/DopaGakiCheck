#!/usr/bin/env python3
"""Render 20 original silent 18-second picture-book clips without any captions.

Each clip has three gentle tableau scenes (0-6s, 6-12s, 12-18s).  The
introductory still comes ONLY from the first tableau. Videos contain zero
text, zero sound and no flashing cuts. Requires Pillow and ffmpeg.
"""
from __future__ import annotations
import argparse
import math
import os
import random
import subprocess
import tempfile
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter
from stories import STORIES

ROOT = Path(__file__).resolve().parents[1]
ANDROID_VIDEOS = ROOT / 'app/src/main/res/raw'
ANDROID_STILLS = ROOT / 'app/src/main/res/drawable-nodpi'
WEB_VIDEOS = ROOT / 'web-demo/clips'
WEB_STILLS = ROOT / 'web-demo/stills'
W, H, SCALE = 432, 768, 2
INK = '#455565'
PAPER = '#FAF3E9'


def sc(z): return round(z*SCALE)
def bounds(v): return tuple(sc(x) for x in v)

class Paint:
    def __init__(self, bg='#EFF2E7'):
        self.img = Image.new('RGB', (W*SCALE,H*SCALE),bg)
        self.draw = ImageDraw.Draw(self.img)
    def ell(self, b, color, outline=INK, width=2):
        self.draw.ellipse(bounds(b), fill=color, outline=outline, width=sc(width) if outline else 1)
    def rect(self, b, color, rad=0, outline=INK, width=2):
        b=bounds(b)
        if rad: self.draw.rounded_rectangle(b, radius=sc(rad), fill=color,outline=outline,width=sc(width) if outline else 1)
        else: self.draw.rectangle(b, fill=color,outline=outline,width=sc(width) if outline else 1)
    def line(self, points, color=INK, width=4):
        self.draw.line([(sc(x),sc(y)) for x,y in points],fill=color,width=sc(width),joint='curve')
    def polygon(self, coords, color, outline=INK, width=2):
        pts=[(sc(x),sc(y)) for x,y in coords]
        self.draw.polygon(pts,fill=color)
        if outline: self.draw.line(pts+[pts[0]],fill=outline,width=sc(width),joint='curve')
    def arc(self,b,start,end,color=INK,width=4): self.draw.arc(bounds(b), start,end, fill=color,width=sc(width))
    def addtexture(self,idx,phase):
        # Subtle, repeatable speckles mimic paper without visual noise.
        rng=random.Random(idx*100+phase)
        for i in range(460):
            x=rng.randint(0,W*SCALE-1); y=rng.randint(0,H*SCALE-1)
            self.draw.point((x,y),fill=(232,226,213))
        return self.img.resize((W,H),Image.Resampling.LANCZOS)

def shadow(p,x,y,rx=54,ry=12): p.ell((x-rx,y-ry,x+rx,y+ry),'#C8C7B7',outline=None)
def rounded(p,x,y,w,h,color,rad=10): p.rect((x,y,x+w,y+h),color,rad)

def bg(p,scene):
    schemes={'stream':('#E4EEDA','#CAD9CF'),'garden':('#E6E9D8','#D7E5CE'),
       'forest':('#E6ECD8','#D8E6CA'),'park':('#E9F0E1','#D4E7D9'),
       'meadow':('#E8F1E0','#DDE5BE'),'room':('#F7EFE1','#EBE2CF'),
       'snow':('#E6F1F5','#F2F6F6'),'beach':('#FAE9CB','#E7DEC7')}
    a,b=schemes[scene]
    p.rect((0,0,432,768),a,outline=None)
    p.rect((0,595,432,768),b,outline=None)
    # ornamental clouds and a subdued paper-book mat
    p.ell((50,120,175,152),'#FDF9EE',outline=None)
    p.ell((92,101,160,146),'#FDF9EE',outline=None)
    p.ell((278,184,393,216),'#FAF7E9',outline=None)
    p.ell((322,165,375,214),'#FAF7E9',outline=None)
    if scene in ('park','forest','meadow','garden'):
        p.rect((0,570,432,768), '#B7D1B5',outline=None)
        for x,y in [(42,602),(401,630),(80,686),(323,683)]:
            p.line([(x,y),(x-7,y-13)],'#769579',2)
            p.line([(x,y),(x+8,y-17)],'#769579',2)
    if scene in ('stream','beach'):
        p.rect((0,540,432,660),'#8DBFC8' if scene=='stream' else '#9CCFD3',outline=None)
        p.rect((0,650,432,768),'#D5CAAE',outline=None)
        for xx,yy in [(68,556),(174,588),(297,617),(359,557)]:
            p.arc((xx,yy,xx+54,yy+11),0,175,'#D7EEF0',2)
    if scene=='snow':
        p.rect((0,570,432,768),'#F1F3F0',outline=None)
        for xx,yy in [(37,620),(109,650),(342,615),(389,699)]:p.ell((xx,yy,xx+6,yy+6),'#D3DFE8',None)
    if scene=='room':
        p.rect((0,580,432,768),'#C5AF94',outline=None)
        p.line([(0,580),(432,580)],'#99836C',4)
        p.rect((42,150,155,350),'#CEE2D6',8,'#A7A899',6)
        p.line([(98,151),(98,350)],'#F8F6E9',8)
        p.line([(42,253),(155,253)],'#F8F6E9',8)
        p.ell((15,118,77,180),'#FFFCED',outline=None)
    # fine paper margin and rounded picture-frame edges
    p.rect((13,49,419,709),'#FFFFFF00' if False else '#E7E5D9',22,outline=None)
    p.rect((18,54,414,704),None if False else a,20,'#C9C7B8',2)
    # restore lower ground after frame so objects sit on the page
    ground = '#BAD3B5' if scene in ('park','forest','meadow','garden') else ('#E8EBE8' if scene=='snow' else ('#D8C5A6' if scene=='beach' else ('#C8B6A2' if scene=='room' else '#C9D5C1')))
    p.rect((20,602,412,700),ground,outline=None)
    if scene=='stream':
        p.rect((20,504,412,613),'#96C1CA',outline=None)
        p.rect((20,612,412,700),'#C9D5C1',outline=None)
        for xx in (35,188,312):p.arc((xx,520,xx+75,540),0,180,'#D1E4E5',2)
    if scene=='beach':
        p.rect((20,504,412,610),'#9FCED4',outline=None)
        p.rect((20,610,412,700),'#E8D5B5',outline=None)
    if scene=='room':
        p.rect((20,602,412,700),'#CDB69C',outline=None)
    if scene=='snow':p.rect((20,599,412,700),'#F5F5F0',outline=None)
    # Slow picture-book scenery. Draw within the paper frame; keep it quiet and
    # behind the characters rather than filling the screen with moving effects.
    if scene in ('stream','garden','forest','park','meadow','beach','snow'):
        p.ell((298,142,356,200),'#F8F2D3',outline=None)
        p.ell((71,207,158,233),'#FBFBF2',outline=None)
        p.ell((100,191,151,227),'#FBFBF2',outline=None)
        p.ell((243,247,334,271),'#FAF9EF',outline=None)
        if scene not in ('beach','snow'):
            p.polygon([(20,477),(103,403),(174,462),(256,391),(412,463),(412,504),(20,504)],'#D4E5CF',outline=None)
            p.polygon([(20,514),(90,457),(162,504),(311,435),(412,492),(412,542),(20,542)],'#BCD6BA',outline=None)
        if scene=='forest':
            p.rect((54,290,67,525),'#9E8F72',rad=4)
            p.ell((28,221,118,333),'#AFCBA7',outline=None)
        if scene=='garden':
            for gx in (63,151,238,334):
                p.line([(gx,465),(gx,516)],'#C2B4A0',5)
            p.line([(20,486),(412,486)],'#C2B4A0',5)
        if scene=='park':
            p.ell((35,445,84,502),'#A0BCA1',outline=None)
            p.ell((363,437,408,504),'#A0BCA1',outline=None)
        if scene=='beach':
            p.rect((20,448,412,505),'#B5DDE1',outline=None)
            for x in (45,227,352):p.arc((x,471,x+54,493),0,178,'#EDF5ED',2)
        if scene=='snow':
            for x in (80,346):
                p.polygon([(x,351),(x-53,454),(x+55,454)],'#93B0A7',outline=None)
                p.polygon([(x,379),(x-44,462),(x+46,462)],'#A2B8AF',outline=None)
    if scene=='room':
        p.rect((45,190,172,406),'#A7C0BC',rad=12)
        p.rect((57,204,161,392),'#D4E5DB',rad=6)
        p.line([(109,204),(109,392)],'#F5F0E6',10)
        p.line([(57,299),(161,299)],'#F5F0E6',10)
        p.ell((263,192,330,246),'#F5EACB',outline=None)
        p.rect((271,395,367,410),'#D1C2B3',rad=4)

def person(p,x,y,k=1,look='happy',arms='down',shirt='#CF8F84'):
    # y is standing feet, body 130*k tall
    p.ell((x-35*k,y-118*k,x+35*k,y-50*k),'#F1D3AD')
    p.ell((x-39*k,y-127*k,x+36*k,y-89*k),'#5C514A')
    p.ell((x-30*k,y-111*k,x+30*k,y-51*k),'#F1D3AD')
    p.ell((x-14*k,y-91*k,x-9*k,y-85*k),INK,None)
    p.ell((x+11*k,y-91*k,x+16*k,y-85*k),INK,None)
    if look=='sad':p.arc((x-12*k,y-75*k,x+13*k,y-59*k),180,360,INK,3)
    else:p.arc((x-12*k,y-76*k,x+13*k,y-62*k),0,180,INK,3)
    p.rect((x-27*k,y-52*k,x+27*k,y+5*k),shirt,14)
    p.line([(x-12*k,y+2*k),(x-14*k,y+35*k)],'#546978',6*k)
    p.line([(x+12*k,y+2*k),(x+14*k,y+35*k)],'#546978',6*k)
    p.ell((x-32*k,y+26*k,x-8*k,y+37*k),'#605B58')
    p.ell((x+6*k,y+26*k,x+30*k,y+37*k),'#605B58')
    if arms=='up':
        p.line([(x-23*k,y-39*k),(x-55*k,y-68*k)],shirt,9*k)
        p.line([(x+23*k,y-39*k),(x+62*k,y-67*k)],shirt,9*k)
        p.ell((x-63*k,y-78*k,x-48*k,y-62*k),'#F1D3AD')
        p.ell((x+54*k,y-77*k,x+69*k,y-61*k),'#F1D3AD')
    elif arms=='reach':
        p.line([(x+21*k,y-36*k),(x+75*k,y-53*k)],shirt,9*k)
        p.ell((x+68*k,y-60*k,x+83*k,y-46*k),'#F1D3AD')
        p.line([(x-23*k,y-36*k),(x-36*k,y-7*k)],shirt,9*k)
    else:
        p.line([(x-24*k,y-32*k),(x-38*k,y-7*k)],shirt,9*k)
        p.line([(x+24*k,y-32*k),(x+38*k,y-7*k)],shirt,9*k)

def critter(p,kind,x,y,k=1,face='happy'):
    # Stylized animal centered at feet y, 80x90, avoids realistic identification issues.
    def e(x1,y1,x2,y2,c,stroke=INK):p.ell((x+x1*k,y+y1*k,x+x2*k,y+y2*k),c,stroke)
    def l(points,c=INK,w=3):p.line([(x+px*k,y+py*k) for px,py in points],c,w*k)
    skins={'rabbit':'#EEE5DA','fox':'#DFA276','hedgehog':'#B78D6C',
           'squirrel':'#CC9B6F','bird':'#E7B981','cat':'#A6B9AE',
           'dog':'#BA9B7D','snail':'#DBCDA6','turtle':'#83A685',
           'beaver':'#B5906F','ant':'#6A5952','crab':'#DC8C75'}
    c=skins.get(kind,'#BFAE99')
    if kind=='ant':
        e(-20,-22,-4,-4,c);e(-2,-25,22,-3,c);e(10,-30,38,-8,c)
        for dx in (-18,2,26):l([(dx,-7),(dx-11,8)],INK,2)
        return
    if kind=='snail':
        e(-30,-58,30,-3,'#C3A17D')
        p.arc((x-18*k,y-49*k,x+17*k,y-14*k),30,320,'#866D63',4)
        l([(24,-12),(43,-31),(40,-56)],INK,4);e(35,-62,46,-49,'#D5BE9D')
        e(22,-9,58,2,'#C0B28E');return
    if kind=='turtle':
        e(-40,-43,35,-3,'#608D73');e(-28,-42,22,-10,'#86AA7B')
        e(32,-33,64,-8,'#A5BC86')
        for dx in (-28,15):e(dx-7,-5,dx+9,14,'#A5BC86')
        return
    if kind=='bird':
        e(-35,-63,26,-11,c);e(-14,-47,18,-22,'#F6E1C1')
        p.polygon([(x+23*k,y-47*k),(x+45*k,y-39*k),(x+22*k,y-31*k)],'#E7A26A')
        e(7,-53,13,-47,INK,None)
        l([(-13,-6),(-17,6)],'#9D8265',3);l([(6,-6),(9,6)],'#9D8265',3)
        return
    if kind=='crab':
        e(-34,-39,34,-2,'#DA947D')
        for xx in (-22,0,22):l([(xx,-5),(xx-16 if xx<0 else xx+16,10)],'#C87766',3)
        l([(-25,-29),(-48,-51)],'#C87766',5);l([(25,-29),(48,-51)],'#C87766',5)
        e(-57,-64,-37,-44,'#ECA28D');e(37,-64,57,-44,'#ECA28D')
        e(-14,-30,-8,-25,INK,None);e(9,-30,15,-25,INK,None)
        return
    if kind=='hedgehog':
        for dx in range(-52,37,13):
            p.polygon([(x+dx*k,y-27*k),(x+(dx+10)*k,y-80*k),(x+(dx+28)*k,y-28*k)],'#806D5D')
    if kind=='squirrel': e(-48,-83,0,-9,'#B67F5D')
    if kind=='fox':
        p.polygon([(x-50*k,y-28*k),(x-69*k,y-74*k),(x-27*k,y-46*k)],'#DFA276')
        p.polygon([(x-28*k,y-72*k),(x-24*k,y-109*k),(x-2*k,y-83*k)],c)
        p.polygon([(x+22*k,y-72*k),(x+30*k,y-109*k),(x+48*k,y-76*k)],c)
    if kind=='rabbit':
        e(-28,-131,-12,-66,c);e(17,-128,32,-66,c)
        e(-23,-124,-16,-78,'#E7B7AD',None);e(20,-122,26,-79,'#E7B7AD',None)
    if kind in ('cat','dog'):
        p.polygon([(x-27*k,y-75*k),(x-35*k,y-108*k),(x-7*k,y-83*k)],c)
        p.polygon([(x+22*k,y-77*k),(x+35*k,y-108*k),(x+41*k,y-74*k)],c)
    e(-38,-68,36,-6,c)
    e(-30,-98,32,-47,c)
    if kind=='fox':e(-19,-63,23,-50,'#F8E8D2')
    e(-15,-81,-10,-75,INK,None);e(13,-81,18,-75,INK,None)
    if face=='sad':p.arc((x-12*k,y-61*k,x+13*k,y-49*k),180,360,INK,2)
    else:p.arc((x-11*k,y-61*k,x+13*k,y-49*k),0,180,INK,2)
    for dx in (-22,18):e(dx-8,-9,dx+11,6,c)

# Story props: all word-free with recognizable silhouettes.
def prop(p,kind,x,y,k=1):
    def e(b,c,o=INK):p.ell((x+b[0]*k,y+b[1]*k,x+b[2]*k,y+b[3]*k),c,o)
    def r(b,c,rad=4):p.rect((x+b[0]*k,y+b[1]*k,x+b[2]*k,y+b[3]*k),c,rad*k)
    def poly(pts,c):p.polygon([(x+xx*k,y+yy*k) for xx,yy in pts],c)
    def line(pts,c=INK,w=3):p.line([(x+xx*k,y+yy*k) for xx,yy in pts],c,w*k)
    if kind=='boat':
        poly([(-48,-11),(50,-11),(27,13),(-26,13)],'#F9F5EA')
        poly([(-31,-12),(0,-55),(34,-12)],'#E6D6BD')
        line([(0,-54),(0,-12)],'#7F8B8C',2)
    elif kind=='branch':
        line([(-80,-17),(46,-10),(73,-38)],'#94745D',11)
        line([(11,-14),(35,-58)],'#94745D',7)
        e((25,-71,58,-44),'#89AB79')
    elif kind=='pole':line([(0,-100),(6,0)],'#9D8A70',8)
    elif kind=='umbrella':
        poly([(-80,-26),(-53,-72),(0,-89),(53,-72),(82,-26)],'#BFA3BB')
        line([(-81,-26),(82,-26)],'#957C96',3)
        line([(0,-89),(0,38)],'#7B6F6B',5)
        p.arc((x-8*k,y+27*k,x+20*k,y+55*k),0,180,'#7B6F6B',4)
    elif kind=='flower':
        r((-31,-3,32,63),'#C7876D',9)
        poly([(-45,-5),(45,-5),(27,65),(-27,65)],'#C8896D')
        line([(0,-7),(0,-99)],'#67876B',7)
        e((-48,-76,-3,-57),'#83A779');e((4,-62,48,-44),'#80A370')
        for a in range(0,360,72):
            ang=math.radians(a)
            cx=math.cos(ang)*24;cy=math.sin(ang)*22-115
            e((cx-16,cy-17,cx+16,cy+17),'#F0CC91')
        e((-13,-128,13,-102),'#CA8D6D')
    elif kind=='scarf':
        poly([(-39,-12),(16,-14),(54,20),(42,33),(14,5),(-39,9)],'#B87771')
        line([(-24,10),(-25,24)],'#B87771',12)
    elif kind=='kite':
        poly([(0,-78),(49,-16),(0,38),(-49,-16)],'#CFB16D')
        line([(0,-78),(0,38)],'#E7DAC2',3)
        line([(-49,-16),(49,-16)],'#E7DAC2',3)
        line([(0,38),(0,125)],'#9D9D92',2)
    elif kind=='plank':r((-145,-11,145,10),'#AF8D6C',3)
    elif kind=='apple':e((-28,-31,28,30),'#C98B77');line([(0,-28),(7,-50)],'#7B6B52',4)
    elif kind=='nest':
        e((-56,-19,58,25),'#BCA37C');e((-40,-9,40,15),'#E3C499')
        for dx in (-50,-24,11,34):line([(dx,0),(dx+21,10)],'#977B62',3)
    elif kind=='twig':line([(-49,10),(45,-12)],'#99795E',8);line([(2,-1),(25,-35)],'#99795E',5)
    elif kind=='balloon':
        e((-36,-74,36,25),'#D4A9B1');poly([(-8,23),(8,23),(0,38)],'#C18C9D')
        line([(0,38),(5,116)],'#8B8583',2)
    elif kind=='vase':
        poly([(-34,-75),(34,-75),(24,-58),(31,24),(22,39),(-25,39),(-30,23),(-24,-58)],'#AAC8C1')
        e((-34,-89,34,-72),'#D0E3D9')
        line([(0,-75),(-8,-139)],'#7FA080',5)
        e((-29,-147,8,-117),'#D9BD89');e((0,-141,31,-113),'#E1CA92')
    elif kind=='vase_tilt':
        # The rim is visibly displaced to the right while the base still rests on the table.
        poly([(-6,-75),(65,-76),(50,-55),(31,24),(22,39),(-23,39),(-27,20),(-19,-57)],'#AAC8C1')
        e((-6,-90,65,-71),'#D0E3D9')
        line([(28,-77),(50,-139)],'#7FA080',5)
        e((31,-153,70,-126),'#D9BD89')
    elif kind=='bench':
        r((-100,-78,100,-50),'#A88A6C',6);r((-100,-35,100,-17),'#AF8C69',5)
        line([(-80,-18),(-88,38)],'#786C63',8);line([(75,-18),(86,38)],'#786C63',8)
    elif kind=='ball':e((-28,-28,28,28),'#DAB78B')
    elif kind=='plane':
        poly([(-68,16),(73,-30),(20,14),(2,37)],'#F4F3E8')
        poly([(-68,16),(10,-1),(2,37)],'#D2DAD3')
    elif kind=='robot':
        r((-44,-75,44,20),'#A1B6C1',12);r((-53,-140,53,-77),'#B5CBD0',13)
        e((-33,-126,-17,-107),'#45586A');e((16,-126,32,-107),'#45586A')
        line([(-33,-3),(-63,19)],'#718A94',10);line([(34,-3),(65,15)],'#718A94',10)
        line([(-21,20),(-21,45)],'#718A94',11);line([(21,20),(21,45)],'#718A94',11)
    elif kind=='plug':
        r((-30,-20,30,30),'#E9DDC9',8)
        line([(-13,-19),(-13,-45)],'#7B7975',5);line([(12,-19),(12,-45)],'#7B7975',5)
        line([(0,30),(55,60)],'#646F76',4)
    elif kind=='snowman':
        e((-61,-95,61,22),'#FAFAF5');e((-47,-176,47,-91),'#FDFCF8')
        e((-19,-149,-12,-142),INK,None);e((16,-149,23,-142),INK,None)
        poly([(0,-130),(33,-121),(0,-119)],'#D7A67A')
        line([(-51,-54),(-90,-78)],'#987C61',7);line([(51,-54),(90,-78)],'#987C61',7)
    elif kind=='snowhead':
        e((-47,-42,47,42),'#FDFCF8');e((-19,-14,-12,-7),INK,None);e((16,-14,23,-7),INK,None)
        poly([(0,2),(31,9),(0,13)],'#D7A67A')
    elif kind=='puddle':e((-115,-30,115,17),'#94BED0',None);p.arc((x-90*k,y-19*k,x+50*k,y+4*k),0,170,'#D9E7E8',2)
    elif kind=='book':
        poly([(-70,-36),(0,-29),(0,26),(-70,20)],'#F5EAD4')
        poly([(0,-29),(70,-36),(70,20),(0,26)],'#ECE2CC')
        line([(0,-29),(0,26)],'#AB9B8C',3)
    elif kind=='lamp':
        poly([(-52,-90),(52,-90),(32,-35),(-32,-35)],'#C0AB86')
        line([(0,-35),(0,45)],'#81766A',8);r((-40,40,40,48),'#948274',4)
    elif kind=='cookie':e((-37,-30,37,30),'#D4B184')
    elif kind=='hat':
        e((-48,-37,48,8),'#BC9E75');r((-77,2,77,17),'#A38A6C',6)
    elif kind=='shell':
        e((-49,-35,49,33),'#E5C8AD')
        for xx in (-30,-10,12,31):line([(0,29),(xx,-28)],'#C09980',3)
    elif kind=='box':r((-60,-75,60,39),'#C8AF8C',7)
    elif kind=='marble':e((-18,-18,18,18),'#94B6C0')
    elif kind=='bike':
        e((-94,0,-22,70),'#A4AEB0');e((29,0,102,70),'#A4AEB0')
        e((-86,8,-31,63),'#E9EEE9');e((37,8,94,63),'#E9EEE9')
        line([(-58,36),(0,-24),(65,36),(-58,36),(-10,42),(0,-24)],'#9C8279',7)
        line([(-4,-30),(24,-30)],'#6E7880',5);line([(60,30),(76,-24),(102,-24)],'#6E7880',5)
        line([(-25,43),(14,43)],'#59646B',4)
    else:raise ValueError('missing prop '+kind)


def tree(p,x=320,y=530,size=1.0):
    p.rect((x-16*size,y-105*size,x+16*size,y+56*size),'#987C67',10)
    for cx,cy,r in [(-44,-144,69),(39,-177,74),(1,-207,87)]:
        p.ell((x+(cx-r)*size,y+(cy-r)*size,x+(cx+r)*size,y+(cy+r)*size),'#9FB99A')
    p.line([(x,y+25*size),(x,y-100*size)],'#927665',7)

def stage(p,i,phase):
    # In every story, the first tableau describes only the initial situation.
    # The final outcome is shown only after second transition at 12 seconds.
    if i==0: # boat, branch, stick, boat freed
        person(p,100,590,.90,arms='reach' if phase==2 else 'down')
        if phase==0: prop(p,'boat',242,546,1.0)
        elif phase==1:
            prop(p,'branch',274,551,1.0);prop(p,'boat',253,520,.86)
        else:
            prop(p,'branch',275,557,1.0);prop(p,'pole',176,575,.75);prop(p,'boat',350,546,.85)
    elif i==1: # umbrella flowers
        for x,y in [(250,225),(321,176),(356,271)]:p.line([(x,y),(x-17,y+29)],'#A0BCC3',3)
        prop(p,'flower',278,535,.78)
        if phase<2:prop(p,'umbrella',278,364,.95)
        else:prop(p,'umbrella',95,405,.85)
        person(p,118,596,.84,arms='reach' if phase==2 else 'down')
    elif i==2: # rabbit and fox scarf
        critter(p,'rabbit',132 if phase<2 else 241,586,1.08)
        if phase==0:prop(p,'scarf',133,507,.85)
        if phase==1:
            prop(p,'scarf',214,595,.84);critter(p,'fox',324,580,1.0)
        if phase==2:
            critter(p,'fox',104,592,1.0);prop(p,'scarf',188,535,.87)
    elif i==3: # kite stuck
        tree(p,312,548,1.05)
        person(p,109,614,.97,arms='reach' if phase==2 else 'up')
        prop(p,'kite',168 if phase==0 else 302,212 if phase==0 else 295,.87)
        if phase==2:p.line([(115,519),(302,345)],'#8D8C84',2)
    elif i==4: # snail bridge
        critter(p,'snail',114 if phase!=2 else 330,572,.88)
        if phase>0:prop(p,'plank',243,526,.66)
        critter(p,'beaver',340 if phase==1 else 365,580,.84)
    elif i==5: # hedgehog/apple squirrel
        critter(p,'hedgehog',120,586,1.0)
        critter(p,'squirrel',345,581,.92)
        prop(p,'apple',175 if phase==0 else (264 if phase==1 else 227),539 if phase==0 else (590 if phase==1 else 533),.85)
    elif i==6: # nest
        tree(p,280,570,1.07);prop(p,'nest',295,315,.83)
        critter(p,'bird',255,269,.89) if phase!=1 else critter(p,'bird',138,598,.85)
        if phase==1:prop(p,'twig',178,614,.75)
        if phase==2:prop(p,'twig',290,322,.68)
    elif i==7: # balloon floating away
        person(p,132,622,.95,arms='up' if phase>0 else 'down',look='sad' if phase==2 else 'happy')
        prop(p,'balloon',173 if phase==0 else (229 if phase==1 else 317),346 if phase==0 else (227 if phase==1 else 131),1 if phase<2 else .72)
    elif i==8: # vase and cat
        p.rect((65,475,370,502),'#BBA38A',8)
        p.line([(96,493),(96,602)],'#A48D77',9);p.line([(341,493),(341,602)],'#A48D77',9)
        critter(p,'cat',170 if phase<2 else 100,471,.67)
        prop(p,'vase_tilt' if phase==1 else 'vase',279 if phase<2 else 250,425,1.0)
        if phase==2:person(p,338,589,.86,arms='reach')
    elif i==9: # dog ball bench
        prop(p,'bench',287,510,1.0)
        critter(p,'dog',105,614,.95)
        if phase!=0:critter(p,'cat',354,605,.74)
        prop(p,'ball',196 if phase==0 else (306 if phase==1 else 198),582,.75)
    elif i==10: # paper plane bird tree
        tree(p,329,573,1.02)
        person(p,113,603,.92,arms='up' if phase==0 else 'reach')
        prop(p,'plane',213 if phase==0 else (328 if phase==1 else 194),335 if phase==0 else (334 if phase==1 else 550),.73)
        if phase==2:critter(p,'bird',325,285,.62)
    elif i==11: # robot
        prop(p,'robot',190,553,.85)
        person(p,325,600,.89,arms='reach' if phase!=0 else 'down')
        if phase>=1:prop(p,'plug',259,543,.61)
        if phase==1:p.ell((198,450,218,470),'#B7B1A9',None)
        if phase==2:
            p.arc((127,345,256,380),0,180,'#E0C37B',5)
            p.ell((143,370,156,383),'#DAAF68',None)
    elif i==12: # snowman
        person(p,94,602,.84,arms='up' if phase==2 else 'down')
        if phase==0:prop(p,'snowman',260,567,.88)
        else:
            p.ell((206,498,314,609),'#FAFAF5')
            prop(p,'snowhead',276 if phase==1 else 260,575 if phase==1 else 462,.85)
    elif i==13: # fox puddle go around
        prop(p,'puddle',249,579,.90)
        critter(p,'fox',104 if phase==0 else (171 if phase==1 else 352),574 if phase!=2 else 626,.9)
        if phase==2:
            p.arc((171,514,335,657),190,343,'#E9DFC3',8)
    elif i==14: # reading sunlight
        p.rect((267,276,387,501),'#A5B7AA',12)
        p.rect((274,283,380,492),'#D5E3D1',8)
        if phase<2:
            p.rect((270,277,321,493),'#B19CA7',8)
            p.rect((330,277,384,493),'#B19CA7',8)
        elif phase==2:
            p.polygon([(273,300),(160,587),(230,590),(382,320)],'#F5E9C6',outline=None)
        person(p,143,594,.8)
        prop(p,'book',187,555,.76)
        prop(p,'lamp',83,418,.67)
        if phase==1:p.rect((76,335,92,350),'#676B71',8)
    elif i==15: # crumbs to ant
        person(p,141,586,.9,arms='reach' if phase==2 else 'down')
        prop(p,'cookie',184,476,.85)
        critter(p,'ant',326 if phase!=2 else 267,583,1.1)
        if phase==2:prop(p,'cookie',252,577,.30)
    elif i==16: # fox hat and turtle water
        critter(p,'fox',100,587,.95,face='sad' if phase>0 else 'happy')
        critter(p,'turtle',321 if phase!=2 else 212,568,.83)
        prop(p,'hat',101 if phase==0 else (314 if phase==1 else 169),428 if phase==0 else (528 if phase==1 else 532),.66)
    elif i==17: # beach crab shell lost
        critter(p,'crab',108 if phase<2 else 253,592,.85)
        prop(p,'shell',225 if phase==0 else (297 if phase==1 else 367),584 if phase==0 else (557 if phase==1 else 526),.72 if phase<2 else .48)
        if phase>0:
            for xx in (249,296,340):p.arc((xx,532,xx+52,546),0,172,'#F5F5EA',3)
    elif i==18: # marble box
        p.rect((39,482,394,515),'#BDA58B',8)
        p.line([(81,514),(81,618)],'#9B886F',9);p.line([(359,514),(359,618)],'#9B886F',9)
        person(p,110,576,.64)
        person(p,360,578,.65,arms='reach' if phase==2 else 'down')
        prop(p,'box',253,454 if phase<2 else 420,.78)
        if phase==0:prop(p,'marble',176,472,.78)
        if phase==1:prop(p,'marble',258,467,.65)
        if phase==2:prop(p,'marble',310,464,.72)
    elif i==19: # bicycle chain fixed
        prop(p,'bike',223,529,.9)
        person(p,120,609,.79)
        if phase>0:person(p,335,607,.75,arms='reach' if phase==1 else 'down')
        if phase==1:p.line([(188,555),(231,571)],'#5E666D',4)
        if phase==2:
            # A later pose suggests riding away.
            p.arc((208,452,342,496),190,355,'#D1B286',3)
    else:raise ValueError(i)


def render_panel(idx,phase,path):
    meta=STORIES[idx]
    p=Paint()
    bg(p,meta['setting'])
    stage(p,idx,phase)
    p.img=p.img.convert('RGB')
    pic=p.addtexture(idx,phase)
    pic.save(path,optimize=True)
    return pic


def make_video(idx, temporary):
    panels=[]
    for phase in range(3):
        path=temporary/f's{idx+1:02d}_{phase}.png'
        render_panel(idx,phase,path)
        panels.append(path)
    ANDROID_STILLS.mkdir(parents=True,exist_ok=True)
    WEB_STILLS.mkdir(parents=True,exist_ok=True)
    still=ANDROID_STILLS/f'still{idx+1:02d}.jpg'
    # Thumbnail is from frame zero only, never the conflict or outcome.
    with Image.open(panels[0]) as im:
        im.save(still,quality=83,optimize=True)
    (WEB_STILLS/still.name).write_bytes(still.read_bytes())
    ANDROID_VIDEOS.mkdir(parents=True,exist_ok=True)
    WEB_VIDEOS.mkdir(parents=True,exist_ok=True)
    output=ANDROID_VIDEOS/f'clip{idx+1:02d}.mp4'
    concat=temporary/f'clip{idx+1:02d}.txt'
    # Two unobtrusive tableau transitions, 6 sec per page; no captions or music.
    concat.write_text(''.join(f"file '{panel}'\nduration 6\n" for panel in panels) + f"file '{panels[-1]}'\n",encoding='utf-8')
    args=['ffmpeg','-hide_banner','-loglevel','error','-y','-f','concat','-safe','0','-i',str(concat),
          '-vf','fps=6,format=yuv420p','-an','-c:v','libx264','-preset','veryfast','-crf','29',
          '-movflags','+faststart','-t','18',str(output)]
    subprocess.run(args,check=True)
    (WEB_VIDEOS/output.name).write_bytes(output.read_bytes())
    return output,still


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--sample',type=int,default=0,help='1-based single clip index')
    args=parser.parse_args()
    indexes=range(len(STORIES)) if args.sample==0 else [args.sample-1]
    with tempfile.TemporaryDirectory(prefix='dopagaki_picturebook_') as d:
        for idx in indexes:
            output,still=make_video(idx,Path(d))
            print(f'{idx+1:02d} {STORIES[idx]["title"]}: {output.stat().st_size} B / thumbnail {still.stat().st_size} B',flush=True)

if __name__=='__main__': main()
