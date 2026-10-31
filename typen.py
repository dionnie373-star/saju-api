"""오행 분포 유형(간단 버전). 개수(counts)만으로 유형을 정한다 — 전통 사주 해석이 아니라 대중용 맛보기다.
문구 원칙: 자연/장인 이미지, 장점 하나 + 귀여운 약점 하나, 좋다/나쁘다 판단 없음, '경향'으로 표현.
"""

ORDER = ["wood", "fire", "earth", "metal", "water"]
# 상생 순서(목→화→토→금→수→목)와 같다. 동률일 때 이 순서로 앞선 쪽을 주(主)로 본다.

# (한글 별명, 독일어 이름, 독일어 한 줄, 한국어 뜻)
SINGLE = {
    "wood": ("원시림형", "Der Urwald", "Wächst in alle Richtungen – und hat schon das nächste Projekt im Kopf.", "사방으로 동시에 자라고, 벌써 다음 프로젝트를 구상 중."),
    "fire": ("태양형", "Die Sonne", "Wärmt jeden Raum auf – braucht danach dringend Abstand zum eigenen Glanz.", "방을 따뜻하게 만들지만, 자기 빛에서 잠시 떨어질 시간이 필요."),
    "earth": ("산형", "Der Berg", "Verlässlich bis in die Wurzeln – bewegt sich nur, wenn er will.", "뿌리까지 믿음직하지만, 움직이는 건 본인이 원할 때만."),
    "metal": ("수정형", "Der Kristall", "Glasklar im Denken – und manchmal scharfkantig im Ton.", "생각은 투명하지만 말투는 가끔 날카롭다."),
    "water": ("심해형", "Die Tiefsee", "Wirkt ruhig, denkt gerade vierzehn Dinge gleichzeitig.", "고요해 보이지만 속으로는 열네 가지를 동시에 생각 중."),
}

BALANCED = ("오케스트라형", "Das Orchester", "Alle fünf Elemente sind da – die Frage ist nur, wer dirigiert.", "다섯 오행이 다 있다. 문제는 누가 지휘하느냐뿐.")

# (주, 부) → (한글 별명, 독일어 이름, 독일어 한 줄, 한국어 뜻)
DUO = {
    ("wood", "fire"): ("불씨형", "Der Funkenflug", "Aus einer Idee werden zehn – und plötzlich ist überall Bewegung.", "아이디어 하나가 열 개가 되고, 어느새 모든 곳이 분주해진다."),
    ("wood", "earth"): ("포도밭형", "Der Weinberg", "Lässt sich Zeit und wächst mit Geduld – guter Wein entsteht schließlich nicht über Nacht.", "서두르지 않고 인내하며 자란다. 좋은 와인은 하루아침에 만들어지지 않으니까."),
    ("wood", "metal"): ("산울타리형", "Die Hecke", "Alles hat seinen Platz – nur spontane Veränderungen brauchen etwas Überzeugungsarbeit.", "모든 것이 제자리에 있지만, 갑작스러운 변화에는 설득이 조금 필요하다."),
    ("wood", "water"): ("숲속 시냇물형", "Der Waldbach", "Findet immer einen Weg – nur selten den direkten.", "늘 길을 찾지만 지름길인 적은 드물다."),
    ("fire", "wood"): ("장작불형", "Das Kaminfeuer", "Gemütlich und ausdauernd – zieht Menschen an wie Mücken das Licht.", "아늑하고 오래 타서 사람들이 자연스럽게 모여든다."),
    ("fire", "earth"): ("화산형", "Der Vulkan", "Lange unauffällig – bis plötzlich alle merken, wie viel Energie darin steckt.", "오랫동안 조용하다가, 어느 순간 모두가 그 안의 에너지를 알아차린다."),
    ("fire", "metal"): ("용광로형", "Der Hochofen", "Enormer Antrieb – wenn er einmal brennt, wärmt es auch ihn selbst.", "엄청난 추진력. 한 번 타오르면 자기도 데워진다."),
    ("fire", "water"): ("온천형", "Die Therme", "Heiß und beruhigend zugleich – niemand weiß, welche Seite gerade dran ist.", "뜨겁고 편안한 면이 공존해서, 지금 어느 쪽인지 아무도 모른다."),
    ("earth", "wood"): ("정원형", "Der Garten", "Hegt und pflegt – und freut sich still über jedes neue Blatt.", "가꾸고 돌보며, 새잎 하나에도 조용히 기뻐한다."),
    ("earth", "fire"): ("도자기 가마형", "Der Brennofen", "Aus Geduld und Hitze entsteht etwas Besonderes – auch wenn der Weg dorthin nicht immer planbar ist.", "인내와 열기에서 특별한 것이 탄생한다. 그 과정이 항상 계획대로 되지는 않지만."),
    ("earth", "metal"): ("금광형", "Die Goldmine", "Wertvoll im Verborgenen – man muss nur tief genug graben.", "숨은 곳에 가치가 있어서, 충분히 깊이 파야 보인다."),
    ("earth", "water"): ("제방형", "Der Deich", "Gibt Halt, wenn alles ins Fließen gerät – und merkt oft erst spät, wie viel er selbst trägt.", "모든 것이 흘러가려 할 때 버팀목이 되어 주지만, 자신이 얼마나 많은 것을 짊어졌는지는 늦게 깨닫는다."),
    ("metal", "wood"): ("목각사형", "Der Holzschnitzer", "Sieht in jedem Rohling schon die fertige Form – und kann nicht aufhören zu feilen.", "원석마다 완성된 모양이 보이고, 다듬기를 멈추지 못한다."),
    ("metal", "fire"): ("대장장이형", "Der Schmied", "Macht aus Hitze etwas Brauchbares – und redet dabei erstaunlich wenig.", "열기를 쓸모 있는 것으로 바꾸고, 그 사이 놀랄 만큼 말이 없다."),
    ("metal", "earth"): ("원석형", "Der Edelstein", "Ruhig, klar und sehr schwer zu beeindrucken.", "고요하고 맑고, 감동시키기 아주 어렵다."),
    ("metal", "water"): ("바위틈 샘물형", "Die Felsquelle", "Klar bis auf den Grund – und tritt erst hervor, wenn man genau hinhört.", "바닥까지 맑고, 귀 기울여야 모습을 드러낸다."),
    ("water", "wood"): ("우림형", "Der Regenwald", "Hier wächst immer etwas Neues – manchmal sogar mehr, als man überblicken kann.", "언제나 새로운 것이 자라난다. 때로는 스스로도 다 파악하기 어려울 만큼."),
    ("water", "fire"): ("천둥번개형", "Das Gewitter", "Spannung in der Luft – es entlädt sich immer genau dann, wenn es nötig ist.", "공기 중의 긴장이 꼭 필요한 순간에 터진다."),
    ("water", "earth"): ("연못형", "Der Teich", "Hält still, spiegelt alles – und merkt sich mehr, als er zeigt.", "가만히 모든 걸 비추고, 보여 주는 것보다 많이 기억한다."),
    ("water", "metal"): ("이슬형", "Der Morgentau", "Leise, klar und früh da – bevor die anderen überhaupt wach sind.", "조용하고 맑고, 남들이 일어나기 전에 이미 와 있다."),
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
