"""
生成复刻科学示意图的PPT
Schematic Mechanism for Synchronous NOx Removal and CO Oxidation over Mn-Fe/N-AC Catalyst
"""
import os
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.util import Cm
from pptx.oxml.ns import qn
from pptx.oxml import parse_xml
import copy
from lxml import etree


# ──────────────────────────────────────────────────────────────────────────────
# 颜色常量
# ──────────────────────────────────────────────────────────────────────────────
BLUE_TITLE_BG   = RGBColor(0x1F, 0x4E, 0x79)   # 深蓝标题背景
WHITE           = RGBColor(0xFF, 0xFF, 0xFF)
BLACK           = RGBColor(0x00, 0x00, 0x00)
DARK_GRAY       = RGBColor(0x26, 0x26, 0x26)

# 四个面板背景色
PANEL_TL_BG     = RGBColor(0xD0, 0xEA, 0xF8)   # 左上：浅蓝
PANEL_TR_BG     = RGBColor(0xFD, 0xF0, 0xD5)   # 右上：浅橙/黄
PANEL_BL_BG     = RGBColor(0xD5, 0xEB, 0xF5)   # 左下：浅蓝
PANEL_BR_BG     = RGBColor(0xFC, 0xE4, 0xEC)   # 右下：浅粉

CENTER_BG       = RGBColor(0xF0, 0xF0, 0xF0)   # 中心浅灰

# 粒子颜色
MN_COLOR        = RGBColor(0x80, 0x40, 0x80)   # 锰：紫色
FE_COLOR        = RGBColor(0xC0, 0x60, 0x20)   # 铁：橙棕
MN3O4_COLOR     = RGBColor(0x90, 0x50, 0x90)   # Mn3O4：紫
FE3O4_COLOR     = RGBColor(0xD0, 0x70, 0x30)   # Fe3O4：橙
CO_COLOR        = RGBColor(0xCC, 0x22, 0x22)   # CO：深红
CO2_COLOR       = RGBColor(0xAA, 0x11, 0x11)
NO_COLOR        = RGBColor(0x70, 0x50, 0x90)   # NO：紫
NH3_COLOR       = RGBColor(0x30, 0x80, 0xB0)   # NH3：蓝
OVEN_VACANCY    = RGBColor(0xF5, 0xF5, 0xDC)   # 氧空位框：米白
ARROW_BLUE      = RGBColor(0x2E, 0x75, 0xB6)   # 箭头蓝色

SLIDE_W = Inches(13.33)
SLIDE_H = Inches(7.5)


def make_prs():
    prs = Presentation()
    prs.slide_width  = SLIDE_W
    prs.slide_height = SLIDE_H
    return prs


# ──────────────────────────────────────────────────────────────────────────────
# 工具函数
# ──────────────────────────────────────────────────────────────────────────────
def add_rect(slide, left, top, width, height,
             fill_color=None, line_color=None, line_width_pt=1.0,
             corner_radius=None):
    """添加矩形色块"""
    shape = slide.shapes.add_shape(
        1,  # MSO_SHAPE_TYPE.RECTANGLE = 1
        Inches(left), Inches(top), Inches(width), Inches(height)
    )
    if fill_color:
        shape.fill.solid()
        shape.fill.fore_color.rgb = fill_color
    else:
        shape.fill.background()

    if line_color:
        shape.line.color.rgb = line_color
        shape.line.width = Pt(line_width_pt)
    else:
        shape.line.fill.background()

    if corner_radius is not None:
        # 通过 XML 设置圆角
        sp = shape._element
        prstGeom = sp.find('.//' + qn('a:prstGeom'))
        if prstGeom is not None:
            avLst = prstGeom.find(qn('a:avLst'))
            if avLst is None:
                avLst = etree.SubElement(prstGeom, qn('a:avLst'))
            gd = etree.SubElement(avLst, qn('a:gd'))
            gd.set('name', 'adj')
            gd.set('fmla', f'val {corner_radius}')

    return shape


def add_oval(slide, left, top, width, height, fill_color, line_color=None, line_width_pt=1.0):
    """添加椭圆"""
    shape = slide.shapes.add_shape(
        9,  # MSO_SHAPE_TYPE.OVAL = 9  (实际为 oval)
        Inches(left), Inches(top), Inches(width), Inches(height)
    )
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill_color
    if line_color:
        shape.line.color.rgb = line_color
        shape.line.width = Pt(line_width_pt)
    else:
        shape.line.fill.background()
    return shape


def add_textbox(slide, left, top, width, height, text,
                font_size=10, bold=False, italic=False,
                color=BLACK, align=PP_ALIGN.LEFT,
                word_wrap=True, font_name="Arial"):
    """添加文本框"""
    txBox = slide.shapes.add_textbox(
        Inches(left), Inches(top), Inches(width), Inches(height)
    )
    tf = txBox.text_frame
    tf.word_wrap = word_wrap
    p = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    run.font.size = Pt(font_size)
    run.font.bold = bold
    run.font.italic = italic
    run.font.color.rgb = color
    run.font.name = font_name
    return txBox


def add_textbox_multiline(slide, left, top, width, height, lines,
                           font_size=9, bold=False, color=BLACK,
                           align=PP_ALIGN.LEFT, font_name="Arial"):
    """多行文本框"""
    txBox = slide.shapes.add_textbox(
        Inches(left), Inches(top), Inches(width), Inches(height)
    )
    tf = txBox.text_frame
    tf.word_wrap = True
    first = True
    for line in lines:
        if first:
            p = tf.paragraphs[0]
            first = False
        else:
            p = tf.add_paragraph()
        p.alignment = align
        run = p.add_run()
        run.text = line
        run.font.size = Pt(font_size)
        run.font.bold = bold
        run.font.color.rgb = color
        run.font.name = font_name
    return txBox


def add_labeled_oval(slide, cx, cy, r, label, fill_color,
                     font_size=7, label_color=WHITE, line_color=None):
    """添加带标签的圆形粒子"""
    left = cx - r
    top  = cy - r
    add_oval(slide, left, top, 2*r, 2*r, fill_color,
             line_color=line_color or fill_color)
    add_textbox(slide, left, top, 2*r, 2*r, label,
                font_size=font_size, bold=True,
                color=label_color, align=PP_ALIGN.CENTER)


def add_arrow_connector(slide, x1, y1, x2, y2,
                         color=ARROW_BLUE, line_width_pt=1.5):
    """使用直线模拟箭头连接（python-pptx connector 有限制，用线代替）"""
    from pptx.util import Emu
    connector = slide.shapes.add_connector(
        1,  # MSO_CONNECTOR_STRAIGHT
        Inches(x1), Inches(y1), Inches(x2), Inches(y2)
    )
    connector.line.color.rgb = color
    connector.line.width = Pt(line_width_pt)
    return connector


# ──────────────────────────────────────────────────────────────────────────────
# 主函数：构建幻灯片
# ──────────────────────────────────────────────────────────────────────────────
def build_slide(prs):
    blank_layout = prs.slide_layouts[6]   # 空白版式
    slide = prs.slides.add_slide(blank_layout)

    # ── 0. 整体背景 (白色) ──────────────────────────────────────────────────
    bg = slide.background
    bg.fill.solid()
    bg.fill.fore_color.rgb = WHITE

    # ── 1. 标题栏 (深蓝) ────────────────────────────────────────────────────
    add_rect(slide, 0, 0, 13.33, 0.62, fill_color=BLUE_TITLE_BG)

    title_text = ("Schematic Mechanism for Synchronous NO\u2093 Removal "
                  "and CO Oxidation over Mn-Fe/N-AC Catalyst")
    tb = slide.shapes.add_textbox(Inches(0.15), Inches(0.05), Inches(13.0), Inches(0.55))
    tf = tb.text_frame
    tf.word_wrap = False
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    run = p.add_run()
    run.text = title_text
    run.font.size = Pt(18)
    run.font.bold = True
    run.font.color.rgb = WHITE
    run.font.name = "Arial"

    # ── 2. 四个面板框 ────────────────────────────────────────────────────────
    # 面板间距与尺寸
    px, py, pw, ph = 0.08, 0.68, 4.50, 3.25   # 左上
    add_rect(slide, px, py, pw, ph, fill_color=PANEL_TL_BG,
             line_color=RGBColor(0x2E, 0x75, 0xB6), line_width_pt=1.5)

    px2, py2, pw2, ph2 = 8.75, 0.68, 4.50, 3.25  # 右上
    add_rect(slide, px2, py2, pw2, ph2, fill_color=PANEL_TR_BG,
             line_color=RGBColor(0xD0, 0x80, 0x20), line_width_pt=1.5)

    px3, py3, pw3, ph3 = 0.08, 4.05, 4.50, 3.25  # 左下
    add_rect(slide, px3, py3, pw3, ph3, fill_color=PANEL_BL_BG,
             line_color=RGBColor(0x2E, 0x75, 0xB6), line_width_pt=1.5)

    px4, py4, pw4, ph4 = 8.75, 4.05, 4.50, 3.25  # 右下
    add_rect(slide, px4, py4, pw4, ph4, fill_color=PANEL_BR_BG,
             line_color=RGBColor(0xC0, 0x40, 0x60), line_width_pt=1.5)

    # ── 3. 中心面板 (灰色) ───────────────────────────────────────────────────
    add_rect(slide, 4.65, 0.68, 4.05, 6.62,
             fill_color=RGBColor(0xE8, 0xE8, 0xE8),
             line_color=RGBColor(0x99, 0x99, 0x99), line_width_pt=1.0)

    # ── 3a. 中心：六方孔道结构（用灰色矩形+暗色椭圆阵列模拟）────────────────
    # 绘制 N-AC 骨架（暗灰方格阵列，模拟 honeycomb 截面）
    struct_l, struct_t = 4.78, 0.85
    cell_w, cell_h = 0.55, 0.55
    cols, rows = 6, 9
    for r in range(rows):
        for c in range(cols):
            cl = struct_l + c * cell_w
            ct = struct_t + r * cell_h
            add_rect(slide, cl, ct, cell_w - 0.04, cell_h - 0.04,
                     fill_color=RGBColor(0xA0, 0xA0, 0xA0),
                     line_color=RGBColor(0x60, 0x60, 0x60), line_width_pt=0.5)
            # 孔道（空心）
            inner_m = 0.08
            add_rect(slide, cl + inner_m, ct + inner_m,
                     cell_w - 0.04 - 2*inner_m, cell_h - 0.04 - 2*inner_m,
                     fill_color=RGBColor(0xD0, 0xD0, 0xD0),
                     line_color=None)

    # ── 3b. 中心：Mn₃O₄ 和 Fe₃O₄ 粒子 ──────────────────────────────────────
    particles = [
        # (cx,   cy,    r,     label,     fill,            lbl_color)
        (5.35,  1.15,  0.22,  "Mn\u2083O\u2084", MN3O4_COLOR, WHITE),
        (6.55,  1.20,  0.22,  "Fe\u2083O\u2084", FE3O4_COLOR, WHITE),
        (5.25,  2.30,  0.20,  "Mn\u2083O\u2084", MN3O4_COLOR, WHITE),
        (6.30,  2.85,  0.20,  "Fe\u2083O\u2084", FE3O4_COLOR, WHITE),
        (5.60,  3.80,  0.20,  "Fe\u2083O\u2084", FE3O4_COLOR, WHITE),
        (6.65,  3.50,  0.18,  "Fe\u2083O\u2084", FE3O4_COLOR, WHITE),
        (5.80,  5.20,  0.18,  "Fe\u2083O\u2084", FE3O4_COLOR, WHITE),
        (6.70,  4.90,  0.18,  "Mn\u2083O\u2084", MN3O4_COLOR, WHITE),
    ]
    for cx, cy, r, label, fc, lc in particles:
        add_labeled_oval(slide, cx, cy, r, label, fc,
                         font_size=6, label_color=lc)

    # N 原子标记（蓝色小圆）
    n_positions = [
        (5.00, 1.60), (5.70, 1.55), (6.20, 1.65),
        (5.10, 2.70), (6.00, 2.40), (6.60, 2.20),
        (5.40, 3.20), (6.30, 3.10), (6.80, 3.80),
        (5.20, 4.30), (5.90, 4.60), (6.50, 5.40),
    ]
    for nx, ny in n_positions:
        add_oval(slide, nx - 0.10, ny - 0.10, 0.20, 0.20,
                 fill_color=RGBColor(0x20, 0x60, 0xC0),
                 line_color=None)
        add_textbox(slide, nx - 0.10, ny - 0.11, 0.20, 0.20, "N",
                    font_size=7, bold=True,
                    color=WHITE, align=PP_ALIGN.CENTER)

    # 中心标签 Mn-Fe/N-AC
    add_textbox(slide, 4.78, 6.85, 3.80, 0.40,
                "Mn-Fe/N-AC",
                font_size=14, bold=True,
                color=BLACK, align=PP_ALIGN.CENTER)

    # ── 4. 左上面板：NH₃ Adsorption and Activation ────────────────────────
    # 面板标题
    add_textbox(slide, 0.12, 0.72, 4.40, 0.35,
                "NH\u2083 Adsorption and Activation",
                font_size=12, bold=True,
                color=BLACK, align=PP_ALIGN.CENTER)

    # 催化剂平台（灰色矩形）
    add_rect(slide, 0.18, 2.60, 4.30, 0.55,
             fill_color=RGBColor(0x80, 0x80, 0x80),
             line_color=None)
    add_textbox(slide, 1.60, 3.08, 1.20, 0.25, "N-AC",
                font_size=9, bold=True,
                color=WHITE, align=PP_ALIGN.CENTER)

    # Mn/Fe + L-acid 粒子
    add_labeled_oval(slide, 0.80, 2.45, 0.28, "Mn/Fe", MN_COLOR,
                     font_size=7, label_color=WHITE)
    add_labeled_oval(slide, 1.30, 2.45, 0.22, "Fe", FE_COLOR,
                     font_size=7, label_color=WHITE)
    add_textbox(slide, 0.55, 2.80, 0.90, 0.22, "L-acid",
                font_size=8, bold=False,
                color=BLACK, align=PP_ALIGN.CENTER)

    # B-acid 粒子
    add_labeled_oval(slide, 2.80, 2.35, 0.25, "B-acid",
                     RGBColor(0xD0, 0xA0, 0x30),
                     font_size=7, label_color=WHITE)

    # Oxygen vacancy 框（虚线样式用实线替代，米色背景）
    add_rect(slide, 1.65, 1.12, 1.45, 0.60,
             fill_color=OVEN_VACANCY,
             line_color=BLACK, line_width_pt=1.0)
    add_textbox(slide, 1.68, 1.12, 1.40, 0.25, "Oxygen vacancy",
                font_size=8, bold=True,
                color=BLACK, align=PP_ALIGN.CENTER)
    add_labeled_oval(slide, 2.20, 1.53, 0.16, "O\u2082",
                     RGBColor(0x20, 0x80, 0x20), font_size=7, label_color=WHITE)

    # NH₃ 分子（蓝色小圆+标签）
    nh3_pos = [(0.35, 0.95), (0.35, 1.55), (0.45, 2.10)]
    for ax, ay in nh3_pos:
        add_labeled_oval(slide, ax, ay, 0.18, "NH\u2083",
                         NH3_COLOR, font_size=6, label_color=WHITE)

    # L-NH₃ 标签
    add_textbox(slide, 0.62, 1.60, 0.80, 0.25, "L-NH\u2083",
                font_size=8, color=BLACK)

    # NH₄⁺ 和 H₄⁺
    add_labeled_oval(slide, 2.95, 1.75, 0.20, "NH\u2084\u207A",
                     RGBColor(0x60, 0x60, 0xC0), font_size=6, label_color=WHITE)
    add_textbox(slide, 2.45, 1.65, 0.45, 0.25, "H\u2084\u207A",
                font_size=8, color=BLACK)

    # 底部说明
    add_textbox(slide, 0.12, 3.20, 4.35, 0.30,
                "Oxygen vacancies in all surface active sites",
                font_size=7.5, italic=True, color=DARK_GRAY)

    # N-doping 注释（右侧，指向中心）
    add_textbox(slide, 4.68, 1.20, 3.90, 0.55,
                "N-doping enhances surface\nbasicity for NH\u2083 capture.",
                font_size=9, italic=True,
                color=DARK_GRAY, align=PP_ALIGN.LEFT)

    # ── 5. 右上面板：Mn-Fe Synergistic Redox Cycle ─────────────────────────
    add_textbox(slide, 8.80, 0.72, 4.40, 0.35,
                "Mn-Fe Synergistic Redox Cycle",
                font_size=12, bold=True,
                color=BLACK, align=PP_ALIGN.CENTER)

    # 反应方程式框
    add_rect(slide, 8.88, 1.15, 4.30, 1.90,
             fill_color=RGBColor(0xFF, 0xF8, 0xE8),
             line_color=RGBColor(0xD0, 0x80, 0x20), line_width_pt=1.0)

    # Mn⁴⁺ + Fe²⁺ ⇌ Mn³⁺ + Fe³⁺
    add_textbox(slide, 8.95, 1.22, 4.15, 0.45,
                "Mn\u2074\u207A + Fe\u00B2\u207A  \u21CC  Mn\u00B3\u207A + Fe\u00B3\u207A",
                font_size=14, bold=True,
                color=BLACK, align=PP_ALIGN.CENTER)

    # e⁻ 箭头标注
    add_textbox(slide, 9.05, 1.72, 1.20, 0.30, "e\u207B",
                font_size=11, bold=True, color=DARK_GRAY)
    add_textbox(slide, 11.45, 1.72, 1.20, 0.30, "e\u207B",
                font_size=11, bold=True, color=DARK_GRAY)
    add_textbox(slide, 11.45, 2.10, 1.20, 0.30, "O\u2090d\u2093",
                font_size=10, bold=True,
                color=RGBColor(0xCC, 0x44, 0x00))

    # 说明文字
    add_textbox_multiline(slide, 8.88, 3.10, 4.35, 0.80,
                          ["Electron transfer forats highly active Mn\u2074\u207A",
                           "oxidation sites and simultaneously activate",
                           "surface adsorbed oxygen species (O\u2090d\u2093)"],
                          font_size=8.5, color=DARK_GRAY)

    # ── 6. 左下面板：Low-Temperature SCR Reaction Path ────────────────────
    add_textbox(slide, 0.12, 4.09, 4.40, 0.22,
                "Low-Temperature SCR Reaction Path",
                font_size=11, bold=True,
                color=BLACK, align=PP_ALIGN.CENTER)
    add_textbox(slide, 0.12, 4.32, 4.40, 0.22,
                "(L-H & E-R Mechanisms)",
                font_size=10, bold=True,
                color=BLACK, align=PP_ALIGN.CENTER)

    # 分隔线（中间竖线）
    add_rect(slide, 2.30, 4.60, 0.03, 2.55,
             fill_color=BLACK, line_color=None)

    # E-R / L-H 标题
    add_textbox(slide, 0.15, 4.58, 2.12, 0.28, "E-R mechanism",
                font_size=9, bold=True, color=BLACK)
    add_textbox(slide, 2.35, 4.58, 2.15, 0.28, "L-H mechanism",
                font_size=9, bold=True, color=BLACK)

    # E-R 侧：NO + L-NH₃ → N₂ + H₂O（左列）
    # Mn/Fe 催化剂
    add_labeled_oval(slide, 0.55, 5.40, 0.28, "Mn/Fe", MN_COLOR,
                     font_size=7, label_color=WHITE)
    add_labeled_oval(slide, 1.10, 5.70, 0.28, "Mn", MN_COLOR,
                     font_size=7, label_color=WHITE)

    # NO 粒子
    add_labeled_oval(slide, 0.55, 4.95, 0.20, "NO", NO_COLOR,
                     font_size=7, label_color=WHITE)
    add_labeled_oval(slide, 1.50, 5.10, 0.20, "NO", NO_COLOR,
                     font_size=7, label_color=WHITE)

    # L-NH₃ 标签（两处）
    add_textbox(slide, 0.75, 5.10, 0.85, 0.22, "L-NH\u2083",
                font_size=8, color=BLACK)
    add_textbox(slide, 0.10, 5.55, 0.85, 0.22, "L-NH\u2083",
                font_size=8, color=BLACK)

    # 催化剂平台 E-R
    add_rect(slide, 0.18, 6.50, 2.00, 0.42,
             fill_color=RGBColor(0x80, 0x80, 0x80), line_color=None)
    add_textbox(slide, 0.40, 6.55, 1.60, 0.30, "N-AC",
                font_size=8, bold=True, color=WHITE)
    add_textbox(slide, 0.10, 6.94, 2.10, 0.25,
                "L-H (co-adsorption)",
                font_size=7.5, bold=True, color=BLACK)

    # L-H 侧：Co-adsorbed L-NH₃, NOₓ → N₂ + H₂O
    add_textbox(slide, 2.38, 4.88, 2.05, 0.30,
                "Co-adsorbed\nL-NH\u2083",
                font_size=7.5, color=BLACK)

    # NO 粒子（右列）
    add_labeled_oval(slide, 3.65, 4.98, 0.20, "NO", NO_COLOR,
                     font_size=7, label_color=WHITE)

    # N₂ + H₂O 产物
    add_textbox(slide, 3.60, 5.22, 1.08, 0.40,
                "N\u2082\n+ H\u2082O",
                font_size=9, bold=True,
                color=RGBColor(0x00, 0x60, 0x00))

    # NOₓ 中间体
    add_textbox(slide, 2.70, 5.65, 1.20, 0.35,
                "NO\u2093 O\u2550N\u2500O",
                font_size=8.5, color=DARK_GRAY)

    # 催化剂平台 L-H
    add_rect(slide, 2.38, 6.50, 2.08, 0.42,
             fill_color=RGBColor(0x80, 0x80, 0x80), line_color=None)
    add_textbox(slide, 2.55, 6.55, 1.75, 0.30, "N-AC",
                font_size=8, bold=True, color=WHITE)

    # 底部说明（底边中心）
    add_textbox(slide, 4.68, 5.95, 3.90, 0.50,
                "Synergy enables\nefficient SCR at 280\u00B0C.",
                font_size=9, italic=True,
                color=DARK_GRAY, align=PP_ALIGN.LEFT)

    # ── 7. 右下面板：CO/HCHO Oxidation Path ───────────────────────────────
    add_textbox(slide, 8.80, 4.09, 4.40, 0.22,
                "CO/HCHO Oxidation Path",
                font_size=11, bold=True,
                color=BLACK, align=PP_ALIGN.CENTER)
    add_textbox(slide, 8.80, 4.32, 4.40, 0.22,
                "(Mars-van Krevelen Mechanism)",
                font_size=10, bold=True,
                color=BLACK, align=PP_ALIGN.CENTER)

    # CO 粒子（红色）
    co_positions = [(8.95, 4.70), (9.25, 5.00), (9.15, 5.70), (9.45, 5.40)]
    for cx, cy in co_positions:
        add_labeled_oval(slide, cx, cy, 0.22, "CO", CO_COLOR,
                         font_size=8, label_color=WHITE)

    # CO₂ 产物
    co2_positions = [(10.65, 4.68), (11.40, 4.68), (12.05, 5.50)]
    for cx, cy in co2_positions:
        add_labeled_oval(slide, cx, cy, 0.24, "CO\u2082", CO2_COLOR,
                         font_size=7, label_color=WHITE)

    # O_ads
    add_labeled_oval(slide, 10.30, 5.20, 0.22, "O\u2090d\u2093",
                     RGBColor(0xCC, 0x44, 0x00), font_size=6.5, label_color=WHITE)
    # O₂
    add_labeled_oval(slide, 12.20, 5.90, 0.22, "O\u2082",
                     RGBColor(0x20, 0x90, 0x20), font_size=8, label_color=WHITE)
    # Fe³⁺
    add_labeled_oval(slide, 12.60, 6.30, 0.22, "Fe\u00B3\u207A",
                     FE_COLOR, font_size=7, label_color=WHITE)

    # Mn/Fe 催化剂平台
    add_labeled_oval(slide, 9.25, 6.30, 0.30, "Mn/Fe", MN_COLOR,
                     font_size=6.5, label_color=WHITE)
    add_labeled_oval(slide, 9.90, 6.30, 0.30, "Mn/Fe", MN_COLOR,
                     font_size=6.5, label_color=WHITE)

    # N-AC 平台（深灰）
    add_rect(slide, 8.88, 6.90, 4.30, 0.38,
             fill_color=RGBColor(0x80, 0x80, 0x80), line_color=None)
    add_textbox(slide, 9.50, 6.93, 2.00, 0.28, "N-AC",
                font_size=9, bold=True, color=WHITE)

    # 底部说明
    add_textbox(slide, 4.68, 5.00, 3.95, 0.55,
                "Mn-Fe cycle accelerates\noxygen activation for\nCO oxidation",
                font_size=9, italic=True,
                color=DARK_GRAY, align=PP_ALIGN.LEFT)

    # ── 8. 中心标注 Mn₃O₄ / Fe₃O₄ 顶部标签 ─────────────────────────────────
    add_textbox(slide, 4.78, 0.70, 1.80, 0.28, "Mn\u2083O\u2084",
                font_size=11, bold=True,
                color=MN3O4_COLOR, align=PP_ALIGN.CENTER)
    add_textbox(slide, 6.35, 0.70, 1.80, 0.28, "Fe\u2083O\u2084",
                font_size=11, bold=True,
                color=FE3O4_COLOR, align=PP_ALIGN.CENTER)

    # ── 9. 面板间连接箭头（用直线+箭头 connector 模拟） ──────────────────────
    arrow_pairs = [
        # 左上 → 中心
        (4.58, 2.05,  4.65, 2.05),
        # 右上 → 中心
        (8.75, 2.05,  8.68, 2.05),
        # 左下 → 中心
        (4.58, 5.67,  4.65, 5.67),
        # 右下 → 中心
        (8.75, 5.67,  8.68, 5.67),
    ]
    for x1, y1, x2, y2 in arrow_pairs:
        add_arrow_connector(slide, x1, y1, x2, y2,
                            color=ARROW_BLUE, line_width_pt=2.0)

    return slide


# ──────────────────────────────────────────────────────────────────────────────
# 入口
# ──────────────────────────────────────────────────────────────────────────────
def main():
    prs = make_prs()
    build_slide(prs)
    out_path = os.path.join(os.path.dirname(__file__),
                            "Mn-Fe_N-AC_Catalyst_Mechanism.pptx")
    prs.save(out_path)
    print(f"[OK] PPT saved => {out_path}")


if __name__ == "__main__":
    main()
