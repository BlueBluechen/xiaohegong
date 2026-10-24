# -*- coding: utf-8 -*-
"""《小小河工》6 页对外方案 —— 以河为目标，孩子是参与者"""
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

SERIF = "Songti SC"
SANS = "PingFang SC"

CREAM = "F7F4EC"; PAPER = "FDFCF8"
DARK = "07363C"; TEAL = "0E5C63"; TEAL2 = "2E7D82"
GOLD = "C9A24B"; GOLD_D = "9A7A2E"; GOLD_L = "E4C987"
INK = "1B2A2A"; BODY = "4A5A59"; MUT = "8B9998"
LINE = "DCE3DF"; GHOST_L = "E9E4D6"; GHOST_D = "0D484F"
TT = "E8F1EE"; GT = "F8EFDC"
D_TXT = "F3F0E7"; D_MUT = "8FB0B1"; D_GOLD = "D9B96A"

SW, SH, M = 13.333, 7.5, 0.85
CW = SW - 2 * M


def _fmt(r, size, font, color, bold=False, spc=None, italic=False):
    r.font.size = Pt(size); r.font.bold = bold; r.font.italic = italic
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


def txt(slide, x, y, w, h, paras, anchor="t"):
    if paras and "anchor" in paras[0]:
        anchor = paras[0]["anchor"]
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
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
            r = para.add_run(); r.text = t
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
        shp.fill.solid(); shp.fill.fore_color.rgb = RGBColor.from_string(fill)
    else:
        shp.fill.background()
    if line:
        shp.line.color.rgb = RGBColor.from_string(line); shp.line.width = Pt(lw)
    else:
        shp.line.fill.background()
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
    shp.fill.solid(); shp.fill.fore_color.rgb = RGBColor.from_string(color)
    shp.line.fill.background()
    style = shp._element.find(qn("p:style"))
    if style is not None:
        shp._element.remove(style)
    shp.shadow.inherit = False
    return shp


def bg(slide, color):
    return rect(slide, 0, 0, SW, SH, fill=color)


def footer(slide, idx, dark=False):
    c = D_MUT if dark else MUT
    txt(slide, M, 7.07, 7.0, 0.24,
        [{"seg": [("小小河工 · AI 公民河流教育计划", {"s": 9, "c": c, "spc": 0.6})]}])
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
s.shapes.add_picture(A("cover_ink.png"), Inches(7.333), Inches(0),
                     width=Inches(6.0), height=Inches(7.5))
rect(s, 7.283, 0, 0.05, 7.5, fill=GOLD)

txt(s, M, 0.92, 6.2, 0.3,
    [{"seg": [("公益项目提案　·　2026　·　北京 · 海淀",
               {"s": 11, "c": GOLD_L, "spc": 2.2})]}])
hline(s, M, 1.38, 0.9, GOLD)

txt(s, M - 0.04, 1.58, 6.2, 1.5,
    [{"seg": [("小小河工", {"s": 96, "f": SERIF, "c": D_TXT, "spc": 6})]}])

txt(s, M, 3.46, 6.2, 0.5,
    [{"seg": [("AI 公民河流教育计划", {"s": 25, "f": SERIF, "c": GOLD_L, "spc": 3})]}])

txt(s, M, 4.02, 6.1, 0.3,
    [{"seg": [("首站　北京 · 海淀 · 清河　23.6 公里 · 十站 · 四条支流",
               {"s": 11.5, "c": "7FA6A4", "spc": 0.4})]}])

hline(s, M, 4.58, 5.9, "1C5559")

txt(s, M, 4.82, 6.0, 0.9,
    [{"lh": 1.55, "seg": [("让每个孩子，", {"s": 21, "c": D_TXT}),
                          ("成为一条河的证人。", {"s": 21, "c": D_GOLD, "f": SERIF})]}])

txt(s, M, 6.55, 6.2, 0.6,
    [{"lh": 1.5, "seg": [("以河为目标　·　孩子是参与者　·　记录是产品",
                          {"s": 10.5, "c": "7FA6A4", "spc": 1.6})]}])

s.notes_slide.notes_text_frame.text = (
    "一句话讲清定位：这个项目的受益人是这条河，孩子是参与者，产品是记录。这是一份公益项目提案，不是一次活动的复盘。")

# ---------------------------------------------------------------- 02 问题
s = prs.slides.add_slide(BLANK)
bg(s, CREAM)
ghost(s, "01")
eyebrow(s, M, 0.63, "01", "问题")

txt(s, M, 0.97, 9.6, 0.65,
    [{"seg": [("清河被修好了，", {"s": 38, "f": SERIF, "c": INK}),
              ("但它还没被读懂。", {"s": 38, "f": SERIF, "c": TEAL})]}])

txt(s, M, 1.88, 7.6, 0.6,
    [{"lh": 1.6, "seg": [("水回到了 III 类，鸟回来了九十余种。可关于它的记录，只来自少数几次取样。",
                          {"s": 13.5, "c": BODY})]}])

rows = [
    ("23.6", "km", "一条河的完整长度",
     "沿线十座水闸、六处古迹、四条支流汇入。监测点集中在几个断面上，两次取样之间的汛期、藻华、鸟群过境，大多没有留下记录。"),
    ("0", "条", "沿岸公众产生、可比较的记录",
     "散步的人每天几十万步，发现散落在朋友圈、相册和记忆里。没有统一口径，无法比较，也无法追溯。"),
    ("1", "次", "大多数孩子与这条河的接触",
     "来过、拍过照、很开心。第二天，这条河在孩子的生活里就消失了。"),
]
ys = [2.78, 3.94, 5.10]
for (num, unit, head, body), y in zip(rows, ys):
    txt(s, M, y - 0.06, 1.55, 0.75,
        [{"seg": [(num, {"s": 30, "f": SERIF, "c": GOLD, "spc": 0.5})]}])
    if unit:
        txt(s, M, y + 0.48, 1.3, 0.3,
            [{"seg": [(unit, {"s": 11, "c": MUT, "spc": 1.0})]}])
    txt(s, M + 1.62, y - 0.03, 5.95, 0.34,
        [{"seg": [(head, {"s": 14.5, "b": True, "c": INK})]}])
    txt(s, M + 1.62, y + 0.37, 6.05, 0.76,
        [{"lh": 1.55, "seg": [(body, {"s": 10.8, "c": BODY})]}])
    if y < 5.0:
        hline(s, M, y + 1.03, 7.55, "E4E0D4")

s.shapes.add_picture(A("gate_dusk.jpg"), Inches(9.05), Inches(1.88),
                     width=Inches(3.7), height=Inches(2.4667))
hline(s, 9.05, 4.52, 0.5, GOLD)
txt(s, 9.05, 4.68, 3.7, 1.2,
    [{"lh": 1.65, "seg": [("清河上的闸，闸上带楼、闸桥一体。沿线十座，每一座都有自己的名字、年份和一次改建。",
                           {"s": 9.8, "c": MUT})]}])

rect(s, M, 6.42, CW, 0.56, fill=DARK)
txt(s, M + 0.42, 6.42, CW - 0.8, 0.56,
    [{"anchor": "m", "seg": [("河有流量，孩子有记忆，城市没有数据。",
                              {"s": 14, "c": D_TXT, "f": SERIF, "spc": 1.2})]}])
footer(s, 2)

s.notes_slide.notes_text_frame.text = (
    "注意：不要把它讲成教育缺口的项目。讲数据缺口——这条河每天被看见几十万次，却没有一条可用的记录。")

# ---------------------------------------------------------------- 03 产品
s = prs.slides.add_slide(BLANK)
bg(s, CREAM)
ghost(s, "02")
eyebrow(s, M, 0.63, "02", "产品")

txt(s, M, 0.97, 10.6, 0.6,
    [{"seg": [("一个孩子的八分钟，", {"s": 36, "f": SERIF, "c": INK}),
              ("是这条河的一次取样。", {"s": 36, "f": SERIF, "c": TEAL})]}])
txt(s, M, 1.80, 10.8, 0.4,
    [{"seg": [("孩子看到的是护照和印章。这条河得到的是十条结构化记录——两者是同一次动作。",
               {"s": 12.5, "c": BODY})]}])

# 左：时间轴（纵向）
LX = M
txt(s, LX, 2.36, 4.2, 0.3,
    [{"seg": [("第一次巡河 · 8 分钟", {"s": 11.5, "b": True, "c": TEAL, "spc": 1.2})]}])
steps = [
    ("0′", "扫码，领护照", "编号 NO.057，职级：见习河工"),
    ("2′", "上岗培训", "先认得这道闸：名字、年份、闸型"),
    ("5′", "现场出勤", "看水、看岸、看鸟，留下一件观察到的事"),
    ("8′", "盖章交班", "记录入库，护照上多一枚章"),
]
sy = 2.78
for t, head, sub in steps:
    txt(s, LX, sy, 0.9, 0.34, [{"seg": [(t, {"s": 12, "f": SERIF, "c": GOLD_D, "b": True})]}])
    txt(s, LX + 0.95, sy - 0.02, 3.35, 0.3, [{"seg": [(head, {"s": 13.5, "b": True, "c": INK})]}])
    txt(s, LX + 0.95, sy + 0.32, 3.4, 0.3, [{"lh": 1.5, "seg": [(sub, {"s": 10.3, "c": BODY})]}])
    sy += 0.86

# 右：四类任务
RX = 6.95
txt(s, RX, 2.36, 5.0, 0.3,
    [{"seg": [("四类任务，决定记录长什么样", {"s": 11.5, "b": True, "c": TEAL, "spc": 1.2})]}])
tasks = [
    ("水文观测", "透明度 · 水色 · 流速", "最容易被机构直接使用"),
    ("物种观察", "水鸟 · 植被 · 声环境", "看物候，看季节之间的差别"),
    ("岸线观察", "岸型 · 植被连续性 · 人为痕迹", "对应河道的物理结构"),
    ("异常通报", "垃圾 · 漂浮物 · 排口", "最先被日常巡护用上的那一类"),
]
ty = 2.74
for name, what, why in tasks:
    rect(s, RX, ty, 5.53, 0.78, fill=PAPER, line=LINE, radius=0.06)
    txt(s, RX + 0.28, ty, 1.5, 0.78, [{"anchor": "m", "seg": [(name, {"s": 13, "b": True, "c": INK})]}])
    txt(s, RX + 1.72, ty + 0.13, 2.1, 0.3, [{"seg": [(what, {"s": 9.8, "c": BODY})]}])
    txt(s, RX + 1.72, ty + 0.44, 3.5, 0.28, [{"seg": [(why, {"s": 9.2, "c": MUT})]}])
    ty += 0.90

hline(s, M, 6.38, CW, "E4E0D4")
txt(s, M, 6.54, 11.4, 0.4,
    [{"seg": [("孩子走完八分钟，这条河多了十条记录。", {"s": 12, "c": BODY}),
              ("接下来的问题只有一个：这些记录，能不能被用。", {"s": 12, "c": TEAL, "b": True})]}])
footer(s, 3)

s.notes_slide.notes_text_frame.text = (
    "这一页讲体验，但落点要在右边：四类任务不是玩法分类，是数据分类。"
    "每一类对应一种可以被使用的东西。")

# ---------------------------------------------------------------- 04 数据
s = prs.slides.add_slide(BLANK)
bg(s, DARK)
ghost(s, "03", dark=True)
eyebrow(s, M, 0.63, "03", "数据", dark=True)

txt(s, M, 0.97, 8.8, 0.6,
    [{"seg": [("一条记录，", {"s": 36, "f": SERIF, "c": D_TXT}),
              ("长什么样。", {"s": 36, "f": SERIF, "c": D_GOLD})]}])
txt(s, M, 1.72, 11.4, 0.4,
    [{"seg": [("「河边有鸟」不是数据。「10 月 22 日 14:32 · 清河闸 05 · 白鹭 2 只 · 有照片」才是。",
               {"s": 12.5, "c": "C9D8D6"})]}])

FIELDS = [
    ("点位", "清河闸 · 点位 05", "空间可比"),
    ("时间", "2026-10-22 14:32", "时间序列"),
    ("类型", "水文 / 物种 / 岸线 / 异常", "决定谁来用"),
    ("观测", "透明度：低；白鹭 ×2", "可统计、可作图"),
    ("证据", "照片 1 张（剥离位置信息）", "可复核"),
    ("环境", "晴 · 前 48 小时无降雨", "否则无法解读"),
    ("观察者", "NO.057 · 巡河员", "可信度加权"),
    ("许可", "CC BY-NC 4.0", "研究机构能用"),
]
TX, TY = M, 2.42
CW1, CW2, CW3 = 1.55, 3.75, 2.55
for i, (a, b, c) in enumerate(FIELDS):
    y = TY + i * 0.5
    txt(s, TX, y, CW1, 0.4, [{"anchor": "m", "seg": [(a, {"s": 10.5, "c": D_GOLD, "spc": 1.2})]}])
    txt(s, TX + CW1, y, CW2, 0.4, [{"anchor": "m", "seg": [(b, {"s": 11.5, "c": D_TXT})]}])
    txt(s, TX + CW1 + CW2, y, CW3, 0.4, [{"anchor": "m", "seg": [(c, {"s": 10, "c": "8FA9A8"})]}])
    hline(s, TX, y + 0.46, CW1 + CW2 + CW3, "17545B")

# 右侧：三道质量关
QX = 8.78
txt(s, QX, 2.42, 3.7, 0.3,
    [{"seg": [("孩子的观察凭什么能用", {"s": 11.5, "b": True, "c": D_GOLD, "spc": 1.0})]}])
hline(s, QX, 2.80, 3.70, "2A6469")
qs = [
    ("AI 预校验", "照片与选项矛盾时提示重拍，坏数据当场拦下"),
    ("同点位交叉", "同一位置多次观测取众数，离群值标灰"),
    ("人工抽检", "按 5% 抽检，连续两季合格的观察者升权重"),
]
qy = 2.96
for name, desc in qs:
    txt(s, QX, qy, 1.35, 0.3, [{"seg": [(name, {"s": 10.8, "b": True, "c": D_TXT})]}])
    txt(s, QX + 1.42, qy, 2.28, 0.72, [{"lh": 1.5, "seg": [(desc, {"s": 9.5, "c": "A9C0BE"})]}])
    qy += 0.86

rect(s, QX, 5.86, 3.70, 0.98, fill=None, line="2A6469", radius=0.06)
txt(s, QX + 0.22, 5.86, 3.3, 0.98,
    [{"anchor": "m", "lh": 1.5, "seg": [("职级不只是游戏奖励，", {"s": 9.8, "c": "93AFAE"}),
                                          ("它是数据权重。", {"s": 9.8, "c": D_GOLD, "b": True})]}])
footer(s, 4, dark=True)

s.notes_slide.notes_text_frame.text = (
    "全篇最硬的一页。字段表就是产品规格，也是对外方案的核心资产。"
    "评委如果只记住一件事，应该是这张表。")

# ---------------------------------------------------------------- 05 价值
s = prs.slides.add_slide(BLANK)
bg(s, CREAM)
ghost(s, "04")
eyebrow(s, M, 0.63, "04", "价值")

txt(s, M, 0.97, 11.4, 0.6,
    [{"seg": [("四类人，", {"s": 35, "f": SERIF, "c": INK}),
              ("从同一条记录里，各取所需。", {"s": 35, "f": SERIF, "c": TEAL})]}])
txt(s, M, 1.80, 11.2, 0.4,
    [{"seg": [("一个公益项目能不能长久，不取决于谁掏钱，取决于每一方是不是真的拿到了东西。",
               {"s": 12.5, "c": BODY})]}])

HX = [M, 3.30, 6.90]
txt(s, HX[0], 2.26, 2.2, 0.26, [{"seg": [("谁", {"s": 9.5, "c": MUT, "spc": 2})]}])
txt(s, HX[1], 2.26, 3.4, 0.26, [{"seg": [("他们想要什么", {"s": 9.5, "c": MUT, "spc": 2})]}])
txt(s, HX[2], 2.26, 5.4, 0.26, [{"seg": [("他们能从这件事里拿到", {"s": 9.5, "c": MUT, "spc": 2})]}])
hline(s, M, 2.56, CW, "D8D3C4")

ROWS = [
    ("孩子与家庭", "一次真实的、能带走的经历",
     "一个身份、一本护照，一条写进成长档案的巡河线"),
    ("公园与文旅", "让人愿意再来一次的理由",
     "一套四季更新、不重复的内容资产，和十个到访理由"),
    ("河长办 / 研究机构", "更密、更省、可比对的观察",
     "一条河的高密度观察网络，补上专业巡测的空档"),
    ("资助方 / 品牌", "能被第三方验证的成果",
     "可追溯、可引用的公益成果，而不是一张活动照片"),
]
ry = 2.72
for role, want, gain in ROWS:
    txt(s, HX[0], ry, 2.35, 0.6, [{"lh": 1.45, "seg": [(role, {"s": 14, "b": True, "c": INK})]}])
    txt(s, HX[1], ry + 0.02, 3.40, 0.6, [{"lh": 1.55, "seg": [(want, {"s": 11, "c": BODY})]}])
    txt(s, HX[2], ry + 0.01, 5.55, 0.6, [{"lh": 1.5, "seg": [(gain, {"s": 12.2, "c": TEAL})]}])
    hline(s, M, ry + 0.78, CW, "E7E2D5")
    ry += 0.92

rect(s, M, 6.28, CW, 0.62, fill="EFEADC", radius=0.05)
txt(s, M + 0.34, 6.28, 2.4, 0.62,
    [{"anchor": "m", "seg": [("合作方式", {"s": 10, "c": MUT, "spc": 2})]}])
txt(s, M + 2.05, 6.28, 9.6, 0.62,
    [{"anchor": "m", "seg": [("点位共建", {"s": 12.5, "c": INK, "b": True}),
                              ("　·　", {"s": 12, "c": GOLD}),
                              ("课程采购", {"s": 12.5, "c": INK, "b": True}),
                              ("　·　", {"s": 12, "c": GOLD}),
                              ("数据赞助", {"s": 12.5, "c": INK, "b": True}),
                              ("　　三种都能从一个点位开始。", {"s": 10.5, "c": MUT})]}])
footer(s, 5)

s.notes_slide.notes_text_frame.text = (
    "这一页不是成本模型，是价值模型。不要先讲谁付费，先讲每一方拿到什么；"
    "拿到的东西成立，钱自然会来。")

# ---------------------------------------------------------------- 06 进展
s = prs.slides.add_slide(BLANK)
bg(s, DARK)
ghost(s, "05", dark=True)
eyebrow(s, M, 0.63, "05", "进展", dark=True)

txt(s, M, 0.97, 10.6, 0.6,
    [{"seg": [("这件事已经开始了。", {"s": 34, "f": SERIF, "c": D_TXT}),
              ("现在扫码，就能走一趟。", {"s": 34, "f": SERIF, "c": D_GOLD})]}])
txt(s, M, 1.72, 7.2, 0.4,
    [{"seg": [("不是规划，是已经能打开的东西——每走完一站，这条河就多一条记录。",
               {"s": 12.5, "c": "C9D8D6"})]}])

DONE = [
    ("01", "可交互的巡河 Demo", "扫码即玩、免下载，十站全部开放，水墨路线图会随进度亮起"),
    ("02", "上岗培训已经成型", "十座闸的名字、年份、闸型，一条河的历史与地理，都在里头"),
    ("03", "现场出勤已经跑通", "四类任务，每条都产出带点位与时间的结构化记录"),
]
dy = 2.36
for no, head, desc in DONE:
    txt(s, M, dy, 0.6, 0.32, [{"seg": [(no, {"s": 10.5, "c": GOLD, "b": True, "spc": 1.0})]}])
    txt(s, M + 0.62, dy - 0.04, 6.0, 0.32, [{"seg": [(head, {"s": 14, "b": True, "c": D_TXT})]}])
    txt(s, M + 0.62, dy + 0.32, 6.1, 0.6, [{"lh": 1.55, "seg": [(desc, {"s": 10.5, "c": "A9C0BE"})]}])
    dy += 1.02

# 右：一个具体的观察例子
PX, PY, PW, PH = 7.52, 2.22, 4.96, 3.50
rect(s, PX, PY, PW, PH, fill=CREAM, radius=0.04)
txt(s, PX + 0.34, PY + 0.28, PW - 0.68, 0.3,
    [{"seg": [("秋冬的河岸，就是最好的教材", {"s": 10, "c": GOLD_D, "spc": 1.4})]}])
txt(s, PX + 0.34, PY + 0.68, PW - 0.68, 0.4,
    [{"lh": 1.5, "seg": [("裸露的河岸石 · 下降的水位线 · 变白的芦苇",
                          {"s": 13, "c": INK, "f": SERIF})]}])
hline(s, PX + 0.34, PY + 1.22, PW - 0.68, "DCD6C6")
LINES = [("孩子学到的是", "物候与水文的常识"),
         ("顺带补上的是", "滨水慢行系统里没写进说明牌的部分"),
         ("真正留下的是", "这个点位、这个季节的一条数据")]
ly = PY + 1.38
for k, v in LINES:
    txt(s, PX + 0.34, ly, 1.25, 0.3, [{"seg": [(k, {"s": 9.5, "c": MUT})]}])
    txt(s, PX + 1.58, ly - 0.02, PW - 1.94, 0.5, [{"lh": 1.5, "seg": [(v, {"s": 10.2, "c": BODY})]}])
    ly += 0.62

hline(s, M, 5.92, CW, "2A6469")
txt(s, M, 6.04, 2.0, 0.3, [{"seg": [("接下来 90 天", {"s": 10, "c": D_GOLD, "spc": 2})]}])
txt(s, M + 1.85, 6.02, 10.5, 0.34,
    [{"seg": [("一段河（1 公里）　·　一所学校　·　一份开放的季节数据集",
               {"s": 12.5, "c": "C9D8D6"})]}])

txt(s, M, 6.52, 11.6, 0.5,
    [{"seg": [("一条河不需要更多赞美。", {"s": 20, "f": SERIF, "c": "C9D8D6"}),
              ("它需要更多记录。", {"s": 20, "f": SERIF, "c": D_GOLD})]}])
footer(s, 6, dark=True)

s.notes_slide.notes_text_frame.text = (
    "这一页讲「已经在做」，不是「打算做」。右边那个秋冬河岸的例子最好现场讲，"
    "因为它同时是生物课、景观课和一条数据。")

prs.core_properties.title = "小小河工 · AI 公民河流教育计划"
prs.core_properties.author = "ACC · 清河"
prs.core_properties.subject = "AI 公民河流教育计划 · 公益项目提案（6 页）"

out = os.path.join(HERE, "小小河工·AI公民河流教育计划-对外方案6页.pptx")
prs.save(out)
print("saved:", out)
