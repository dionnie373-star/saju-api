"""디자인 QA용 테스트 PDF 생성 스크립트.

목적: production과 완전히 동일한 렌더링 함수(build_pdf, _report_text_to_flowables,
_build_daewoon_timeline_drawing, _draw_branded_footer)를 그대로 호출해서 PDF를
만든다. AI(Claude API) 호출도, 이메일 발송도, 결제도 전혀 하지 않는다 —
report_text는 실제 형식(##/-/> 마크다운)을 따르는 예시 텍스트일 뿐이다.
디자인/코드는 전혀 수정하지 않음.
"""
import os
import sys

sys.path.insert(0, "/home/claude/saju-api")
os.environ.setdefault("ANTHROPIC_API_KEY", "test-not-used")
os.environ.setdefault("BREVO_API_KEY", "test-not-used")
os.environ.setdefault("FROM_EMAIL", "test@example.com")
os.environ.setdefault("FROM_NAME", "Palja Test")

from app import run_calculation
from report_facts import compute_daewoon_facts
from report_pipeline import build_pdf, _build_daewoon_timeline_drawing
from reportlab.platypus import Paragraph, Spacer
from reportlab.lib.units import mm
import report_pipeline as rp

calc = run_calculation({
    "name": "Test Person",
    "birth_date": "1991-03-14",
    "birth_time": "07:30",
    "birth_city": "Berlin",
    "gender": "female",
    "daewoon_count": 8,
})

daewoon_facts = compute_daewoon_facts(calc["daewoon"])

MONTHS = [
    "Januar — Ressourcen im Fokus", "Februar — Die innere Verfassung neu justieren",
    "März — Verstärkung und inneres Wachstum", "April — Wiederannäherung an Substanz",
    "Mai — Talente zeigen sich", "Juni — Intensität und innerer Ausdruck",
    "Juli — Die Schwelle von Ausdruck zu Ergebnis", "August — Grenzen und Klärung",
    "September — Substanz verfestigt sich", "Oktober — Die lange Ressourcen-Phase beginnt",
    "November — Beziehung kommt in den Fokus", "Dezember — Innere Neuausrichtung zum Jahresende",
]

lines = []
lines.append("## Einleitung")
lines.append("")
lines.append(
    "Dies ist ein Beispieltext zu reinen Design-QA-Zwecken (Platzhalterinhalt, "
    "keine echte KI-Generierung). Er folgt exakt demselben Markdown-Format "
    "(##, -, >), das die echten Produktionsberichte verwenden, damit das "
    "PDF-Layout 1:1 dem entspricht, was ein zahlender Kunde tatsächlich erhält."
)
lines.append("")
lines.append(
    "- Deine Fünf-Elemente-Zusammensetzung im Überblick"
)
lines.append("- Eine erste Einschätzung deiner Persönlichkeit")
lines.append("- Rückblick & Ausblick aufs Jahr")
lines.append("")
lines.append("> Der Anfang ist die Hälfte von allem.")
lines.append("")

for i, m in enumerate(MONTHS, start=1):
    lines.append(f"## {i}. {m}")
    lines.append("")
    lines.append(
        "Dieser Monat bringt eine Verschiebung im energetischen Gleichgewicht mit sich. "
        "Was im vergangenen Zeitraum begonnen wurde, verlangt jetzt nach Klarheit statt "
        "nach weiterem Ausgreifen. Achte besonders auf Momente, in denen sich Substanz "
        "und Ausdruck die Waage halten — genau dort liegt in diesem Monat dein Ansatzpunkt."
    )
    lines.append("")
    lines.append(
        "**Reflexionsfrage:** Welcher Teil deines Lebens verdient in diesem Monat "
        "neu bewertet zu werden?"
    )
    lines.append("")
    if i == 7:
        lines.append("> Nicht jede Ruhephase ist Stillstand — manche ist Sammlung.")
        lines.append("")

lines.append("## Dein Jahr im Überblick: Rhythmen und Rhythmuswechsel")
lines.append("")
lines.append(
    "Über das gesamte Jahr hinweg zeigt sich ein wiederkehrendes Muster von Aufbau, "
    "Verdichtung und Neuausrichtung. Dieses Muster ist kein Zufall, sondern folgt der "
    "energetischen Struktur deines Geburtsbildes."
)
lines.append("")
lines.append("## Deine Lebensphasen (Daewoon)")
lines.append("")
lines.append(
    "Die obige Zeitlinie zeigt deine 10-Jahres-Lebensphasen von Geburt bis ins hohe "
    "Alter. Jede Phase ist einer von vier Achsen zugeordnet: Ressourcen, Beziehung, "
    "Talent & Werk oder Stabilität."
)
lines.append("")
lines.append("> Eine Lebensphase ist kein Urteil, sondern ein Klima, in dem du handelst.")
lines.append("")
lines.append("## Abschließende Gedanken")
lines.append("")
lines.append(
    "Dieser Bericht dient der Unterhaltung und persönlichen Selbstreflexion und "
    "ersetzt keine medizinische oder psychologische Beratung. Wir hoffen, er gibt "
    "dir neue Perspektiven auf die Muster in deinem Leben."
)

report_text = "\n".join(lines)
print("report_text word count:", len(report_text.split()))

intro_flowables = [
    Paragraph("Deine Lebenskarte auf einen Blick", rp._PDF_STYLES["h2"]),
    rp._H2_RULE,
    _build_daewoon_timeline_drawing(daewoon_facts),
    Spacer(1, 6 * mm),
]

out_path = "/home/claude/saju-api/design_qa/palja_test_report.pdf"
build_pdf(
    out_path,
    title="Deine Saju-Lebenskarte",
    subtitle="Erstellt für Test Person",
    report_text=report_text,
    intro_flowables=intro_flowables,
)
print("PDF written to", out_path)
