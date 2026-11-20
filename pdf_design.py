"""PDF 표지 + "한눈에 보기"(오행 분포 차트, 사주 기둥 표) 디자인 모듈.

설계 결정(2026-10-10, 사용자 확정): A안(Modern Korean System) + 한지 느낌은 은은하게.
- 한지 질감은 표지에만 깐다. 본문 페이지는 평평한 흰 바탕(인쇄/잉크 절약).
- 오행 색은 오행 도형·차트에만 쓴다(상품/축 구분 용도 금지).
- 차트와 표는 LLM 문장이 아니라 run_calculation()의 pillars 데이터로 코드가 그린다.
- 천간·지지는 한글(병, 진 등)로 표기, 모두 같은 잉크색. 오행은 색 점 + 글자로 함께 표기(색만으로 구분하지 않음).

report_pipeline.build_pdf(cover=True, overview_flowables=...)가 사용한다.
이 모듈은 report_pipeline을 import하지 않는다(순환 방지). Fraunces/WorkSans는
report_pipeline이 먼저 등록하고, 한글 글꼴(KoreanSerif)은 여기서 등록한다.
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
from reportlab.platypus import KeepTogether, Paragraph, Spacer, Table, TableStyle

_BASE = os.path.dirname(__file__)
_KO_FONT_PATH = os.path.join(_BASE, "fonts", "NotoSerifKR-Hangul-SemiBold.ttf")
_COVER_TEXTURE_PATH = os.path.join(_BASE, "pdf_assets", "hanji_cover.jpg")

INK = "#211D1A"
INK_SOFT = "#5E564E"
INK_ICON = "#4A433C"
RULE = "#E6DFD2"
ACCENT = "#C1442E"

# 상생 순서(시계 방향): 목 → 화 → 토 → 금 → 수.  ※ 오행 색/도형은 제안안(사주 전문가 확인 전)
ELEMENT_ORDER = ["목", "화", "토", "금", "수"]
ELEMENT_COLORS = {
    "목": "#3F7A63", "화": "#C1442E", "토": "#A97E2A", "금": "#758492", "수": "#26364F",
}
# 한자 대신 한글 오행 이름 (한자는 중국 느낌이 나서 쓰지 않는다 — 2026-10-10 결정)
ELEMENT_KO = {"목": "나무", "화": "불", "토": "흙", "금": "쇠", "수": "물"}
ELEMENT_NAMES = {
    "de": {"목": "Holz", "화": "Feuer", "토": "Erde", "금": "Metall", "수": "Wasser"},
    "fr": {"목": "Bois", "화": "Feu", "토": "Terre", "금": "Métal", "수": "Eau"},
    "es": {"목": "Madera", "화": "Fuego", "토": "Tierra", "금": "Metal", "수": "Agua"},
    "en": {"목": "Wood", "화": "Fire", "토": "Earth", "금": "Metal", "수": "Water"},
}

STRINGS = {
    "de": {
        "overview": "Dein Profil auf einen Blick",
        "overview_named": "Profil auf einen Blick: {name}",
        "chart_title": "Deine Fünf Elemente",
        "chart_note": "Anzahl der Elemente in deinen Säulen (Himmelsstämme und Erdzweige).",
        "pillars_title": "Deine vier Säulen",
        # 궁합 리포트(두 사람 각각의 개요): "Deine/Vos"가 누구를 가리키는지 헷갈리지 않게 중립 표현
        "chart_title_named": "Die fünf Elemente",
        "chart_note_named": "Anzahl der Elemente in den Säulen (Himmelsstämme und Erdzweige).",
        "pillars_title_named": "Die vier Säulen",
        "cols": ["Stunde", "Tag", "Monat", "Jahr"],
        "rows": ["Himmelsstamm", "Erdzweig"],
        "unknown": "unbekannt",
        "table_note": "Die Zeichen sind die koreanischen Namen der Himmelsstämme (oben) und Erdzweige (unten), "
                      "den Bausteinen jeder Säule. Darunter steht das zugehörige Element.",
        "hour_note": "Ohne Geburtszeit wird keine Stundensäule berechnet. "
                     "Die Elementverteilung beruht dann auf den drei übrigen Säulen.",
        "footer_line": "palja.de  ·  Koreanische Saju-Lehre zur Selbstreflexion",
    },
    "fr": {
        "overview": "Votre profil en un coup d'œil",
        "overview_named": "Profil en un coup d'œil : {name}",
        "chart_title": "Vos cinq éléments",
        "chart_note": "Nombre d'éléments dans vos piliers (troncs célestes et branches terrestres).",
        "pillars_title": "Vos quatre piliers",
        "chart_title_named": "Les cinq éléments",
        "chart_note_named": "Nombre d'éléments dans les piliers (troncs célestes et branches terrestres).",
        "pillars_title_named": "Les quatre piliers",
        "cols": ["Heure", "Jour", "Mois", "Année"],
        "rows": ["Tronc céleste", "Branche terrestre"],
        "unknown": "inconnue",
        "table_note": "Les caractères sont les noms coréens des troncs célestes (en haut) et des branches terrestres "
                      "(en bas), les éléments de base de chaque pilier. Dessous figure l'élément correspondant.",
        "hour_note": "Sans heure de naissance, le pilier de l'heure n'est pas calculé. "
                     "La répartition des éléments repose alors sur les trois autres piliers.",
        "footer_line": "palja.fr  ·  Le Saju coréen pour la réflexion personnelle",
    },
    "es": {
        "overview": "Tu perfil de un vistazo",
        "overview_named": "Perfil de un vistazo: {name}",
        "chart_title": "Tus cinco elementos",
        "chart_note": "Número de elementos en tus pilares (troncos celestes y ramas terrestres).",
        "pillars_title": "Tus cuatro pilares",
        "chart_title_named": "Los cinco elementos",
        "chart_note_named": "Número de elementos en los pilares (troncos celestes y ramas terrestres).",
        "pillars_title_named": "Los cuatro pilares",
        "cols": ["Hora", "Día", "Mes", "Año"],
        "rows": ["Tronco celeste", "Rama terrestre"],
        "unknown": "desconocida",
        "table_note": "Los caracteres son los nombres coreanos de los troncos celestes (arriba) y de las ramas terrestres "
                      "(abajo), los elementos básicos de cada pilar. Debajo figura el elemento correspondiente.",
        "hour_note": "Sin la hora de nacimiento no se calcula el pilar de la hora. "
                     "La distribución de elementos se basa entonces en los otros tres pilares.",
        "footer_line": (os.environ.get("ES_DOMAIN", "").strip() or "palja.de/es") + "  ·  El Saju coreano para la reflexión personal",
    },
    "en": {
        "overview": "Your profile at a glance",
        "overview_named": "Profile at a glance: {name}",
        "chart_title": "Your five elements",
        "chart_note": "Number of elements in your pillars (heavenly stems and earthly branches).",
        "pillars_title": "Your four pillars",
        "chart_title_named": "The five elements",
        "chart_note_named": "Number of elements in the pillars (heavenly stems and earthly branches).",
        "pillars_title_named": "The four pillars",
        "cols": ["Hour", "Day", "Month", "Year"],
        "rows": ["Heavenly stem", "Earthly branch"],
        "unknown": "unknown",
        "table_note": "The characters are the Korean names of the heavenly stems (top) and the earthly branches "
                      "(bottom), the building blocks of each pillar. The matching element is shown below them.",
        "hour_note": "Without a birth time, no hour pillar is calculated. "
                     "The element distribution is then based on the other three pillars.",
        "footer_line": (os.environ.get("EN_DOMAIN", "").strip() or "palja.de/en") + "  ·  Korean Saju for personal reflection",
    },
}


def _register_fonts():
    if "KoreanSerif" not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont("KoreanSerif", _KO_FONT_PATH))


_register_fonts()


def _s(lang):
    return STRINGS.get(lang, STRINGS["de"])


def _names(lang):
    return ELEMENT_NAMES.get(lang, ELEMENT_NAMES["de"])


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
    canvas.setFillColor(HexColor(INK_SOFT))
    for el in ELEMENT_ORDER:
        _draw_element_icon(canvas, el, cx, cy_icons, r)
        canvas.setFont("KoreanSerif", 10)
        canvas.drawCentredString(cx, cy_icons - r - 5.5 * mm, ELEMENT_KO[el])
        cx += 2 * r + gap

    # 4) 제목, 부제 (긴 제목은 폭에 맞춰 글자 크기 축소)
    max_w = w - 44 * mm
    size = 34
    while stringWidth(title, "Fraunces", size) > max_w and size > 20:
        size -= 1
    canvas.setFillColor(HexColor(INK))
    canvas.setFont("Fraunces", size)
    canvas.drawCentredString(w / 2, cy_icons - 30 * mm, title)
    canvas.setFillColor(HexColor(INK_SOFT))
    sub_size = 12.5
    while stringWidth(subtitle, "WorkSans-Italic", sub_size) > max_w and sub_size > 9:
        sub_size -= 0.5
    canvas.setFont("WorkSans-Italic", sub_size)
    canvas.drawCentredString(w / 2, cy_icons - 40 * mm, subtitle)

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
    label_w = 36 * mm
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
        # 라벨: 한글 오행 이름 + 독일어/프랑스어 이름 (색 점은 막대 색과 동일)
        d.add(String(0, y + bar_h / 2 - 3.6, ELEMENT_KO[el], fontName="KoreanSerif", fontSize=12,
                     fillColor=HexColor(INK)))
        d.add(String(15 * mm, y + bar_h / 2 - 3, names[el], fontName="WorkSans", fontSize=9.5,
                     fillColor=HexColor(INK)))
        n = counts.get(el, 0)
        if n > 0:
            bw = plot_w * n / vmax
            d.add(Rect(plot_x, y, bw, bar_h, fillColor=HexColor(ELEMENT_COLORS[el]),
                       strokeColor=None))
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
    hanja = ParagraphStyle("pl_hanja", fontName="KoreanSerif", fontSize=24, leading=30, textColor=HexColor(INK),
                           alignment=1)
    dash = ParagraphStyle("pl_dash", fontName="WorkSans", fontSize=22, leading=30, textColor=HexColor("#B5ACA0"),
                          alignment=1)
    unk = ParagraphStyle("pl_unk", fontName="WorkSans-Italic", fontSize=9, leading=12, textColor=HexColor("#8A8074"),
                         alignment=1)

    def cell(key, idx):
        p = pillars.get(key)
        if key == "hour" and (not hour_known or not p):
            return [Paragraph("–", dash), Paragraph(st["unknown"], unk)]
        ch = p["hangul"][idx]
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
                             body_style=None, name=None):
    """calc_result: run_calculation() 결과(pillars 필요). hour_known: 출생시각을 입력했는지.

    name: 궁합 리포트처럼 한 문서에 여러 사람의 개요를 넣을 때 제목에 붙일 이름."""
    st = _s(lang)
    pillars = calc_result["pillars"]
    counts = count_elements(pillars, hour_known)

    h3 = ParagraphStyle("ov_h3", fontName="Fraunces", fontSize=13, leading=17, textColor=HexColor(INK),
                        spaceBefore=6 * mm, spaceAfter=1.5 * mm)
    note = ParagraphStyle("ov_note", fontName="WorkSans", fontSize=8.5, leading=12, textColor=HexColor(INK_SOFT),
                          spaceAfter=3 * mm)

    out = []
    if h2_style is not None:
        if name:
            from xml.sax.saxutils import escape
            heading = st["overview_named"].format(name=escape(name))
        else:
            heading = st["overview"]
        out.append(Paragraph(heading, h2_style))
        if h2_rule is not None:
            out.append(h2_rule)
    sfx = "_named" if name else ""
    out.append(Paragraph(st["chart_title" + sfx], h3))
    out.append(Paragraph(st["chart_note" + sfx], note))
    out.append(build_element_chart(counts, lang=lang))
    out.append(Paragraph(st["pillars_title" + sfx], h3))
    out.append(build_pillars_table(pillars, hour_known=hour_known, lang=lang))
    out.append(Spacer(1, 2 * mm))
    out.append(Paragraph(st["table_note"], note))
    if not hour_known:
        out.append(Paragraph(st["hour_note"], note))
    out.append(Spacer(1, 6 * mm))
    return out


# ---------------------------------------------------------------------------
# 대운 한눈에 보기 표 (프리미엄 리포트): 나이 / 연도 / 간지 / 오행 / 축, 현재 행 강조
# 데이터는 run_calculation()의 daewoon["entries"]에서 코드로만 그린다(LLM 문장 아님).
# ---------------------------------------------------------------------------

_DW_STRINGS = {
    "de": {"title": "Deine acht Lebensphasen im Überblick",
           "cols": ["Alter", "Ab Jahr", "Zyklus", "Elemente", "Schwerpunkt"], "here": "DU BIST HIER",
           "axes": {"재물운": "Ressourcen", "관계운": "Beziehung", "직업운": "Talent & Werk", "총운": "Stabilität"},
           "note": "Jede Phase dauert zehn Jahre. Der Schwerpunkt benennt das Thema, das in diesem Zyklus im Vordergrund steht."},
    "fr": {"title": "Vos huit phases de vie en un coup d'œil",
           "cols": ["Âge", "Dès l'année", "Cycle", "Éléments", "Thème"], "here": "VOUS ÊTES ICI",
           "axes": {"재물운": "Ressources", "관계운": "Relations", "직업운": "Talents & œuvre", "총운": "Équilibre"},
           "note": "Chaque phase dure dix ans. Le thème indique ce qui est au premier plan pendant ce cycle."},
    "es": {"title": "Tus ocho etapas de vida de un vistazo",
           "cols": ["Edad", "Desde el año", "Ciclo", "Elementos", "Tema"], "here": "ESTÁS AQUÍ",
           "axes": {"재물운": "Recursos", "관계운": "Relaciones", "직업운": "Talento y obra", "총운": "Equilibrio"},
           "note": "Cada etapa dura diez años. El tema indica lo que ocupa el primer plano en ese ciclo."},
    "en": {"title": "Your eight life phases at a glance",
           "cols": ["Age", "From year", "Cycle", "Elements", "Focus"], "here": "YOU ARE HERE",
           "axes": {"재물운": "Resources", "관계운": "Relationships", "직업운": "Talent & work", "총운": "Balance"},
           "note": "Each phase lasts ten years. The focus names the theme in the foreground during that cycle."},
}


def build_daewoon_table(entries, *, lang="de", width_mm=166, h3_style=None):
    """entries: run_calculation()["daewoon"]["entries"]. 반환: flowable 리스트."""
    st = _DW_STRINGS.get(lang, _DW_STRINGS["de"])
    names = _names(lang)
    head = ParagraphStyle("dw_head", fontName="WorkSans-Bold", fontSize=8.5, leading=11, textColor=HexColor(INK))
    cell = ParagraphStyle("dw_cell", fontName="WorkSans", fontSize=9, leading=12, textColor=HexColor(INK))
    soft = ParagraphStyle("dw_soft", fontName="WorkSans", fontSize=9, leading=12, textColor=HexColor(INK_SOFT))
    ko = ParagraphStyle("dw_ko", fontName="KoreanSerif", fontSize=15, leading=18, textColor=HexColor(INK))
    here = ParagraphStyle("dw_here", fontName="WorkSans-Bold", fontSize=6.5, leading=8, textColor=HexColor(ACCENT))
    note = ParagraphStyle("dw_note", fontName="WorkSans", fontSize=8.5, leading=12, textColor=HexColor(INK_SOFT),
                          spaceBefore=2 * mm)

    def dot(el):
        return f'<font color="{ELEMENT_COLORS[el]}" size="10">●</font>&nbsp;{names[el]}'

    data = [[Paragraph(c, head) for c in st["cols"]]]
    current_row = None
    for i, e in enumerate(entries, start=1):
        p = e["pillar"]
        age = f'{e["start_age"]}–{e["end_age"]}'
        if e.get("is_current"):
            current_row = i
            age_cell = [Paragraph(f"<b>{age}</b>", cell), Paragraph(st["here"], here)]
        else:
            age_cell = Paragraph(age, cell)
        els = Paragraph(f'{dot(p["cheon_gan_element"])}<br/>{dot(p["ji_ji_element"])}', cell)
        data.append([age_cell, Paragraph(str(e["start_year"]), soft), Paragraph(p["hangul"], ko), els,
                     Paragraph(st["axes"].get(e["axis"], e["axis"]), cell)])

    w = width_mm * mm
    cw = [26 * mm, 22 * mm, 22 * mm, 50 * mm, w - 120 * mm]
    t = Table(data, colWidths=cw, repeatRows=1)
    style = [
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LINEBELOW", (0, 0), (-1, 0), 0.8, HexColor(INK)),
        ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]
    for r in range(1, len(data) - 1):
        style.append(("LINEBELOW", (0, r), (-1, r), 0.4, HexColor(RULE)))
    if current_row:
        style += [("BACKGROUND", (0, current_row), (-1, current_row), HexColor("#F6EEE6")),
                  ("LINEBEFORE", (0, current_row), (0, current_row), 2.5, HexColor(ACCENT))]
    t.setStyle(TableStyle(style))
    out = []
    if h3_style is not None:
        out.append(Paragraph(st["title"], h3_style))
    out += [t, Paragraph(st["note"], note)]
    return [KeepTogether(out), Spacer(1, 4 * mm)]


# ---------------------------------------------------------------------------
# 프리미엄 보강 3종 (모두 코드로 계산·렌더링, LLM 문장 아님)
#  1) 챕터 시작 카드(대운 한 시기의 나이·연도·간지·오행·축)
#  2) "Deine Grundlage" 카드(일간·강약·용신·희신)
#  3) 향후 10년 세운 표(해마다 간지·오행, 용신 오행이 들어오는 해 표시)
# ---------------------------------------------------------------------------

import re as _re

_HANJA_EL = {"木": "목", "火": "화", "土": "토", "金": "금", "水": "수"}

_EX_STRINGS = {
    "de": {
        "years_label": "Jahre", "from": "ab", "here": "DU BIST HIER",
        "axes": {"재물운": "Schwerpunkt: Ressourcen", "관계운": "Schwerpunkt: Beziehung",
                 "직업운": "Schwerpunkt: Talent & Werk", "총운": "Schwerpunkt: Gesamtgleichgewicht"},
        "f_core": "Dein Kern", "f_strength": "Stärke des Kerns", "f_support": "Stützt das Gleichgewicht",
        "f_accompany": "Begleitet es",
        "levels": {"balanced": "ausgewogen", "strong": "kräftig", "light": "zart"},
        "y_title": "Die nächsten zehn Jahre im Überblick",
        "y_cols": ["Jahr", "Alter", "Jahressäule", "Elemente", "Zyklus", "Hinweis"],
        "y_support": "stützendes Element",
        "y_note": "Jedes Jahr trägt eine eigene Säule aus zwei Elementen. Die Tabelle zeigt nur, welche Elemente auftauchen; sie ist keine Vorhersage.",
    },
    "fr": {
        "years_label": "ans", "from": "dès", "here": "VOUS ÊTES ICI",
        "axes": {"재물운": "Thème : ressources", "관계운": "Thème : relations",
                 "직업운": "Thème : talents et œuvre", "총운": "Thème : équilibre général"},
        "f_core": "Votre noyau", "f_strength": "Force du noyau", "f_support": "Soutient l'équilibre",
        "f_accompany": "L'accompagne",
        "levels": {"balanced": "équilibrée", "strong": "marquée", "light": "légère"},
        "y_title": "Les dix prochaines années en un coup d'œil",
        "y_cols": ["Année", "Âge", "Pilier de l'année", "Éléments", "Cycle", "Repère"],
        "y_support": "élément de soutien",
        "y_note": "Chaque année porte un pilier de deux éléments. Le tableau montre seulement quels éléments apparaissent ; ce n'est pas une prédiction.",
    },
    "es": {
        "years_label": "años", "from": "desde", "here": "ESTÁS AQUÍ",
        "axes": {"재물운": "Tema: recursos", "관계운": "Tema: relaciones",
                 "직업운": "Tema: talento y obra", "총운": "Tema: equilibrio general"},
        "f_core": "Tu núcleo", "f_strength": "Fuerza del núcleo", "f_support": "Apoya el equilibrio",
        "f_accompany": "Lo acompaña",
        "levels": {"balanced": "equilibrada", "strong": "marcada", "light": "suave"},
        "y_title": "Los próximos diez años de un vistazo",
        "y_cols": ["Año", "Edad", "Pilar del año", "Elementos", "Ciclo", "Nota"],
        "y_support": "elemento de apoyo",
        "y_note": "Cada año lleva un pilar de dos elementos. La tabla solo muestra qué elementos aparecen; no es una predicción.",
    },
    "en": {
        "years_label": "years", "from": "from", "here": "YOU ARE HERE",
        "axes": {"재물운": "Focus: resources", "관계운": "Focus: relationships",
                 "직업운": "Focus: talent & work", "총운": "Focus: overall balance"},
        "f_core": "Your core", "f_strength": "Strength of the core", "f_support": "Supports the balance",
        "f_accompany": "Accompanies it",
        "levels": {"balanced": "balanced", "strong": "pronounced", "light": "gentle"},
        "y_title": "The next ten years at a glance",
        "y_cols": ["Year", "Age", "Year pillar", "Elements", "Cycle", "Note"],
        "y_support": "supporting element",
        "y_note": "Each year carries a pillar of two elements. The table only shows which elements appear; it is not a prediction.",
    },
}


def _ex(lang):
    return _EX_STRINGS.get(lang, _EX_STRINGS["de"])


def parse_yongsin_elements(compact):
    """compact 문자열에서 용신/희신 오행(한글) 추출. 못 찾으면 None."""
    y = _re.search(r"용신=([목화토금수])", compact or "")
    h = _re.search(r"희신 ([木火土金水])", compact or "")
    return (y.group(1) if y else None), (_HANJA_EL.get(h.group(1)) if h else None)


def build_phase_card(entry, *, lang="de", width_mm=166):
    """챕터 시작 카드: 나이대·시작 연도 / 간지(한글) / 오행 색 점 / 축."""
    st, ex = _DW_STRINGS.get(lang, _DW_STRINGS["de"]), _ex(lang)
    names = _names(lang)
    p = entry["pillar"]
    age = ParagraphStyle("pc_age", fontName="Fraunces", fontSize=17, leading=20, textColor=HexColor(INK))
    sub = ParagraphStyle("pc_sub", fontName="WorkSans", fontSize=8.5, leading=11, textColor=HexColor(INK_SOFT))
    ko = ParagraphStyle("pc_ko", fontName="KoreanSerif", fontSize=20, leading=24, textColor=HexColor(INK))
    small = ParagraphStyle("pc_small", fontName="WorkSans", fontSize=9, leading=12, textColor=HexColor(INK))
    tag = ParagraphStyle("pc_tag", fontName="WorkSans-Bold", fontSize=7, leading=9, textColor=HexColor(ACCENT))

    def dot(el):
        return f'<font color="{ELEMENT_COLORS[el]}" size="10">●</font>&nbsp;{names[el]}'

    left = [Paragraph(f'{entry["start_age"]}–{entry["end_age"]}', age),
            Paragraph(f'{ex["years_label"]} · {ex["from"]} {entry["start_year"]}', sub)]
    mid = [Paragraph(p["hangul"], ko)]
    els = Paragraph(f'{dot(p["cheon_gan_element"])}<br/>{dot(p["ji_ji_element"])}', small)
    right = [Paragraph(ex["axes"].get(entry["axis"], entry["axis"]), small)]
    if entry.get("is_current"):
        right.append(Paragraph(ex["here"], tag))
    w = width_mm * mm
    t = Table([[left, mid, els, right]], colWidths=[34 * mm, 22 * mm, 38 * mm, w - 94 * mm])
    fill = "#F6EEE6" if entry.get("is_current") else "#F7F4EE"
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BACKGROUND", (0, 0), (-1, -1), HexColor(fill)),
        ("LINEBEFORE", (0, 0), (0, 0), 3, HexColor(ACCENT if entry.get("is_current") else INK_SOFT)),
        ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))
    return KeepTogether([Spacer(1, 1.5 * mm), t, Spacer(1, 3 * mm)])


def build_foundation_card(calc_result, *, lang="de", width_mm=166):
    """"Deine Grundlage" 카드: 일간 오행·강약·용신·희신. 값은 계산 결과에서만 가져온다."""
    ex = _ex(lang)
    names = _names(lang)
    day = calc_result["pillars"]["day"]
    core_el = day["cheon_gan_element"]
    core_ko = day["hangul"][0]
    lvl = (calc_result.get("ilgan_strength") or {}).get("level", "")
    score = (calc_result.get("ilgan_strength") or {}).get("score")
    key = "strong" if "강" in lvl else "light" if "약" in lvl else "balanced"
    yong, hee = parse_yongsin_elements(calc_result.get("compact", ""))

    lab = ParagraphStyle("fc_lab", fontName="WorkSans", fontSize=8, leading=10, textColor=HexColor(INK_SOFT))
    big = ParagraphStyle("fc_big", fontName="Fraunces", fontSize=14, leading=18, textColor=HexColor(INK))
    ko = ParagraphStyle("fc_ko", fontName="KoreanSerif", fontSize=20, leading=24, textColor=HexColor(INK))

    def dot(el):
        return (f'<font name="WorkSans" color="{ELEMENT_COLORS[el]}" size="12">●</font>&nbsp;{names[el]}'
                if el else "–")

    strength = ex["levels"][key] + (f' ({score:.1f}/10)'.replace(".", ",") if (score is not None and lang == "de") else
                                     (f' ({score:.1f}/10)' if score is not None else ""))
    cells = [
        [Paragraph(ex["f_core"], lab), Paragraph(core_ko, ko), Paragraph(dot(core_el), big)],
        [Paragraph(ex["f_strength"], lab), Paragraph(strength, big)],
        [Paragraph(ex["f_support"], lab), Paragraph(dot(yong), big)],
        [Paragraph(ex["f_accompany"], lab), Paragraph(dot(hee), big)],
    ]
    w = width_mm * mm
    t = Table([cells], colWidths=[w * 0.25] * 4)
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BACKGROUND", (0, 0), (-1, -1), HexColor("#F7F4EE")),
        ("LINEBEFORE", (1, 0), (-1, 0), 0.4, HexColor(RULE)),
        ("TOPPADDING", (0, 0), (-1, -1), 8), ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
    ]))
    return KeepTogether([Spacer(1, 1.5 * mm), t, Spacer(1, 3 * mm)])


def build_yearly_table(calc_result, *, lang="de", width_mm=166, h3_style=None):
    """향후 10년 세운 표. calc_result["yearly"]: {"2026": {"year_pillar": {...}}, ...}"""
    yearly = calc_result.get("yearly") or {}
    rows = sorted((v for v in yearly.values() if v.get("year_pillar")), key=lambda v: v["year"])
    if not rows:
        return []
    ex, names = _ex(lang), _names(lang)
    entries = (calc_result.get("daewoon") or {}).get("entries") or []
    try:
        birth_year = int(calc_result["input"]["birth_datetime_parsed"][:4])
    except Exception:  # noqa: BLE001
        birth_year = None
    yong, _hee = parse_yongsin_elements(calc_result.get("compact", ""))

    head = ParagraphStyle("yr_head", fontName="WorkSans-Bold", fontSize=8.5, leading=11, textColor=HexColor(INK))
    cell = ParagraphStyle("yr_cell", fontName="WorkSans", fontSize=9, leading=12, textColor=HexColor(INK))
    soft = ParagraphStyle("yr_soft", fontName="WorkSans", fontSize=8.5, leading=11, textColor=HexColor(INK_SOFT))
    ko = ParagraphStyle("yr_ko", fontName="KoreanSerif", fontSize=15, leading=18, textColor=HexColor(INK))
    note = ParagraphStyle("yr_note", fontName="WorkSans", fontSize=8.5, leading=12, textColor=HexColor(INK_SOFT),
                          spaceBefore=2 * mm)

    def dot(el):
        return f'<font color="{ELEMENT_COLORS[el]}" size="10">●</font>&nbsp;{names[el]}'

    data = [[Paragraph(c, head) for c in ex["y_cols"]]]
    for v in rows:
        y, yp = v["year"], v["year_pillar"]
        a, b = yp["cheon_gan_element"], yp["ji_ji_element"]
        age = (y - birth_year) if birth_year else ""
        phase = ""
        for e in entries:
            if e["start_year"] <= y < e["start_year"] + 10:
                phase = f'{e["start_age"]}–{e["end_age"]}'
        hint = f'<font color="{ELEMENT_COLORS[yong]}" size="10">●</font>&nbsp;{ex["y_support"]}' if yong in (a, b) else ""
        data.append([Paragraph(f"<b>{y}</b>", cell), Paragraph(str(age), soft), Paragraph(yp["hangul"], ko),
                     Paragraph(f"{dot(a)}<br/>{dot(b)}", cell), Paragraph(phase, soft), Paragraph(hint, soft)])
    w = width_mm * mm
    t = Table(data, colWidths=[16 * mm, 14 * mm, 28 * mm, 38 * mm, 22 * mm, w - 118 * mm], repeatRows=1)
    style = [("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("LINEBELOW", (0, 0), (-1, 0), 0.8, HexColor(INK)),
             ("TOPPADDING", (0, 0), (-1, -1), 2.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5)]
    for r in range(1, len(data) - 1):
        style.append(("LINEBELOW", (0, r), (-1, r), 0.4, HexColor(RULE)))
    t.setStyle(TableStyle(style))
    out = []
    if h3_style is not None:
        out.append(Paragraph(ex["y_title"], h3_style))
    out += [t, Paragraph(ex["y_note"], note)]
    return [KeepTogether(out), Spacer(1, 4 * mm)]
