# -*- coding: utf-8 -*-
import os
from lxml import etree
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR, MSO_AUTO_SIZE
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.ns import qn

HERE = os.path.dirname(os.path.abspath(__file__))
A = lambda f: os.path.join(HERE, "assets", f)
MM = 1/25.4
SERIF="Songti SC"; SANS="PingFang SC"
CREAM="F5F1E7"; DARK="07363C"; TEAL="0E4A52"; GOLD="C9A24B"; GOLD_D="9A7A2E"
INK="0A2E33"; BODY="394F50"; MUT="8B9895"; LINE="DCD5C4"; SEAL="B5432F"
D_TXT="F3F0E7"; D_GOLD="D9B96A"; D_MUT="8FB0B1"

def _fmt(r,size,font,color,bold=False,spc=None):
    r.font.size=Pt(size); r.font.bold=bold
    r.font.color.rgb=RGBColor.from_string(color); r.font.name=font
    rPr=r._r.get_or_add_rPr()
    for tag in ("ea","cs"):
        el=rPr.find(qn("a:"+tag))
        if el is None: el=etree.SubElement(rPr,qn("a:"+tag))
        el.set("typeface",font)
    if spc is not None: rPr.set("spc",str(int(spc*100)))

ALIGN={"l":PP_ALIGN.LEFT,"c":PP_ALIGN.CENTER,"r":PP_ALIGN.RIGHT}
ANCH={"t":MSO_ANCHOR.TOP,"m":MSO_ANCHOR.MIDDLE,"b":MSO_ANCHOR.BOTTOM}

def txt(sl,x,y,w,h,paras,anchor="t"):
    if paras and "anchor" in paras[0]: anchor=paras[0]["anchor"]
    tb=sl.shapes.add_textbox(Inches(x*MM),Inches(y*MM),Inches(w*MM),Inches(h*MM))
    tf=tb.text_frame; tf.word_wrap=True; tf.auto_size=MSO_AUTO_SIZE.NONE
    tf.margin_left=tf.margin_right=tf.margin_top=tf.margin_bottom=0
    tf.vertical_anchor=ANCH[anchor]
    for i,p in enumerate(paras):
        pa=tf.paragraphs[0] if i==0 else tf.add_paragraph()
        pa.alignment=ALIGN[p.get("al","l")]
        if p.get("lh"): pa.line_spacing=p["lh"]
        pa.space_before=Pt(p.get("sb",0)); pa.space_after=Pt(p.get("sa",0))
        for t,d in p["seg"]:
            r=pa.add_run(); r.text=t
            _fmt(r,d.get("s",10),d.get("f",SANS),d.get("c",INK),d.get("b",False),d.get("spc"))
    return tb

def rect(sl,x,y,w,h,fill=None,line=None,radius=None,lw=0.75):
    shp=sl.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE if radius else MSO_SHAPE.RECTANGLE,
        Inches(x*MM),Inches(y*MM),Inches(w*MM),Inches(h*MM))
    if radius:
        try: shp.adjustments[0]=radius
        except: pass
    if fill: shp.fill.solid(); shp.fill.fore_color.rgb=RGBColor.from_string(fill)
    else: shp.fill.background()
    if line: shp.line.color.rgb=RGBColor.from_string(line); shp.line.width=Pt(lw)
    else: shp.line.fill.background()
    st=shp._element.find(qn("p:style"))
    if st is not None: shp._element.remove(st)
    shp.shadow.inherit=False
    shp.text_frame.word_wrap=True
    return shp

def hline(sl,x,y,w,color=LINE,h=0.4):
    return rect(sl,x,y,w,h,fill=color)

def dot(sl,cx,cy,d,color):
    shp=sl.shapes.add_shape(MSO_SHAPE.OVAL,Inches((cx-d/2)*MM),Inches((cy-d/2)*MM),Inches(d*MM),Inches(d*MM))
    shp.fill.solid(); shp.fill.fore_color.rgb=RGBColor.from_string(color)
    shp.line.fill.background()
    st=shp._element.find(qn("p:style"))
    if st is not None: shp._element.remove(st)
    shp.shadow.inherit=False

W,H=297,420
prs=Presentation(); prs.slide_width=Inches(W*MM); prs.slide_height=Inches(H*MM)
s=prs.slides.add_slide(prs.slide_layouts[6])
rect(s,0,0,W,H,fill=CREAM)

# ================= 页眉（最后绘制，置顶） =================
def header():
    rect(s,0,0,W,92,fill=DARK)

    txt(s,16,15,150,6,[{"seg":[("北京 · 清河",{"s":9,"c":D_GOLD,"spc":3.2})]}])
    txt(s,14.4,22,180,44,[{"seg":[("小小河工",{"s":108,"f":SERIF,"c":D_TXT,"spc":4})]}])
    txt(s,16,64,170,6,[{"seg":[("AI 公民河流教育计划",{"s":12.5,"c":D_GOLD,"spc":3.4})]}])
    txt(s,16,75,170,9,[{"seg":[("走一趟，替这条河记十件事。",{"s":14,"f":SERIF,"c":"C9D8D6"})]}])

    # 右侧三数
    ST=[("23.6","km","干流长度"),("10","座","水闸分十段"),("4","类","可采集任务")]
    sx=186
    for v,u,k in ST:
        txt(s,sx,30,30,12,[{"seg":[(v,{"s":26,"f":SERIF,"c":D_TXT}),(u,{"s":9,"c":D_MUT})]}])
        txt(s,sx,44,34,4,[{"seg":[(k,{"s":7.5,"c":D_MUT,"spc":1.2})]}])
        sx+=33

# ================= 河带 =================
bh=297*410/2400
s.shapes.add_picture(A("poster_band.png"), Inches(0), Inches(92*MM), width=Inches(W*MM), height=Inches(bh*MM))
txt(s,16,92+bh+3,200,5,[{"seg":[("清河 · 十座水闸 · 四条支流　│　朱印处为起点：安河闸",{"s":7.5,"c":MUT,"spc":1.6})]}])

# ================= 三块屏 =================
SHOT_Y=158; SH_H=152; SH_W=SH_H*430/900
gap=(W-2*16-SH_W*3)/2
shots=[("demo-02-巡河.png","巡河","到达点位，任务才会掉落"),
       ("demo-02-点位.png","记录","按点位排，谁记的都在这儿"),
       ("demo-04-探索.png","探索","拍一张，听它在系统里干什么")]
for i,(fn,t,d) in enumerate(shots):
    x=16+i*(SH_W+gap)
    rect(s,x-0.6,SHOT_Y-0.6,SH_W+1.2,SH_H+1.2,fill="FFFFFF",line=LINE,radius=0.03)
    s.shapes.add_picture(os.path.join(HERE,"预览图",fn), Inches(x*MM), Inches(SHOT_Y*MM),
                         width=Inches(SH_W*MM), height=Inches(SH_H*MM))
    txt(s,x,SHOT_Y+SH_H+6,SH_W,6,[{"seg":[("0%d"% (i+1),{"s":8,"f":SERIF,"c":GOLD_D}),
                                          ("　"+t,{"s":12,"b":True,"c":INK})]}])
    txt(s,x,SHOT_Y+SH_H+13,SH_W+2,5,[{"seg":[(d,{"s":8.5,"c":BODY})]}])

# ================= 数据条 =================
DY=SHOT_Y+SH_H+30
hline(s,16,DY-6,W-32,LINE,0.6)
txt(s,16,DY,60,5,[{"seg":[("一条记录长什么样",{"s":8,"c":MUT,"spc":2})]}])
FIELDS=[("点位","清河闸 05"),("时间","10-22 14:32"),("类型","水文观测"),
        ("观测","透明度·低"),("证据","照片 1 张"),("观察者","NO.057")]
fx=16
for k,v in FIELDS:
    wv=38
    rect(s,fx,DY+8,wv,16,fill="FBF8F0",line=LINE,radius=0.05)
    txt(s,fx+3,DY+10,wv-6,3.5,[{"seg":[(k,{"s":6.5,"c":GOLD_D,"spc":1.4})]}])
    txt(s,fx+3,DY+14.5,wv-6,4,[{"seg":[(v,{"s":8,"c":INK})]}])
    fx+=wv+4

USES=[("孩子","一个身份、一本护照、一条巡河线"),
      ("公众","按点位看这条河的四季"),
      ("机构","可直接引用的结构化记录")]
ux=16
for name,desc in USES:
    txt(s,ux,DY+30,60,4,[{"seg":[(name,{"s":9,"b":True,"c":TEAL}),
                                  ("　"+desc,{"s":8,"c":BODY})]}])
    ux+=92

# ================= 页脚 =================
rect(s,0,H-46,W,46,fill=DARK)
qs=H-46+12
s.shapes.add_picture(A("qr_demo.png"),Inches((W-16-30)*MM),Inches((qs-8)*MM),width=Inches(28*MM),height=Inches(28*MM))

out=os.path.join(HERE,"小小河工-A3海报.pptx")
prs.save(out)
print("saved",out)
