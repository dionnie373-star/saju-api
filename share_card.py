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


def render_card(view, lang="de"):
    """view -> PNG bytes."""
    t = TXT.get(lang, TXT["de"])
    W, H = 1080, 1350
    im = _bg(W, H)
    d = ImageDraw.Draw(im)

    # 상단 로고
    d.rounded_rectangle([72, 70, 128, 126], radius=6, fill=RED)
    d.text((100, 98), "팔자", font=_ko(22), fill=(255, 255, 255), anchor="mm")
    d.text((150, 98), "PALJA", font=_fr(40), fill=INK, anchor="lm")
    d.text((W - 72, 98), t["head"], font=_ws(30), fill=MUTE, anchor="rm")

    # 메인 카드
    d.rounded_rectangle([72, 190, W - 72, 1190], radius=36, fill=CARD, outline=LINE, width=3)

    day_key = view["pillars"]["day"]["stem"]
    day_name = view["pillars"]["day"]["stem_name"]
    d.text((W // 2, 262), t["day"].upper(), font=_wb(26), fill=FAINT, anchor="mm")
    _icon(d, day_key, W // 2, 385, 86)
    d.text((W // 2, 565), KO[day_key], font=_ko(140), fill=INK, anchor="mm")
    d.text((W // 2, 695), t["type"].format(n=day_name), font=_fr(54), fill=COLORS[day_key], anchor="mm")

    d.line([(150, 755), (W - 150, 755)], fill=LINE, width=2)

    # 오행 5칸
    d.text((W // 2, 806), t["dist"], font=_ws(28), fill=MUTE, anchor="mm")
    counts = {c["key"]: c["n"] for c in view["counts"]}
    names = {c["key"]: c["name"] for c in view["counts"]}
    total = max(1, int(view.get("total") or sum(counts.values())))
    x0, step = 150 + 70, (W - 300 - 140) / 4.0
    mx = max(counts.values()) or 1
    for i, key in enumerate(ORDER):
        cx = x0 + step * i
        n = counts.get(key, 0)
        r = 36
        if n == 0:
            d.ellipse([cx - r, 905 - r, cx + r, 905 + r], outline=LINE, width=4)
            d.text((cx, 905), "", font=_ws(20), fill=FAINT, anchor="mm")
        else:
            _icon(d, key, cx, 905, r)
        d.text((cx, 977), KO[key], font=_ko(30), fill=INK if n else FAINT, anchor="mm")
        d.text((cx, 1015), names.get(key, ""), font=_ws(21), fill=MUTE if n else FAINT, anchor="mm")
        d.text((cx, 1049), f"{n}/{total}", font=_wb(22), fill=COLORS[key] if n else FAINT, anchor="mm")
        _ = mx

    # 하단: 광고처럼 보이지 않게 작은 서명 한 줄
    d.text((W // 2, 1246), t["hook"], font=_ws(32), fill=MUTE, anchor="mm")
    d.text((W // 2, 1292), t["host"], font=_wb(34), fill=RED, anchor="mm")
    d.text((W // 2, 1328), t["note"], font=_ws(20), fill=FAINT, anchor="mm")

    buf = io.BytesIO()
    im.save(buf, "PNG", optimize=True)
    return buf.getvalue()
