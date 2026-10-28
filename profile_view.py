"""무료 프로필 즉시 결과(웹 화면)용 데이터 + 고정 문구.

AI를 쓰지 않는다: 계산 결과(네 기둥, 오행 개수, 2027 세운)에서 바로 만들어서
즉시 응답하고, 비용·지연·환각이 없다. 문구는 사람이 쓴 고정 템플릿이며
"가능성/성찰" 어조만 쓴다(점술 단정·과학 암시 금지, 사이트 면책과 동일).
전체 AI 리포트는 선택 사항인 PDF 이메일(/signup)에 그대로 남는다.
"""

ELEMENTS = ["목", "화", "토", "금", "수"]
ELEM_KEY = {"목": "wood", "화": "fire", "토": "earth", "금": "metal", "수": "water"}

# 언어별: 기본 이름, 관사 포함형(문장 중간), 문장 첫머리형은 첫 글자를 대문자로.
NAMES = {
    "de": {"목": "Holz", "화": "Feuer", "토": "Erde", "금": "Metall", "수": "Wasser"},
    "fr": {"목": "Bois", "화": "Feu", "토": "Terre", "금": "Métal", "수": "Eau"},
    "es": {"목": "Madera", "화": "Fuego", "토": "Tierra", "금": "Metal", "수": "Agua"},
    "en": {"목": "Wood", "화": "Fire", "토": "Earth", "금": "Metal", "수": "Water"},
}
THE = {
    "de": dict(NAMES["de"]),
    "fr": {"목": "le Bois", "화": "le Feu", "토": "la Terre", "금": "le Métal", "수": "l'Eau"},
    "es": {"목": "la Madera", "화": "el Fuego", "토": "la Tierra", "금": "el Metal", "수": "el Agua"},
    "en": dict(NAMES["en"]),
}

KW = {
    "de": {"목": "Wachstum und neue Anfänge", "화": "Ausdruck und Sichtbarkeit", "토": "Stabilität und Verbindlichkeit",
           "금": "Klarheit und Entscheidungen", "수": "Tiefe und Anpassung"},
    "fr": {"목": "croissance et nouveaux départs", "화": "expression et visibilité", "토": "stabilité et engagement",
           "금": "clarté et décisions", "수": "profondeur et adaptation"},
    "es": {"목": "crecimiento y nuevos comienzos", "화": "expresión y visibilidad", "토": "estabilidad y compromiso",
           "금": "claridad y decisiones", "수": "profundidad y adaptación"},
    "en": {"목": "growth and new beginnings", "화": "expression and visibility", "토": "stability and commitment",
           "금": "clarity and decisions", "수": "depth and adaptability"},
}

T = {
    "de": {
        "day_title": "Dein Tageselement: {name}",
        "day_intro": "Im Saju steht das Tageselement für den Kern deiner Persönlichkeit – ein traditionelles Bild, kein Urteil. ",
        "day": {
            "목": "Holz wird mit Wachstum, Neugier und dem Wunsch verbunden, sich zu entwickeln. Frag dich: Wo möchtest du gerade wachsen?",
            "화": "Feuer wird mit Wärme, Ausdruck und Begeisterung verbunden. Frag dich: Wo gibst du gern Licht – und wann brauchst du selbst Ruhe?",
            "토": "Erde wird mit Verlässlichkeit, Mitte und Geduld verbunden. Frag dich: Wo bist du für andere der feste Punkt – und wo darfst du selbst Halt annehmen?",
            "금": "Metall wird mit Klarheit, Struktur und hohen Maßstäben verbunden. Frag dich: Wo hilft dir dein Anspruch – und wo darf er milder werden?",
            "수": "Wasser wird mit Tiefe, Anpassungsfähigkeit und Intuition verbunden. Frag dich: Wann lässt du dich treiben – und wann gibst du deinem Fluss eine Richtung?",
        },
        "dist_title": "Deine Elemente-Verteilung",
        "dom_one": "{the} ist in deinem Profil am stärksten vertreten ({n} von {total} Positionen). ",
        "dom_multi": "{names} sind in deinem Profil gleich stark vertreten ({n} von {total} Positionen) – dein Profil hat mehrere Schwerpunkte. ",
        "dom": {
            "목": "Das kann auf viel Antrieb zum Wachsen und Anfangen hindeuten. Zur Reflexion: Wo darf ein Vorhaben auch einmal in Ruhe reifen?",
            "화": "Das kann auf viel Energie und Ausdruckskraft hindeuten. Zur Reflexion: Wann braucht deine Begeisterung eine Pause?",
            "토": "Das kann auf viel Bodenhaftung und Verantwortungsgefühl hindeuten. Zur Reflexion: Wo darf etwas auch leicht und beweglich bleiben?",
            "금": "Das kann auf viel Sinn für Ordnung und Klarheit hindeuten. Zur Reflexion: Wo darf etwas auch unfertig bleiben?",
            "수": "Das kann auf viel Tiefgang und Anpassungsfähigkeit hindeuten. Zur Reflexion: Wo würde dir ein klarer Entschluss helfen?",
        },
        "lack_one": "{the} kommt in deinem Profil nicht vor. Die Tradition liest das nicht als Mangel, sondern als Themenfeld. ",
        "lack_multi": "Nicht vertreten sind: {names}. Die Tradition liest das nicht als Mangel, sondern als Themenfelder. ",
        "lack": {
            "목": "Wachstum und Aufbruch sind dann weniger „eingebaut“ – du kannst sie bewusst suchen, etwa indem du etwas Neues lernst.",
            "화": "Wärme und Ausdruck sind dann weniger „eingebaut“ – du kannst sie bewusst suchen, etwa durch Begegnungen, Bewegung oder Kreatives.",
            "토": "Bodenhaftung und Routine sind dann weniger „eingebaut“ – du kannst sie bewusst aufbauen, etwa durch kleine Rituale.",
            "금": "Struktur und Abgrenzung sind dann weniger „eingebaut“ – du kannst sie bewusst üben, etwa durch klare Absprachen.",
            "수": "Ruhe und Rückzug sind dann weniger „eingebaut“ – du kannst sie bewusst einplanen, etwa durch echte Pausen.",
        },
        "balanced": "Alle fünf Elemente sind vertreten – dein Profil wirkt in diesem Punkt ausgewogen. ",
        "no_hour": "Ohne Geburtszeit haben wir nur drei Säulen berechnet; mit der Uhrzeit kann sich die Verteilung noch verändern.",
        "y_title": "Dein Blick auf 2027",
        "y_two": "Das Saju-Jahr 2027 steht unter {the1} (oben) und {the2} (unten). {N1}: {kw1}. {N2}: {kw2}. ",
        "y_one": "Das Saju-Jahr 2027 steht unter {the1} (oben wie unten). {N1}: {kw1}. ",
        "y_zero": "{the} fehlt in deinem Profil – 2027 bringt dieses Thema von außen ins Spiel. ",
        "y_high": "{the} ist bei dir ohnehin stark – 2027 kann das noch verstärken. ",
        "y_mid": "{the} ist bei dir vorhanden – 2027 kann dieses Element zusätzlich anregen. ",
        "y_close": "Das ist ein Überblick zur Reflexion, keine Vorhersage. Wie das Jahr Monat für Monat aussehen kann, zeigt der Jahresreport.",
    },
    "fr": {
        "day_title": "Votre élément du jour : {name}",
        "day_intro": "Dans le Saju, l'élément du jour représente le noyau de votre personnalité – une image traditionnelle, pas un verdict. ",
        "day": {
            "목": "Le Bois est associé à la croissance, à la curiosité et au désir d'évoluer. Question pour vous : où cherchez-vous à grandir en ce moment ?",
            "화": "Le Feu est associé à la chaleur, à l'expression et à l'enthousiasme. Question pour vous : où donnez-vous volontiers de la lumière, et quand avez-vous besoin de calme ?",
            "토": "La Terre est associée à la fiabilité, au centre et à la patience. Question pour vous : où êtes-vous le point d'appui des autres, et où pouvez-vous accepter du soutien ?",
            "금": "Le Métal est associé à la clarté, à la structure et aux exigences élevées. Question pour vous : où votre exigence vous sert-elle, et où peut-elle s'adoucir ?",
            "수": "L'Eau est associée à la profondeur, à l'adaptabilité et à l'intuition. Question pour vous : quand vous laissez-vous porter, et quand donnez-vous une direction à votre courant ?",
        },
        "dist_title": "Votre répartition des éléments",
        "dom_one": "{The} est l'élément le plus présent dans votre profil ({n} positions sur {total}). ",
        "dom_multi": "{names} sont également présents dans votre profil ({n} positions sur {total}) – votre profil a plusieurs points forts. ",
        "dom": {
            "목": "Cela peut indiquer beaucoup d'élan pour commencer et grandir. Pour réfléchir : où un projet peut-il aussi mûrir tranquillement ?",
            "화": "Cela peut indiquer beaucoup d'énergie et de force d'expression. Pour réfléchir : quand votre enthousiasme a-t-il besoin d'une pause ?",
            "토": "Cela peut indiquer beaucoup d'ancrage et le sens des responsabilités. Pour réfléchir : où quelque chose peut-il rester plus léger et souple ?",
            "금": "Cela peut indiquer un fort sens de l'ordre et de la clarté. Pour réfléchir : où quelque chose peut-il rester inachevé ?",
            "수": "Cela peut indiquer de la profondeur et une grande capacité d'adaptation. Pour réfléchir : où une décision claire vous aiderait-elle ?",
        },
        "lack_one": "{The} n'apparaît pas dans votre profil. La tradition n'y voit pas un défaut, mais un thème à explorer. ",
        "lack_multi": "Ne sont pas représentés : {names}. La tradition n'y voit pas un défaut, mais des thèmes à explorer. ",
        "lack": {
            "목": "La croissance et l'élan sont alors moins « intégrés » : vous pouvez les cultiver volontairement, par exemple en apprenant quelque chose de nouveau.",
            "화": "La chaleur et l'expression sont alors moins « intégrées » : vous pouvez les chercher volontairement, par des rencontres, du mouvement ou de la création.",
            "토": "L'ancrage et la régularité sont alors moins « intégrés » : vous pouvez les construire volontairement, par de petits rituels.",
            "금": "La structure et les limites sont alors moins « intégrées » : vous pouvez les exercer volontairement, par des accords clairs.",
            "수": "Le calme et le retrait sont alors moins « intégrés » : vous pouvez les prévoir volontairement, par de vraies pauses.",
        },
        "balanced": "Les cinq éléments sont présents : sur ce point, votre profil semble équilibré. ",
        "no_hour": "Sans l'heure de naissance, nous n'avons calculé que trois piliers ; la répartition peut encore changer avec l'heure.",
        "y_title": "Votre regard sur 2027",
        "y_two": "L'année Saju 2027 est placée sous {the1} (en haut) et {the2} (en bas). {N1} : {kw1}. {N2} : {kw2}. ",
        "y_one": "L'année Saju 2027 est placée sous {the1} (en haut comme en bas). {N1} : {kw1}. ",
        "y_zero": "{The} manque dans votre profil : 2027 apporte ce thème de l'extérieur. ",
        "y_high": "{The} est déjà très {pres} chez vous : 2027 peut renforcer cet élément. ",
        "y_mid": "{The} est {pres} chez vous : 2027 peut activer cet élément davantage. ",
        "y_close": "Ceci est un aperçu pour la réflexion, pas une prédiction. Le rapport annuel détaille l'année mois par mois.",
    },
    "es": {
        "day_title": "Tu elemento del día: {name}",
        "day_intro": "En el Saju, el elemento del día representa el núcleo de tu personalidad: una imagen tradicional, no un veredicto. ",
        "day": {
            "목": "La Madera se asocia con el crecimiento, la curiosidad y el deseo de desarrollarse. Pregúntate: ¿dónde buscas crecer ahora mismo?",
            "화": "El Fuego se asocia con la calidez, la expresión y el entusiasmo. Pregúntate: ¿dónde das luz con gusto y cuándo necesitas calma?",
            "토": "La Tierra se asocia con la fiabilidad, el centro y la paciencia. Pregúntate: ¿dónde eres el punto de apoyo de otros y dónde puedes aceptar apoyo?",
            "금": "El Metal se asocia con la claridad, la estructura y las altas exigencias. Pregúntate: ¿dónde te ayuda tu exigencia y dónde puede ser más suave?",
            "수": "El Agua se asocia con la profundidad, la adaptabilidad y la intuición. Pregúntate: ¿cuándo te dejas llevar y cuándo das dirección a tu cauce?",
        },
        "dist_title": "La distribución de tus elementos",
        "dom_one": "{The} es el elemento más presente en tu perfil ({n} de {total} posiciones). ",
        "dom_multi": "{names} están igual de presentes en tu perfil ({n} de {total} posiciones): tu perfil tiene varios puntos fuertes. ",
        "dom": {
            "목": "Puede indicar mucho impulso para empezar y crecer. Para reflexionar: ¿dónde puede un proyecto madurar con calma?",
            "화": "Puede indicar mucha energía y fuerza expresiva. Para reflexionar: ¿cuándo necesita una pausa tu entusiasmo?",
            "토": "Puede indicar mucho arraigo y sentido de la responsabilidad. Para reflexionar: ¿dónde puede algo ser más ligero y flexible?",
            "금": "Puede indicar un fuerte sentido del orden y la claridad. Para reflexionar: ¿dónde puede algo quedar inacabado?",
            "수": "Puede indicar profundidad y gran capacidad de adaptación. Para reflexionar: ¿dónde te ayudaría una decisión clara?",
        },
        "lack_one": "{The} no aparece en tu perfil. La tradición no lo ve como una carencia, sino como un tema por explorar. ",
        "lack_multi": "No están presentes: {names}. La tradición no lo ve como una carencia, sino como temas por explorar. ",
        "lack": {
            "목": "El crecimiento y el impulso están entonces menos «incorporados»: puedes cultivarlos a propósito, por ejemplo aprendiendo algo nuevo.",
            "화": "La calidez y la expresión están entonces menos «incorporadas»: puedes buscarlas a propósito, con encuentros, movimiento o creatividad.",
            "토": "El arraigo y la rutina están entonces menos «incorporados»: puedes construirlos a propósito, con pequeños rituales.",
            "금": "La estructura y los límites están entonces menos «incorporados»: puedes practicarlos a propósito, con acuerdos claros.",
            "수": "La calma y el retiro están entonces menos «incorporados»: puedes planificarlos a propósito, con pausas reales.",
        },
        "balanced": "Los cinco elementos están presentes: en este punto tu perfil parece equilibrado. ",
        "no_hour": "Sin la hora de nacimiento solo hemos calculado tres pilares; la distribución aún puede cambiar con la hora.",
        "y_title": "Tu mirada a 2027",
        "y_two": "El año Saju 2027 está bajo {the1} (arriba) y {the2} (abajo). {N1}: {kw1}. {N2}: {kw2}. ",
        "y_one": "El año Saju 2027 está bajo {the1} (arriba y abajo). {N1}: {kw1}. ",
        "y_zero": "{The} falta en tu perfil: 2027 trae este tema desde fuera. ",
        "y_high": "{The} ya es muy fuerte en ti: 2027 puede reforzar este elemento. ",
        "y_mid": "{The} está presente en ti: 2027 puede activar este elemento aún más. ",
        "y_close": "Es una visión general para reflexionar, no una predicción. El informe anual detalla el año mes a mes.",
    },
    "en": {
        "day_title": "Your Day Element: {name}",
        "day_intro": "In Saju, the Day Element stands for the core of your personality – a traditional image, not a verdict. ",
        "day": {
            "목": "Wood is associated with growth, curiosity and the wish to develop. Ask yourself: where do you want to grow right now?",
            "화": "Fire is associated with warmth, expression and enthusiasm. Ask yourself: where do you like to give light, and when do you need calm yourself?",
            "토": "Earth is associated with reliability, centre and patience. Ask yourself: where are you the steady point for others, and where can you accept support?",
            "금": "Metal is associated with clarity, structure and high standards. Ask yourself: where does your standard help you, and where can it soften?",
            "수": "Water is associated with depth, adaptability and intuition. Ask yourself: when do you let yourself drift, and when do you give your flow a direction?",
        },
        "dist_title": "Your element balance",
        "dom_one": "{The} is the most present element in your profile ({n} of {total} positions). ",
        "dom_multi": "{names} are equally present in your profile ({n} of {total} positions) – your profile has several strengths. ",
        "dom": {
            "목": "This may point to plenty of drive to start things and grow. For reflection: where can a project also be left to ripen quietly?",
            "화": "This may point to plenty of energy and expressiveness. For reflection: when does your enthusiasm need a break?",
            "토": "This may point to plenty of grounding and sense of responsibility. For reflection: where can something stay light and flexible?",
            "금": "This may point to a strong sense of order and clarity. For reflection: where can something stay unfinished?",
            "수": "This may point to depth and strong adaptability. For reflection: where would a clear decision help you?",
        },
        "lack_one": "{The} does not appear in your profile. The tradition does not read this as a flaw, but as a theme to explore. ",
        "lack_multi": "Not represented: {names}. The tradition does not read this as a flaw, but as themes to explore. ",
        "lack": {
            "목": "Growth and momentum are then less “built in” – you can cultivate them on purpose, for example by learning something new.",
            "화": "Warmth and expression are then less “built in” – you can look for them on purpose, through meeting people, movement or creativity.",
            "토": "Grounding and routine are then less “built in” – you can build them on purpose, with small rituals.",
            "금": "Structure and boundaries are then less “built in” – you can practise them on purpose, with clear agreements.",
            "수": "Calm and retreat are then less “built in” – you can plan for them on purpose, with real breaks.",
        },
        "balanced": "All five elements are present – in this respect your profile looks balanced. ",
        "no_hour": "Without a birth time we calculated only three pillars; with the time, the balance may still change.",
        "y_title": "Your look at 2027",
        "y_two": "The Saju year 2027 stands under {the1} (above) and {the2} (below). {N1}: {kw1}. {N2}: {kw2}. ",
        "y_one": "The Saju year 2027 stands under {the1} (above and below). {N1}: {kw1}. ",
        "y_zero": "{The} is missing in your profile – 2027 brings this theme in from outside. ",
        "y_high": "{The} is already strong in you – 2027 may strengthen it further. ",
        "y_mid": "{The} is present in you – 2027 may stir it further. ",
        "y_close": "This is an overview for reflection, not a prediction. The annual report shows how the year can look month by month.",
    },
}


def _cap(s):
    return s[:1].upper() + s[1:]


_FEM = {"fr": {"토", "수"}, "es": {"목", "토"}}


def _gender_fmt(lang, e):
    fem = e in _FEM.get(lang, set())
    if lang == "fr":
        return {"pres": "présente" if fem else "présent", "lo": "l'"}
    if lang == "es":
        return {"pres": "", "lo": "la" if fem else "lo"}
    return {"pres": "", "lo": ""}


def _join(names, lang):
    if len(names) <= 1:
        return "".join(names)
    word = {"de": "und", "fr": "et", "es": "y", "en": "and"}[lang]
    return ", ".join(names[:-1]) + f" {word} " + names[-1]


def build_profile_view(calc_result, lang):
    """calc_result(run_calculation 반환값) -> 웹 화면용 dict. 개인정보(이름·이메일·입력값)는 담지 않는다."""
    t = T[lang]
    names = NAMES[lang]
    the = THE[lang]
    pillars = calc_result["pillars"]
    counts = {e: int(calc_result["element_counts"].get(e, 0)) for e in ELEMENTS}
    total = sum(counts.values())
    hour_known = bool(pillars.get("hour"))

    def pillar_view(p):
        if not p:
            return None
        return {
            "hanja": p["hanja"],
            "stem": ELEM_KEY[p["cheon_gan_element"]], "stem_name": names[p["cheon_gan_element"]],
            "branch": ELEM_KEY[p["ji_ji_element"]], "branch_name": names[p["ji_ji_element"]],
        }

    day_el = pillars["day"]["cheon_gan_element"]
    mx = max(counts.values())
    dominant = [e for e in ELEMENTS if counts[e] == mx] if mx > 0 else []
    lacking = [e for e in ELEMENTS if counts[e] == 0]

    sections = []
    sections.append({"title": t["day_title"].format(name=names[day_el]), "key": ELEM_KEY[day_el],
                     "text": t["day_intro"] + t["day"][day_el]})

    dist = ""
    if len(dominant) == 1:
        e = dominant[0]
        dist += t["dom_one"].format(The=_cap(the[e]), the=the[e], n=mx, total=total) + t["dom"][e] + "\n\n"
    elif dominant:
        dist += t["dom_multi"].format(names=_cap(_join([the[e] if lang in ("fr", "es") else names[e] for e in dominant], lang)),
                                      n=mx, total=total).strip() + "\n\n"
    if lacking:
        if len(lacking) == 1:
            e = lacking[0]
            dist += t["lack_one"].format(The=_cap(the[e]), the=the[e]) + t["lack"][e]
        else:
            dist += t["lack_multi"].format(names=_join([names[e] for e in lacking], lang))
            dist += " ".join(t["lack"][e] for e in lacking[:2])
    else:
        dist += t["balanced"].strip()
    if not hour_known:
        dist += "\n\n" + t["no_hour"]
    sections.append({"title": t["dist_title"], "key": None, "text": dist.strip()})

    yp = (calc_result.get("yearly") or {}).get("2027", {}).get("year_pillar")
    if yp:
        e1, e2 = yp["cheon_gan_element"], yp["ji_ji_element"]
        kw = KW[lang]
        if e1 == e2:
            y = t["y_one"].format(the1=the[e1], N1=_cap(the[e1]), kw1=kw[e1])
            personal = [e1]
        else:
            y = t["y_two"].format(the1=the[e1], the2=the[e2], N1=_cap(the[e1]), N2=_cap(the[e2]), kw1=kw[e1], kw2=kw[e2])
            personal = [e1, e2]
        for e in personal:
            c = counts[e]
            k = "y_zero" if c == 0 else ("y_high" if c >= 3 else "y_mid")
            y += t[k].format(The=_cap(the[e]), the=the[e], **_gender_fmt(lang, e))
        y += t["y_close"]
        sections.append({"title": t["y_title"], "key": None, "text": y.strip()})

    return {
        "pillars": {k: pillar_view(pillars.get(k)) for k in ("year", "month", "day", "hour")},
        "counts": [{"key": ELEM_KEY[e], "name": names[e], "n": counts[e]} for e in ELEMENTS],
        "total": total,
        "hour_known": hour_known,
        "sections": sections,
    }
