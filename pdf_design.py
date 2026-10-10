"""PDF 표지 + "한눈에 보기"(오행 분포 차트, 사주 기둥 표) 디자인 모듈.

설계 결정(2026-10-10, 사용자 확정): A안(Modern Korean System) + 한지 느낌은 은은하게.
- 한지 질감은 표지에만 깐다. 본문 페이지는 평평한 흰 바탕(인쇄/잉크 절약).
- 오행 색은 오행 도형·차트에만 쓴다(상품/축 구분 용도 금지).
- 차트와 표는 LLM 문장이 아니라 run_calculation()의 pillars 데이터로 코드가 그린다.
- 한자는 모두 같은 잉크색. 오행은 색 점 + 글자로 함께 표기(색만으로 구분하지 않음).

report_pipeline.build_pdf(cover=True, overview_flowables=...)가 사용한다.
이 모듈은 report_pipeline을 import하지 않는다(순환 방지). Fraunces/WorkSans는
report_pipeline이 먼저 등록하고, 한자 글꼴(HanjaSerif)은 여기서 등록한다.
"""
from __future__ import annotations

import os

from reportlab.graphics.shapes import Drawing, Line, Rect, String
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle

_BASE = os.path.dirname(__file__)
_HANJA_FONT_PATH = os.path.join(_BASE, "fonts", "NotoSerifKR-Hanja-SemiBold.ttf")
_COVER_TEXTURE_PATH = os.path.join(_BASE, "pdf_assets", "hanji_cover.jpg")

INK = "#211D1A"
INK_SOFT = "#5E564E"
INK_ICON = "#4A433C"
RULE = "#E6DFD2"
ACCENT = "#C1442E"

# 상생 순서(시계 방향): 목 → 화 → 토 → 금 → 수.  ※ 오행 색/도형은 제안안(사주 전문가 확인 전)
ELEMENT_ORDER = ["목", "화", "토", "금", "수"]
ELEMENT_COLORS = {
    "목": "#3F7A63", "화": "#C1442E", "토": "#B98A2E", "금": "#8C98A4", "수": "#26364F",
}
ELEMENT_HANJA = {"목": "木", "화": "火", "토": "土", "금": "金", "수": "水"}
ELEMENT_NAMES = {
    "de": {"목": "Holz", "화": "Feuer", "토": "Erde", "금": "Metall", "수": "Wasser"},
    "fr": {"목": "Bois", "화": "Feu", "토": "Terre", "금": "Métal", "수": "Eau"},
}

STRINGS = {
    "de": {
        "overview": "Dein Profil auf einen Blick",
        "chart_title": "Deine Fünf Elemente",
        "chart_note": "Anzahl der Elemente in deinen Säulen (Himmelsstämme und Erdzweige).",
        "pillars_title": "Deine vier Säulen",
        "cols": ["Stunde", "Tag", "Monat", "Jahr"],
        "rows": ["Himmelsstamm", "Erdzweig"],
        "unknown": "unbekannt",
        "hour_note": "Ohne Geburtszeit wird keine Stundensäule berechnet. "
                     "Die Elementverteilung beruht dann auf den drei übrigen Säulen.",
        "footer_line": "palja.de  ·  Koreanische Saju-Lehre zur Selbstreflexion",
    },
    "fr": {
        "overview": "Ton profil en un coup d'œil",
        "chart_title": "Tes cinq éléments",
        "chart_note": "Nombre d'éléments dans tes piliers (troncs célestes et branches terrestres).",
        "pillars_title": "Tes quatre piliers",
        "cols": ["Heure", "Jour", "Mois", "Année"],
        "rows": ["Tronc céleste", "Branche terrestre"],
        "unknown": "inconnue",
        "hour_note": "Sans heure de naissance, le pilier de l'heure n'est pas calculé. "
                     "La répartition des éléments repose alors sur les trois autres piliers.",
        "footer_line": "palja.fr  ·  Le Saju coréen pour la réflexion personnelle",
    },
}


def _register_fonts():
    if "HanjaSerif" not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont("HanjaSerif", _HANJA_FONT_PATH))


_register_fonts()


def _s(lang):
    return STRINGS["fr" if lang == "fr" else "de"]


def _names(lang):
    return ELEMENT_NAMES["fr" if lang == "fr" else "de"]


# ---------------------------------------------------------------------------
# 데이터: 기둥에서 오행 개수 직접 세기 (표와 차트가 항상 일치하도록)
# ---------------------------------------------------------------------------

def count_elements(pillars, hour_known=True):
    counts = {e: 0 for e in ELEMENT_ORDER}
    for key in ("hour", "day", "month", "year"):
        if key == "hour" and not hour_known:
            continue
        p = pillars.get(key)
        if not p:
            continue
        for fld in ("cheon_gan_element", "ji_ji_element"):
            el = p.get(fld)
            if el in counts:
                counts[el] += 1
    return counts


# ---------------------------------------------------------------------------
# 오행 도형 (표지 아이콘용). 색 원 + 흰 도형
# ---------------------------------------------------------------------------

def _draw_element_icon(c, element, cx, cy, r):
    c.saveState()
    c.setFillColor(HexColor(ELEMENT_COLORS[element]))
    c.circle(cx, cy, r, stroke=0, fill=1)
    c.setFillColorRGB(1, 1, 1)
    c.setStrokeColorRGB(1, 1, 1)
    g = r * 0.5
    if element == "목":      # 삼각형
        p = c.beginPath()
        p.moveTo(cx, cy + g); p.lineTo(cx - g * 0.95, cy - g * 0.7); p.lineTo(cx + g * 0.95, cy - g * 0.7)
        p.close(); c.drawPath(p, stroke=0, fill=1)
    elif element == "화":    # 불꽃(물방울)
        p = c.beginPath()
        p.moveTo(cx, cy + g * 1.05)
        p.curveTo(cx + g * 0.2, cy + g * 0.45, cx + g * 0.85, cy + g * 0.1, cx + g * 0.7, cy - g * 0.35)
        p.curveTo(cx + g * 0.55, cy - g * 0.9, cx - g * 0.55, cy - g * 0.9, cx - g * 0.7, cy - g * 0.35)
        p.curveTo(cx - g * 0.85, cy + g * 0.1, cx - g * 0.2, cy + g * 0.45, cx, cy + g * 1.05)
        p.close(); c.drawPath(p, stroke=0, fill=1)
    elif element == "토":    # 정사각형
        c.rect(cx - g * 0.8, cy - g * 0.8, g * 1.6, g * 1.6, stroke=0, fill=1)
    elif element == "금":    # 원(링)
        c.setLineWidth(r * 0.16)
        c.circle(cx, cy, g * 0.8, stroke=1, fill=0)
    else:                    # 수: 물결 두 줄
        c.setLineWidth(r * 0.15)
        c.setLineCap(1)
        for dy in (g * 0.35, -g * 0.35):
            p = c.beginPath()
            p.moveTo(cx - g * 0.95, cy + dy)
            p.curveTo(cx - g * 0.5, cy + dy + g * 0.5, cx - g * 0.1, cy + dy + g * 0.5, cx, cy + dy)
            p.curveTo(cx + g * 0.1, cy + dy - g * 0.5, cx + g * 0.5, cy + dy - g * 0.5, cx + g * 0.95, cy + dy)
            c.drawPath(p, stroke=1, fill=0)
    c.restoreState()


# ---------------------------------------------------------------------------
# 표지 (onFirstPage 콜백)
# ---------------------------------------------------------------------------

def draw_cover(canvas, doc, *, title, subtitle, lang="de"):
    w, h = A4
    canvas.saveState()
    # 1) 한지 질감 (전면, 가로 맞춤 + 세로 중앙 크롭)
    if os.path.exists(_COVER_TEXTURE_PATH):
        iw, ih = 1152, 1728
        scale = w / iw
        draw_h = ih * scale
        canvas.drawImage(_COVER_TEXTURE_PATH, 0, h - draw_h, width=w, height=draw_h)
    else:
        canvas.setFillColor(HexColor("#F6F2E8"))
        canvas.rect(0, 0, w, h, stroke=0, fill=1)

    # 2) 워드마크
    canvas.setFillColor(HexColor(INK))
    canvas.setFont("Fraunces", 15)
    word = "PALJA"
    tracking = 4
    tw = sum(stringWidth(ch, "Fraunces", 15) for ch in word) + tracking * (len(word) - 1)
    x = (w - tw) / 2
    y = h - 28 * mm
    for ch in word:
        canvas.drawString(x, y, ch)
        x += stringWidth(ch, "Fraunces", 15) + tracking

    # 3) 오행 아이콘 5개 (목→화→토→금→수), 중앙 블록
    cy_icons = h * 0.60
    r = 6.2 * mm
    gap = 5 * mm
    total = 5 * 2 * r + 4 * gap
    cx = (w - total) / 2 + r
    for el in ELEMENT_ORDER:
        _draw_element_icon(canvas, el, cx, cy_icons, r)
        cx += 2 * r + gap

    # 4) 제목, 부제 (긴 제목은 폭에 맞춰 글자 크기 축소)
    max_w = w - 44 * mm
    size = 34
    while stringWidth(title, "Fraunces", size) > max_w and size > 20:
        size -= 1
    canvas.setFillColor(HexColor(INK))
    canvas.setFont("Fraunces", size)
    canvas.drawCentredString(w / 2, cy_icons - 24 * mm, title)
    canvas.setFillColor(HexColor(INK_SOFT))
    sub_size = 12.5
    while stringWidth(subtitle, "WorkSans-Italic", sub_size) > max_w and sub_size > 9:
        sub_size -= 0.5
    canvas.setFont("WorkSans-Italic", sub_size)
    canvas.drawCentredString(w / 2, cy_icons - 34 * mm, subtitle)

    # 5) 하단 얇은 선 + 한 줄
    canvas.setStrokeColor(HexColor(RULE))
    canvas.setLineWidth(0.6)
    canvas.line(w / 2 - 12 * mm, 30 * mm, w / 2 + 12 * mm, 30 * mm)
    canvas.setFillColor(HexColor(INK_SOFT))
    canvas.setFont("WorkSans", 8.5)
    canvas.drawCentredString(w / 2, 22 * mm, _s(lang)["footer_line"])
    canvas.restoreState()


# ---------------------------------------------------------------------------
# 오행 분포 차트 (가로 막대)
# ---------------------------------------------------------------------------

def build_element_chart(counts, *, lang="de", width_mm=166):
    names = _names(lang)
    width = width_mm * mm
    row_h = 9 * mm
    top_pad = 2 * mm
    bottom_pad = 7 * mm
    height = top_pad + row_h * 5 + bottom_pad
    label_w = 30 * mm
    plot_x = label_w + 2 * mm
    plot_w = width - plot_x - 10 * mm
    vmax = max(max(counts.values()), 4)

    d = Drawing(width, height)
    # 눈금선 (정수마다)
    axis_y = bottom_pad - 1 * mm
    for v in range(0, vmax + 1):
        gx = plot_x + plot_w * v / vmax
        d.add(Line(gx, axis_y, gx, height - top_pad, strokeColor=HexColor(RULE), strokeWidth=0.5))
        d.add(String(gx, axis_y - 4 * mm, str(v), fontName="WorkSans", fontSize=7,
                     fillColor=HexColor("#786F67"), textAnchor="middle"))

    for i, el in enumerate(ELEMENT_ORDER):
        y = height - top_pad - (i + 1) * row_h + 1.6 * mm
        bar_h = row_h - 3.2 * mm
        # 라벨: 한자 + 독일어/프랑스어 이름 (색 점은 막대 색과 동일)
        d.add(String(0, y + bar_h / 2 - 3.6, ELEMENT_HANJA[el], fontName="HanjaSerif", fontSize=12,
                     fillColor=HexColor(INK)))
        d.add(String(9 * mm, y + bar_h / 2 - 3, names[el], fontName="WorkSans", fontSize=9.5,
                     fillColor=HexColor(INK)))
        n = counts.get(el, 0)
        if n > 0:
            bw = plot_w * n / vmax
            d.add(Rect(plot_x, y, bw, bar_h, fillColor=HexColor(ELEMENT_COLORS[el]),
                       strokeColor=HexColor(INK_ICON), strokeWidth=0.5))
            vx = plot_x + bw + 2 * mm
        else:
            vx = plot_x + 2 * mm
        d.add(String(vx, y + bar_h / 2 - 3, str(n), fontName="WorkSans-Bold", fontSize=9.5,
                     fillColor=HexColor(INK)))
    return d


# ---------------------------------------------------------------------------
# 사주 기둥 표 (시 / 일 / 월 / 년 × 천간 / 지지)
# ---------------------------------------------------------------------------

def build_pillars_table(pillars, *, hour_known=True, lang="de", width_mm=166):
    st = _s(lang)
    names = _names(lang)
    order = ["hour", "day", "month", "year"]

    small = ParagraphStyle("pl_small", fontName="WorkSans", fontSize=8, leading=10, textColor=HexColor(INK_SOFT),
                           alignment=1)
    head = ParagraphStyle("pl_head", fontName="WorkSans-Bold", fontSize=8.5, leading=11, textColor=HexColor(INK),
                          alignment=1)
    rowlab = ParagraphStyle("pl_row", fontName="WorkSans", fontSize=8.5, leading=11, textColor=HexColor(INK_SOFT))
    hanja = ParagraphStyle("pl_hanja", fontName="HanjaSerif", fontSize=26, leading=30, textColor=HexColor(INK),
                           alignment=1)
    dash = ParagraphStyle("pl_dash", fontName="WorkSans", fontSize=22, leading=30, textColor=HexColor("#B5ACA0"),
                          alignment=1)
    unk = ParagraphStyle("pl_unk", fontName="WorkSans-Italic", fontSize=9, leading=12, textColor=HexColor("#8A8074"),
                         alignment=1)

    def cell(key, idx):
        p = pillars.get(key)
        if key == "hour" and (not hour_known or not p):
            return [Paragraph("–", dash), Paragraph(st["unknown"], unk)]
        ch = p["hanja"][idx]
        el = p["cheon_gan_element" if idx == 0 else "ji_ji_element"]
        dot = f'<font color="{ELEMENT_COLORS[el]}" size="11">●</font>'
        return [Paragraph(ch, hanja), Paragraph(f"{dot}&nbsp;{names[el]}", small)]

    data = [["" ] + [Paragraph(c, head) for c in st["cols"]]]
    for idx in (0, 1):
        data.append([Paragraph(st["rows"][idx], rowlab)] + [cell(k, idx) for k in order])

    label_w = 30 * mm
    col_w = (width_mm * mm - label_w) / 4
    t = Table(data, colWidths=[label_w] + [col_w] * 4, rowHeights=[8 * mm, 22 * mm, 22 * mm])
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LINEBELOW", (0, 0), (-1, 0), 0.8, HexColor(INK)),
        ("LINEBELOW", (0, 1), (-1, 1), 0.5, HexColor(RULE)),
        ("LINEBELOW", (0, 2), (-1, 2), 0.5, HexColor(RULE)),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]))
    return t


# ---------------------------------------------------------------------------
# "한눈에 보기" 페이지 flowable 묶음
# ---------------------------------------------------------------------------

def build_overview_flowables(calc_result, *, hour_known=True, lang="de", h2_style=None, h2_rule=None,
                             body_style=None):
    """calc_result: run_calculation() 결과(pillars 필요). hour_known: 출생시각을 입력했는지."""
    st = _s(lang)
    pillars = calc_result["pillars"]
    counts = count_elements(pillars, hour_known)

    h3 = ParagraphStyle("ov_h3", fontName="Fraunces", fontSize=13, leading=17, textColor=HexColor(INK),
                        spaceBefore=6 * mm, spaceAfter=1.5 * mm)
    note = ParagraphStyle("ov_note", fontName="WorkSans", fontSize=8.5, leading=12, textColor=HexColor(INK_SOFT),
                          spaceAfter=3 * mm)

    out = []
    if h2_style is not None:
        out.append(Paragraph(st["overview"], h2_style))
        if h2_rule is not None:
            out.append(h2_rule)
    out.append(Paragraph(st["chart_title"], h3))
    out.append(Paragraph(st["chart_note"], note))
    out.append(build_element_chart(counts, lang=lang))
    out.append(Paragraph(st["pillars_title"], h3))
    out.append(build_pillars_table(pillars, hour_known=hour_known, lang=lang))
    if not hour_known:
        out.append(Spacer(1, 2 * mm))
        out.append(Paragraph(st["hour_note"], note))
    out.append(Spacer(1, 6 * mm))
    return out
