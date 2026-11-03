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
         "Eine Idee, die einer von euch nur halb ausspricht, könnte vom anderen sofort weitergedacht werden, etwa beim Planen eines Ausflugs. Dann kann ein Gespräch von drei Sätzen schon zu einem fertigen Plan werden. Kritisch kann es werden, wenn dabei niemand mehr fragt, ob beide es wirklich wollen.",
         "Wobei kam zwischen euch zuletzt etwas leicht ins Rollen, und habt ihr dabei auch gefragt, ob beide es wollen?"),
        ("aufgaben_fliessen", "aufgaben",
         "Bei einer gemeinsamen Aufgabe könnte sich die Arbeit fast ohne Absprache verteilen: einer beginnt, der andere ergänzt. Dann kann es passieren, dass einer dauerhaft dieselbe Rolle übernimmt und es erst bemerkt, wenn es ihm zu viel wird.",
         "Welche Aufgabe landet bei euch immer bei derselben Person, und passt das für beide?"),
        ("mass_gemeinsam", "massstab",
         "Ob etwas gut genug ist, könntet ihr ähnlich einschätzen, etwa beim Aufräumen oder bei einem Termin. Das kann Reibung sparen. Fällt das Maß bei einem von euch einmal anders aus, kann der andere das schnell als Desinteresse lesen.",
         "Wo seid ihr euch beim „gut genug“ einig, und wo nicht?"),
    ),
    "wonjin": (
        ("bemerkung_nachhall", "wirkung",
         "Ein kurzer Satz wie „Das hättest du auch früher sagen können“ könnte bei einem von euch am Abend noch nachhallen, während der andere ihn nach fünf Minuten vergessen hat. Dann kann aus einer Nebenbemerkung ein Schweigen werden, dessen Grund niemand ausspricht.",
         "Welcher Satz hat zuletzt bei einem von euch nachgehallt, ohne dass der andere es gemerkt hat?"),
        ("geste_anders", "geste",
         "Wenn einer von euch spontan das Abendessen übernimmt oder eine Aufgabe abnimmt, könnte der andere das als Einmischung lesen statt als Hilfe. Dann kann ein Dank ausbleiben, und der Helfende fühlt sich nicht gesehen.",
         "Welche Hilfe wollt ihr voneinander ausdrücklich, und welche lieber nicht?"),
        ("rueckmeldung", "rueckmeldung",
         "Eine Nachricht, die nur mit „ok“ beantwortet wird, könnte für den einen erledigt bedeuten und für den anderen kühl wirken. Dann kann ein kleines Missverständnis tagelang mitlaufen.",
         "Was bedeutet ein knappes „ok“ für jeden von euch?"),
        ("zuneigung_ausdruck", "zuneigung",
         "Einer von euch zeigt Zuneigung eher mit Worten, der andere eher mit Taten, etwa indem er den Kaffee macht oder das Auto volltankt. Dann könnte der eine sich ungeliebt fühlen, obwohl der andere längst etwas für ihn getan hat.",
         "Woran merkt jeder von euch, dass er geliebt wird?"),
    ),
    "chung": (
        ("prioritaeten", "prioritaeten",
         "Bei der Planung eines freien Samstags könnte einer zuerst fragen, was Ruhe braucht, der andere, was auf keinen Fall ausfallen soll. Dann kann eine Diskussion über den Samstag in Wahrheit eine über Prioritäten sein.",
         "Was muss an einem gemeinsamen freien Tag für jeden von euch unbedingt vorkommen?"),
        ("veraenderung", "veraenderung",
         "Wenn ein Treffen kurzfristig eine Stunde früher stattfinden soll, könnte der eine das als Chance sehen und der andere als Störung. Dann kann der Streit um die Uhrzeit schnell größer wirken als die Uhrzeit selbst.",
         "Wie viel Vorlauf braucht jeder von euch, wenn sich ein Plan ändert?"),
        ("haltung_zeigen", "haltung",
         "Bei der Wahl eines Restaurants könnte einer sofort einen Vorschlag machen, während der andere erst alle Optionen sehen will. Dann kann der Schnelle sich ausgebremst fühlen und der Gründliche überrumpelt.",
         "Wer entscheidet bei euch schneller, und wie geht der andere damit um?"),
        ("nach_dem_streit", "streit",
         "Nach einem Streit könnte einer sofort darüber reden wollen, während der andere erst Abstand braucht. Dann kann das Warten für den einen wie Zurückweisung wirken und das Drängen für den anderen wie Druck.",
         "Was braucht jeder von euch nach einem Streit, und wie sagt ihr das, bevor es so weit ist?"),
    ),
    "hyung": (
        ("ton_schaerfe", "wirkung",
         "Ein Satz, der als sachlicher Hinweis gemeint ist, könnte in einem müden Moment schärfer klingen als beabsichtigt. Dann kann die Antwort ebenfalls schärfer ausfallen, und aus dem Hinweis wird ein Wortwechsel über den Ton.",
         "In welchen Momenten wird euer Ton schneller scharf, und wer merkt es zuerst?"),
        ("heikles_thema", "heikel",
         "Ein Thema, das ihr beide kennt und eher umgeht, könnte im falschen Moment doch auf den Tisch kommen. Dann kann es sich anfühlen, als sei alles Ungesagte auf einmal da.",
         "Welches Thema schiebt ihr gemeinsam vor euch her, und wann wäre ein guter Zeitpunkt dafür?"),
    ),
    "hyung_partial": (
        ("details", "details",
         "Beim Planen einer gemeinsamen Reise könnte einer die Details festlegen wollen, während der andere vieles offen lassen möchte. Dann kann der eine sich allein verantwortlich fühlen und der andere kontrolliert.",
         "Welche Details braucht jeder von euch vorab, und welche nicht?"),
        ("geklaert", "geklaert",
         "Etwas, das ihr schon besprochen glaubt, könnte nach Wochen wieder auftauchen, weil es für einen von euch noch offen war. Dann kann ein „Das hatten wir doch“ auf ein „Für mich war das nie geklärt“ treffen.",
         "Woran merkt ihr, dass eine Sache für beide wirklich geklärt ist?"),
        ("grenzen_benennen", "grenzen",
         "Wenn einem von euch etwas zu viel wird, etwa Nachfragen oder Planänderungen, könnte er das erst sagen, wenn es schon deutlich zu viel ist. Dann kann die Reaktion für den anderen unerwartet heftig wirken.",
         "Wie sagt ihr früh genug, dass euch etwas zu viel wird?"),
    ),
    "pa": (
        ("beilaeufige_absprache", "absprache",
         "Ein „Wir könnten ja mal im Sommer wegfahren“ im Vorbeigehen könnte für den einen ein Gedanke sein und für den anderen schon eine Zusage. Dann kann Enttäuschung entstehen, obwohl nie etwas verbindlich vereinbart wurde.",
         "Woran erkennt ihr, ob ein Satz eine Idee oder eine Verabredung ist?"),
        ("vertraute_ablaeufe", "ablauf",
         "Ein eingespielter Ablauf, etwa wer was wann erledigt, könnte stocken, sobald einer ihn ohne Ankündigung anders macht. Dann kann aus einer Kleinigkeit ein Streit darüber werden, worauf man sich verlassen konnte.",
         "Welcher eingespielte Ablauf soll bei euch nur nach Absprache geändert werden?"),
        ("kleine_entscheidungen", "kleinkram",
         "Kleine Entscheidungen wie Film, Essen oder Abfahrtszeit könnten sich bei euch oft im „Ist mir egal“ verlieren. Dann kann sich auf Dauer einer übergangen fühlen, ohne dass es je Streit gab.",
         "Wer von euch sagt öfter „egal“, obwohl es nicht egal ist?"),
        ("nachrichten_takt", "takt",
         "Einer von euch könnte tagsüber gern öfter schreiben, der andere erst abends antworten. Dann kann das späte Antworten wie Desinteresse wirken und das häufige Schreiben wie Kontrolle.",
         "Wie oft und wann tut es jedem von euch gut, voneinander zu hören?"),
    ),
    "hae": (
        ("stille_annahmen", "unausgesprochen",
         "Einer von euch könnte davon ausgehen, dass ein Termin selbstverständlich gemeinsam wahrgenommen wird, ohne es je erwähnt zu haben. Dann kann der andere etwas anderes planen, und beide sind überrascht.",
         "Was nehmt ihr beim anderen als selbstverständlich an, ohne es je gesagt zu haben?"),
        ("bekannt_voraussetzen", "unausgesprochen",
         "Eine Information, die nur nebenbei fiel, etwa eine geänderte Uhrzeit, könnte nur zur Hälfte ankommen, weil jeder annimmt, der andere wisse Bescheid. Dann kann einer pünktlich dastehen, während der andere nichts ahnt.",
         "Welche Information gebt ihr nur nebenbei weiter, und wie stellt ihr sicher, dass sie ankommt?"),
        ("form_mitteilung", "wirkung",
         "Eine wichtige Nachricht per kurzer Textnachricht könnte anders wirken als im Gespräch. Dann kann der Inhalt untergehen, während der Tonfall hängen bleibt.",
         "Was besprecht ihr lieber im Gespräch als schriftlich?"),
        ("alleine_zeit", "freiraum",
         "Wenn einer von euch einen Abend allein verbringen möchte, könnte der andere das als Abstand deuten. Dann kann aus dem Wunsch nach Ruhe ein Gespräch darüber werden, ob noch alles in Ordnung ist.",
         "Wie sagt ihr einander, dass ihr Zeit für euch braucht, ohne dass es nach Rückzug klingt?"),
    ),
    "banhap": (
        ("ausgangspunkt", "ausgangspunkt",
         "Bei einem Wochenendausflug könnte einer das Ziel schon im Kopf haben, während der andere erst unterwegs Lust darauf bekommt. Dann kann der eine sich ausgebremst fühlen und der andere gedrängt.",
         "Wer gibt bei euch die Richtung vor, und wann wird das zum Druck?"),
        ("idee_unfertig", "idee",
         "Eine halb ausgesprochene Idee, etwa „Wir sollten mal woanders wohnen“, könnte vom anderen schon als Plan verstanden werden. Dann kann aus einer Überlegung ein Streit über ein vermeintliches Versprechen werden.",
         "Woran erkennt ihr, ob ein Satz ein Gedanke oder ein Plan ist?"),
        ("interessen_teil", "interessen",
         "Bei einem gemeinsamen Hobby könnte einer tief einsteigen wollen, der andere nur gelegentlich mitmachen. Dann kann der Eifrige sich allein gelassen fühlen und der andere sich unter Druck gesetzt.",
         "Welche Interessen wollt ihr teilen, und welche behält jeder lieber für sich?"),
    ),
    "stem_hap": (
        ("gedanken_verbinden", "idee",
         "Wenn einer laut denkt, könnte der andere die Gedanken schon zu Ende führen. Das kann sich nach Verständnis anfühlen, aber auch dazu führen, dass der Erste sich nicht ausreden lassen darf.",
         "Wann wollt ihr, dass der andere nur zuhört und nichts ergänzt?"),
        ("blick_erweitern", "blick",
         "Auf einen neuen Vorschlag, etwa für den Urlaub, könnte einer von euch mit Neugier reagieren und der andere mit Skepsis. Dann kann die Skepsis wie Ablehnung klingen, obwohl sie nur Prüfen bedeutet.",
         "Wie reagiert jeder von euch zuerst auf einen neuen Vorschlag des anderen?"),
        ("ausdruck_ergaenzt", "ausdruck",
         "Einer könnte Gefühle schnell in Worte fassen, der andere eher in Gesten. Dann kann der Wortreiche sich unverstanden fühlen, weil Gesten allein ihm nicht genügen.",
         "Welche Worte oder Gesten braucht jeder von euch, um sich gesehen zu fühlen?"),
    ),
    "same_trine_group": (
        ("gruppe_wege", "gruppe",
         "Bei einem gemeinsamen Ziel, etwa einer Reise oder einem Vorhaben, könntet ihr in dieselbe Richtung wollen, aber unterschiedliche Wege wählen. Dann kann der Weg zum Streitpunkt werden, obwohl das Ziel feststeht.",
         "Bei welchem Ziel seid ihr euch einig, und wo geht ihr unterschiedlich dorthin?"),
        ("reichweite", "reichweite",
         "Bei Plänen für die nächsten Monate könnte einer weit vorausdenken und der andere im Moment bleiben. Dann kann der Vorausdenkende sich allein verantwortlich fühlen.",
         "Wie weit im Voraus plant jeder von euch gern?"),
    ),
    "same_branch": (
        ("beobachtung", "beobachtung",
         "Manche Gewohnheiten des anderen, etwa beim Aufstehen oder Aufräumen, könnten euch vertraut vorkommen, fast wie bei einem selbst. Dann kann gerade dieser Spiegel nerven, denn was man selbst kennt, stört am anderen oft besonders.",
         "Welche Angewohnheit des anderen kennt ihr auch von euch selbst?"),
        ("schaetzen_anders", "schaetzen",
         "Was jeder an der Beziehung schätzt, könnte ähnlich klingen, etwa Verlässlichkeit, aber Verschiedenes meinen. Dann kann „Verlässlichkeit“ für den einen Pünktlichkeit heißen und für den anderen, da zu sein, wenn es zählt.",
         "Was bedeutet Verlässlichkeit für jeden von euch konkret?"),
        ("erinnerung", "erinnerung",
         "Ein gemeinsamer Moment könnte in der Erinnerung beider unterschiedlich aussehen. Dann kann ein „So war das doch gar nicht“ mehr Gewicht bekommen als der Moment selbst.",
         "Welchen gemeinsamen Moment erinnert jeder von euch anders?"),
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
