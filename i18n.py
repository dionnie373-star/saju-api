"""언어별(독일어 de / 프랑스어 fr / 스페인어 es / 영어 en) 리포트 설정.

report_pipeline이 lang 값("de"|"fr"|"es"|"en")에 따라 가져다 쓰는 순수 데이터 모듈이다.
독일어(de)는 기존 report_pipeline의 상수/템플릿을 그대로 쓰고(회귀 방지),
여기에는 "프랑스어" 설정만 둔다.

프랑스어 프롬프트는 독일어 프롬프트 JSON 4개를 통째로 복제하지 않고,
기존 프롬프트(한국어 지시문)를 그대로 불러와 맨 앞에 "언어 전환 지시" 블록을
붙이는 방식으로 만든다 — 사주 계산 규칙/구조/검증 규칙은 언어와 무관하게
동일하고, 바뀌는 건 출력 언어·호칭·오행 이름·금지어·면책 문구뿐이기 때문이다.
(프롬프트 규칙을 고칠 때 두 벌을 따로 고칠 필요가 없다.)
"""

import re

SUPPORTED_LANGS = ("de", "fr", "es", "en")


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

    fr/es: "독일어"라는 지시어를 해당 언어명으로 치환하고(출력 언어 지시가 본문 끝의
    "순수 독일어 텍스트만 출력하세요"에도 있어서, 앞쪽 override만으로는 모델이
    독일어로 출력하는 것이 실측으로 확인됨), 첫 메시지 앞에 override, 마지막
    메시지 끝에 최종 확인 블록을 붙인다.
    """
    blocks = PROMPT_BLOCKS.get(lang)
    if not blocks:
        return text
    override, closing, lang_name_ko = blocks
    text = text.replace("독일어", lang_name_ko)
    if is_first_message:
        text = override + text
    if is_last_message:
        text = text + closing
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


# 면책 문구의 "부정형" 사용은 허용한다: "…et non un diagnostic de personnalité scientifiquement
# établi"는 과학적 근거를 '암시'하는 게 아니라 정반대로 선을 긋는 문장이다(2026-10-11 실제
# 궁합 주문에서 모델이 이 문장을 매번 써서 재생성 2회가 다 실패하고 경고만 남았음).
FR_NEGATED_SCIENCE_RE = re.compile(
    r"\b(?:non|pas|ni|sans)\b[^.!?\n]{0,80}?\bscientifi(?:quement\s+établi(?:e|s|es)?|que|ques)\b", re.IGNORECASE)


def fr_mechanical_issues(report_text):
    issues = []
    report_text = FR_NEGATED_SCIENCE_RE.sub(" ", report_text)
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
        "Vous disposez de 60 jours : notre garantie volontaire « satisfait ou remboursé » s\'applique à cet achat. "
        "Écrivez-nous simplement si le rapport ne vous convient pas."
    ),
    "promo": "Envie de savoir à quel point vous vous accordez avec quelqu'un d'autre ?",
    "promo_link": "→ Test de compatibilité Saju (9,90 €)",
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


# ===========================================================================
# 스페인어(es) — 2026-10-11 사전 준비(es-prep 브랜치). 공개 전 원어민/법률 검토 필수.
# 설계 결정(사용자 확인 필요):
#  - 호칭은 독일어(du)와 같은 결의 비격식 "tú". 복수 2인칭(vosotros/ustedes)과 voseo는
#    스페인/중남미 어느 쪽으로도 치우치지 않도록 쓰지 않는다("español neutro").
#  - 오행: Madera / Fuego / Tierra / Metal / Agua.
# ===========================================================================

_ES_PROMPT_OVERRIDE = """\
[언어 전환 지시 — 최우선. 아래 본문의 "독일어" 관련 모든 문구보다 이 블록이 우선합니다]
이 리포트는 독일어가 아니라 **스페인어**로 작성합니다. 아래 본문에 나오는 "독일어", 독일어 예시 문장/소제목/용어는 전부 같은 의도의 스페인어로 바꿔서 적용하세요.
- 출력 언어: 스페인어 원어민 카피라이터 수준의 자연스러운 "중립 스페인어(español neutro)". 스페인 전용 또는 특정 중남미 국가 전용 속어/어휘는 피하세요. 영어/한국어 직역투, 존재하지 않는 신조어, 어색한 관청체, 이중부정 금지(독일어 때와 동일).
- 호칭: 반드시 "tú"(2인칭 단수 비격식)로 서술하세요. "usted/ustedes/vosotros/vuestro/vos"는 쓰지 마세요. 본문의 "du" 규칙은 "tú" 규칙으로 읽으세요. 궁합 리포트에서 두 사람을 함께 가리킬 때는 이름을 쓰거나 "ambos"/"los dos"로 쓰고 "vosotros"는 쓰지 마세요. 특히 "ustedes", "sus"(2인칭 복수 소유), 복수 명령형("Tomen", "Descarten", "Piensen", "Hagan")으로 두 사람에게 직접 말을 거는 것도 금지입니다 — 이는 스페인 독자에게 격식 차린 라틴아메리카식 어투로 들립니다. 대신 3인칭으로 쓰세요(예: "Lucía y Daniel pueden quedarse con lo que les resulte útil y dejar lo que no encaje con su experiencia" 대신 "Lo que Lucía y Daniel hagan con estas tendencias es siempre decisión de ambos; cada uno puede quedarse con lo que le resulte útil y dejar lo que no encaje con su experiencia"). 마무리 문단에도 같은 규칙을 적용하세요. 주어 대명사 "tú"는 강조할 때만 쓰고 평소엔 동사 활용으로 충분합니다(스페인어 자연스러움).
- 문법 세부(실제 출력에서 발견된 오류 방지): 오행 이름이 문장의 주어일 때는 정관사를 붙이세요("el Agua se acompañaba de la Tierra" — "Agua se acompañaba de Tierra" 금지). "한 가지 생각만 남긴다면" 같은 가정문은 "Si tuvieras que quedarte con una sola idea…" 또는 "Si hubiera que quedarse con una sola idea…"로 쓰고, "Si tuviera que quedarse"처럼 주어가 어긋난 활용은 쓰지 마세요.
- 오행 이름은 반드시 이 다섯 단어만: "Madera"(목), "Fuego"(화), "Tierra"(토), "Metal"(금), "Agua"(수). 금(金)을 "Oro"라고 쓰지 마세요. (본문의 Holz/Feuer/Erde/Metall/Wasser/Gold 규칙을 이 단어들로 읽으세요.)
- 한국 전통 표기: 기본은 "coreana"(예: "tradición coreana del Saju"). "china"로 한정하지 마세요. 역사적 정확성이 필요할 때만 "de Asia Oriental"를 보조로 쓰세요. "BaZi" 대신 "Saju"(예: "informe anual Saju")를 기본으로 쓰세요.
- 금지 단어(본문의 Schicksal 등 독일어 금지어 대신 이것을 적용): "destino"(및 "destinos" — 부정문 "no es el destino"에서도 쓰지 말고 "camino de vida", "año", "etapa"로 대체), "fatalidad", "empírico", "científico/científica/científicamente", "los estudios demuestran/muestran", "estadísticamente significativo", "validado/validada"(과학적 검증 암시), "revela/demuestra/garantiza"(단정).
- 독일어에만 해당하는 문법/연어 규칙(Leistungen erbracht, Bedarf nach/an, kein/nicht ein 등)은 스페인어에 적용되지 않으므로 무시하세요. 대신 스페인어에서 어색한 영어식 직역(예: "hacer sentido", "aplicar a un trabajo", "realizar un esfuerzo" 남발)을 피하세요.
- 성별 일치: 독자의 성별을 모르므로 "contento/contenta", "preparado/preparada", "cansado/cansada"처럼 성별에 따라 형태가 달라지는 형용사/분사로 독자를 직접 묘사하지 마세요(성별 중립 표현으로 우회: "te sientes con ganas de…", "tienes energía para…"). 궁합 리포트에서 성별 정보가 "keine Angabe"이면 이름을 반복해 쓰세요.
- 문장 부호: 의문문/감탄문은 반드시 역물음표/역느낌표로 여는 스페인어 규칙("¿…?", "¡…!")을 지키세요. 따옴표는 큰따옴표(" ")를 쓰세요.
- 월 이름은 스페인어 소문자가 아닌 챕터 소제목에서는 대문자 시작("Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre")으로 쓰세요. 챕터 소제목은 예를 들어 "Enero — Recursos que quieren mostrarse"처럼 그 달 축에 맞게 스페인어로 쓰세요.
- 본문의 독일어 예시 소제목은 다음 스페인어로 대응하세요: "Dein Jahr auf einen Blick" → "Tu año de un vistazo"; "Monate, in denen vieles leichter fließen kann" → "Los meses en que todo puede fluir con más facilidad"; "Monate für mehr Achtsamkeit" → "Los meses para prestar más atención".
- 상품명: Jahresreport → "informe anual", Lebenskarte → "mapa de vida", Kompatibilitäts-Check → "test de compatibilidad". 프리미엄 소개 문장("인생 전체의 더 긴 흐름이 궁금하다면")도 스페인어로, 구간 개수는 "8 etapas de vida de diez años"라고 쓰세요.
- 무료 리포트의 유료 리포트 구매 유도 블록은 다음 스페인어 구조로 쓰세요(독일어 예시 블록 대신): 제목 "### Tu informe anual Saju 2027 — 9,90 €", 그다음 "Lo que te espera:" 아래 불릿 5개(Tu eje personal para 2027 / 12 capítulos mensuales con impulsos Saju personalizados / Preguntas de reflexión sobre amor, trabajo y crecimiento personal / Tus fortalezas personales y posibles tensiones internas / Una brújula anual con preguntas concretas para tus propias decisiones), 마무리 문장 "Un informe de reflexión personal basado en la tradición Saju — ni un diagnóstico de personalidad con base científica, ni una predicción segura del futuro." (금액은 소수점 쉼표 "9,90 €".)
- 마지막 면책 문구는 스페인어로: "Este contenido se ofrece con fines de entretenimiento y reflexión personal; no sustituye el consejo médico ni psicológico."
- 분량 기준(단어 수)은 스페인어 단어 기준으로 동일하게 적용합니다(스페인어도 독일어보다 단어 수가 많아지는 경향이 있으니 기준 미달이 되지 않도록 하세요).
- 출력은 순수 스페인어 텍스트만. 한글/한자/독일어/프랑스어/영어 단어(예: "Holz", "Feuer", "Du", "dein", "vous", "your")가 섞이지 않게 하세요.

--- 아래부터 원래 지시문 ---
"""

_ES_PROMPT_CLOSING = """

[최종 확인 — 가장 중요, 출력 직전에 반드시 지킬 것]
위 지시문에는 독일어 예시가 많지만, 실제 출력은 **처음부터 끝까지 스페인어**여야 합니다. 제목·소제목·본문·불릿·면책 문구 전부 스페인어이고, 호칭은 "tú", 오행은 Madera/Fuego/Tierra/Metal/Agua 입니다. 독일어 단어(und, der, die, das, ist, nicht, dein, Jahr, Energie 등)가 하나라도 섞이면 안 됩니다. 순수 스페인어 텍스트만 출력하세요.
"""

PROMPT_BLOCKS = {
    "fr": (_FR_PROMPT_OVERRIDE, _FR_PROMPT_CLOSING, "프랑스어"),
    "es": (_ES_PROMPT_OVERRIDE, _ES_PROMPT_CLOSING, "스페인어"),
}

ES_DESTINO_RE = re.compile(r"\bdestinos?\b|\bfatalidad(?:es)?\b|\bdestinad[oa]s?\b", re.IGNORECASE)
ES_BANNED_REGEXES = [
    (ES_DESTINO_RE, "destino/fatalidad"),
    (re.compile(r"\bemp[ií]ric[oa]s?\b|\bempíricamente\b", re.IGNORECASE), "empírico"),
    (re.compile(r"\bcient[ií]fic(?:o|a|os|as|amente)\b", re.IGNORECASE), "científico"),
    (re.compile(r"\blos estudios (?:demuestran|muestran|prueban)\b", re.IGNORECASE), "los estudios demuestran"),
    (re.compile(r"\bestad[ií]sticamente significativ", re.IGNORECASE), "estadísticamente significativo"),
    (re.compile(r"\bvalidad[oa]s?\b", re.IGNORECASE), "validado"),
    (re.compile(r"\b(?:revela|revelan|demuestra|demuestran|garantiza|garantizan)\b", re.IGNORECASE),
     "revela/demuestra/garantiza"),
    (re.compile(r"\boportunidad única\b|\búltima oportunidad\b|\bmomento ideal\b|\bmomento decisivo\b|\bpor primera vez\b|\bcon el corazón acelerado\b", re.IGNORECASE),
     "표현 금지(희소성/긴박감/범위 밖 단정)"),
    (re.compile(r"\b(?:fuego|tierra|madera|metal|agua)\s+(?:del\s+)?cielo\b", re.IGNORECASE), "천간/지지 직역('Fuego del cielo' 등)"),
    # 독자(tú)를 성별 일치 형용사/분사로 묘사: "estás preparado", "te sientes cansada"
    (re.compile(
        r"\b(?:est[aá]s|eres|ser[aá]s|estar[aá]s|te sientes|te notas|te encuentras|quedas)\s+(?:(?:más|menos|muy|bastante|algo|siempre|a veces|tan|demasiado)\s+)?[\wáéíóúüñ]+(?:ado|ada|ido|ida|ados|adas|idos|idas|oso|osa|ivo|iva)\b",
        re.IGNORECASE), "독자(tú)를 성별 일치 형용사/분사로 묘사('estás preparado' 등)"),
]
# "tú"로 쓰기로 했으므로 격식/복수 2인칭이 나오면 걸러낸다.
ES_FORMAL_RE = re.compile(r"\b(?:usted|ustedes|vosotros|vosotras|vuestro|vuestra|vuestros|vuestras|os\s+(?:sentís|encontráis)|vos|tenéis|sois|podéis|queréis|diferenciáis)\b", re.IGNORECASE)
# 금(金) = Metal. "Oro"(금속 이름) 사용 금지.
ES_WRONG_ELEMENT_RE = re.compile(r"\belemento\s+Oro\b|\bel\s+Oro\b")
ES_ENGLISH_LEAK_RE = re.compile(
    r"\b(?:deepened|deepen|growing|moving|feeling|the|with|your|and|because|which|while|between|energy|flow|"
    r"journey|focused|mindful|gentle|healing)\b",
    re.IGNORECASE,
)
ES_GERMAN_LEAK_RE = re.compile(r"\b(?:Holz|Feuer|Erde|Metall|Wasser|Dein|Deine|Jahresreport)\b")
ES_FRENCH_LEAK_RE = re.compile(r"\b(?:vous|votre|vos|Bois|Feu|Terre|Métal|Eau|rapport annuel)\b")
ES_GERMAN_STOPWORDS_RE = re.compile(r"\b(?:und|der|die|nicht|dein|deine|deinen|ein|eine|mit|auch|wird|ist)\b")
ES_NEGATED_SCIENCE_RE = re.compile(
    r"\b(?:no|ni|sin)\b[^.!?\n]{0,80}?\b(?:con base científica|diagnóstico científico|científic[oa]s?|científicamente (?:comprobad[oa]s?|probad[oa]s?|demostrad[oa]s?|establecid[oa]s?)|base científica)\b",
    re.IGNORECASE)


def es_mechanical_issues(report_text):
    issues = []
    report_text = ES_NEGATED_SCIENCE_RE.sub(" ", report_text)
    german_hits = ES_GERMAN_STOPWORDS_RE.findall(report_text)
    if len(german_hits) >= 3:
        issues.append(
            f"리포트가 스페인어가 아니라 독일어로 작성됨(독일어 단어 {len(german_hits)}개 감지) — "
            f"전체를 순수 스페인어로 다시 작성해야 함"
        )
    for rx, label in ES_BANNED_REGEXES:
        if rx.search(report_text):
            issues.append(f"금지 단어 '{label}' 포함됨")
    if ES_WRONG_ELEMENT_RE.search(report_text):
        issues.append("'Oro'라는 단어로 금(金)을 표현함 - 반드시 'Metal'로 써야 함")
    formal = ES_FORMAL_RE.findall(report_text)
    if formal:
        issues.append(
            f"격식/복수 2인칭(usted/vosotros 등) {len(formal)}회 사용됨 - 스페인어 리포트는 "
            f"반드시 'tú' 단수 비격식만 써야 함"
        )
    eng = {m.lower() for m in ES_ENGLISH_LEAK_RE.findall(report_text)}
    if eng:
        issues.append(f"영어 단어가 섞여 있음: {', '.join(sorted(eng))} — 전부 스페인어로 바꿔야 함")
    if ES_GERMAN_LEAK_RE.search(report_text):
        issues.append("독일어 단어(Holz/Feuer/Erde/Metall/Wasser/Dein 등)가 섞여 있음 - 전부 스페인어로 바꿔야 함")
    if ES_FRENCH_LEAK_RE.search(report_text):
        issues.append("프랑스어 단어(vous/votre/Bois/Feu 등)가 섞여 있음 - 전부 스페인어로 바꿔야 함")
    return issues


ES_STRINGS = {
    "toc_heading": "Contenido",
    "you_are_here": "ESTÁS AQUÍ",
    "lifemap_heading": "Tu mapa de vida de un vistazo",
    "axis_labels": {
        "재물운": "Recursos",
        "관계운": "Relaciones",
        "직업운": "Talentos y obra",
        "총운": "Estabilidad",
    },
    "free": {
        "pdf_title": "Tu perfil Saju",
        "subtitle_named": "Elaborado para {name}",
        "subtitle_anon": "Tu perfil personal de los cinco elementos",
        "filename": "Palja-Perfil.pdf",
        "subject": "Tu perfil Saju gratuito está listo ✨",
        "intro": (
            "tu perfil personal de los cinco elementos, según la tradición coreana del Saju, "
            "ya está listo: lo encontrarás adjunto a este correo en formato PDF."
        ),
    },
    "paid": {
        "pdf_title": "Tu informe anual Saju",
        "subtitle_named": "Elaborado para {name}",
        "subtitle_anon": "Tu informe anual personal",
        "filename": "Palja-Informe-anual.pdf",
        "subject": "Tu informe anual de Palja está listo 📖",
        "intro": (
            "gracias por tu compra. Tu informe anual personal, según la tradición coreana "
            "del Saju, con los 12 meses en detalle, va adjunto a este correo en formato PDF."
        ),
    },
    "premium": {
        "pdf_title": "Tu mapa de vida Saju",
        "subtitle_named": "Elaborado para {name}",
        "subtitle_anon": "Tu mapa de vida personal",
        "filename": "Palja-Mapa-de-vida.pdf",
        "subject": "Tu mapa de vida de Palja está listo 🧭",
        "intro": (
            "gracias por tu compra. Tu mapa de vida personal, según la tradición coreana "
            "del Saju, con tus etapas de diez años, va adjunto a este correo en formato PDF."
        ),
    },
    "compatibility": {
        "pdf_title": "Tu compatibilidad Saju",
        "filename": "Palja-Compatibilidad.pdf",
        "subject": "Tu compatibilidad Saju está lista 💫",
        "intro": "gracias por tu compra. Tu análisis de compatibilidad Saju va adjunto a este correo en formato PDF.",
    },
    "hello": "Hola{name_suffix},",
    "disclaimer": (
        "Palja se ofrece con fines de entretenimiento y reflexión personal; "
        "no sustituye el consejo médico ni psicológico."
    ),
    "withdrawal_confirmation": (
        "Tienes 60 días: nuestra garantía voluntaria de devolución del dinero se aplica a esta compra. "
        "Escríbenos si el informe no es para ti."
    ),
    "promo": "¿Quieres saber cuánto conectas con otra persona?",
    "promo_link": "→ Test de compatibilidad Saju (9,90 €)",
    "footer_questions": "¿Alguna duda? Escríbenos a",
    "footer_links": [
        ("es/aviso-legal", "Aviso legal"),
        ("es/privacidad", "Privacidad"),
        ("es/desistimiento", "Desistimiento"),
    ],
    "promo_anchor": "compatibilidad",
    "geo_notice": (
        "Nota: no pudimos identificar con certeza el lugar de nacimiento {cities}. "
        "Para el cálculo usamos de forma aproximada las coordenadas de Madrid. "
        "En casos poco frecuentes, esto puede influir ligeramente en la hora considerada. "
        "Si tienes dudas, escríbenos a dionnie373@gmail.com."
    ),
}
FR_STRINGS["promo_anchor"] = "compatibilite"


# ===========================================================================
# 영어(en) — 2026-10-28 (feature/en-global). 전 세계 독자(영국/미국 제외, 비원어민 다수) 대상.
# 설계 결정(사람 검토 필요):
#  - 호칭은 "you"(영어에는 tu/vous 구분이 없다). 궁합 리포트는 두 사람이 함께 읽으므로 이름/"both"/"they"
#    3인칭으로 쓴다(es와 같은 원칙). 프롬프트로만 강제한다("you"는 무료/연간/프리미엄에서 필수라 코드로 막을 수 없음).
#  - 오행: Wood / Fire / Earth / Metal / Water (금(金)을 "Gold"로 쓰지 않는다).
#  - 철자: 미국식 중립(center, color, behavior, recognize, practice). 영국식 철자는 기계 검사에서 걸러낸다.
#  - 쉬운 국제 영어: 짧은 문장, 관용구/문화 종속 표현 금지(관용구 목록은 기계 검사).
#  - 통화는 USD("$10.00", "$24.90").
# ===========================================================================

_EN_PROMPT_OVERRIDE = """\
[언어 전환 지시 — 최우선. 아래 본문의 "독일어" 관련 모든 문구보다 이 블록이 우선합니다]
이 리포트는 독일어가 아니라 **영어**로 작성합니다. 아래 본문에 나오는 "독일어", 독일어 예시 문장/소제목/용어는 전부 같은 의도의 영어로 바꿔서 적용하세요.
- 출력 언어: 쉬운 국제 영어(plain, neutral international English). 독자는 전 세계에 있고 비원어민이 많습니다. 짧은 문장(대부분 20단어 이하), 흔한 단어, 축약형(don't 등) 없이 완전한 형태, 능동태. 관용구·문화 종속 표현(스포츠/명절/학제 비유)·유행어(journey, navigate, unlock, embrace, tapestry, dance) 금지. 직역투, 존재하지 않는 신조어, 어색한 관청체, 이중부정 금지(독일어 때와 동일).
- 철자: 미국식 중립 철자로 통일(center, color, behavior, favor, recognize, organize, practice, program, gray, judgment, neighbor, analyze). 영국식 철자(centre, colour, behaviour, realise, practise 등)는 쓰지 마세요.
- 호칭: 독자는 항상 "you/your"(단수). 본문의 "du" 규칙은 "you" 규칙으로 읽으세요. 궁합 리포트에서는 두 사람이 함께 읽으므로 "you/your"로 말을 걸지 말고 이름, "both", "the two of them" 3인칭으로 쓰세요. 두 사람에게 하는 복수 명령형도 금지입니다.
- 오행 이름은 반드시 이 다섯 단어만: "Wood"(목), "Fire"(화), "Earth"(토), "Metal"(금), "Water"(수). 금(金)을 "Gold"라고 쓰지 마세요. (본문의 Holz/Feuer/Erde/Metall/Wasser/Gold 규칙을 이 단어들로 읽으세요.)
- 한국 전통 표기: 기본은 "Korean"(예: "the Korean Saju tradition"). "Chinese"로 한정하지 마세요. 역사적 정확성이 필요할 때만 "East Asian"을 보조로 쓰세요. "BaZi" 대신 "Saju"(예: "Saju annual report")를 기본으로 쓰세요.
- 금지 단어(본문의 Schicksal 등 독일어 금지어 대신 이것을 적용): "destiny"/"fate"/"fated"/"fateful"/"fatality"(부정문에서도 쓰지 말고 "path", "year", "phase"로 대체), "empirical", "scientific/scientifically"(연간 리포트 마무리의 부정형 문장 제외), "studies show/prove", "statistically significant", "validated", "reveals/proves/guarantees/demonstrates"(단정).
- 독일어에만 해당하는 문법/연어 규칙(Leistungen erbracht, Bedarf nach/an, kein/nicht ein 등)은 영어에 적용되지 않으므로 무시하세요.
- 성별: 독자의 성별·가족 상황·직업을 가정하지 마세요. 궁합 리포트에서 성별 정보가 "keine Angabe"/"not specified"이면 이름을 반복해 쓰세요.
- 월 이름은 영어로("January" … "December"). 챕터 소제목은 예를 들어 "January — Resources that are ready to show"처럼 동사 없는 짧은 명사구로 쓰세요.
- 본문의 독일어 예시 소제목은 다음 영어로 대응하세요: "Dein Jahr auf einen Blick" → "Your year at a glance"; "Monate, in denen vieles leichter fließen kann" → "Months in which things may flow more easily"; "Monate für mehr Achtsamkeit" → "Months for more attention".
- 상품명: Jahresreport → "annual report", Lebenskarte → "life map", Kompatibilitäts-Check → "compatibility check". 프리미엄 소개 문장("인생 전체의 더 긴 흐름이 궁금하다면")도 영어로, 구간 개수는 "8 life phases of ten years"라고 쓰세요. 금액은 "$10.00"/"$24.90" 형식입니다.
- 무료 리포트의 유료 리포트 구매 유도 블록은 다음 영어 구조로 쓰세요(독일어 예시 블록 대신): 제목 "### Your Saju annual report 2027 — $10.00", 그다음 "What you will get:" 아래 불릿 5개(Your personal theme for 2027 / 12 monthly chapters with personal Saju impulses / Reflection questions about love, work and personal growth / Your personal strengths and possible inner tensions / A yearly compass with concrete questions for your own decisions), 마무리 "A personal reflection report based on the Saju tradition. It is not a scientific personality diagnosis, and it is not a certain prediction of the future."
- 마지막 면책 문구는 영어로: "This content is offered for entertainment and personal reflection. It does not replace medical or psychological advice."
- 분량 기준(단어 수)은 영어 단어 기준으로 동일하게 적용합니다(영어는 스페인어/독일어보다 단어 수가 적게 나오는 경향이 있으니 기준 미달이 되지 않도록 구체적 예시를 충분히 넣으세요).
- 출력은 순수 영어 텍스트만. 한글/한자/독일어/프랑스어/스페인어 단어(예: "Holz", "Feuer", "Du", "dein", "vous", "tú")가 섞이지 않게 하세요.

--- 아래부터 원래 지시문 ---
"""

_EN_PROMPT_CLOSING = """

[최종 확인 — 가장 중요, 출력 직전에 반드시 지킬 것]
위 지시문에는 독일어 예시가 많지만, 실제 출력은 **처음부터 끝까지 영어**여야 합니다. 제목·소제목·본문·불릿·면책 문구 전부 영어이고, 독자 호칭은 "you"(궁합은 이름/both 3인칭), 오행은 Wood/Fire/Earth/Metal/Water, 철자는 미국식 중립입니다. 독일어 단어(und, der, die, das, ist, nicht, dein, Jahr, Energie 등)가 하나라도 섞이면 안 됩니다. 순수 영어 텍스트만 출력하세요.
"""

PROMPT_BLOCKS["en"] = (_EN_PROMPT_OVERRIDE, _EN_PROMPT_CLOSING, "영어")

# "destiny"/"fate" 계열. "destination"은 \b 경계로 제외된다. fatal(ity)는 "fatality"만 잡는다.
EN_DESTINY_RE = re.compile(
    r"\bdestin(?:y|ies|ed)\b|\bfate[sd]?\b|\bfateful(?:ly)?\b|\bfatalit(?:y|ies)\b|\bfatalis(?:m|tic|tically)\b",
    re.IGNORECASE)
_EN_ASSERT_VERBS = r"(?:reveals?|proves?|proven|guarantees?|guaranteed|demonstrates?|demonstrated)"
EN_BANNED_REGEXES = [
    (EN_DESTINY_RE, "destiny/fate/fatality"),
    (re.compile(r"\bempirical(?:ly)?\b", re.IGNORECASE), "empirical"),
    (re.compile(r"\bscientific(?:ally)?\b|\bscience-based\b|\bevidence-based\b", re.IGNORECASE), "scientific"),
    (re.compile(r"\bstudies\s+(?:show|prove|demonstrate|confirm|have shown)\b|\bresearch\s+(?:shows|proves|confirms)\b", re.IGNORECASE), "studies show"),
    (re.compile(r"\bstatistically\s+significant\b", re.IGNORECASE), "statistically significant"),
    (re.compile(r"\bvalidated?\b", re.IGNORECASE), "validated"),
    (re.compile(r"\b" + _EN_ASSERT_VERBS + r"\b", re.IGNORECASE), "reveals/proves/guarantees/demonstrates"),
    (re.compile(
        r"\bunique opportunity\b|\brare opportunity\b|\bonce[- ]in[- ]a[- ]lifetime\b|\blast chance\b|\bfinal chance\b|"
        r"\bideal (?:moment|time)\b|\bperfect (?:moment|time)\b|\bdecisive moment\b|\bnow is the time\b|\bit is time to\b|"
        r"\bfor the first time\b|\bheart(?:s)? (?:racing|pounding|beating fast)\b|\bracing heart\b", re.IGNORECASE),
     "표현 금지(희소성/긴박감/범위 밖 단정)"),
    # 천간/지지 직역: "Fire of heaven", "heavenly Fire", "Fire in the sky"
    (re.compile(
        r"\b(?:wood|fire|earth|metal|water)\s+(?:of|from|in|on)\s+(?:the\s+)?(?:heaven|heavens|sky)\b|"
        r"\b(?:heavenly|celestial)\s+(?:wood|fire|earth|metal|water|element)s?\b", re.IGNORECASE),
     "천간/지지 직역('Fire of heaven' 등)"),
    # 독자 성별을 가정하는 이중 표기: "he or she", "his/her", "(s)he"
    (re.compile(r"\bhe\s+or\s+she\b|\bhis\s+or\s+her\b|\bhim\s+or\s+her\b|\bhis/her\b|\bhe/she\b|\bs/he\b|\(s\)he\b", re.IGNORECASE),
     "성별 이중 표기('he or she' 등)"),
]
# 영국식 철자(미국식 중립으로 통일). 대표적인 -our/-ise/-re/-ogue/기타만 명시한다.
EN_BRITISH_SPELLING_RE = re.compile(
    r"\b(?:colour\w*|favour\w*|behaviour\w*|honour\w*|labour\w*|neighbour\w*|flavour\w*|rumour\w*|humour\w*|"
    r"centre[sd]?|centring|metre|fibre|theatre|"
    r"realis\w+|recognis\w+|organis\w+|analys(?:e|ed|es|ing)|summaris\w+|emphasis(?:e|ed|es|ing)|prioritis\w+|"
    r"familiaris\w+|apologis\w+|criticis(?:e|ed|es|ing)|minimis\w+|maximis\w+|stabilis\w+|harmonis\w+|"
    r"practis(?:e|ed|es|ing)|licence|defence|offence|judgement|programme[sd]?|grey|ageing|learnt|spelt|"
    r"whilst|amongst|cosy)\b",
    re.IGNORECASE)
# 쉬운 국제 영어 규칙: 관용구/유행어/문화 종속 표현(프롬프트가 금지한 목록).
EN_IDIOM_RE = re.compile(
    r"\bat the end of the day\b|\bon the same page\b|\bgo(?:es|ing)? with the flow\b|\bcomfort zone\b|\broller\s?coaster\b|"
    r"\bball is in your court\b|\bbreak the ice\b|\bthink outside the box\b|\bgame[- ]changer\b|\btip of the iceberg\b|"
    r"\bsilver lining\b|\bdouble-edged sword\b|\bin a nutshell\b|\bpiece of cake\b|\bhit the ground running\b|"
    r"\btapestry\b|\bunlock(?:s|ed|ing)?\s+(?:your|the|new)\b|\bdelve\b", re.IGNORECASE)
# 타 언어 혼입(독일어/프랑스어/스페인어 단어, 한글)
EN_GERMAN_LEAK_RE = re.compile(r"\b(?:Holz|Feuer|Erde|Metall|Wasser|Dein|Deine|Jahresreport|Lebenskarte)\b")
EN_FRENCH_LEAK_RE = re.compile(r"\b(?:vous|votre|vos|Bois|Feu|Terre|Métal|Eau|rapport annuel)\b")
EN_SPANISH_LEAK_RE = re.compile(r"\b(?:usted|ustedes|Madera|Fuego|Tierra|Agua|informe anual|mapa de vida)\b")
EN_GERMAN_STOPWORDS_RE = re.compile(r"\b(?:und|der|das|nicht|dein|deine|deinen|ein|eine|mit|auch|wird|ist)\b")
EN_ROMANCE_STOPWORDS_RE = re.compile(r"\b(?:les|des|une|est|dans|los|las|una|para|esta|este|pero)\b")
EN_HANGUL_RE = re.compile(r"[ᄀ-ᇿ㄰-㆏가-힣]")
# 면책 문구의 부정형은 허용한다: "It is not a scientific personality diagnosis"는 과학적 근거를 암시하지 않고
# 선을 긋는 문장이다(fr/es와 동일 원칙). 같은 문장 안에서 부정어 뒤 80자 이내의 scientific만 제외한다.
EN_NEGATED_SCIENCE_RE = re.compile(
    r"\b(?:not|no|nor|neither|never|without|isn't|aren't|doesn't|cannot)\b[^.!?\n]{0,80}?\bscien(?:tific(?:ally)?|ce-based)\b",
    re.IGNORECASE)
# "validated"도 같은 방식으로 "not validated"를 허용하지는 않는다(과학 검증 암시 단어 자체를 피한다).


def en_mechanical_issues(report_text):
    issues = []
    report_text = EN_NEGATED_SCIENCE_RE.sub(" ", report_text)
    german_hits = EN_GERMAN_STOPWORDS_RE.findall(report_text)
    if len(german_hits) >= 3:
        issues.append(
            f"리포트가 영어가 아니라 독일어로 작성됨(독일어 단어 {len(german_hits)}개 감지) — "
            f"전체를 순수 영어로 다시 작성해야 함"
        )
    romance_hits = EN_ROMANCE_STOPWORDS_RE.findall(report_text)
    if len(romance_hits) >= 3:
        issues.append(
            f"리포트가 영어가 아니라 프랑스어/스페인어로 작성됨(해당 언어 기능어 {len(romance_hits)}개 감지) — "
            f"전체를 순수 영어로 다시 작성해야 함"
        )
    for rx, label in EN_BANNED_REGEXES:
        if rx.search(report_text):
            issues.append(f"금지 단어 '{label}' 포함됨")
    if re.search(r"\belement\s+Gold\b|\bthe\s+Gold\b|\bGold\s+element\b", report_text):
        issues.append("'Gold'라는 단어로 금(金)을 표현함 - 반드시 'Metal'로 써야 함")
    british = sorted({m.lower() for m in EN_BRITISH_SPELLING_RE.findall(report_text)})
    if british:
        issues.append(f"영국식 철자 사용됨: {', '.join(british[:8])} — 미국식 중립 철자(center, color, behavior, recognize, practice)로 통일해야 함")
    idioms = sorted({m.group(0).lower() for m in EN_IDIOM_RE.finditer(report_text)})
    if idioms:
        issues.append(f"관용구/유행어 사용됨: {', '.join(idioms[:6])} — 쉬운 국제 영어로 바꿔야 함")
    if EN_GERMAN_LEAK_RE.search(report_text):
        issues.append("독일어 단어(Holz/Feuer/Erde/Metall/Wasser/Dein 등)가 섞여 있음 - 전부 영어로 바꿔야 함")
    if EN_FRENCH_LEAK_RE.search(report_text):
        issues.append("프랑스어 단어(vous/votre/Bois/Feu 등)가 섞여 있음 - 전부 영어로 바꿔야 함")
    if EN_SPANISH_LEAK_RE.search(report_text):
        issues.append("스페인어 단어(usted/Madera/Fuego 등)가 섞여 있음 - 전부 영어로 바꿔야 함")
    if EN_HANGUL_RE.search(report_text):
        issues.append("한글이 섞여 있음 - 전부 영어로 바꿔야 함")
    return issues


EN_STRINGS = {
    "toc_heading": "Contents",
    "you_are_here": "YOU ARE HERE",
    "lifemap_heading": "Your life map at a glance",
    "axis_labels": {
        "재물운": "Resources",
        "관계운": "Relationships",
        "직업운": "Talents & work",
        "총운": "Stability",
    },
    "free": {
        "pdf_title": "Your Saju profile",
        "subtitle_named": "Prepared for {name}",
        "subtitle_anon": "Your personal five-elements profile",
        "filename": "Palja-Profile.pdf",
        "subject": "Your free Saju profile is ready ✨",
        "intro": (
            "your personal five-elements profile, based on the Korean Saju tradition, "
            "is ready. You can find it as a PDF attached to this email."
        ),
    },
    "paid": {
        "pdf_title": "Your Saju annual report",
        "subtitle_named": "Prepared for {name}",
        "subtitle_anon": "Your personal annual report",
        "filename": "Palja-Annual-Report.pdf",
        "subject": "Your Palja annual report is ready 📖",
        "intro": (
            "thank you for your purchase. Your personal annual report, based on the Korean Saju tradition "
            "and covering all 12 months in detail, is attached to this email as a PDF."
        ),
    },
    "premium": {
        "pdf_title": "Your Saju life map",
        "subtitle_named": "Prepared for {name}",
        "subtitle_anon": "Your personal life map",
        "filename": "Palja-Life-Map.pdf",
        "subject": "Your Palja life map is ready 🧭",
        "intro": (
            "thank you for your purchase. Your personal life map, based on the Korean Saju tradition "
            "and covering your ten-year life phases, is attached to this email as a PDF."
        ),
    },
    "compatibility": {
        "pdf_title": "Your Saju compatibility",
        "filename": "Palja-Compatibility.pdf",
        "subject": "Your Saju compatibility check is ready 💫",
        "intro": "thank you for your purchase. Your Saju compatibility check is attached to this email as a PDF.",
    },
    "hello": "Hello{name_suffix},",
    "disclaimer": (
        "Palja is offered for entertainment and personal reflection. "
        "It does not replace medical or psychological advice."
    ),
    "withdrawal_confirmation": (
        "You have 60 days: our voluntary money-back guarantee applies to this purchase. "
        "Just write to us if the report is not right for you."
    ),
    "promo": "Would you like to see how well you connect with another person?",
    "promo_link": "→ Saju compatibility check ($10.00)",
    "footer_questions": "Questions? Write to us at",
    "footer_links": [
        ("en/legal-notice", "Legal notice"),
        ("en/privacy", "Privacy"),
    ],
    "promo_anchor": "compatibility",
    "geo_notice": (
        "Note: we could not find the place of birth {cities} with certainty. "
        "For the calculation we used approximate coordinates in central Germany. "
        "In rare cases this can slightly change the hour that was used. "
        "If you have questions, write to us at dionnie373@gmail.com."
    ),
}

# lang → 문구 사전 (de는 report_pipeline/pdf_design의 기존 상수를 그대로 쓴다)
STRINGS = {"fr": FR_STRINGS, "es": ES_STRINGS, "en": EN_STRINGS}

# lang → 면책 부정형/금지어 검사 함수, "숙명" 계열 정규식과 라벨
MECHANICAL_ISSUES = {"fr": fr_mechanical_issues, "es": es_mechanical_issues, "en": en_mechanical_issues}
DESTINY_RE = {"fr": FR_DESTIN_RE, "es": ES_DESTINO_RE, "en": EN_DESTINY_RE}
DESTINY_LABEL = {"de": "Schicksal", "fr": "destin", "es": "destino", "en": "destiny"}
