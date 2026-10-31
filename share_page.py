"""공유 카드 이미지(/t/<code>.png)와 읽기 전용 공유 페이지(/t/<code>).

code = 오행 개수 5자리 + 일간 원소 인덱스 1자리 (예: 031020 → 목0 화3 토1 금0 수2 합 6, 일간=목).
서버에는 아무것도 저장하지 않는다. 링크에는 생년월일·출생지·이름·기둥이 들어가지 않는다.
"""
import html
import re
from functools import lru_cache

from flask import Blueprint, Response, abort, request

import share_card
import typen

bp = Blueprint("share_page", __name__)

ORDER = typen.ORDER
_CODE_RE = re.compile(r"^[0-8]{5}[0-4]$")

UI = {
    "de": {"title": "Dein Elementetyp", "cta": "Finde deinen Elementetyp – kostenlos", "cta_sub": "Dein Profil in 10 Sekunden, ohne E-Mail.",
           "counts": "Die fünf Elemente", "privacy": "Datenschutz", "note_h": "Hinweis", "type_of": "Elementetyp",
           "alt": "Karte: {name}", "lang": "de", "privacy_href": "/datenschutz"},
    "en": {"title": "Your element type", "cta": "Find your element type – free", "cta_sub": "Your profile in 10 seconds, no email needed.",
           "counts": "The five elements", "privacy": "Privacy", "note_h": "Note", "type_of": "Element type",
           "alt": "Card: {name}", "lang": "en", "privacy_href": "/en/privacy"},
    "fr": {"title": "Ton type d'éléments", "cta": "Découvre ton type d'éléments – gratuit", "cta_sub": "Ton profil en 10 secondes, sans e-mail.",
           "counts": "Les cinq éléments", "privacy": "Confidentialité", "note_h": "Remarque", "type_of": "Type d'éléments",
           "alt": "Carte : {name}", "lang": "fr", "privacy_href": "/datenschutz"},
    "es": {"title": "Tu tipo de elementos", "cta": "Descubre tu tipo de elementos – gratis", "cta_sub": "Tu perfil en 10 segundos, sin correo.",
           "counts": "Los cinco elementos", "privacy": "Privacidad", "note_h": "Nota", "type_of": "Tipo de elementos",
           "alt": "Tarjeta: {name}", "lang": "es", "privacy_href": "/datenschutz"},
}
HOME = {"de": "/", "en": "/", "fr": "/", "es": "/"}


def make_code(counts, day_key):
    return "".join(str(int(counts.get(k, 0))) for k in ORDER) + str(ORDER.index(day_key))


def parse_code(code):
    if not _CODE_RE.match(code or ""):
        return None
    counts = {k: int(c) for k, c in zip(ORDER, code[:5])}
    if sum(counts.values()) not in (6, 8):
        return None
    return counts, ORDER[int(code[5])]


def _host_lang():
    import app as _a  # 요청 시점에만 import(순환 방지)
    if _a._is_one_host():
        return "en"
    if _a._is_fr_host():
        return "fr"
    if _a._is_es_host():
        return "es"
    return "de"


def _view(counts, day_key, lang):
    names = typen.EL_NAME[lang]
    return {"counts": [{"key": k, "n": counts[k], "name": names[k]} for k in ORDER],
            "total": sum(counts.values()), "pillars": {"day": {"stem": day_key}}}


@lru_cache(maxsize=512)
def _png(code, lang):
    counts, day = parse_code(code)
    return share_card.render_card(_view(counts, day, lang), lang)


def _noindex(resp):
    resp.headers["X-Robots-Tag"] = "noindex, nofollow"
    resp.headers["Referrer-Policy"] = "no-referrer"
    return resp


@bp.route("/t/<code>.png", methods=["GET"])
def card_png(code):
    if not parse_code(code):
        abort(404)
    resp = Response(_png(code, _host_lang()), mimetype="image/png")
    resp.headers["Cache-Control"] = "public, max-age=86400"
    return _noindex(resp)


@bp.route("/t/<code>", methods=["GET"])
def card_page(code):
    parsed = parse_code(code)
    if not parsed:
        abort(404)
    counts, day = parsed
    lang = _host_lang()
    ui = UI[lang]
    ct = typen.card_texts(counts, day, lang)
    e = lambda s: html.escape(str(s), quote=True)
    names = typen.EL_NAME[lang]
    total = sum(counts.values())
    bars = "".join(
        '<li><span class="dot" style="background:%s"></span><span class="en">%s</span>'
        '<span class="bar"><i style="width:%d%%;background:%s"></i></span><span class="n">%d</span></li>'
        % (share_card_hex(k), e(names[k]), int(100 * counts[k] / max(1, max(counts.values()))) if counts[k] else 0,
           share_card_hex(k), counts[k])
        for k in ORDER)
    miss = "".join("<li>%s</li>" % e(m) for m in ct["missing"])
    host = (request.host or "").split(":")[0]
    img_url = "https://%s/t/%s.png" % (host, code)
    page = """<!doctype html>
<html lang="%(lang)s"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>%(title)s: %(name)s – Palja</title>
<meta name="robots" content="noindex,nofollow"><meta name="referrer" content="no-referrer">
<meta name="description" content="%(line)s">
<meta property="og:title" content="%(title)s: %(name)s"><meta property="og:description" content="%(line)s">
<meta property="og:type" content="website"><meta property="og:image" content="%(img)s"><meta property="og:image:width" content="1080"><meta property="og:image:height" content="1350">
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:image" content="%(img)s">
<link rel="icon" href="/favicon.svg">
<style>
@font-face{font-family:'Fraunces';src:url('/assets/fonts/Fraunces-SemiBold.ttf');font-display:swap}
@font-face{font-family:'Work Sans';src:url('/assets/fonts/WorkSans-Regular.ttf');font-display:swap}
:root{--ink:#211D1A;--mute:#5E564E;--paper:#F6F2E8;--card:#FFFDF9;--line:#E6DFD2;--red:#C1442E}
*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font-family:'Work Sans',system-ui,sans-serif;line-height:1.55}
main{max-width:520px;margin:0 auto;padding:24px 16px 48px}
.brand{font-family:'Fraunces',Georgia,serif;font-size:22px;letter-spacing:.08em;margin:0 0 18px}
.card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:18px}
.card img{display:block;width:100%%;height:auto;border-radius:10px}
h1{font-family:'Fraunces',Georgia,serif;font-size:26px;line-height:1.2;margin:18px 0 4px}
.sub{color:var(--mute);margin:0 0 10px;font-size:15px}
.line{font-family:'Fraunces',Georgia,serif;font-size:19px;margin:0 0 18px}
ul{list-style:none;margin:0;padding:0}li{display:flex;align-items:center;gap:10px;margin:8px 0;font-size:14px;color:var(--mute)}
.dot{width:12px;height:12px;border-radius:50%%;flex:0 0 12px}.en{flex:0 0 74px}.bar{flex:1;height:10px;background:#EFE8DB;border-radius:6px;overflow:hidden}.bar i{display:block;height:100%%;border-radius:6px}.n{flex:0 0 40px;text-align:right}
.miss{margin-top:6px;font-size:13px}.miss li{display:block;margin:2px 0;color:#8A8074}
.cta{display:block;text-align:center;background:var(--red);color:#fff;text-decoration:none;font-weight:600;padding:15px 18px;border-radius:10px;margin-top:22px;font-size:17px}
.cta-sub{text-align:center;color:var(--mute);font-size:13.5px;margin:8px 0 0}
.note{margin-top:22px;font-size:12.5px;color:#8A8074}
footer{margin-top:18px;font-size:12.5px;text-align:center}footer a{color:#8A8074}
</style></head><body><main>
<p class="brand">PALJA</p>
<div class="card"><img src="/t/%(code)s.png" alt="%(alt)s" width="1080" height="1350">
<h1>%(name)s</h1><p class="sub">%(subtitle)s</p><p class="line">%(line)s</p>
<ul aria-label="%(counts_h)s">%(bars)s</ul><ul class="miss">%(miss)s</ul></div>
<a class="cta" href="/?src=share">%(cta)s</a><p class="cta-sub">%(cta_sub)s</p>
<p class="note">%(note)s</p>
<footer><a href="%(privacy_href)s">%(privacy)s</a></footer>
</main>
<script>try{if(localStorage.getItem('palja_nohit')!=='1'&&navigator.sendBeacon){navigator.sendBeacon('/api/ev',new Blob([JSON.stringify({ev:'card_page',src:'share'})],{type:'application/json'}));}}catch(e){}</script>
</body></html>""" % {
        "lang": ui["lang"], "title": e(ui["title"]), "name": e(ct["name"]), "line": e(ct["line"]), "img": e(img_url),
        "code": code, "alt": e(ui["alt"].format(name=ct["name"])), "subtitle": e(ct["subtitle"]), "counts_h": e(ui["counts"]),
        "bars": bars, "miss": miss, "cta": e(ui["cta"]), "cta_sub": e(ui["cta_sub"]), "note": e(ct["note"]),
        "privacy_href": e(ui["privacy_href"]), "privacy": e(ui["privacy"]),
    }
    return _noindex(Response(page, mimetype="text/html"))


def share_card_hex(key):
    r, g, b = share_card.COLORS[key]
    return "#%02X%02X%02X" % (r, g, b)
