"""공유 카드 이미지(1080x1350 PNG) 생성. 개인정보(이름·생일·출생지)는 카드에 넣지 않는다.
입력은 profile_view.build_profile_view()가 만든 view dict(기둥 5색 코드와 개수뿐)."""
import io
import os
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE, "fonts")

INK = (33, 29, 26)
MUTE = (94, 86, 78)
FAINT = (167, 158, 147)
PAPER = (246, 242, 232)
CARD = (255, 253, 249)
LINE = (230, 223, 210)
RED = (193, 68, 46)

COLORS = {"wood": (63, 122, 99), "fire": (193, 68, 46), "earth": (169, 126, 42),
          "metal": (117, 132, 146), "water": (38, 54, 79)}
KO = {"wood": "나무", "fire": "불", "earth": "흙", "metal": "쇠", "water": "물"}
ORDER = ["wood", "fire", "earth", "metal", "water"]

TXT = {
    "de": {"head": "Mein Saju-Profil", "day": "Tageselement", "type": "{n}-Typ", "dist": "Meine fünf Elemente",
           "hook": "Welcher Elementetyp bist du?", "host": "palja.de", "note": "Zur Unterhaltung und Selbstreflexion"},
    "fr": {"head": "Mon profil Saju", "day": "Élément du jour", "type": "Type {n}", "dist": "Mes cinq éléments",
           "hook": "Quel est ton type d'éléments ?", "host": "palja.fr", "note": "Pour le plaisir et la réflexion"},
    "es": {"head": "Mi perfil Saju", "day": "Elemento del día", "type": "Tipo {n}", "dist": "Mis cinco elementos",
           "hook": "¿Cuál es tu tipo de elementos?", "host": "palja.es", "note": "Para entretenimiento y reflexión"},
    "en": {"head": "My Saju profile", "day": "Day element", "type": "{n} type", "dist": "My five elements",
           "hook": "Which element type are you?", "host": "palja.one", "note": "For entertainment and self-reflection"},
}


def _font(name, size):
    return ImageFont.truetype(os.path.join(FONTS, name), size)


def _fr(s):
    return _font("Fraunces-SemiBold.ttf", s)


def _ws(s):
    return _font("WorkSans-Regular.ttf", s)


def _wb(s):
    return _font("WorkSans-Bold.ttf", s)


def _ko(s):
    return _font("NotoSerifKR-Hangul-SemiBold.ttf", s)


def _icon(d, key, cx, cy, r):
    """오행 아이콘: 컬러 원 + 흰색 도형(사이트 첫 화면과 같은 모양)."""
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=COLORS[key])
    w = (255, 255, 255)
    k = r / 22.0
    if key == "wood":
        d.polygon([(cx, cy - 11 * k), (cx + 10 * k, cy + 7 * k), (cx - 10 * k, cy + 7 * k)], fill=w)
    elif key == "fire":
        d.ellipse([cx - 7.5 * k, cy - 1 * k, cx + 7.5 * k, cy + 12 * k], fill=w)
        d.polygon([(cx, cy - 12 * k), (cx + 7 * k, cy + 3 * k), (cx - 7 * k, cy + 3 * k)], fill=w)
    elif key == "earth":
        d.rectangle([cx - 9 * k, cy - 9 * k, cx + 9 * k, cy + 9 * k], fill=w)
    elif key == "metal":
        d.ellipse([cx - 10 * k, cy - 10 * k, cx + 10 * k, cy + 10 * k], outline=w, width=max(2, int(3.4 * k)))
    else:
        for off in (-5, 5):
            pts = []
            for i in range(0, 41):
                x = cx - 11 * k + 22 * k * i / 40
                import math
                y = cy + off * k + 3.2 * k * math.sin(i / 40 * 2 * math.pi * 1.0 + math.pi)
                pts.append((x, y))
            d.line(pts, fill=w, width=max(2, int(3 * k)), joint="curve")


def _bg(w, h):
    im = Image.new("RGB", (w, h), PAPER)
    v = Image.new("L", (w, h), 0)
    ImageDraw.Draw(v).ellipse([-w * 0.25, -h * 0.15, w * 1.25, h * 1.15], fill=255)
    v = v.filter(ImageFilter.GaussianBlur(min(w, h) * 0.18))
    edge = Image.new("RGB", (w, h), (226, 214, 192))
    return Image.composite(im, edge, v)


def _wrap(d, text, font, maxw):
    words, lines, cur = text.split(" "), [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if d.textlength(trial, font=font) <= maxw or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def _fit(d, text, make_font, start, maxw, minsize=40):
    s = start
    while s > minsize and d.textlength(text, font=make_font(s)) > maxw:
        s -= 2
    return make_font(s)


def _illustration(de_name):
    import typen
    names = [v[1] for v in typen.SINGLE.values()] + [typen.BALANCED[1]] + [v[1] for v in typen.DUO.values()]
    idx = names.index(de_name) + 1
    return Image.open(os.path.join(HERE, "static_site", "img", "typen", "%02d.png" % idx)).convert("RGB")


def render_card(view, lang="de"):
    """view -> PNG bytes. 유형 이름·일러스트·오행 개수만 담는다(개인정보 없음)."""
    import typen
    t = TXT.get(lang, TXT["de"])
    counts = {c["key"]: c["n"] for c in view["counts"]}
    names = {c["key"]: c["name"] for c in view["counts"]}
    total = max(1, int(view.get("total") or sum(counts.values())))
    day_key = view["pillars"]["day"]["stem"]
    ct = typen.card_texts(counts, day_key, lang)

    W, H = 1080, 1350
    im = _bg(W, H)
    d = ImageDraw.Draw(im)

    # 상단 로고
    d.rounded_rectangle([72, 70, 128, 126], radius=6, fill=RED)
    d.text((100, 98), "팔자", font=_ko(22), fill=(255, 255, 255), anchor="mm")
    d.text((150, 98), "PALJA", font=_fr(40), fill=INK, anchor="lm")
    d.text((W - 72, 98), t["head"], font=_ws(30), fill=MUTE, anchor="rm")

    # 메인 카드
    cx0, cy0, cx1, cy1 = 72, 170, W - 72, 1166
    d.rounded_rectangle([cx0, cy0, cx1, cy1], radius=36, fill=CARD, outline=LINE, width=3)

    # 일러스트(곱하기 합성으로 종이 배경 제거)
    ill = _illustration(ct["de_name"])
    scale = min(460 / ill.width, 330 / ill.height)
    ill = ill.resize((int(ill.width * scale), int(ill.height * scale)), Image.LANCZOS)
    ox, oy = (W - ill.width) // 2, 215 + (330 - ill.height) // 2
    region = im.crop((ox, oy, ox + ill.width, oy + ill.height))
    from PIL import ImageChops
    im.paste(ImageChops.multiply(region, ill), (ox, oy))
    d = ImageDraw.Draw(im)

    # 유형 이름
    fnt = _fit(d, ct["name"], _fr, 84, 880)
    d.text((W // 2, 600), ct["name"], font=fnt, fill=INK, anchor="mm")
    # 부제
    sub_font = _ws(27)
    sub_lines = _wrap(d, ct["subtitle"], sub_font, 860)
    y = 686
    for ln in sub_lines[:2]:
        d.text((W // 2, y), ln, font=sub_font, fill=COLORS.get(day_key, MUTE) if False else MUTE, anchor="mm")
        y += 36
    # 한 줄 문구
    line_font = _fr(34)
    y += 30
    for ln in _wrap(d, ct["line"], line_font, 840)[:3]:
        d.text((W // 2, y), ln, font=line_font, fill=INK, anchor="mm")
        y += 48

    d.line([(150, 905), (W - 150, 905)], fill=LINE, width=2)
    d.text((W // 2, 945), t["dist"], font=_ws(26), fill=MUTE, anchor="mm")
    x0, step = 150 + 70, (W - 300 - 140) / 4.0
    for i, key in enumerate(ORDER):
        cx = x0 + step * i
        n = counts.get(key, 0)
        r = 32
        if n == 0:
            d.ellipse([cx - r, 1010 - r, cx + r, 1010 + r], outline=LINE, width=4)
        else:
            _icon(d, key, cx, 1010, r)
        d.text((cx, 1065), KO[key], font=_ko(28), fill=INK if n else FAINT, anchor="mm")
        d.text((cx, 1097), names.get(key, ""), font=_ws(20), fill=MUTE if n else FAINT, anchor="mm")
        d.text((cx, 1127), str(n), font=_wb(30), fill=COLORS[key] if n else FAINT, anchor="mm")

    # 하단: 광고처럼 보이지 않게 작은 서명 한 줄
    d.text((W // 2, 1206), t["hook"], font=_ws(32), fill=MUTE, anchor="mm")
    d.text((W // 2, 1250), t["host"], font=_wb(34), fill=RED, anchor="mm")
    d.text((W // 2, 1300), t["note"], font=_ws(20), fill=FAINT, anchor="mm")

    buf = io.BytesIO()
    im.save(buf, "PNG", optimize=True)
    return buf.getvalue()
