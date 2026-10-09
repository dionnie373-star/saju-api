"""언어별(독일어 de / 프랑스어 fr) 리포트 설정.

report_pipeline이 lang 값("de"|"fr")에 따라 가져다 쓰는 순수 데이터 모듈이다.
독일어(de)는 기존 report_pipeline의 상수/템플릿을 그대로 쓰고(회귀 방지),
여기에는 "프랑스어" 설정만 둔다.

프랑스어 프롬프트는 독일어 프롬프트 JSON 4개를 통째로 복제하지 않고,
기존 프롬프트(한국어 지시문)를 그대로 불러와 맨 앞에 "언어 전환 지시" 블록을
붙이는 방식으로 만든다 — 사주 계산 규칙/구조/검증 규칙은 언어와 무관하게
동일하고, 바뀌는 건 출력 언어·호칭·오행 이름·금지어·면책 문구뿐이기 때문이다.
(프롬프트 규칙을 고칠 때 두 벌을 따로 고칠 필요가 없다.)
"""

import re

SUPPORTED_LANGS = ("de", "fr")


def normalize_lang(value):
    value = (value or "").strip().lower()
    return value if value in SUPPORTED_LANGS else "de"


# ---------------------------------------------------------------------------
# 프롬프트 언어 전환 블록 (한국어 지시문 — 모델이 읽는 용도)
# ---------------------------------------------------------------------------

_FR_PROMPT_OVERRIDE = """\
[언어 전환 지시 — 최우선. 아래 본문의 "독일어" 관련 모든 문구보다 이 블록이 우선합니다]
이 리포트는 독일어가 아니라 **프랑스어**로 작성합니다. 아래 본문에 나오는 "독일어", 독일어 예시 문장/소제목/용어는 전부 같은 의도의 프랑스어로 바꿔서 적용하세요.
- 출력 언어: 프랑스어 원어민 카피라이터 수준의 자연스러운 문장. 영어/한국어 직역투 금지. 존재하지 않는 신조어, 어색한 관청체, 이중부정 금지(이 원칙은 독일어 때와 동일).
- 호칭: 반드시 "vous"(존댓말)로 서술하세요. "tu/toi/ton/ta/tes"는 절대 쓰지 마세요. 본문의 "du" 규칙은 "vous" 규칙으로 읽으세요. 궁합 리포트에서 두 사람을 함께 가리킬 때도 "vous deux"/"vous" 로 쓰세요.
- 오행 이름은 반드시 이 다섯 단어만: "Bois"(목), "Feu"(화), "Terre"(토), "Métal"(금), "Eau"(수). 금(金)을 "Or"라고 쓰지 마세요. (본문의 Holz/Feuer/Erde/Metall/Wasser/Gold 규칙을 이 단어들로 읽으세요.)
- 한국 전통 표기: 기본은 "coréenne"(예: "tradition coréenne du Saju"). "chinoise"로 한정하지 마세요. 역사적 정확성이 필요할 때만 "d'Asie de l'Est"를 보조로 쓰세요. "BaZi" 대신 "Saju"(예: "rapport annuel Saju")를 기본으로 쓰세요.
- 금지 단어(본문의 Schicksal 등 독일어 금지어 대신 이것을 적용): "destin"(및 destinée/destinées — 부정문 "ce n'est pas le destin"에서도 쓰지 말고 "parcours de vie", "année", "période"로 대체), "fatalité", "empirique", "scientifique", "scientifiquement", "des études montrent", "significatif/significative"(통계적 의미), "validé/validée"(과학적 검증 암시).
- 독일어에만 해당하는 문법/연어 규칙(Leistungen erbracht, Bedarf nach/an, kein/nicht ein 등)은 프랑스어에 적용되지 않으므로 무시하세요. 대신 프랑스어에서 어색한 직역·영어식 표현(예: "faire sens", "adresser un problème")을 피하세요.
- 성별 일치: 독자의 성별을 모르므로 "heureux/heureuse", "prêt/prête"처럼 성별에 따라 형태가 달라지는 표현으로 독자를 직접 묘사하지 마세요(성별 중립 표현으로 우회). 궁합 리포트에서 성별 정보가 "keine Angabe"이면 이름을 반복해 쓰세요.
- 월 이름은 프랑스어로("Janvier", "Février", "Mars", "Avril", "Mai", "Juin", "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"). 챕터 소제목은 예를 들어 "Janvier — Des ressources qui souhaitent se montrer"처럼 그 달 축에 맞게 프랑스어로 쓰세요.
- 본문의 독일어 예시 소제목은 다음 프랑스어로 대응하세요: "Dein Jahr auf einen Blick" → "Votre année en un coup d'œil"; "Monate, in denen vieles leichter fließen kann" → "Les mois où les choses peuvent couler plus facilement"; "Monate für mehr Achtsamkeit" → "Les mois pour davantage d'attention".
- 상품명: Jahresreport → "rapport annuel", Lebenskarte → "carte de vie", Kompatibilitäts-Check → "test de compatibilité". 프리미엄 소개 문장("인생 전체의 더 긴 흐름이 궁금하다면")도 프랑스어로, 구간 개수는 "8 périodes de vie de dix ans"라고 쓰세요.
- 무료 리포트의 유료 리포트 구매 유도 블록은 다음 프랑스어 구조로 쓰세요(독일어 예시 블록 대신): 제목 "### Votre rapport annuel Saju 2027 — 9,90 €", 그다음 "Ce qui vous attend :" 아래 불릿 5개(Votre axe personnel pour 2027 / 12 chapitres mensuels avec des impulsions Saju personnalisées / Des questions de réflexion sur l'amour, le travail et le développement personnel / Vos forces personnelles et d'éventuelles tensions intérieures / Une boussole annuelle avec des questions concrètes pour vos propres décisions), 마무리 문장 "Un rapport de réflexion personnel fondé sur la tradition Saju — ni diagnostic scientifique de la personnalité, ni prédiction certaine de l'avenir."
- 마지막 면책 문구는 프랑스어로: "Ce contenu est proposé à des fins de divertissement et de réflexion personnelle ; il ne remplace pas un avis médical ou psychologique."
- 분량 기준(단어 수)은 프랑스어 단어 기준으로 동일하게 적용합니다(프랑스어는 독일어보다 단어 수가 많아지는 경향이 있으니 기준 미달이 되지 않도록 하세요).
- 출력은 순수 프랑스어 텍스트만. 한글/한자/독일어 단어(예: "Holz", "Feuer", "Du", "dein")가 섞이지 않게 하세요.

--- 아래부터 원래 지시문 ---
"""


_FR_PROMPT_CLOSING = """

[최종 확인 — 가장 중요, 출력 직전에 반드시 지킬 것]
위 지시문에는 독일어 예시가 많지만, 실제 출력은 **처음부터 끝까지 프랑스어**여야 합니다. 제목·소제목·본문·불릿·면책 문구 전부 프랑스어이고, 호칭은 "vous", 오행은 Bois/Feu/Terre/Métal/Eau 입니다. 독일어 단어(und, der, die, das, ist, nicht, dein, Jahr, Energie 등)가 하나라도 섞이면 안 됩니다. 순수 프랑스어 텍스트만 출력하세요.
"""


def localize_prompt_text(text, lang, *, is_first_message=True, is_last_message=True):
    """프롬프트 메시지 본문을 lang에 맞게 변환한다. de는 그대로.

    fr: "독일어"라는 지시어를 "프랑스어"로 치환하고(출력 언어 지시가 본문 끝의
    "순수 독일어 텍스트만 출력하세요"에도 있어서, 앞쪽 override만으로는 모델이
    독일어로 출력하는 것이 실측으로 확인됨), 첫 메시지 앞에 override, 마지막
    메시지 끝에 최종 확인 블록을 붙인다.
    """
    if lang != "fr":
        return text
    text = text.replace("독일어", "프랑스어")
    if is_first_message:
        text = _FR_PROMPT_OVERRIDE + text
    if is_last_message:
        text = text + _FR_PROMPT_CLOSING
    return text


# ---------------------------------------------------------------------------
# 기계적 검사 규칙
# ---------------------------------------------------------------------------

# 프랑스어: 정규식 기반(대소문자 무시). "destination" 같은 단어를 잘못 잡지
# 않도록 단어 경계와 활용형만 명시한다.
FR_DESTIN_RE = re.compile(r"\bdestin(?:s|ée|ées)?\b|\bfatalité\b", re.IGNORECASE)
FR_BANNED_REGEXES = [
    (FR_DESTIN_RE, "destin/destinée/fatalité"),
    (re.compile(r"\bempiri(?:que|ques|quement)\b", re.IGNORECASE), "empirique"),
    (re.compile(r"\bscientifi(?:que|ques|quement)\b", re.IGNORECASE), "scientifique"),
    (re.compile(r"\bdes études (?:montrent|prouvent|démontrent)\b", re.IGNORECASE), "des études montrent"),
    (re.compile(r"\bstatistiquement significatif", re.IGNORECASE), "statistiquement significatif"),
    (re.compile(r"\bvalidé(?:e|s|es)?\b", re.IGNORECASE), "validé"),
    (re.compile(r"\b(?:révèl(?:e|ent|era|erait)|prouv(?:e|ent)|garantit|garantissent)\b", re.IGNORECASE), "révèle/prouve/garantit"),
    (re.compile(r"\bopportunité rare\b|\blongueur exceptionnelle\b|\bmoment idéal\b|\bdernière chance\b|\bmoment décisif\b|\bpour la première fois\b|\bcœur battant\b", re.IGNORECASE), "표현 금지(희소성/긴박감/범위 밖 단정)"),
    (re.compile(r"\b(?:feu|terre|bois|métal|eau)\s+en\s+(?:ciel|terre)\b", re.IGNORECASE), "천간/지지 직역('Feu en ciel' 등)"),
    # 독자(vous)를 성별 변화 분사/형용사로 묘사: "vous êtes aligné", "vous pourriez être sollicité"
    (re.compile(
        r"\bvous\b[^.!?\n]{0,40}?\b(?:êtes|serez|seriez|étiez|être)\s+(?:(?:plus|moins|très|souvent|parfois|davantage|également|aussi|bien)\s+)?[\wàâçéèêëîïôûùüÿœ]+(?:é|ée|és|ées)\b",
        re.IGNORECASE), "독자(vous)를 성별 일치 분사로 묘사('vous êtes aligné' 등)"),
]
# "vous"로 쓰기로 했으므로 비격식(tu 계열)이 나오면 걸러낸다.
FR_INFORMAL_RE = re.compile(r"\b(?:tu|toi|tes|ta)\b", re.IGNORECASE)
# 금(金) = Métal. "Or"(금속 이름) 사용 금지 — 문장 첫머리 접속사 "Or,"는 허용해야
# 하므로 "élément Or"/"l'Or" 같은 명백한 경우만 잡는다.
FR_WRONG_ELEMENT_RE = re.compile(r"\b[ée]l[ée]ment\s+Or\b|\bl['’]Or\b")
# 영어 단어 혼입("s'est deepened" 등) — 프랑스어에 없는 영어 기능어/흔한 동사형을 잡는다.
FR_ENGLISH_LEAK_RE = re.compile(
    r"\b(?:deepened|deepen|growing|moving|feeling|balance[ds]?|the|with|your|and|because|which|while|between|energy|flow|"
    r"journey|focus(?:ed)?|mindful|insight|gentle|healing)\b",
    re.IGNORECASE,
)
# 독일어 흔적(프롬프트의 독일어 용어가 새어 나온 경우)
FR_GERMAN_LEAK_RE = re.compile(r"\b(?:Holz|Feuer|Erde|Metall|Wasser|Dein|Deine|Jahresreport)\b")


# 프롬프트 지시문이 독일어 예시투성이라서 모델이 통째로 독일어로 출력하는 사고가
# 실제로 있었다(2026-10-09 프랑스어 파일럿 테스트). 독일어 기능어(프랑스어에는
# 없는 단어)가 3개 이상 나오면 "독일어로 출력됨"으로 보고 재생성시킨다.
FR_GERMAN_STOPWORDS_RE = re.compile(r"\b(?:und|der|die|das|nicht|dein|deine|deinen|ein|eine|mit|auch|wird|ist)\b")


def fr_mechanical_issues(report_text):
    issues = []
    german_hits = FR_GERMAN_STOPWORDS_RE.findall(report_text)
    if len(german_hits) >= 3:
        issues.append(
            f"리포트가 프랑스어가 아니라 독일어로 작성됨(독일어 단어 {len(german_hits)}개 감지) — "
            f"전체를 순수 프랑스어로 다시 작성해야 함"
        )
    for rx, label in FR_BANNED_REGEXES:
        if rx.search(report_text):
            issues.append(f"금지 단어 '{label}' 포함됨")
    if FR_WRONG_ELEMENT_RE.search(report_text):
        issues.append("'Or'라는 단어로 금(金)을 표현함 - 반드시 'Métal'로 써야 함")
    informal = FR_INFORMAL_RE.findall(report_text)
    if informal:
        issues.append(
            f"비격식 호칭(tu/toi/ta/tes) {len(informal)}회 사용됨 - 프랑스어 리포트는 "
            f"반드시 'vous/votre/vos' 존댓말만 써야 함"
        )
    eng = {m.lower() for m in FR_ENGLISH_LEAK_RE.findall(report_text)}
    # "balance"/"focus"/"insight"는 프랑스어에도 쓰이는 차용어이므로 단독으로는 제외
    eng -= {"balance", "balances", "focus", "insight", "gentle"}
    if eng:
        issues.append(f"영어 단어가 섞여 있음: {', '.join(sorted(eng))} — 전부 프랑스어로 바꿔야 함")
    if FR_GERMAN_LEAK_RE.search(report_text):
        issues.append("독일어 단어(Holz/Feuer/Erde/Metall/Wasser/Dein 등)가 섞여 있음 - 전부 프랑스어로 바꿔야 함")
    return issues


# ---------------------------------------------------------------------------
# PDF / 이메일 문구
# ---------------------------------------------------------------------------

FR_STRINGS = {
    "toc_heading": "Sommaire",
    "you_are_here": "VOUS ÊTES ICI",
    "lifemap_heading": "Votre carte de vie en un coup d'œil",
    "axis_labels": {
        "재물운": "Ressources",
        "관계운": "Relations",
        "직업운": "Talents & œuvre",
        "총운": "Stabilité",
    },
    "free": {
        "pdf_title": "Votre profil Saju",
        "subtitle_named": "Établi pour {name}",
        "subtitle_anon": "Votre profil personnel des cinq éléments",
        "filename": "Palja-Profil.pdf",
        "subject": "Votre profil Saju gratuit est prêt ✨",
        "intro": (
            "votre profil personnel des cinq éléments, selon la tradition coréenne du Saju, "
            "est prêt — vous le trouverez en pièce jointe de cet e-mail au format PDF."
        ),
    },
    "paid": {
        "pdf_title": "Votre rapport annuel Saju",
        "subtitle_named": "Établi pour {name}",
        "subtitle_anon": "Votre rapport annuel personnel",
        "filename": "Palja-Rapport-annuel.pdf",
        "subject": "Votre rapport annuel Palja est prêt 📖",
        "intro": (
            "merci pour votre achat. Votre rapport annuel personnel, selon la tradition coréenne "
            "du Saju — avec les 12 mois en détail — est joint à cet e-mail au format PDF."
        ),
    },
    "premium": {
        "pdf_title": "Votre carte de vie Saju",
        "subtitle_named": "Établi pour {name}",
        "subtitle_anon": "Votre carte de vie personnelle",
        "filename": "Palja-Carte-de-vie.pdf",
        "subject": "Votre carte de vie Palja est prête 🧭",
        "intro": (
            "merci pour votre achat. Votre carte de vie personnelle, selon la tradition coréenne "
            "du Saju — avec vos périodes de vie de dix ans — est jointe à cet e-mail au format PDF."
        ),
    },
    "compatibility": {
        "pdf_title": "Votre compatibilité Saju",
        "filename": "Palja-Compatibilite.pdf",
        "subject": "Votre compatibilité Saju est prête 💫",
        "intro": "merci pour votre achat. Votre analyse de compatibilité Saju est jointe à cet e-mail au format PDF.",
    },
    "hello": "Bonjour{name_suffix},",
    "disclaimer": (
        "Palja est proposé à des fins de divertissement et de réflexion personnelle ; "
        "il ne remplace pas un avis médical ou psychologique."
    ),
    "withdrawal_confirmation": (
        "Confirmation : vous avez expressément demandé que nous commencions l'exécution du contrat avant "
        "l'expiration du délai de rétractation et reconnu que vous perdez votre droit de rétractation dès "
        "que ce rapport a été fourni. Notre garantie volontaire de 60 jours reste inchangée."
    ),
    "promo": "Envie de savoir à quel point vous vous accordez avec quelqu'un d'autre ?",
    "promo_link": "→ Test de compatibilité Saju (4,90 €)",
    "footer_questions": "Une question ? Écrivez-nous à",
    "footer_links": [
        ("fr/mentions-legales", "Mentions légales"),
        ("fr/confidentialite", "Confidentialité"),
        ("fr/retractation", "Rétractation"),
    ],
    "geo_notice": (
        "Remarque : nous n'avons pas pu identifier avec certitude le lieu de naissance {cities}. "
        "Pour le calcul, nous avons utilisé approximativement les coordonnées de Paris. "
        "Dans de rares cas, cela peut légèrement influencer l'heure retenue. "
        "Pour toute question, écrivez-nous à dionnie373@gmail.com."
    ),
}
