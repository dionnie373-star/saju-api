"""오행 분포 유형(간단 버전). 개수(counts)만으로 유형을 정한다 — 전통 사주 해석이 아니라 대중용 맛보기다.
문구 원칙: 자연/장인 이미지, 장점 하나 + 귀여운 약점 하나, 좋다/나쁘다 판단 없음, '경향'으로 표현.
"""

ORDER = ["wood", "fire", "earth", "metal", "water"]
# 상생 순서(목→화→토→금→수→목)와 같다. 동률일 때 이 순서로 앞선 쪽을 주(主)로 본다.

# (한글 별명, 독일어 이름, 독일어 한 줄, 한국어 뜻)  — 2차 첨삭(GPT) 반영본
SINGLE = {
    "wood": ("원시림형", "Der Urwald", "Wächst in alle Richtungen – und hat schon das nächste Projekt im Kopf.", "사방으로 자라고, 벌써 다음 프로젝트를 구상 중."),
    "fire": ("태양형", "Die Sonne", "Wärmt jeden Raum auf – braucht danach dringend Abstand zum eigenen Glanz.", "방을 따뜻하게 만들지만, 자기 빛에서 잠시 떨어질 시간이 필요."),
    "earth": ("산형", "Der Berg", "Verlässlich bis in die Wurzeln – bewegt sich nur, wenn er will.", "뿌리까지 믿음직하지만, 움직이는 건 본인이 원할 때만."),
    "metal": ("수정형", "Der Kristall", "Glasklar im Denken – und manchmal scharfkantig im Ton.", "생각은 투명하지만 말투는 가끔 날카롭다."),
    "water": ("심해형", "Die Tiefsee", "Wirkt tiefenentspannt – im Kopf laufen gerade vierzehn Tabs.", "아주 태연해 보이지만, 머릿속에는 탭 14개가 열려 있다."),
}

BALANCED = ("오케스트라형", "Das Orchester", "Alle fünf Elemente kommen vor – die Frage ist nur, wer dirigiert.", "다섯 오행이 모두 나타난다. 문제는 누가 지휘하느냐뿐.")

# (주, 부) → (한글 별명, 독일어 이름, 독일어 한 줄, 한국어 뜻)
DUO = {
    ("wood", "fire"): ("불씨형", "Der Funkenflug", "Aus einer Idee werden zehn – und plötzlich ist überall Bewegung.", "아이디어 하나가 열 개가 되고, 어느새 모든 곳이 분주해진다."),
    ("wood", "earth"): ("포도밭형", "Der Weinberg", "Wächst mit Geduld – guter Wein braucht eben Zeit.", "인내하며 자란다. 좋은 와인에는 시간이 필요하니까."),
    ("wood", "metal"): ("산울타리형", "Die Hecke", "Alles hat seinen Platz – spontane Veränderungen müssen erst einmal wachsen.", "모든 것이 제자리에 있다. 갑작스러운 변화도 일단 자리를 잡아야 한다."),
    ("wood", "water"): ("숲속 시냇물형", "Der Waldbach", "Findet meist einen Weg – nur selten den direkten.", "대개 길을 찾지만 지름길인 적은 드물다."),
    ("fire", "wood"): ("장작불형", "Das Kaminfeuer", "Verbreitet Wärme und gute Laune – und merkt oft gar nicht, wie viele sich versammeln.", "온기와 좋은 분위기를 퍼뜨리지만, 얼마나 많은 사람이 모였는지 잘 모른다."),
    ("fire", "earth"): ("화산형", "Der Vulkan", "Lange ruhig – und überrascht dann alle, manchmal sogar sich selbst.", "오래 조용하다가 모두를 놀라게 한다. 가끔은 자기 자신까지."),
    ("fire", "metal"): ("용광로형", "Der Hochofen", "Bringt ordentlich Hitze ins Spiel – und braucht manchmal selbst eine Abkühlung.", "분위기를 뜨겁게 만들지만, 가끔 본인에게도 냉각 시간이 필요하다."),
    ("fire", "water"): ("온천형", "Die heiße Quelle", "Bringt Ruhe und Wärme zusammen – nur die eigene Temperatur schwankt manchmal.", "평온함과 따뜻함을 함께 주지만, 자기 온도는 가끔 오르내린다."),
    ("earth", "wood"): ("정원형", "Der Garten", "Hegt und pflegt – und freut sich über jedes neue Blatt manchmal ein bisschen zu sehr.", "가꾸고 돌보며, 새잎 하나에도 가끔 지나치게 기뻐한다."),
    ("earth", "fire"): ("도자기 가마형", "Der Brennofen", "Aus Geduld und Hitze entsteht etwas Besonderes – auch wenn nicht alles nach Plan läuft.", "인내와 열기에서 특별한 것이 탄생한다. 모든 과정이 계획대로 흘러가지는 않지만."),
    ("earth", "metal"): ("금광형", "Die Goldmine", "Wertvoll im Verborgenen – leider steht kein Wegweiser davor.", "숨은 곳에 가치가 있지만, 안내 표지판은 없다."),
    ("earth", "water"): ("제방형", "Der Deich", "Gibt Halt, wenn alles ins Fließen gerät – und merkt oft spät, wie viel er selbst trägt.", "모든 것이 흘러가려 할 때 버팀목이 되어 주지만, 자신이 얼마나 많은 것을 짊어졌는지는 늦게 깨닫는다."),
    ("metal", "wood"): ("목각사형", "Der Holzschnitzer", "Erkennt die Form schon im Holz – und schnitzt gern noch ein bisschen weiter.", "나무에서 이미 완성된 형태를 알아보고, 조금 더 다듬기를 즐긴다."),
    ("metal", "fire"): ("대장장이형", "Der Schmied", "Macht aus Hitze etwas Brauchbares – und redet dabei erstaunlich wenig.", "열기를 쓸모 있는 것으로 바꾸고, 그 사이 놀랄 만큼 말이 없다."),
    ("metal", "earth"): ("원석형", "Der Edelstein", "Ruhig und klar – und manchmal etwas zu gut darin, unbeeindruckt zu bleiben.", "고요하고 맑지만, 감동하지 않는 데 지나치게 능숙할 때가 있다."),
    ("metal", "water"): ("바위틈 샘물형", "Die Felsquelle", "Sprudelt leise und klar – und wird leicht überhört.", "조용하고 맑게 솟지만, 쉽게 지나쳐진다."),
    ("water", "wood"): ("우림형", "Der Regenwald", "Hier wächst oft etwas Neues – manchmal sogar mehr, als man überblicken kann.", "자주 새로운 것이 자라난다. 때로는 스스로도 다 파악하기 어려울 만큼."),
    ("water", "fire"): ("천둥번개형", "Das Gewitter", "Spannung liegt in der Luft – und wann es kracht, weiß niemand so genau.", "공기 중에 긴장감이 감돈다. 언제 번개가 칠지는 아무도 정확히 모른다."),
    ("water", "earth"): ("연못형", "Der Teich", "Hält still, spiegelt alles – und merkt sich mehr, als er zeigt.", "가만히 모든 걸 비추고, 보여 주는 것보다 많이 기억한다."),
    ("water", "metal"): ("이슬형", "Der Morgentau", "Leise und klar – schon da, bevor die anderen wach sind, und weg, sobald es laut wird.", "조용하고 맑다. 남들이 깨기 전에 와 있지만, 시끄러워지면 사라진다."),
}

# 없는 오행 꼬리표 (독일어, 한국어 뜻)
MISSING = {
    "wood": ("Holz erscheint in dieser vereinfachten Übersicht nicht.", "이 간단 보기에서는 나무가 보이지 않습니다."),
    "fire": ("Feuer erscheint in dieser vereinfachten Übersicht nicht.", "이 간단 보기에서는 불이 보이지 않습니다."),
    "earth": ("Erde erscheint in dieser vereinfachten Übersicht nicht.", "이 간단 보기에서는 흙이 보이지 않습니다."),
    "metal": ("Metall erscheint in dieser vereinfachten Übersicht nicht.", "이 간단 보기에서는 쇠가 보이지 않습니다."),
    "water": ("Wasser erscheint in dieser vereinfachten Übersicht nicht.", "이 간단 보기에서는 물이 보이지 않습니다."),
}

NOTE = ("Eine spielerische Vereinfachung der fünf Elemente anhand der sichtbaren Zeichen – keine vollständige Saju-Analyse und keine klassische Deutung. Nur zur Unterhaltung und Selbstreflexion.",
        "표면에 나타난 글자를 바탕으로 오행을 재미있게 단순화한 표현입니다. 완전한 사주 분석이나 전통적인 사주 해석이 아니며, 오락과 자기 성찰을 위한 것입니다.")

# 카드 부제(상대 표현: '강하다'가 아니라 '가장 많이 나타남')
SUBTITLE = {
    "single": "{a} steht im Vordergrund",
    "duo": "{a} am stärksten vertreten · {b} als zweites Element",
    "balanced": "Alle fünf Elemente sind sichtbar",
}


def classify(counts, day_key=None):
    """counts: {'wood': n, ...}. 반환: dict(kind, ko, de, line, missing=[keys])."""
    total = sum(counts.values()) or 1
    present = [k for k in ORDER if counts.get(k, 0) > 0]
    missing = [k for k in ORDER if counts.get(k, 0) == 0]
    # 동률: 일간 원소를 먼저, 그다음 상생 순서
    def rank(k):
        return (-counts.get(k, 0), 0 if k == day_key else 1, ORDER.index(k))
    ranked = sorted(ORDER, key=rank)
    top, second = ranked[0], ranked[1]
    if len(present) == 5 and counts[top] <= max(2, round(total * 0.4)):
        ko, de, line, _ = BALANCED
        return {"kind": "balanced", "ko": ko, "de": de, "line": line, "missing": []}
    if counts.get(second, 0) <= 1:
        ko, de, line, _ = SINGLE[top]
        return {"kind": "single", "key": top, "ko": ko, "de": de, "line": line, "missing": missing}
    ko, de, line, _ = DUO[(top, second)]
    return {"kind": "duo", "key": top, "key2": second, "ko": ko, "de": de, "line": line, "missing": missing}


# ───────── 다국어 텍스트 (3차 현지화: GPT 초안 + 충돌 3건 수정) ─────────
import json as _json
import os as _os

_I18N = {}
try:
    with open(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "typen_i18n.json"), encoding="utf-8") as _f:
        _I18N = _json.load(_f)
except Exception:  # 파일이 없어도 독일어로 동작
    _I18N = {}

EL_NAME = {
    "de": {"wood": "Holz", "fire": "Feuer", "earth": "Erde", "metal": "Metall", "water": "Wasser"},
    "fr": {"wood": "Bois", "fire": "Feu", "earth": "Terre", "metal": "Métal", "water": "Eau"},
    "es": {"wood": "Madera", "fire": "Fuego", "earth": "Tierra", "metal": "Metal", "water": "Agua"},
    "en": {"wood": "Wood", "fire": "Fire", "earth": "Earth", "metal": "Metal", "water": "Water"},
}
_SUB = {
    "de": {"single": "{a} steht im Vordergrund", "duo": "{a} am stärksten vertreten · {b} als zweites Element",
           "balanced": "Alle fünf Elemente sind sichtbar"},
    "en": {"single": "{a} is most represented", "duo": "A blend of {a} and {b}",
           "balanced": "All five elements are visible"},
    "fr": {"single": "L'élément {a} est le plus représenté", "duo": "Un mélange de {a} et de {b}",
           "balanced": "Les cinq éléments sont visibles"},
    "es": {"single": "El elemento {a} es el más presente", "duo": "Una combinación de {a} y {b}",
           "balanced": "Los cinco elementos son visibles"},
}
_MISS = {
    "de": "{x} erscheint in dieser vereinfachten Übersicht nicht.",
    "en": "{x} doesn't appear in this simplified overview.",
    "fr": "L'élément {x} n'apparaît pas dans cet aperçu simplifié.",
    "es": "El elemento {x} no aparece en esta versión simplificada.",
}
_NOTE = {
    "de": NOTE[0],
    "en": "A playful simplification of the five elements based on the visible characters – not a full Saju analysis or classical reading. For entertainment and self-reflection only.",
    "fr": "Une simplification ludique des cinq éléments à partir des caractères visibles – ni analyse Saju complète ni lecture classique. Pour le divertissement et la réflexion personnelle.",
    "es": "Una simplificación lúdica de los cinco elementos a partir de los caracteres visibles – ni un análisis Saju completo ni una lectura clásica. Solo para entretenimiento y reflexión personal.",
}


def card_texts(counts, day_key=None, lang="de"):
    """카드·결과 화면용 문구 묶음. 개인정보 없음(개수만 입력)."""
    r = classify(counts, day_key)
    lang = lang if lang in EL_NAME else "de"
    names = EL_NAME[lang]
    de_name = r["de"]
    name, line = de_name, r["line"]
    if lang != "de":
        loc = _I18N.get(lang, {}).get(de_name)
        if loc:
            name, line = loc[0], loc[1]
    sub = _SUB[lang]
    if r["kind"] == "balanced":
        subtitle = sub["balanced"]
    elif r["kind"] == "single":
        subtitle = sub["single"].format(a=names[r["key"]])
    else:
        subtitle = sub["duo"].format(a=names[r["key"]], b=names[r["key2"]])
    return {"kind": r["kind"], "ko": r["ko"], "de_name": de_name, "name": name, "line": line,
            "subtitle": subtitle,
            "missing": [_MISS[lang].format(x=names[k]) for k in r["missing"]],
            "note": _NOTE[lang]}


def illustration_no(de_name):
    """일러스트 파일 번호(1~26). 순서 = SINGLE(5) + BALANCED(1) + DUO(20)."""
    names = [v[1] for v in SINGLE.values()] + [BALANCED[1]] + [v[1] for v in DUO.values()]
    return names.index(de_name) + 1
