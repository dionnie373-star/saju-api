#!/usr/bin/env python3
"""Builds the EN/FR/ES guide pages (static_site/<lang>/guides|guias/*.html) from tools/guides_<lang>.py.
Structure mirrors the German static_site/wissen/*.html pages. Run: python3 tools/build_guides.py"""
import importlib, json, os, sys, html as _h
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
KEYS = ["horoscope","newyear","calc","elements","gapja","sheep","ddi","bazi","ilju","pillars","yinyang"]
DE_SLUG = dict(horoscope="chinesisches-horoskop-2027", newyear="chinesisches-neujahr-2027", calc="chinesisches-tierkreiszeichen-berechnen",
  elements="fuenf-elemente-saju", gapja="gapja-60er-zyklus-hwangap", sheep="jahr-des-feuer-schafs-2027", ddi="koreanisches-tierkreiszeichen-ddi",
  bazi="saju-und-bazi-unterschied", ilju="tagessaeule-ilju-saju", pillars="vier-saeulen-saju", yinyang="yin-und-yang-saju")
SRC = dict(horoscope="cta-horoskop-2027", newyear="cta-neujahr-2027", calc="cta-tierzeichen", elements="cta-fuenf-elemente", gapja="cta-gapja",
  sheep="cta-feuer-schaf", ddi="cta-ddi", bazi="cta-saju-bazi", ilju="cta-ilju", pillars="cta-vier-saeulen", yinyang="cta-yin-yang")
# prefix = public path of the guide section on palja.de; host = canonical origin + path used on the language domain
LANGS = {
 "en": dict(prefix="/en/guides", dirname="en/guides", origin="https://palja.one", hpath="/en/guides", home="/en/"),
 "fr": dict(prefix="/fr/guides", dirname="fr/guides", origin="https://palja.fr", hpath="/guides", home="/fr/"),
 "es": dict(prefix="/es/guias", dirname="es/guias", origin="https://palja.es", hpath="/guias", home="/es/"),
}
CSS = open(os.path.join(ROOT, "static_site", "wissen", "yin-und-yang-saju.html"), encoding="utf-8").read()
CSS = CSS[CSS.index("<style>"):CSS.index("</style>")+8]
def esc(s): return _h.escape(s, quote=True)
def slug(lang, key, mod): return mod.SLUGS[key]
def alt_urls(key, mods):
    d = {"de": f"https://palja.de/wissen/{DE_SLUG[key]}"}
    for l, cfg in LANGS.items():
        d[l] = f"{cfg['origin']}{cfg['hpath']}/{mods[l].SLUGS[key]}"
    return d
def page(lang, mod, mods, key):
    cfg = LANGS[lang]; U = mod.UI; A = mod.ARTICLES[key]
    def L(m):  # {L:key} -> internal link path
        return f"{cfg['prefix']}/{mod.SLUGS[m]}"
    body = A["body"]
    for k in KEYS: body = body.replace("{L:%s}" % k, L(k))
    me = f"{cfg['origin']}{cfg['hpath']}/{mod.SLUGS[key]}"
    alts = alt_urls(key, mods)
    hrefl = "".join(f'<link rel="alternate" hreflang="{l}" href="{u}">\n' for l, u in alts.items())
    ld = json.dumps({"@context":"https://schema.org","@type":"Article","headline":A["h1"],"description":A["desc"],"inLanguage":lang,"mainEntityOfPage":me,
        "publisher":{"@type":"Organization","name":"Palja","url":cfg["origin"]+"/"}}, ensure_ascii=False)
    cta_p = U["cta_p"] + (" " + A["cta_extra"] if A.get("cta_extra") else "")
    return f'''<!doctype html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(A["title"])} | Palja</title>
<meta name="description" content="{esc(A["desc"])}">
<meta name="robots" content="noindex, nofollow"><!-- pilot: removed automatically on the public language domain -->
<link rel="canonical" href="{me}">
{hrefl}<meta property="og:type" content="article">
<meta property="og:site_name" content="Palja">
<meta property="og:title" content="{esc(A["title"])}">
<meta property="og:description" content="{esc(A["desc"])}">
<meta property="og:url" content="{me}">
<meta property="og:image" content="https://palja.de/images/og-image.jpg">
<link rel="icon" type="image/svg+xml" href="/favicon.svg">
<link rel="stylesheet" href="/assets/fonts/fonts.css">
<script type="application/ld+json">{ld}</script>
{CSS}
</head>
<body>
<div class="wrap">
  <a class="back" href="{cfg["home"]}">{U["back"]}</a>
  <h1>{A["h1"]}</h1>
  <p class="lead">{A["lead"]}</p>

{body.strip()}

  <div class="cta">
    <h2>{U["cta_h"]}</h2>
    <p>{cta_p}</p>
    <a class="btn" href="{cfg["home"]}?src={SRC[key]}">{U["btn"]}</a>
  </div>
  <nav class="more"><a href="{cfg["prefix"]}/">{U["all"]}</a></nav>
  <p class="note">{U["note"]}</p>
</div>
<script>
try {{ var s = "seo-{lang}-{SRC[key][4:]}"; var q = (new URLSearchParams(location.search).get('src') || '').toLowerCase(); if (q) s = q; if (localStorage.getItem('palja_nohit') !== '1' && navigator.sendBeacon) navigator.sendBeacon('/api/hit', new Blob([JSON.stringify({{src: s, path: location.pathname}})], {{type: 'application/json'}})); }} catch (e) {{}}
</script>
</body>
</html>
'''
def index(lang, mod, mods):
    cfg = LANGS[lang]; U = mod.UI
    me = f"{cfg['origin']}{cfg['hpath']}/"
    items = "".join(f'<li><a href="{cfg["prefix"]}/{mod.SLUGS[k]}">{mod.ARTICLES[k]["index_title"]}</a><span class="d">{mod.ARTICLES[k]["index_desc"]}</span></li>' for k in KEYS)
    return f'''<!doctype html>
<html lang="{lang}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(U["index_title"])} | Palja</title>
<meta name="description" content="{esc(U["index_desc"])}">
<meta name="robots" content="noindex, nofollow"><!-- pilot: removed automatically on the public language domain -->
<link rel="canonical" href="{me}">
<link rel="icon" type="image/svg+xml" href="/favicon.svg">
<link rel="stylesheet" href="/assets/fonts/fonts.css">
<style>
  body {{ margin:0; background:#FAF7F1; font-family:'Work Sans',sans-serif; color:#211D1A; line-height:1.7; }}
  h1 {{ font-family:'Fraunces',serif; font-size:32px; }} a {{ color:#C1442E; }}
  .wrap {{ max-width:720px; margin:0 auto; padding:48px 6vw 80px; }}
  li {{ margin:12px 0; }} .d {{ color:#6B625A; font-size:15px; display:block; }}
  .back {{ display:inline-block; margin-bottom:28px; font-size:14px; text-decoration:none; color:#6B625A; }}
</style></head><body><div class="wrap">
<a class="back" href="{cfg["home"]}">{U["back"]}</a>
<h1>{U["index_h1"]}</h1>
<p>{U["index_intro"]}</p>
<ul>{items}</ul>
</div></body></html>
'''
def main():
    mods = {l: importlib.import_module(f"guides_{l}") for l in LANGS}
    for l, mod in mods.items():
        assert set(mod.ARTICLES) == set(KEYS) and set(mod.SLUGS) == set(KEYS), l
        out = os.path.join(ROOT, "static_site", LANGS[l]["dirname"]); os.makedirs(out, exist_ok=True)
        for k in KEYS:
            open(os.path.join(out, mod.SLUGS[k] + ".html"), "w", encoding="utf-8").write(page(l, mod, mods, k))
        open(os.path.join(out, "index.html"), "w", encoding="utf-8").write(index(l, mod, mods))
        print(l, "ok", len(KEYS) + 1)
if __name__ == "__main__": main()
