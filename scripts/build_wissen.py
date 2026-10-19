# -*- coding: utf-8 -*-
"""Erzeugt static_site/wissen/*.html (deutsche Ratgeber-Seiten) aus ARTICLES. Aufruf: python3 scripts/build_wissen.py"""
import html, json, os

OUT = os.path.join(os.path.dirname(__file__), "..", "static_site", "wissen")
BASE = "https://palja.de"
DISCLAIMER = "Saju ist eine traditionelle Deutungslehre und dient hier der Unterhaltung und Selbstreflexion. Es sind keine Vorhersagen und kein Ersatz für professionelle Beratung."

TIERE = ["Ratte", "Ochse", "Tiger", "Hase", "Drache", "Schlange", "Pferd", "Schaf", "Affe", "Hahn", "Hund", "Schwein"]
def tier(year): return TIERE[(year - 2020) % 12]
def jahre(t):
    ys = [y for y in range(1960, 2028) if tier(y) == t]
    return ", ".join(str(y) for y in ys[-5:])

BEZUG_2027 = {
    "Ratte": "Keine besondere Beziehung zum Schaf. Das Jahresthema (Feuer und Erde) wirkt eher allgemein.",
    "Ochse": "Ochse und Schaf stehen sich im Tierkreis gegenüber (丑未, „Gegenüberstellung“). Traditionell liest man das als Thema Spannung und Veränderung.",
    "Tiger": "Keine besondere Beziehung zum Schaf. Das Jahresthema wirkt eher allgemein.",
    "Hase": "Hase, Schaf und Schwein bilden den „Holz-Dreierbund“ (亥卯未), eine verbindende Konstellation.",
    "Drache": "Keine besondere Beziehung zum Schaf. Das Jahresthema wirkt eher allgemein.",
    "Schlange": "Keine besondere Beziehung zum Schaf. Das Jahresthema wirkt eher allgemein.",
    "Pferd": "Pferd und Schaf gelten als „Paar“ (午未, Harmonie), eine der klassisch freundlichen Verbindungen.",
    "Schaf": "Dein eigenes Zeichen kehrt wieder. Man liest das traditionell als Jahr, in dem man stärker auf sich selbst schaut.",
    "Affe": "Keine besondere Beziehung zum Schaf. Das Jahresthema wirkt eher allgemein.",
    "Hahn": "Keine besondere Beziehung zum Schaf. Das Jahresthema wirkt eher allgemein.",
    "Hund": "Hund und Schaf stehen in einer „Reibung“ (戌未, Strafe/Xing). Traditionell liest man das als Thema Reibung und Klärung.",
    "Schwein": "Schwein, Hase und Schaf bilden den „Holz-Dreierbund“ (亥卯未), eine verbindende Konstellation.",
}

def table_rows():
    return "".join(f"<tr><td>{t}</td><td>{jahre(t)}</td></tr>" for t in TIERE)

def bezug_rows():
    return "".join(f"<tr><td>{t}</td><td>{html.escape(BEZUG_2027[t])}</td></tr>" for t in TIERE)

ARTICLES = [
{
 "slug": "chinesisches-horoskop-2027",
 "src": "seo-horoskop-2027",
 "title": "Chinesisches Horoskop 2027: Das Jahr des Feuer-Schafs",
 "desc": "2027 ist im chinesischen und koreanischen Kalender das Jahr 丁未, das Feuer-Schaf. Was das bedeutet, wann das Jahr beginnt und wie die zwölf Tierzeichen dazu stehen.",
 "h1": "Chinesisches Horoskop 2027: das Jahr des Feuer-Schafs",
 "lead": "2027 ist im chinesischen und koreanischen Kalender das Jahr 丁未 (Jeongmi): das Feuer-Schaf. Hier erfährst du, wann dieses Jahr wirklich beginnt, was die Zeichen bedeuten und wie die zwölf Tiere traditionell zum Schaf stehen.",
 "body": f"""
<h2>Was bedeutet 丁未?</h2>
<p>Jedes Jahr hat im ostasiatischen Kalender zwei Zeichen: einen <strong>Himmelsstamm</strong> (zehn Möglichkeiten) und einen <strong>Erdzweig</strong> (zwölf Möglichkeiten, die Tiere). 2027 lautet die Kombination 丁未.</p>
<ul>
<li><strong>丁 (Ding)</strong> steht für Yin-Feuer: die ruhige Flamme, Wärme, Ausdruck, Licht im Kleinen.</li>
<li><strong>未 (Wei)</strong> ist das Schaf. Sein zugehöriges Element ist Erde, und es steht für den Spätsommer.</li>
</ul>
<p>Daraus entsteht das Bild des „Feuer-Schafs“: Feuer und Erde, also Wärme auf festem Boden. Wie viel man in so ein Bild hineinliest, ist Auslegungssache.</p>

<h2>Wann beginnt das Jahr wirklich?</h2>
<p>Das Saju-Jahr beginnt nicht am 1. Januar und nicht zum Mondneujahr, sondern bei <strong>Lichun</strong> (立春, „Frühlingsbeginn“), um den 4. Februar. Wer im Januar 2027 geboren wird, gehört zum Tier des Vorjahres, 2026 also zum Pferd. Wer im Dezember geboren wird, hat das Tier des laufenden Jahres. Die genaue Uhrzeit von Lichun ändert sich von Jahr zu Jahr, weshalb Menschen mit Geburtstag Anfang Februar genau nachrechnen sollten.</p>

<h2>Welches Tier bist du?</h2>
<p>Die Tiere wiederholen sich alle zwölf Jahre. Die folgende Übersicht zeigt jeweils die letzten fünf Jahrgänge (für Geburtstage nach Lichun):</p>
<table class="t"><tr><th>Tier</th><th>Jahrgänge</th></tr>{table_rows()}</table>

<h2>Wie stehen die Tiere zum Schaf?</h2>
<p>In der Lehre werden Beziehungen zwischen den Tieren beschrieben: Harmonien, Gegenüberstellungen, Reibungen und Dreierbünde. Hier eine traditionelle Leseweise für 2027. Sie ist ein Gedankenanstoß, keine Prognose:</p>
<table class="t"><tr><th>Dein Tier</th><th>Beziehung zum Schaf-Jahr</th></tr>{bezug_rows()}</table>

<h2>Warum das Tierzeichen nur ein Teil ist</h2>
<p>Das Tier des Geburtsjahres ist nur eine von acht Zeichen (daher der koreanische Name <em>Palja</em>, 팔자, „acht Zeichen“). Im Saju gibt es vier Säulen: Jahr, Monat, Tag und Stunde, jede mit je einem Himmelsstamm und einem Erdzweig. Die Tag-Säule gilt als dein „Ich“. Wer nur das Tier kennt, kennt also nur einen Teil des Bildes.</p>
""",
},
{
 "slug": "jahr-des-feuer-schafs-2027",
 "src": "seo-feuer-schaf",
 "title": "Jahr des Feuer-Schafs 2027: Symbolik, Element und Tierbeziehungen",
 "desc": "Das Feuer-Schaf (丁未) im Saju: Yin-Feuer trifft auf Schaf (Erde). Symbolik, Beziehungen zu Pferd, Ochse, Hund, Hase und Schwein, und was du bei der Deutung beachten solltest.",
 "h1": "Das Jahr des Feuer-Schafs 2027 im Saju",
 "lead": "Das Feuer-Schaf 丁未 verbindet ein ruhiges, wärmendes Feuer mit dem Schaf, das zur Erde und zum Spätsommer gehört. Dieser Beitrag erklärt die Symbolik, die vier klassischen Tierbeziehungen und warum Deutung hier immer Auslegung ist.",
 "body": """
<h2>Feuer und Erde: das Bild des Jahres</h2>
<p>Im Saju haben die fünf Elemente (Holz, Feuer, Erde, Metall, Wasser) jeweils eine Reihe von Stichworten. Für Feuer sind das Wärme, Ausdruck und Sommer, für Erde Mitte, Stabilität und Spätsommer. 丁 ist <strong>Yin-Feuer</strong>: kein Lagerfeuer, sondern eher eine Kerze oder eine Glut. 未, das Schaf, trägt Erde in sich. Zusammen entsteht ein Bild von Wärme, die sich auf festen Boden setzt.</p>
<p>Wichtig: Das ist Symbolsprache. Sie lädt zum Nachdenken ein, etwa mit der Frage, wo in deinem Leben Wärme und Stabilität gerade zusammenfinden könnten. Sie sagt nicht, was passieren wird.</p>

<h2>Vier klassische Beziehungen zum Schaf</h2>
<h3>Pferd und Schaf: Harmonie (午未)</h3>
<p>Pferd und Schaf bilden eine der „Sechs Harmonien“. In der Lehre wird sie als freundliche, unterstützende Verbindung beschrieben. Das Pferd-Jahr 2026 geht damit unmittelbar in ein Schaf-Jahr über, in dem die beiden Zeichen „nebeneinander“ stehen.</p>
<h3>Ochse und Schaf: Gegenüberstellung (丑未)</h3>
<p>Ochse und Schaf liegen im Tierkreis genau gegenüber. Das nennt man <em>Chong</em>, wörtlich „Zusammenstoß“. Traditionell liest man darin Bewegung, Veränderung, manchmal Spannung. Es ist keine „schlechte“ Konstellation, sondern eine bewegte.</p>
<h3>Hund und Schaf: Reibung (戌未)</h3>
<p>Hund, Ochse und Schaf bilden zusammen eine „Strafe“-Konstellation (<em>Xing</em>). Gemeint ist weniger Strafe als Reibung: etwas, das sich nicht sofort fügt und Klärung braucht.</p>
<h3>Hase, Schwein und Schaf: Dreierbund Holz (亥卯未)</h3>
<p>Schwein, Hase und Schaf gehören zu einem „Dreierbund“, der im Saju mit dem Element Holz verbunden wird: Wachstum und Anfang. Er gilt als verbindende Konstellation.</p>

<h2>Und mein eigenes Zeichen?</h2>
<p>Wer selbst Schaf ist (Jahrgänge nach Lichun 2015, 2003, 1991, 1979, 1967 und davor), erlebt ein „Rückkehrjahr“. In Korea spricht man oft vom <em>Ddi-Jahr</em> (띠해), dem Jahr des eigenen Tieres, das traditionell mit Wiederholung und Selbstprüfung verbunden wird. Manche sehen darin Chance, andere ein Jahr der Vorsicht. Beides sind Lesarten, keine Tatsachen.</p>

<h2>Wie du so eine Deutung nutzen kannst</h2>
<ul>
<li>Als <strong>Fragenliste</strong>: Welche Themen (Wärme, Stabilität, Beziehungen, Selbstbild) beschäftigen mich gerade?</li>
<li>Als <strong>Gesprächsanlass</strong> mit Freunden oder Familie, wie man es in Korea zum Jahreswechsel oft macht.</li>
<li>Nicht als Grundlage für <strong>große Entscheidungen</strong> wie Geld, Gesundheit oder Beruf.</li>
</ul>
<p>Für den Einstieg lohnt der Überblick <a href="/wissen/chinesisches-horoskop-2027">Chinesisches Horoskop 2027</a>, wo du dein Tier und die Jahrgänge findest.</p>
""",
},
]

PAGE = """<!doctype html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} | Palja</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{url}">
<meta property="og:type" content="article">
<meta property="og:site_name" content="Palja">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="https://palja.de/images/og-image.jpg">
<link rel="icon" type="image/svg+xml" href="/favicon.svg">
<link rel="stylesheet" href="/assets/fonts/fonts.css">
<script type="application/ld+json">{ld}</script>
<style>
  body {{ margin:0; background:#FAF7F1; font-family:'Work Sans',sans-serif; color:#211D1A; line-height:1.75; }}
  h1,h2,h3 {{ font-family:'Fraunces',serif; font-weight:600; line-height:1.25; }}
  a {{ color:#C1442E; }} a:hover {{ color:#9C3624; }}
  .wrap {{ max-width:720px; margin:0 auto; padding:48px 6vw 80px; }}
  .back {{ display:inline-block; margin-bottom:28px; font-size:14px; text-decoration:none; color:#6B625A; }}
  h1 {{ font-size:34px; margin:0 0 16px; }} h2 {{ font-size:23px; margin:40px 0 10px; }} h3 {{ font-size:18px; margin:26px 0 6px; }}
  .lead {{ font-size:18px; color:#4a423b; }}
  table.t {{ border-collapse:collapse; width:100%; margin:16px 0; font-size:15px; }}
  table.t th, table.t td {{ text-align:left; padding:9px 10px; border-bottom:1px solid #E4DCCF; vertical-align:top; }}
  table.t th {{ font-weight:600; color:#6B625A; }}
  .cta {{ margin:48px 0 8px; padding:26px 24px; background:#F3EEE4; border:1px solid #E4DCCF; border-radius:12px; }}
  .cta h2 {{ margin:0 0 8px; font-size:22px; }}
  .btn {{ display:inline-block; margin-top:8px; padding:13px 22px; background:#C1442E; color:#fff; border-radius:8px; text-decoration:none; font-weight:600; }}
  .btn:hover {{ background:#9C3624; color:#fff; }}
  .note {{ font-size:13px; color:#8A8074; margin-top:28px; }}
  nav.more {{ margin-top:36px; font-size:15px; }}
</style>
</head>
<body>
<div class="wrap">
  <a class="back" href="/">← Zu Palja</a>
  <h1>{h1}</h1>
  <p class="lead">{lead}</p>
  {body}
  <div class="cta">
    <h2>Dein Fünf-Elemente-Profil, kostenlos</h2>
    <p>Aus deinem Geburtsdatum (und, wenn du sie kennst, der Uhrzeit) erstellen wir dein persönliches Profil nach der koreanischen Saju-Lehre.</p>
    <a class="btn" href="/?src={cta}">Kostenloses Profil erstellen</a>
  </div>
  <nav class="more"><a href="/wissen/">Alle Ratgeber</a></nav>
  <p class="note">{disclaimer}</p>
</div>
<script>
try {{ var s = {src_js}; if (navigator.sendBeacon) navigator.sendBeacon('/api/hit', new Blob([JSON.stringify({{src: s, path: location.pathname}})], {{type: 'application/json'}})); }} catch (e) {{}}
</script>
</body>
</html>
"""

INDEX = """<!doctype html>
<html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Ratgeber: Saju und chinesisches Horoskop | Palja</title>
<meta name="description" content="Ratgeber zu Saju, chinesischem Horoskop und den fünf Elementen, verständlich erklärt aus koreanischer Sicht.">
<link rel="canonical" href="https://palja.de/wissen/">
<link rel="icon" type="image/svg+xml" href="/favicon.svg">
<link rel="stylesheet" href="/assets/fonts/fonts.css">
<style>
  body {{ margin:0; background:#FAF7F1; font-family:'Work Sans',sans-serif; color:#211D1A; line-height:1.7; }}
  h1 {{ font-family:'Fraunces',serif; font-size:32px; }} a {{ color:#C1442E; }}
  .wrap {{ max-width:720px; margin:0 auto; padding:48px 6vw 80px; }}
  li {{ margin:12px 0; }} .d {{ color:#6B625A; font-size:15px; display:block; }}
  .back {{ display:inline-block; margin-bottom:28px; font-size:14px; text-decoration:none; color:#6B625A; }}
</style></head><body><div class="wrap">
<a class="back" href="/">← Zu Palja</a>
<h1>Ratgeber</h1>
<p>Saju und das chinesische Horoskop, verständlich erklärt. Alles zur Unterhaltung und Selbstreflexion, ohne Vorhersagen.</p>
<ul>{items}</ul>
</div></body></html>
"""

def main():
    os.makedirs(OUT, exist_ok=True)
    items = ""
    for a in ARTICLES:
        url = f"{BASE}/wissen/{a['slug']}"
        ld = json.dumps({"@context": "https://schema.org", "@type": "Article", "headline": a["title"],
                         "description": a["desc"], "inLanguage": "de", "mainEntityOfPage": url,
                         "author": {"@type": "Organization", "name": "Palja"},
                         "publisher": {"@type": "Organization", "name": "Palja"}}, ensure_ascii=False)
        page = PAGE.format(title=html.escape(a["title"]), desc=html.escape(a["desc"]), url=url, ld=ld,
                           h1=html.escape(a["h1"]), lead=html.escape(a["lead"]), body=a["body"],
                           src=a["src"], cta=a["src"].replace("seo-","cta-",1), src_js=json.dumps(a["src"]), disclaimer=DISCLAIMER)
        with open(os.path.join(OUT, a["slug"] + ".html"), "w", encoding="utf-8") as f:
            f.write(page)
        items += f'<li><a href="/wissen/{a["slug"]}">{html.escape(a["h1"])}</a><span class="d">{html.escape(a["desc"])}</span></li>'
    with open(os.path.join(OUT, "index.html"), "w", encoding="utf-8") as f:
        f.write(INDEX.format(items=items))
    sm = os.path.join(os.path.dirname(__file__), "..", "static_site", "sitemap.xml")
    x = open(sm, encoding="utf-8").read()
    import re
    x = re.sub(r"\s*<url>\s*<loc>https://palja.de/wissen[^<]*</loc>.*?</url>", "", x, flags=re.S)
    add = "".join(f"  <url>\n    <loc>{u}</loc>\n    <changefreq>monthly</changefreq>\n    <priority>0.7</priority>\n  </url>\n"
                  for u in [BASE + "/wissen/"] + [f"{BASE}/wissen/{a['slug']}" for a in ARTICLES])
    x = x.replace("</urlset>", add + "</urlset>")
    open(sm, "w", encoding="utf-8").write(x)
    print("OK", len(ARTICLES), "Artikel")

if __name__ == "__main__":
    main()
