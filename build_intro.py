# -*- coding: utf-8 -*-
import os
from lxml import etree
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR, MSO_AUTO_SIZE
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.ns import qn
HERE=os.path.dirname(os.path.abspath(__file__)); A=lambda f: os.path.join(HERE,"assets",f)
P=lambda f: os.path.join(HERE,"预览图",f)
SERIF="Songti SC"; SANS="PingFang SC"
CREAM="F7F4EC"; PAPER="FDFCF8"; DARK="07363C"; TEAL="0E5C63"; TEAL2="2E7D82"
GOLD="C9A24B"; GOLD_D="9A7A2E"; GOLD_L="E4C987"; INK="1B2A2A"; BODY="4A5A59"; MUT="8B9998"
LINE="DCE3DF"; GHOST="E9E4D6"; GHOST_D="0D484F"; TT="E8F1EE"; SEAL="B5432F"
D_TXT="F3F0E7"; D_MUT="8FB0B1"; D_GOLD="D9B96A"
SW,SH,M=13.333,7.5,0.85; CW=SW-2*M
def _f(r,s,fo,c,b=False,sp=None):
    r.font.size=Pt(s); r.font.bold=b; r.font.color.rgb=RGBColor.from_string(c); r.font.name=fo
    p=r._r.get_or_add_rPr()
    for t in ("ea","cs"):
        e=p.find(qn("a:"+t))
        if e is None: e=etree.SubElement(p,qn("a:"+t))
        e.set("typeface",fo)
    if sp is not None: p.set("spc",str(int(sp*100)))
AL={"l":PP_ALIGN.LEFT,"c":PP_ALIGN.CENTER,"r":PP_ALIGN.RIGHT}; AN={"t":MSO_ANCHOR.TOP,"m":MSO_ANCHOR.MIDDLE}
def txt(sl,x,y,w,h,ps,a="t"):
    if ps and "anchor" in ps[0]: a=ps[0]["anchor"]
    tb=sl.shapes.add_textbox(Inches(x),Inches(y),Inches(w),Inches(h))
    tf=tb.text_frame; tf.word_wrap=True; tf.auto_size=MSO_AUTO_SIZE.NONE
    tf.margin_left=tf.margin_right=tf.margin_top=tf.margin_bottom=0
    tf.vertical_anchor=AN[a]
    for i,p in enumerate(ps):
        pa=tf.paragraphs[0] if i==0 else tf.add_paragraph()
        pa.alignment=AL[p.get("al","l")]
        if p.get("lh"): pa.line_spacing=p["lh"]
        pa.space_before=Pt(p.get("sb",0)); pa.space_after=Pt(p.get("sa",0))
        for t,d in p["seg"]:
            r=pa.add_run(); r.text=t
            _f(r,d.get("s",12),d.get("f",SANS),d.get("c",INK),d.get("b",False),d.get("spc"))
    return tb
def rect(sl,x,y,w,h,fill=None,line=None,rad=None,lw=0.75):
    sh=sl.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE if rad else MSO_SHAPE.RECTANGLE,
        Inches(x),Inches(y),Inches(w),Inches(h))
    if rad:
        try: sh.adjustments[0]=rad
        except: pass
    if fill: sh.fill.solid(); sh.fill.fore_color.rgb=RGBColor.from_string(fill)
    else: sh.fill.background()
    if line: sh.line.color.rgb=RGBColor.from_string(line); sh.line.width=Pt(lw)
    else: sh.line.fill.background()
    st=sh._element.find(qn("p:style"))
    if st is not None: sh._element.remove(st)
    sh.shadow.inherit=False
    return sh
def hline(sl,x,y,w,c=LINE,h=0.008): rect(sl,x,y,w,h,fill=c)
def bg(sl,c): rect(sl,0,0,SW,SH,fill=c)
def eyebrow(sl,y,no,label,dark=False):
    txt(sl,M,y,6,0.3,[{"seg":[(no,{"s":10.5,"c":D_GOLD if dark else GOLD_D,"b":True,"spc":1.6}),("   ",{"s":10.5}),
                              (label,{"s":10.5,"c":D_MUT if dark else MUT,"spc":2.4})]}])
def ghost(sl,num,dark=False):
    txt(sl,10.9,0.35,1.6,1.3,[{"al":"r","lh":1.0,"seg":[(num,{"s":78,"f":SERIF,"c":GHOST_D if dark else GHOST})]}])
def foot(sl,i,dark=False):
    c=D_MUT if dark else MUT
    txt(sl,M,7.07,7,0.24,[{"seg":[("小小河工 · AI+ 公民河流教育计划",{"s":9,"c":c,"spc":0.6})]}])
    txt(sl,9.2,7.07,3.28,0.24,[{"al":"r","seg":[("%02d / 06"%i,{"s":9,"c":c,"spc":1.2})]}])
def phone(sl,path,x,y,h):
    w=h*430/900
    rect(sl,x-0.05,y-0.05,w+0.1,h+0.1,fill="FFFFFF",line=LINE,rad=0.03,lw=0.6)
    sl.shapes.add_picture(path,Inches(x),Inches(y),width=Inches(w),height=Inches(h))
    return w

prs=Presentation(); prs.slide_width=Inches(SW); prs.slide_height=Inches(SH)
BLANK=prs.slide_layouts[6]

# ---------- 01 封面 ----------
s=prs.slides.add_slide(BLANK); bg(s,DARK)
txt(s,M,0.72,6,0.3,[{"seg":[("产品介绍　·　2026",{"s":10.5,"c":D_GOLD,"spc":2.6})]}])
hline(s,M,1.12,0.9,GOLD)
txt(s,M-0.05,1.4,9,1.5,[{"seg":[("小小河工",{"s":88,"f":SERIF,"c":D_TXT,"spc":4})]}])
txt(s,M,3.02,8,0.5,[{"seg":[("AI+ 公民河流教育计划",{"s":21,"f":SERIF,"c":D_GOLD,"spc":3.2})]}])
txt(s,M,3.95,8.4,0.9,[{"seg":[("一条河不需要更多赞美。",{"s":17,"c":D_TXT}),
                             ("它需要更多记录。",{"s":17,"c":D_GOLD,"f":SERIF})]}])
txt(s,M,6.62,7,0.3,[{"seg":[("首站　·　北京清河",{"s":10,"c":"7FA6A4","spc":2.2})]}])

# ---------- 02 这条河 ----------
s=prs.slides.add_slide(BLANK); bg(s,CREAM); ghost(s,"01"); eyebrow(s,0.60,"01","这条河")
txt(s,M,0.92,11.6,0.6,[{"seg":[("一条河的六十年，",{"s":33,"f":SERIF,"c":INK}),
                                ("和它的 23.6 公里。",{"s":33,"f":SERIF,"c":TEAL})]}])
txt(s,M,1.66,11.4,1.0,[{"lh":1.62,"seg":[
 ("1965 年，安河闸建成，清河的起点从西山脚下挪到了京密引水渠东岸。六十年后，水回到了 III 类，鸟回来了九十余种，沿岸长出了十座公园。",{"s":11.2,"c":BODY})]}])
txt(s,M,2.34,11.4,0.4,[{"lh":1.62,"seg":[
 ("可关于这条河的记录，仍然只来自少数几次取样——两次取样之间的汛期、藻华、鸟群过境，大多没有留下痕迹。",{"s":11.2,"c":TEAL})]}])
bh=11.63*460/2400
s.shapes.add_picture(A("deck_map.png"),Inches(M),Inches(2.66),width=Inches(11.63),height=Inches(bh))
txt(s,M,2.66+bh+0.04,7,0.3,[{"seg":[("西起西山碧云寺 · 东至温榆河口 · 沿线十座水闸 · 四条支流汇入",{"s":8.5,"c":MUT,"spc":1.2})]}])
NUMS=[("23.6","公里","干流长度"),("10","座","水闸分十段"),("6","处","沿岸古迹"),("90+","种","观察到的鸟类")]
nx=M
for v,u,k in NUMS:
    txt(s,nx,5.62,2.6,0.5,[{"seg":[(v,{"s":26,"f":SERIF,"c":TEAL}),(u,{"s":9,"c":MUT})]}])
    txt(s,nx,6.12,2.6,0.3,[{"seg":[(k,{"s":9,"c":MUT,"spc":1.4})]}])
    nx+=2.92
hline(s,M,5.50,CW,"E4E0D4")
foot(s,2)

# ---------- 03 十座闸 ----------
s=prs.slides.add_slide(BLANK); bg(s,CREAM); ghost(s,"02"); eyebrow(s,0.60,"02","内容")
txt(s,M,0.92,11.6,0.6,[{"seg":[("十座闸，",{"s":33,"f":SERIF,"c":INK}),
                              ("就是一条河的十节课。",{"s":33,"f":SERIF,"c":TEAL})]}])
txt(s,M,1.62,11.4,0.4,[{"seg":[("每一座闸都有名字、年份、闸型和一段自己的故事。这是孩子上岗前要认下的东西，也是这套内容最难被复制的地方。",{"s":10.8,"c":BODY})]}])
GATES=[("01","安河闸","—","京密引水渠东岸，南距颐和园约 1 公里。「清0」起点，1965 年建，双孔钢闸泄洪"),
 ("02","肖家河闸","1.6 km","肖家河桥西。彩虹桥地标，安河闸到此处河道最曲折"),
 ("03","树村闸","1.9 km","圆明园正北。闸上带楼、闸桥一体，十闸中最美的一座"),
 ("04","京包闸","1.7 km","京包铁路西侧。箭亭立交四线交汇，万泉河在此汇入"),
 ("05","清河闸","2.4 km","清河大桥西侧。小月河口，旁有明代广济桥与古清真寺"),
 ("06","下清河闸","2.6 km","奥森北墙外。闸桥一体，只供步行与骑行；自此岸坡转自然"),
 ("07","羊坊闸","2.9 km","立水桥西南 600 米。两岸土坡之始，清洋河在此汇入"),
 ("08","外环跌水闸","1.4 km","地铁 13 号线外 150 米。十闸中唯一的拦水坝"),
 ("09","沈家闸","4.3 km","温榆河公园西部。闸距最远的一段，进入滨水慢行系统"),
 ("10","沙子营闸","0.3 km","清河尾端。唯一翻板式钢闸，全开时平卧可当桥")]
TY=2.28
for i,(no,nm,dist,desc) in enumerate(GATES):
    y=TY+i*0.415
    txt(s,M,y,0.5,0.34,[{"anchor":"m","seg":[(no,{"s":8.5,"c":GOLD_D,"spc":0.8})]}])
    txt(s,M+0.55,y,1.45,0.34,[{"anchor":"m","seg":[(nm,{"s":10.5,"b":True,"c":INK})]}])
    txt(s,M+2.05,y,1.1,0.34,[{"anchor":"m","seg":[(dist,{"s":9,"c":MUT})]}])
    txt(s,M+3.2,y,8.4,0.34,[{"anchor":"m","seg":[(desc,{"s":9.6,"c":BODY})]}])
    hline(s,M,y+0.385,11.55,"EBE6D9")
txt(s,M,6.62,11.4,0.4,[{"seg":[("四类知识域：水闸工程　·　历史遗产　·　三山五园　·　生态科普",{"s":9.5,"c":TEAL,"spc":1.2})]}])
foot(s,3)

# ---------- 04 三种用法 ----------
s=prs.slides.add_slide(BLANK); bg(s,CREAM); ghost(s,"03"); eyebrow(s,0.60,"03","产品")
txt(s,M,0.92,11,0.6,[{"seg":[("一个 App，",{"s":33,"f":SERIF,"c":INK}),("三种用法。",{"s":33,"f":SERIF,"c":TEAL})]}])
txt(s,M,1.66,11.2,0.4,[{"seg":[("线上培训、现场巡河、自由探索——三件事互不打扰，共用一本护照。",{"s":11.5,"c":BODY})]}])
COLS=[("clean-02-巡河.png","巡河","要到了才解锁","到达点位 → 掉落任务 → 拍照记录"),
      ("clean-02-点位.png","记录","看所有人的","按点位排，谁记过什么都在这里"),
      ("clean-04-探索.png","探索","随手就能用","拍一张，听它在系统里干什么")]
for i,(f,t,d1,d2) in enumerate(COLS):
    x=1.55+i*3.55
    phone(s,P(f),x,2.20,3.9)
    txt(s,x-0.05,6.26,2.1,0.3,[{"seg":[("0%d"%(i+1),{"s":9,"f":SERIF,"c":GOLD_D}),("　"+t,{"s":12.5,"b":True,"c":INK})]}])
    txt(s,x-0.05,6.56,2.3,0.3,[{"seg":[(d1,{"s":9.2,"c":TEAL,"b":True})]}])
    txt(s,x-0.05,6.82,2.35,0.3,[{"seg":[(d2,{"s":8.8,"c":MUT})]}])
foot(s,4)

# ---------- 05 记录与价值 ----------
s=prs.slides.add_slide(BLANK); bg(s,CREAM); ghost(s,"04"); eyebrow(s,0.60,"04","记录")
txt(s,M,0.92,11,0.6,[{"seg":[("一条记录，",{"s":33,"f":SERIF,"c":INK}),("长什么样。",{"s":33,"f":SERIF,"c":TEAL})]}])
txt(s,M,1.66,11.2,0.4,[{"seg":[("孩子以为在盖章，其实在给这条河建档——下面这些字段，就是研究机构能直接引用的格式。",{"s":11.2,"c":BODY})]}])
F=[("点位","清河闸 · 点位 05","空间可比"),("时间","10-22 14:32","时间序列"),
   ("类型","水文 / 物种 / 岸线 / 异常","决定谁来用"),("观测","透明度：低；白鹭 ×2","可统计、可作图"),
   ("证据","照片 1 张（剥离位置）","可复核"),("观察者","NO.057 · 巡河员","可信度加权"),
   ("许可","CC BY-NC 4.0","机构能用")]
TY=2.28
for i2,(a,b,c) in enumerate(F):
    y=TY+i2*0.50
    txt(s,M,y,1.5,0.42,[{"anchor":"m","seg":[(a,{"s":10.2,"c":GOLD_D,"spc":1.2})]}])
    txt(s,M+1.5,y,3.5,0.42,[{"anchor":"m","seg":[(b,{"s":10.8,"c":INK})]}])
    txt(s,M+5.0,y,2.2,0.42,[{"anchor":"m","seg":[(c,{"s":9.4,"c":MUT})]}])
    hline(s,M,y+0.46,7.3,"E7E2D5")
QX=8.15
txt(s,QX,2.26,4.3,0.3,[{"seg":[("四种人，各取所需",{"s":10.8,"b":True,"c":TEAL,"spc":1.2})]}])
hline(s,QX,2.60,4.33,"D8D3C4")
U=[("孩子与家庭","一个身份、一本护照、一条写进成长档案的巡河线"),
   ("公园与文旅","一套四季更新、不重复的内容资产，和十个到访理由"),
   ("河长办 / 研究机构","高密度、低成本、可比对的观察网络，补上专业巡测的空档"),
   ("资助方 / 品牌","可追溯、可引用的公益成果，而不是一张活动照片")]
uy=2.76
for n,d in U:
    txt(s,QX,uy,4.3,0.3,[{"seg":[(n,{"s":10.5,"b":True,"c":INK})]}])
    txt(s,QX,uy+0.26,4.3,0.5,[{"lh":1.45,"seg":[(d,{"s":9.2,"c":BODY})]}])
    uy+=0.79
foot(s,5)

# ---------- 06 现在 ----------
s=prs.slides.add_slide(BLANK); bg(s,DARK); ghost(s,"05",True); eyebrow(s,0.60,"05","现在",True)
txt(s,M,0.92,11,0.6,[{"seg":[("现在扫码，",{"s":33,"f":SERIF,"c":D_TXT}),("就能走一趟。",{"s":33,"f":SERIF,"c":D_GOLD})]}])
txt(s,M,1.66,8.4,0.4,[{"seg":[("不是规划，是已经能打开的东西。",{"s":11.5,"c":"C9D8D6"})]}])
D=[("01","可交互的 Demo","扫码即玩、免下载，十站全部开放，水墨路线随进度亮起"),
   ("02","上岗培训已成型","十座闸的名字、年份、闸型，一条河的历史与地理都在里头"),
   ("03","现场出勤已跑通","四类任务，每条产出带点位与时间的结构化记录")]
dy=2.24
for no,h,d in D:
    txt(s,M,dy,0.6,0.3,[{"seg":[(no,{"s":10,"c":GOLD,"b":True,"spc":1.0})]}])
    txt(s,M+0.62,dy-0.04,5.6,0.3,[{"seg":[(h,{"s":13,"b":True,"c":D_TXT})]}])
    txt(s,M+0.62,dy+0.30,6.1,0.6,[{"lh":1.5,"seg":[(d,{"s":10,"c":"A9C0BE"})]}])
    dy+=0.92
QX,QY,QS=8.62,2.18,1.45
s.shapes.add_picture(A("qr_demo.png"),Inches(QX),Inches(QY),width=Inches(QS),height=Inches(QS))
txt(s,QX-0.4,QY+QS+0.1,QS+0.8,0.3,[{"al":"r","seg":[("扫码开始巡河",{"s":8.8,"c":"9FC0C6","spc":1.0})]}])
# 记录字段条
hline(s,M,5.96,CW,"2A6469")
txt(s,M,6.10,2.2,0.3,[{"seg":[("接下来 90 天",{"s":9,"c":D_GOLD,"spc":2})]}])
txt(s,M+1.85,6.08,10.4,0.3,[{"seg":[("一段河（1 公里）　·　一所学校　·　一份开放的季节数据集",{"s":11,"c":"C9D8D6"})]}])
txt(s,M,6.48,11.6,0.5,[{"seg":[("一条河不需要更多赞美。",{"s":18,"f":SERIF,"c":"C9D8D6"}),
                             ("它需要更多记录。",{"s":18,"f":SERIF,"c":D_GOLD})]}])
foot(s,6,True)

prs.core_properties.title="小小河工 · AI+ 公民河流教育计划"
out=os.path.join(HERE,"小小河工-产品介绍6页.pptx")
prs.save(out); print("saved",out)
