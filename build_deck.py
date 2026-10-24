# -*- coding: utf-8 -*-
"""搭建《一条河 · AI 公民河流教育计划》6 页产品方案"""
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

SERIF = "Songti SC"     # 展示 / 大标题 / 数字
SANS  = "PingFang SC"   # 正文 / 标签

CREAM = "F7F4EC"; PAPER = "FDFCF8"
DARK  = "07363C"; TEAL = "0E5C63"; TEAL2 = "2E7D82"
GOLD  = "C9A24B"; GOLD_D = "9A7A2E"; GOLD_L = "E4C987"
INK   = "1B2A2A"; BODY = "4A5A59"; MUT = "8B9998"
LINE  = "DCE3DF"; GHOST_L = "E9E4D6"; GHOST_D = "0D484F"
TT    = "E8F1EE"; GT = "F8EFDC"
D_TXT = "F3F0E7"; D_MUT = "8FB0B1"; D_GOLD = "D9B96A"

SW, SH, M = 13.333, 7.5, 0.85
CW = SW - 2 * M


def _fmt(r, size, font, color, bold=False, spc=None, italic=False):
    r.font.size = Pt(size)
    r.font.bold = bold
    r.font.italic = italic
    r.font.color.rgb = RGBColor.from_string(color)
    r.font.name = font
    rPr = r._r.get_or_add_rPr()
    for tag in ("ea", "cs"):
        el = rPr.find(qn("a:" + tag))
        if el is None:
            el = etree.SubElement(rPr, qn("a:" + tag))
        el.set("typeface", font)
    if spc is not None:
        rPr.set("spc", str(int(spc * 100)))


ALIGN = {"l": PP_ALIGN.LEFT, "c": PP_ALIGN.CENTER, "r": PP_ALIGN.RIGHT}
ANCH = {"t": MSO_ANCHOR.TOP, "m": MSO_ANCHOR.MIDDLE, "b": MSO_ANCHOR.BOTTOM}


def txt(slide, x, y, w, h, paras, anchor="t", wrap=True):
    if paras and "anchor" in paras[0]:
        anchor = paras[0]["anchor"]
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = wrap
    tf.auto_size = MSO_AUTO_SIZE.NONE
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = ANCH[anchor]
    for i, p in enumerate(paras):
        para = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        para.alignment = ALIGN[p.get("al", "l")]
        if p.get("lh"):
            para.line_spacing = p["lh"]
        para.space_before = Pt(p.get("sb", 0))
        para.space_after = Pt(p.get("sa", 0))
        for t, d in p["seg"]:
            r = para.add_run()
            r.text = t
            _fmt(r, d.get("s", 12), d.get("f", SANS), d.get("c", INK),
                 d.get("b", False), d.get("spc"))
    return tb


def rect(slide, x, y, w, h, fill=None, line=None, radius=None, lw=1.0):
    shp = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE if radius else MSO_SHAPE.RECTANGLE,
        Inches(x), Inches(y), Inches(w), Inches(h))
    if radius:
        try:
            shp.adjustments[0] = radius
        except Exception:
            pass
    if fill:
        shp.fill.solid()
        shp.fill.fore_color.rgb = RGBColor.from_string(fill)
    else:
        shp.fill.background()
    if line:
        shp.line.color.rgb = RGBColor.from_string(line)
        shp.line.width = Pt(lw)
    else:
        shp.line.fill.background()
    # 去掉主题样式引用（否则 LibreOffice / PowerPoint 会带默认阴影）
    style = shp._element.find(qn("p:style"))
    if style is not None:
        shp._element.remove(style)
    shp.shadow.inherit = False
    shp.text_frame.word_wrap = True
    return shp


def hline(slide, x, y, w, color=LINE, h=0.008):
    return rect(slide, x, y, w, h, fill=color)


def dot(slide, cx, cy, d, color):
    shp = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(cx - d / 2), Inches(cy - d / 2),
                                 Inches(d), Inches(d))
    shp.fill.solid()
    shp.fill.fore_color.rgb = RGBColor.from_string(color)
    shp.line.fill.background()
    style = shp._element.find(qn("p:style"))
    if style is not None:
        shp._element.remove(style)
    shp.shadow.inherit = False
    return shp


def bg(slide, color):
    r = rect(slide, 0, 0, SW, SH, fill=color)
    return r


def footer(slide, idx, dark=False):
    c = D_MUT if dark else MUT
    txt(slide, M, 7.07, 7.0, 0.24,
        [{"seg": [("一条河 · AI 公民河流教育计划", {"s": 9, "c": c, "spc": 0.6})]}])
    txt(slide, 9.2, 7.07, 3.28, 0.24,
        [{"al": "r", "seg": [("%02d / 06" % idx, {"s": 9, "c": c, "spc": 1.2})]}])


def ghost(slide, num, dark=False):
    txt(slide, 10.9, 0.35, 1.6, 1.3,
        [{"al": "r", "lh": 1.0, "seg": [(num, {"s": 78, "f": SERIF,
                                               "c": GHOST_D if dark else GHOST_L})]}])


def eyebrow(slide, x, y, no, label, dark=False):
    txt(slide, x, y, 6.0, 0.3,
        [{"seg": [(no, {"s": 10.5, "f": SANS, "c": D_GOLD if dark else GOLD_D, "b": True, "spc": 1.6}),
                  ("   ", {"s": 10.5}),
                  (label, {"s": 10.5, "f": SANS, "c": D_MUT if dark else MUT, "spc": 2.4})]}])


# ======================================================================
prs = Presentation()
prs.slide_width = Inches(SW)
prs.slide_height = Inches(SH)
BLANK = prs.slide_layouts[6]

# ---------------------------------------------------------------- 01 封面
s = prs.slides.add_slide(BLANK)
bg(s, DARK)

# 右侧影像
s.shapes.add_picture(A("cover_swan.jpg"), Inches(7.333), Inches(0),
                     width=Inches(6.0), height=Inches(7.5))
rect(s, 7.283, 0, 0.05, 7.5, fill=GOLD)

txt(s, M, 0.92, 6.2, 0.3,
    [{"seg": [("2026　AI + 公益 黑客松　·　联合提案",
               {"s": 11, "c": GOLD_L, "spc": 2.2})]}])
hline(s, M, 1.38, 0.9, GOLD)

txt(s, M - 0.04, 1.58, 6.2, 1.5,
    [{"seg": [("一条河", {"s": 96, "f": SERIF, "c": D_TXT, "spc": 6})]}])

txt(s, M, 3.46, 6.2, 0.5,
    [{"seg": [("AI 公民河流教育计划", {"s": 25, "f": SERIF, "c": GOLD_L, "spc": 3})]}])

txt(s, M, 4.02, 6.1, 0.3,
    [{"seg": [("首款产品　小天鹅寻母记 2.0　·　由「清河十闸」升级",
               {"s": 11.5, "c": "7FA6A4", "spc": 0.4})]}])

hline(s, M, 4.58, 5.9, "1C5559")

txt(s, M, 4.82, 6.0, 0.9,
    [{"lh": 1.55, "seg": [("让每个孩子，", {"s": 21, "c": D_TXT}),
                          ("成为一条河的证人。", {"s": 21, "c": D_GOLD, "f": SERIF})]}])

txt(s, M, 6.55, 6.2, 0.6,
    [{"lh": 1.5, "seg": [("北京 · 清河　23.6 公里　·　十座水闸　·　沿岸九十余种鸟类",
                          {"s": 10.5, "c": "7FA6A4", "spc": 0.6})]}])

s.notes_slide.notes_text_frame.text = (
    "开场不要先讲技术。先讲一个画面：这条 23.6 公里的河，每年被几十万人走过，"
    "但没有一个孩子能带走它。我们今天带来的是：让每个孩子成为这条河的证人。")

# ---------------------------------------------------------------- 02 问题
s = prs.slides.add_slide(BLANK)
bg(s, CREAM)
ghost(s, "01")
eyebrow(s, M, 0.63, "01", "问题")

txt(s, M, 0.97, 9.6, 0.65,
    [{"seg": [("清河被修好了，", {"s": 38, "f": SERIF, "c": INK}),
              ("但它还没被读懂。", {"s": 38, "f": SERIF, "c": TEAL})]}])

txt(s, M, 1.92, 7.7, 0.8,
    [{"lh": 1.6, "seg": [("水回到了 III 类，鸟回来了九十余种。但一条河真正活下来，"
                          "靠的不是治理，是被看见。", {"s": 13.5, "c": BODY})]}])

rows = [
    ("23.6", "km", "一条穿城而过的河，没有一门以它为教材的课",
     "沿线十座真闸、日均三千到五千人的公园。孩子来过、拍过照，却没人告诉他：脚下这道闸，为什么建在这里。"),
    ("1 : 30", "", "一位自然导师，对三十个孩子",
     "户外自然教育最缺的不是热情，是师资。一个人问不出三十个不同的问题，也记不住三十条不同的观察。"),
    ("0", "", "活动结束，没有留下一条数据",
     "没有学习效果的证据，也没有一条对河流有用的记录——资助方无法评估，项目无法迭代，孩子下个假期不会再回来。"),
]
ys = [2.86, 4.02, 5.18]
for (num, unit, head, body), y in zip(rows, ys):
    txt(s, M, y - 0.06, 1.55, 0.75,
        [{"al": "l", "seg": [(num, {"s": 30, "f": SERIF, "c": GOLD, "spc": 0.5})]}])
    if unit:
        txt(s, M, y + 0.48, 1.3, 0.3,
            [{"seg": [(unit, {"s": 11, "c": MUT, "spc": 1.0})]}])
    txt(s, M + 1.62, y - 0.03, 5.95, 0.34,
        [{"seg": [(head, {"s": 14.5, "b": True, "c": INK})]}])
    txt(s, M + 1.62, y + 0.37, 6.05, 0.76,
        [{"lh": 1.55, "seg": [(body, {"s": 10.8, "c": BODY})]}])
    if y < 5.1:
        hline(s, M, y + 1.03, 7.55, "E4E0D4")

# 右侧影像 + 图注
s.shapes.add_picture(A("gate_dusk.jpg"), Inches(9.05), Inches(1.92),
                     width=Inches(3.7), height=Inches(2.4667))
hline(s, 9.05, 4.56, 0.5, GOLD)
txt(s, 9.05, 4.72, 3.7, 1.0,
    [{"lh": 1.65, "seg": [("清河上的闸，闸上带楼、闸桥一体。沿线十座，每一座都有自己的名字、年份和一次改建。",
                           {"s": 9.8, "c": MUT})]}])

# 底部结论条
rect(s, M, 6.42, CW, 0.56, fill=DARK)
txt(s, M + 0.42, 6.42, CW - 0.8, 0.56,
    [{"anchor": "t", "lh": 1.0, "seg": [("河有流量，孩子有记忆，城市没有数据。",
                                        {"s": 14, "c": D_TXT, "f": SERIF, "spc": 1.2})]}])
s.shapes[-1].text_frame.vertical_anchor = MSO_ANCHOR.MIDDLE
footer(s, 2)

s.notes_slide.notes_text_frame.text = (
    "数字是递降的：23.6 公里、1 比 30、最后一个 0。"
    "这几年清河治理的成果是真实的，但治理的下一步是「公众参与」，而公众参与的前提是「有人真的认识这条河」。")

# ---------------------------------------------------------------- 03 产品
s = prs.slides.add_slide(BLANK)
bg(s, CREAM)
ghost(s, "02")
eyebrow(s, M, 0.63, "02", "产品")

txt(s, M, 0.97, 10.2, 0.6,
    [{"seg": [("一款游戏，长出", {"s": 36, "f": SERIF, "c": INK}),
              ("三种公共资产。", {"s": 36, "f": SERIF, "c": TEAL})]}])
txt(s, M, 1.86, 10.6, 0.4,
    [{"seg": [("游戏只是入口。真正被留下的是三样东西：孩子会问问题的能力、一条河的连续观测、一套别的城市能直接复制的模板。",
               {"s": 12.5, "c": BODY})]}])

bands = [
    ("01", "玩 · 入口", "已建成 · 可扫码", "FDFCF8", LINE,
     "小天鹅寻母：沿清河十闸闯关，每过一闸，解锁一段这条河的十年之变。已有可交互 Demo，纯网页、免下载。"),
    ("02", "探 · 核心", "本次新增", TT, None,
     "每座闸后接一个真实任务——水色、流速、鸟类、垃圾、桥与芦苇。不是四选一，是走出去看、拍下来、记下来。"),
    ("03", "报 · 价值", "本次新增", GT, None,
     "观察经 AI 识别与交叉校验后，进入公开的「清河健康地图」；同时生成孩子的《河流护照》与班级学情。"),
]
ys = [2.42, 3.55, 4.68]
for (no, name, tag, fill, ln, desc), y in zip(bands, ys):
    rect(s, M, y, CW, 1.02, fill=fill, line=ln, radius=0.055)
    txt(s, M + 0.32, y, 0.72, 1.02,
        [{"anchor": "m", "seg": [(no, {"s": 22, "f": SERIF, "c": GOLD})]}])
    txt(s, M + 1.06, y, 1.6, 1.02,
        [{"anchor": "m", "seg": [(name, {"s": 15.5, "b": True, "c": INK})]}])
    txt(s, M + 2.72, y, 6.55, 1.02,
        [{"anchor": "m", "lh": 1.62, "seg": [(desc, {"s": 11.2, "c": BODY})]}])
    txt(s, M + 9.55, y, 1.9, 1.02,
        [{"al": "r", "anchor": "m", "seg": [(tag, {"s": 9, "c": GOLD_D if no == "01" else TEAL2, "spc": 0.3})]}])

# 时间轴
hline(s, M, 5.95, CW, "E4E0D4")
txt(s, M, 6.06, 4.0, 0.3,
    [{"seg": [("一个孩子的 40 分钟", {"s": 11.5, "b": True, "c": TEAL, "spc": 1.2})]}])

tl = [("0′", "扫码开始"), ("5′", "第一闸开启"), ("12′", "领到任务"),
      ("20′", "拍下水面"), ("30′", "AI 追问"), ("40′", "生成护照")]
x0, x1 = 1.12, 12.14
step = (x1 - x0) / (len(tl) - 1)
hline(s, x0, 6.53, x1 - x0, "D8D3C4")
for i, (t, label) in enumerate(tl):
    cx = x0 + i * step
    dot(s, cx, 6.53, 0.115, GOLD if i in (0, 5) else TEAL)
    al = "l" if i == 0 else ("r" if i == len(tl) - 1 else "c")
    lx = cx - 0.02 if al == "l" else (cx - 1.78 if al == "r" else cx - 0.9)
    txt(s, lx, 6.68, 1.8, 0.24,
        [{"al": al, "seg": [(t + " ", {"s": 10.5, "f": SERIF, "c": GOLD_D, "b": True}),
                            (label, {"s": 9.6, "c": BODY})]}])
footer(s, 3)

s.notes_slide.notes_text_frame.text = (
    "这一页是全篇的骨架。玩是钩子，探是核心，报才是公益价值所在。"
    "注意第三条：孩子的观察会变成公开数据，这是把教育项目和公益数据打通的唯一办法。")

# ---------------------------------------------------------------- 04 AI
s = prs.slides.add_slide(BLANK)
bg(s, DARK)
ghost(s, "03", dark=True)
eyebrow(s, M, 0.63, "03", "AI", dark=True)

txt(s, M, 0.97, 9.8, 0.6,
    [{"seg": [("为什么", {"s": 36, "f": SERIF, "c": D_TXT}),
              ("非得", {"s": 36, "f": SERIF, "c": D_GOLD}),
              ("是 AI。", {"s": 36, "f": SERIF, "c": D_TXT})]}])
txt(s, M, 1.86, 11.5, 0.4,
    [{"seg": [("一位自然导师对三十个孩子，问不出三十个不同的问题。AI 可以——而且每一句追问，都顺手变成了一条可用的数据。",
               {"s": 12.5, "c": "C9D8D6"})]}])

# 对话卡片
CX, CY, CWd, CHd = M, 2.40, 5.55, 4.46
rect(s, CX, CY, CWd, CHd, fill=CREAM, radius=0.05)
# 头像
s.shapes.add_picture(A("swan_mark.png"), Inches(CX + 0.3), Inches(CY + 0.20),
                     width=Inches(0.3), height=Inches(0.3))
txt(s, CX + 0.72, CY + 0.23, 2.6, 0.26,
    [{"seg": [("小天鹅向导", {"s": 10.5, "b": True, "c": TEAL})]}])
txt(s, CX + 2.9, CY + 0.25, 2.4, 0.24,
    [{"al": "r", "seg": [("点位 05 · 清河闸 · 14:32", {"s": 8.6, "c": MUT})]}])
hline(s, CX + 0.3, CY + 0.62, CWd - 0.6, "DCD6C6")

bubbles = [
    ("swan", "你拍的这块水面，颜色像什么？"),
    ("kid", "有点绿。"),
    ("swan", "草地那种绿，还是墨汁那种绿？能看见水底的石子吗？"),
    ("kid", "看不见石头。"),
    ("swan", "好，那记下来：看不清水底。是水太深，还是水太浑？"),
]
y = CY + 0.80
for who, text in bubbles:
    if who == "swan":
        w = 4.05
        h = 0.46 if len(text) <= 23 else 0.68
        rect(s, CX + 0.3, y, w, h, fill="E7EFEC", radius=0.16)
        txt(s, CX + 0.52, y, w - 0.44, h,
            [{"anchor": "m", "lh": 1.45, "seg": [(text, {"s": 11, "c": INK})]}])
    else:
        w = 2.55
        h = 0.38
        rect(s, CX + CWd - 0.3 - w, y, w, h, fill=TEAL, radius=0.18)
        txt(s, CX + CWd - 0.3 - w + 0.2, y, w - 0.4, h,
            [{"al": "r", "anchor": "m", "seg": [(text, {"s": 11, "c": "FFFFFF"})]}])
    y += h + 0.12

# 记录条
rect(s, CX + 0.3, CY + CHd - 0.54, CWd - 0.6, 0.40, fill="E4D7B4", radius=0.1)
txt(s, CX + 0.5, CY + CHd - 0.54, CWd - 1.0, 0.40,
    [{"anchor": "m", "seg": [("已记录　清河闸 05 · 透明度 低 · 14:32", {"s": 9.2, "c": "6B5417", "b": True})]}])
txt(s, CX + 0.5, CY + CHd - 0.54, CWd - 1.0, 0.40,
    [{"al": "r", "anchor": "m", "seg": [("今日第 87 条", {"s": 9.2, "c": "9A7A2E"})]}])

# 右栏
RX = 6.95
RW = 5.55
abil = [
    ("01", "追问", "不公布答案，按孩子说的话决定下一个问题。一次对话，就是一次分层教学。"),
    ("02", "看见", "一张随手拍，变成一条带物种、点位、时间的观测记录。"),
    ("03", "校验", "知识库检索 + 同点位多人交叉 + 官方水质比对，坏数据进不了地图。"),
    ("04", "举证", "每个孩子一份《河流护照》，每个班一份学情。公益项目第一次有了效果证据。"),
]
ys = [2.52, 3.42, 4.32, 5.22]
for (no, name, desc), y in zip(abil, ys):
    txt(s, RX, y - 0.04, 0.5, 0.3,
        [{"seg": [(no, {"s": 10, "c": GOLD, "b": True, "spc": 0.8})]}])
    txt(s, RX + 0.52, y - 0.07, 0.9, 0.32,
        [{"seg": [(name, {"s": 14.5, "b": True, "c": D_TXT})]}])
    txt(s, RX + 1.38, y - 0.04, RW - 1.38, 0.7,
        [{"lh": 1.55, "seg": [(desc, {"s": 10.6, "c": "A9C0BE"})]}])
    if no != "04":
        hline(s, RX, y + 0.78, RW, "155056")

# 底线
rect(s, RX, 6.24, RW, 0.62, fill=None, line="2A6469", radius=0.08)
txt(s, RX + 0.22, 6.24, RW - 0.44, 0.62,
    [{"anchor": "m", "lh": 1.45, "seg": [("底线　", {"s": 9, "c": D_GOLD, "b": True, "spc": 0.5}),
                                          ("不采集人脸与精确坐标　·　AI 输出人工抽审　·　不排名、不羞辱、不制造焦虑",
                                           {"s": 8.8, "c": "93AFAE"})]}])
footer(s, 4, dark=True)

s.notes_slide.notes_text_frame.text = (
    "这段对话不是设计稿，是我们认为 AI 在这个场景里唯一站得住的用法：不是出题，是追问。"
    "追问的价值在于——它同时产出了两样东西：孩子的思考，和一条结构化观测。")

# ---------------------------------------------------------------- 05 模式
s = prs.slides.add_slide(BLANK)
bg(s, CREAM)
ghost(s, "04")
eyebrow(s, M, 0.63, "04", "模式")

txt(s, M, 0.97, 10.8, 0.6,
    [{"seg": [("免费给孩子，", {"s": 35, "f": SERIF, "c": INK}),
              ("卖给愿意为「效果」付费的人。", {"s": 35, "f": SERIF, "c": TEAL})]}])
txt(s, M, 1.86, 11.0, 0.4,
    [{"seg": [("公益项目最怕的不是没钱，是说不清钱变成了什么。所以我们先把三件事分清楚：谁被服务、谁在付费、什么是公共的。",
               {"s": 12.5, "c": BODY})]}])

cols = [
    ("谁被服务", "永久免费", GOLD,
     ["公立学校与社区儿童之家", "没有研学预算的家庭", "缺少自然导师的班级"]),
    ("谁在付费", "为效果买单", TEAL,
     ["场景方：场地、IP 与现场运营", "基金会：项目经费与督导", "企业与政府采购：算力、CSR、研学服务"]),
    ("什么是公共的", "开放出去", TEAL2,
     ["内容模板：一河一校，换城市 4 周上线", "观测数据 API，开放可下载", "研学报告标准与教师手册"]),
]
xs = [M, 4.78, 8.72]
for (title, sub, color, items), x in zip(cols, xs):
    txt(s, x, 2.52, 2.6, 0.3,
        [{"seg": [(title, {"s": 14, "b": True, "c": INK})]}])
    txt(s, x, 2.84, 2.8, 0.26,
        [{"seg": [(sub, {"s": 9.5, "c": color, "spc": 1.4})]}])
    hline(s, x, 3.14, 3.4, "D8D3C4")
    yy = 3.28
    for it in items:
        rect(s, x, yy + 0.10, 0.075, 0.075, fill=color)
        txt(s, x + 0.24, yy, 3.18, 0.62,
            [{"lh": 1.55, "seg": [(it, {"s": 10.6, "c": BODY})]}])
        yy += 0.62

# 图表横条：四个承诺
rect(s, M, 5.28, CW, 0.9, fill="EFEADC", radius=0.05)
txt(s, M + 0.34, 5.28, 3.4, 0.9,
    [{"anchor": "m", "lh": 1.45, "seg": [("首期 90 天，", {"s": 11, "c": BODY}),
                                          ("我们只敢承诺四个数", {"s": 11, "b": True, "c": INK})]}])
metrics = [("500", "名", "儿童完成完整探究"), ("1万", "条", "有效观测入库"),
           ("+25", "%", "前后测学习增益"), ("3", "条", "建议被采纳")]
mx = 4.12
for val, unit, label in metrics:
    txt(s, mx, 5.28, 1.4, 0.44,
        [{"anchor": "m", "seg": [(val, {"s": 19, "f": SERIF, "c": TEAL, "b": True}),
                                  (unit, {"s": 9, "c": MUT})]}])
    txt(s, mx, 5.72, 1.75, 0.3,
        [{"seg": [(label, {"s": 8.8, "c": MUT})]}])
    mx += 2.16

txt(s, M, 6.5, 11.4, 0.4,
    [{"seg": [("我们不拿 DAU 衡量公益。", {"s": 17, "f": SERIF, "c": INK}),
              ("　一次有效的追问、一条可用的记录、一个被学校留下的班，才是这套东西真正在长的部分。",
               {"s": 11, "c": BODY})]}])
footer(s, 5)

s.notes_slide.notes_text_frame.text = (
    "公益的可持续不是靠情怀，是靠把「谁付费」和「谁受益」分开。"
    "免费的是孩子，付费的是场景方、基金会和政府——他们买的不是曝光，是可被验证的效果。")

# ---------------------------------------------------------------- 06 计划
s = prs.slides.add_slide(BLANK)
bg(s, DARK)
ghost(s, "05", dark=True)
eyebrow(s, M, 0.63, "05", "计划", dark=True)

txt(s, M, 0.97, 9.9, 0.6,
    [{"seg": [("48 小时让它跑起来，", {"s": 35, "f": SERIF, "c": D_TXT}),
              ("90 天让它被验证。", {"s": 35, "f": SERIF, "c": D_GOLD})]}])

plan = [
    ("48 H", "黑客松现场 · 把「AI」从文案变成真的",
     ["真 AI 追问替换写死的提示　·　拍照识别接通 1 个点位",
      "一份《河流护照》　·　公开地图骨架，能看见别人的记录"]),
    ("90 D", "一所学校 · 一个学期",
     ["3 个班 · 500 名儿童 · 1 万条观测",
      "教师手册 v1 与前后测　·　开源模板 v0.1"]),
    ("12 M", "三条河 · 三个城市",
     ["换数据即复制　·　数据接入区级河长制平台",
      "模板开放给其他流域的公益伙伴"]),
]
ys = [2.0, 3.26, 4.52]
for (tag, head, desc), y in zip(plan, ys):
    txt(s, M, y, 1.15, 0.4,
        [{"seg": [(tag, {"s": 17, "f": SERIF, "c": D_GOLD, "spc": 1.0})]}])
    txt(s, M + 1.22, y - 0.03, 6.0, 0.32,
        [{"seg": [(head, {"s": 13.5, "b": True, "c": D_TXT})]}])
    txt(s, M + 1.22, y + 0.36, 6.15, 0.72,
        [{"lh": 1.62, "seg": [(line, {"s": 10.5, "c": "A9C0BE"})]} for line in desc])
    if tag != "12 M":
        hline(s, M, y + 1.12, 7.35, "155056")

# 右栏
RX = 8.78
txt(s, RX, 2.0, 1.4, 0.3,
    [{"seg": [("我们在找", {"s": 13, "b": True, "c": D_GOLD, "spc": 1.5})]}])
hline(s, RX, 2.36, 3.70, "2A6469")
seek = ["1 所试点学校（一个班就够）", "1 家公益机构（渠道与儿童服务经验）",
        "1 位水利 / 生态专家（把关知识库）", "算力，和一台景区大屏"]
yy = 2.52
for it in seek:
    rect(s, RX, yy + 0.08, 0.06, 0.06, fill=GOLD)
    txt(s, RX + 0.22, yy, 3.5, 0.56,
        [{"lh": 1.5, "seg": [(it, {"s": 10.3, "c": "C9D8D6"})]}])
    yy += 0.58

rect(s, RX, 4.92, 3.70, 0.72, fill=None, line=GOLD_D, radius=0.08)
txt(s, RX + 0.24, 4.92, 3.2, 0.72,
    [{"anchor": "m", "seg": [("给我们 48 小时，", {"s": 13, "b": True, "c": D_TXT}),
                              ("和一个班的孩子。", {"s": 13, "b": True, "c": D_GOLD})]}])

hline(s, M, 6.16, CW, "2A6469")
txt(s, M, 6.36, 11.6, 0.5,
    [{"seg": [("一条河不需要更多赞美。", {"s": 20, "f": SERIF, "c": "C9D8D6"}),
              ("它需要更多证人。", {"s": 20, "f": SERIF, "c": D_GOLD})]}])
footer(s, 6, dark=True)

s.notes_slide.notes_text_frame.text = (
    "收尾要具体：48 小时不是做 PPT，是把现在写死的提示换成真 AI，把一条记录真的传上地图。"
    "最后的诉求只有一个班。")

prs.core_properties.title = "一条河 · AI 公民河流教育计划"
prs.core_properties.author = "ACC · 清河文旅"
prs.core_properties.subject = "AI + 公益 黑客松联合提案（6 页）"

out = os.path.join(HERE, "一条河·AI公民河流教育计划-产品方案6页.pptx")
prs.save(out)
print("saved:", out, len(prs.slides.__iter__.__self__._sldIdLst), "slides")
