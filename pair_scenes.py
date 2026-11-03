"""궁합 리포트용 '일상 장면 후보'와 '패턴 별명' 선택 (2026-11-03).

배경: 모델에게 장면을 즉흥으로 쓰게 하면 일반론(바넘 효과)과 반복이 생긴다.
그래서 관계 종류별 후보 은행을 코드에 두고, 두 사람의 계산 결과(관계 종류·지지 글자·위치)로
후보를 결정적으로 고른다. 같은 두 사람은 항상 같은 후보, 다른 쌍은 다른 후보가 나온다.

원칙
- 계산된 관계에 대해서만 장면을 준다(관계를 새로 만들지 않는다).
- 장면은 가능성 어조이며, 직업·가족·돈·건강 같은 생활 영역을 가정하지 않는다.
- 한 리포트에서 같은 family의 장면을 두 번 쓰지 않는다. 장면은 최대 MAX_SCENES개.
- 독일어 문장 첫머리에 대문자 'Ihr'를 쓰지 않는다(리포트 검사가 격식체로 본다).
- 귀문관살은 장면 후보를 두지 않는다(근거 수준이 낮아 가볍게만 다룬다).
- 별명은 편집용 제목이며 전통 용어가 아니다. 길흉·운명 표현을 쓰지 않는다.
"""

from __future__ import annotations

import hashlib

MAX_SCENES = 3

# 장면을 고르는 관계 순서(앞쪽 우선). 같은 순서가 곧 한정된 슬롯 안의 우선순위다.
SCENE_ORDER = (
    "yukhap", "wonjin", "chung", "hyung", "hyung_partial", "pa", "hae",
    "banhap", "stem_hap", "same_trine_group", "same_branch",
)

# 별명 분류용
CONNECTION_CODES = {"yukhap", "stem_hap", "banhap"}
TENSION_CODES = {"wonjin", "gwimun", "chung", "hyung", "hyung_partial", "pa", "hae"}

PATTERN_NAMES = {
    "both": "Nähe mit leiser Reibung",
    "connection": "Gemeinsame Anknüpfungspunkte",
    "tension": "Unterschiedliche Blickwinkel",
    "trine_only": "Gemeinsame Grundrichtung",
    "same_only": "Gemeinsamer Bezugspunkt",
    "none": "Eure eigene Verbindung",
}

KO_LABEL = {
    "yukhap": "육합(harmonische Verbindung)",
    "wonjin": "원진(emotionale Spannungen)",
    "chung": "충(unterschiedliche Impulse)",
    "hyung": "자묘형(Reibungspunkte)",
    "hyung_partial": "부분 형(Reibungspunkte)",
    "pa": "파(kleine Spannungen)",
    "hae": "해(unausgesprochene Missverständnisse)",
    "banhap": "반합(teilweise gemeinsame Dynamik)",
    "stem_hap": "천간합(verbindender Impuls)",
    "same_trine_group": "같은 삼합 그룹(gemeinsame Grundrichtung)",
    "same_branch": "같은 지지(gleicher Zweig)",
}

# (theme, family, 장면, 질문). theme은 은행 전체에서 유일, family는 같은 리포트 안에서 중복 금지.
BANK = {
    "yukhap": (
        ("idee_waechst", "idee",
         "Eine Idee könnte im Gespräch zwischen euch fast von selbst Form annehmen, ohne dass lange erklärt werden muss, was gemeint ist.",
         "Wobei kam zwischen euch zuletzt etwas leicht ins Rollen, und was hat dabei geholfen?"),
        ("aufgaben_fliessen", "aufgaben",
         "Bei gemeinsamen Aufgaben könnte sich eine Aufteilung ergeben, die sich für beide stimmig anfühlt, ohne dass sie lange verhandelt werden muss.",
         "Welche Aufgaben teilt ihr schon so, dass sich niemand allein zuständig fühlt?"),
        ("mass_gemeinsam", "massstab",
         "Bei einer Frage, die euch beide betrifft, könntet ihr überraschend schnell einen gemeinsamen Maßstab finden, auch wenn jeder auf anderem Weg dorthin kommt.",
         "Wo habt ihr einen gemeinsamen Maßstab gefunden, obwohl euer Weg dorthin verschieden war?"),
    ),
    "wonjin": (
        ("bemerkung_nachhall", "wirkung",
         "Eine beiläufige Bemerkung könnte bei einem von euch länger nachklingen, als sie gemeint war, während sie für den anderen längst vergessen ist.",
         "Gibt es Sätze, die bei einem von euch länger nachklingen als beim anderen, und wisst ihr voneinander davon?"),
        ("geste_anders", "geste",
         "Eine gut gemeinte Geste könnte anders ankommen als gedacht, ohne dass jemand etwas falsch gemacht hat.",
         "Welche kleine Geste bedeutet jedem von euch etwas anderes?"),
        ("rueckmeldung", "rueckmeldung",
         "Eine Rückmeldung könnte vom einen als hilfreicher Hinweis, vom anderen als persönliche Kritik gehört werden.",
         "Woran merkt ihr, ob eine Rückmeldung als Hinweis gemeint war und auch so angekommen ist?"),
    ),
    "chung": (
        ("prioritaeten", "prioritaeten",
         "In derselben Situation könnten bei euch unterschiedliche Prioritäten zuerst kommen, ohne dass eine davon richtiger wäre.",
         "Was kommt bei einer gemeinsamen Entscheidung für jeden von euch zuerst?"),
        ("veraenderung", "veraenderung",
         "Eine Veränderung könnte für den einen vor allem eine neue Möglichkeit sein, für den anderen ein Anlass, Bewährtes erst zu prüfen.",
         "Was seht ihr zuerst, wenn sich etwas Vertrautes ändert: die Chance oder das, was bleiben soll?"),
        ("haltung_zeigen", "haltung",
         "Wenn euch etwas wichtig ist, könnte der eine es deutlich aussprechen und der andere es eher indirekt zeigen.",
         "Woran erkennt ihr beim anderen, dass ihm etwas wirklich wichtig ist?"),
    ),
    "hyung": (
        ("ton_schaerfe", "wirkung",
         "Ein knapper Satz oder ein bestimmter Ton könnte bei einem von euch schärfer ankommen, als er gemeint war.",
         "Welcher Ton ist für jeden von euch noch in Ordnung, und wann wird es zu scharf?"),
        ("heikles_thema", "heikel",
         "Bei einem heiklen Thema könnte der eine sofort darüber sprechen wollen, während der andere zuerst Abstand braucht.",
         "Wie sprecht ihr ein heikles Thema an: sofort oder erst mit etwas Abstand?"),
    ),
    "hyung_partial": (
        ("details", "details",
         "Bei gleichem Ziel könnten einzelne Details zu unterschiedlichen Vorstellungen führen.",
         "Bei welchen Details habt ihr dasselbe Ziel, aber verschiedene Wege im Kopf?"),
        ("geklaert", "geklaert",
         "Wann eine Sache ausreichend geklärt ist, könnte für jeden von euch etwas anderes bedeuten.",
         "Woran merkt jeder von euch, dass etwas ausreichend geklärt ist?"),
        ("grenzen_benennen", "grenzen",
         "Was für den einen noch im Rahmen liegt, könnte für den anderen schon zu weit gehen, und das zeigt sich oft erst, wenn jemand es ausspricht.",
         "Wo liegen eure Grenzen, wenn ihr gemeinsam etwas festlegt?"),
    ),
    "pa": (
        ("beilaeufige_absprache", "absprache",
         "Eine beiläufige Absprache könnte für den einen unverbindlich sein und für den anderen schon fest gelten.",
         "Wann ist eine beiläufige Absprache für jeden von euch schon verbindlich?"),
        ("vertraute_ablaeufe", "ablauf",
         "Ein vertrauter Ablauf könnte gelegentlich stocken, weil jeder eine andere Vorstellung davon hat, wie es weitergeht.",
         "Welche gewohnten Abläufe funktionieren bei euch nur, wenn ihr sie kurz abstimmt?"),
        ("kleine_entscheidungen", "kleinkram",
         "Mehrere kleine Entscheidungen könnten sich unterschiedlich anfühlen, auch wenn keine einzelne davon wichtig ist.",
         "Welche kleinen Dinge entscheidet ihr verschieden, ohne dass es wirklich wichtig wäre?"),
    ),
    "hae": (
        ("stille_annahmen", "unausgesprochen",
         "In einer Situation könnte jeder von euch von anderen Voraussetzungen ausgehen, ohne es sofort zu merken.",
         "Welche unausgesprochene Annahme spielt bei euch manchmal mit?"),
        ("bekannt_voraussetzen", "unausgesprochen",
         "Eine Information könnte nur zur Hälfte ankommen, weil jeder annimmt, der andere wisse ohnehin Bescheid.",
         "Was setzt ihr beim anderen als bekannt voraus, ohne es je gesagt zu haben?"),
        ("form_mitteilung", "wirkung",
         "Die Art, wie etwas mitgeteilt wird, könnte für einen von euch mehr wiegen als der Inhalt.",
         "Was zählt für jeden von euch mehr, wenn etwas Wichtiges mitgeteilt wird: die Form oder der Inhalt?"),
    ),
    "banhap": (
        ("ausgangspunkt", "ausgangspunkt",
         "Ein Thema könnte euch verbinden, obwohl euch nicht dieselben Einzelheiten daran interessieren; die Gemeinsamkeit liegt dann eher im Ausgangspunkt.",
         "Bei welchem Thema teilt ihr den Ausgangspunkt, auch wenn euch Verschiedenes daran reizt?"),
        ("idee_unfertig", "idee",
         "Eine gemeinsame Idee könnte schon erkennbar sein, während einzelne Teile noch offen sind; daraus muss nicht sofort ein fertiger Plan werden.",
         "Welche gemeinsame Idee ist bei euch schon spürbar, obwohl noch nicht alles feststeht?"),
        ("interessen_teil", "interessen",
         "Eure Interessen könnten sich in einem Bereich überschneiden, während andere Bereiche bewusst eigen bleiben.",
         "Wo überschneiden sich eure Interessen, und was möchte jeder für sich behalten?"),
    ),
    "stem_hap": (
        ("gedanken_verbinden", "idee",
         "Zwei unterschiedliche Gedanken könnten sich an einer Stelle zu einer gemeinsamen Idee ergänzen, ohne dass einer seine Sicht aufgeben muss.",
         "Wo habt ihr zwei verschiedene Gedanken zu einer gemeinsamen Idee verbunden?"),
        ("blick_erweitern", "blick",
         "Eine Sichtweise des einen könnte dem anderen helfen, etwas Vertrautes neu zu sehen.",
         "Welche Sichtweise des anderen hat schon einmal den eigenen Blick erweitert?"),
        ("ausdruck_ergaenzt", "ausdruck",
         "Dieselbe Idee könnte von jedem von euch anders ausgedrückt werden, und gerade die Mischung zeigt eine weitere Seite.",
         "Wie ergänzt sich eure unterschiedliche Art, dieselbe Idee auszudrücken?"),
    ),
    "same_trine_group": (
        ("gruppe_wege", "gruppe",
         "Eine gemeinsame Gruppenzugehörigkeit bedeutet nicht, dass ihr gleich denkt oder handelt, kann aber ein Anlass sein, Ähnliches und Eigenes nebeneinander zu betrachten.",
         "Wo erkennt ihr eine gemeinsame Grundlage, obwohl eure Sichtweisen verschieden bleiben?"),
        ("reichweite", "reichweite",
         "Ein ähnlicher Bezugspunkt könnte nur einen begrenzten Bereich betreffen. Es lohnt sich, genau hinzusehen, was ihr tatsächlich teilt.",
         "Was teilt ihr bei einem gemeinsamen Thema wirklich, und was eher nicht?"),
    ),
    "same_branch": (
        ("beobachtung", "beobachtung",
         "Dass derselbe Zweig bei euch auftaucht, ist zunächst eine rechnerische Beobachtung und sagt nichts darüber, ob ihr euch gleicht.",
         "Welche Gemeinsamkeiten erkennt ihr tatsächlich, unabhängig von dieser Berechnung?"),
        ("schaetzen_anders", "schaetzen",
         "Etwas, das ihr beide schätzt, könnte jedem von euch aus anderen Gründen wichtig sein.",
         "Was schätzt ihr beide, aber aus verschiedenen Gründen?"),
        ("erinnerung", "erinnerung",
         "Eine gemeinsame Erfahrung könnte bei jedem von euch anders in Erinnerung geblieben sein.",
         "Welche gemeinsame Erfahrung erinnert ihr unterschiedlich?"),
    ),
}


def _codes_present(result):
    """compare() 결과에서 성립한 관계 코드 -> 그 관계를 처음 보인 쌍(핵심 우선)."""
    found = {}
    pairs = list(result.get("branch_pairs", [])) + list(result.get("stem_pairs", []))
    pairs.sort(key=lambda p: 0 if p.get("priority") == "primary" else 1)
    for p in pairs:
        for code in p.get("relations", []):
            found.setdefault(code, p)
        if p.get("same_branch"):
            found.setdefault("same_branch", p)
    return found


def _start_index(code, pair, n):
    key = "|".join([
        code,
        "".join(sorted((pair.get("a", ""), pair.get("b", "")))),
        f"{pair.get('person_a_position', '')}-{pair.get('person_b_position', '')}",
    ])
    return int(hashlib.md5(key.encode("utf-8")).hexdigest(), 16) % n


def pattern_name(result):
    """계산된 관계 조합 전체를 보고 별명 하나를 고른다. 같은 삼합 그룹/같은 지지만 있으면 따로 취급."""
    codes = set(_codes_present(result))
    has_conn = bool(codes & CONNECTION_CODES)
    has_tens = bool(codes & TENSION_CODES)
    if has_conn and has_tens:
        return PATTERN_NAMES["both"]
    if has_conn:
        return PATTERN_NAMES["connection"]
    if has_tens:
        return PATTERN_NAMES["tension"]
    if "same_trine_group" in codes:
        return PATTERN_NAMES["trine_only"]
    if "same_branch" in codes:
        return PATTERN_NAMES["same_only"]
    return PATTERN_NAMES["none"]


def select(result):
    """{"pattern_name": str, "scenes": [{code, theme, family, scene, question}]}"""
    present = _codes_present(result)
    scenes, used_families = [], set()
    for code in SCENE_ORDER:
        if len(scenes) >= MAX_SCENES:
            break
        pair = present.get(code)
        bank = BANK.get(code)
        if pair is None or not bank:
            continue
        start = _start_index(code, pair, len(bank))
        for k in range(len(bank)):
            theme, family, scene, question = bank[(start + k) % len(bank)]
            if family in used_families:
                continue
            used_families.add(family)
            scenes.append({"code": code, "theme": theme, "family": family,
                           "scene": scene, "question": question})
            break
    return {"pattern_name": pattern_name(result), "scenes": scenes}


def build_scene_text(selection):
    """프롬프트용 블록. 장면은 후보이며, 리포트에서는 자연스러운 독일어 문장으로 풀어 쓴다."""
    lines = [
        "[편집 장면 후보와 패턴 별명 - 코드가 두 사람의 계산 결과로 고른 것]",
        f"- 패턴 별명(편집용 제목이며 전통 용어가 아님): {selection['pattern_name']}",
    ]
    if selection["scenes"]:
        lines.append("- 아래 관계에만 장면 후보가 주어졌습니다. 이 관계들을 설명하는 단락에서 해당 후보의 주제를 쓰세요(문장은 다듬어도 되지만 주제를 바꾸거나 다른 장면을 새로 만들지 마세요):")
        for s in selection["scenes"]:
            lines.append(f"  · {KO_LABEL[s['code']]} / 장면 후보: {s['scene']} / 질문 후보: {s['question']}")
    else:
        lines.append("- 이번에는 장면 후보가 없습니다. 장면을 지어내지 말고 계산된 관계만 중립적으로 설명하세요.")
    return "\n".join(lines)
