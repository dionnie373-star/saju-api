"""오행 분포 유형(간단 버전). 개수(counts)만으로 유형을 정한다 — 전통 사주 해석이 아니라 대중용 맛보기다.
문구 원칙: 자연/장인 이미지, 장점 하나 + 귀여운 약점 하나, 좋다/나쁘다 판단 없음, '경향'으로 표현.
"""

ORDER = ["wood", "fire", "earth", "metal", "water"]
# 상생 순서(목→화→토→금→수→목)와 같다. 동률일 때 이 순서로 앞선 쪽을 주(主)로 본다.

# (한글 별명, 독일어 이름, 독일어 한 줄, 한국어 뜻)
SINGLE = {
    "wood": ("원시림형", "Der Urwald", "Wächst in alle Richtungen gleichzeitig – und plant schon das nächste Projekt.", "사방으로 동시에 자라고, 벌써 다음 프로젝트를 구상 중."),
    "fire": ("태양형", "Die Sonne", "Wärmt jeden Raum auf – braucht danach dringend Abstand zum eigenen Glanz.", "방을 따뜻하게 만들지만, 자기 빛에서 잠시 떨어질 시간이 필요."),
    "earth": ("산형", "Der Berg", "Verlässlich bis in die Wurzeln – bewegt sich nur, wenn er will.", "뿌리까지 믿음직하지만, 움직이는 건 본인이 원할 때만."),
    "metal": ("수정형", "Der Kristall", "Glasklar im Denken – und manchmal scharfkantig im Ton.", "생각은 투명하지만 말투는 가끔 날카롭다."),
    "water": ("심해형", "Die Tiefsee", "Wirkt ruhig, denkt gerade vierzehn Dinge gleichzeitig.", "고요해 보이지만 속으로는 열네 가지를 동시에 생각 중."),
}

BALANCED = ("오케스트라형", "Das Orchester", "Alle fünf Elemente sind da – die Frage ist nur, wer dirigiert.", "다섯 오행이 다 있다. 문제는 누가 지휘하느냐뿐.")

# (주, 부) → (한글 별명, 독일어 이름, 독일어 한 줄, 한국어 뜻)
DUO = {
    ("wood", "fire"): ("불씨형", "Der Funkenflug", "Eine Idee, und schon brennt der ganze Wald – Löschen nicht vorgesehen.", "아이디어 하나에 숲 전체가 타오른다. 끄는 건 계획에 없음."),
    ("wood", "earth"): ("포도밭형", "Der Weinberg", "Geduldig verwurzelt – gute Dinge brauchen bei ihm einfach Zeit.", "참을성 있게 뿌리내림. 좋은 건 시간이 걸린다고 믿는다."),
    ("wood", "metal"): ("분재형", "Der Bonsai", "Wächst nach Plan, geschnitten und gepflegt – und lässt sich ungern umtopfen.", "계획대로 다듬어져 자라며, 화분 옮기는 건 싫어한다."),
    ("wood", "water"): ("숲속 시냇물형", "Der Waldbach", "Findet immer einen Weg – nur selten den direkten.", "늘 길을 찾지만 지름길인 적은 드물다."),
    ("fire", "wood"): ("장작불형", "Das Kaminfeuer", "Gemütlich und ausdauernd – zieht Menschen an wie Mücken das Licht.", "아늑하고 오래 타서 사람들이 자연스럽게 모여든다."),
    ("fire", "earth"): ("화산형", "Der Vulkan", "Lange ruhig, dann ein Auftritt, den alle noch Jahre später erzählen.", "오래 조용하다가, 몇 년씩 회자될 등장을 한다."),
    ("fire", "metal"): ("용광로형", "Der Hochofen", "Enormer Antrieb – wenn er einmal brennt, wärmt es auch ihn selbst.", "엄청난 추진력. 한 번 타오르면 자기도 데워진다."),
    ("fire", "water"): ("온천형", "Die Therme", "Heiß und beruhigend zugleich – niemand weiß, welche Seite gerade dran ist.", "뜨겁고 편안한 면이 공존해서, 지금 어느 쪽인지 아무도 모른다."),
    ("earth", "wood"): ("정원형", "Der Garten", "Hegt und pflegt – und freut sich still über jedes neue Blatt.", "가꾸고 돌보며, 새잎 하나에도 조용히 기뻐한다."),
    ("earth", "fire"): ("도자기 가마형", "Der Brennofen", "Formt Dinge mit Hitze und Geduld – das Ergebnis überrascht auch ihn.", "열과 인내로 무언가를 빚는다. 결과는 본인도 놀란다."),
    ("earth", "metal"): ("금광형", "Die Goldmine", "Wertvoll im Verborgenen – man muss nur tief genug graben.", "숨은 곳에 가치가 있어서, 충분히 깊이 파야 보인다."),
    ("earth", "water"): ("제방형", "Der Deich", "Hält zusammen, was auseinanderfließen will – und bekommt selten Dank dafür.", "흩어지려는 걸 붙잡아 주지만 고맙다는 말은 드물게 듣는다."),
    ("metal", "wood"): ("목각사형", "Der Holzschnitzer", "Sieht in jedem Rohling schon die fertige Form – und kann nicht aufhören zu feilen.", "원석마다 완성된 모양이 보이고, 다듬기를 멈추지 못한다."),
    ("metal", "fire"): ("대장장이형", "Der Schmied", "Macht aus Hitze etwas Brauchbares – und redet dabei erstaunlich wenig.", "열기를 쓸모 있는 것으로 바꾸고, 그 사이 놀랄 만큼 말이 없다."),
    ("metal", "earth"): ("원석형", "Der Edelstein", "Ruhig, klar und sehr schwer zu beeindrucken.", "고요하고 맑고, 감동시키기 아주 어렵다."),
    ("metal", "water"): ("바위틈 샘물형", "Die Felsquelle", "Klar bis auf den Grund – und tritt erst hervor, wenn man genau hinhört.", "바닥까지 맑고, 귀 기울여야 모습을 드러낸다."),
    ("water", "wood"): ("우림형", "Der Regenwald", "Fantasie im Dauerregen – irgendwas blüht immer.", "상상력이 계속 쏟아져서 늘 무언가 피어난다."),
    ("water", "fire"): ("천둥번개형", "Das Gewitter", "Spannung in der Luft – es entlädt sich immer genau dann, wenn es nötig ist.", "공기 중의 긴장이 꼭 필요한 순간에 터진다."),
    ("water", "earth"): ("연못형", "Der Teich", "Hält still, spiegelt alles – und merkt sich mehr, als er zeigt.", "가만히 모든 걸 비추고, 보여 주는 것보다 많이 기억한다."),
    ("water", "metal"): ("이슬형", "Der Morgentau", "Leise, klar und früh da – bevor die anderen überhaupt wach sind.", "조용하고 맑고, 남들이 일어나기 전에 이미 와 있다."),
}

# 없는 오행 꼬리표 (독일어, 한국어 뜻)
MISSING = {
    "wood": ("Ohne Holz: Ideen sind da, das Wachsenlassen übst du noch.", "나무 없음: 아이디어는 있고, 키워 가는 건 연습 중."),
    "fire": ("Ohne Feuer: Du glühst leise – von außen sieht man es nicht sofort.", "불 없음: 조용히 타올라서 겉으로는 바로 안 보인다."),
    "earth": ("Ohne Erde: Du schwebst gern – Boden unter den Füßen ist Übungssache.", "흙 없음: 떠다니기를 좋아해서, 땅을 딛는 건 연습 중."),
    "metal": ("Ohne Metall: Du lässt vieles offen – Entscheidungen brauchen ein bisschen länger.", "쇠 없음: 많은 걸 열어 두어 결정이 조금 오래 걸린다."),
    "water": ("Ohne Wasser: Du gehst direkt – Pausen sind kein Reflex.", "물 없음: 곧장 가는 편이라 쉬는 건 반사적으로 안 나온다."),
}

NOTE = ("Vereinfachte Darstellung für Unterhaltung und Selbstreflexion – keine Deutung nach der klassischen Saju-Lehre.",
        "전통 사주 해석이 아니라 오락과 자기 성찰용으로 단순화한 표현입니다.")


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
