#!/usr/bin/env python3
"""실제 AI 생성 + PDF 렌더링 검증 스크립트 (로컬/테스트 환경 전용).

운영 서버에서 돌리지 말 것. 이메일은 보내지 않는다(send_email을 가로채 PDF만 저장).
고객 데이터·결제와 무관하며, 아래 샘플 생년월일은 모두 가상의 테스트 값이다.

사용법:
  export ANTHROPIC_API_KEY=...        # 본인 환경에서만 설정
  cd saju-api
  python3 tools/verify_ai_reports.py --out /tmp/palja_verify            # 전체(무료·연간·일생·궁합)
  python3 tools/verify_ai_reports.py --out /tmp/palja_verify --products annual,lifetime --dry
  python3 tools/verify_ai_reports.py --out /tmp/palja_verify --products compat --charts 1

주의: 리포트 1개당 생성에 200~250초, API 비용이 든다. 기본값(4상품 x 샘플 3 + 반복 1)은 오래 걸리므로
먼저 --charts 1 --products annual 로 한 번 돌려 보는 것을 권장한다.

산출물(--out):
  <product>_<chart>.txt / .pdf   생성 원문과 실제 PDF
  summary.md / summary.json      자동 점검 결과(PASS/WARN/FAIL)와 유사도 표
점검은 '명백한 오류 탐지'용이다. 문장 품질·전통 해석의 적절성은 사람이 원문을 읽고 판단해야 한다.
"""
import argparse
import itertools
import json
import os
import re
import shutil
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

# 가상의 테스트 차트(실제 고객 데이터 아님). 3번째는 연말·시간 모름 케이스, 4번째는 1번의 반복 실행.
CHARTS = [
    {"id": "c1", "name": "Testa", "birth_date": "1984-09-27", "birth_time": "20:00", "birth_city": "Seoul", "gender": "male"},
    {"id": "c2", "name": "Testb", "birth_date": "1991-03-08", "birth_time": "07:30", "birth_city": "Berlin", "gender": "female"},
    {"id": "c3", "name": "Testc", "birth_date": "1978-12-31", "birth_time": "", "birth_city": "", "gender": "male"},
]
PRODUCT_TARGET_WORDS = {"free": (450, 1400), "annual": (2500, 4500), "lifetime": (3200, 5200), "compat": (450, 1500)}
FORBIDDEN = ["Schicksal", "garantiert", "beweist", "offenbart", "einmalige Gelegenheit", "letzte Chance",
             "idealer Zeitpunkt", "entscheidender Moment", "empirisch", "signifikant", "validiert"]
MONTHS_DE = ["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September", "Oktober",
             "November", "Dezember"]

results = []  # (product, chart, level, message)


def add(product, chart, level, msg):
    results.append((product, chart, level, msg))


def words(text):
    return re.findall(r"[A-Za-zÄÖÜäöüß0-9]+", text)


def shingles(text, n=5):
    w = [x.lower() for x in words(text)]
    return {tuple(w[i:i + n]) for i in range(max(0, len(w) - n + 1))}


def jaccard(a, b):
    sa, sb = shingles(a), shingles(b)
    return len(sa & sb) / len(sa | sb) if (sa | sb) else 0.0


def common_checks(product, chart, text):
    lo, hi = PRODUCT_TARGET_WORDS[product]
    n = len(words(text))
    add(product, chart, "PASS" if lo <= n <= hi else "WARN", f"단어 수 {n} (기준 {lo}~{hi})")
    if re.search(r"[㐀-鿿豈-﫿]", text):
        add(product, chart, "FAIL", "한자가 본문에 있음(PDF 폰트에서 네모로 깨짐)")
    if re.search(r"\b(Sie|Ihnen|Ihre[rnms]?)\b(?!\s*,?\s*(und|oder)?\s*euch)", text) and product != "compat":
        add(product, chart, "WARN", "격식체(Sie/Ihnen/Ihre) 의심 - 원문 확인")
    hits = [w for w in FORBIDDEN if w.lower() in text.lower()]
    if hits:
        add(product, chart, "FAIL", f"금지 표현: {', '.join(hits)}")
    if re.search(r"^\s*\|?[-: ]*\|[-: |]+$", text, re.M) and product != "annual":
        add(product, chart, "WARN", "마크다운 표 구분선 발견(PDF 표 렌더링 확인 필요)")
    if "{{" in text or "}}" in text:
        add(product, chart, "FAIL", "치환되지 않은 {{변수}}가 남음")


def annual_checks(chart, text, calc):
    for bad in ("Reflexionsfrage", "Reflexionsreport"):
        if bad in text:
            add("annual", chart, "FAIL", f"연간 약속과 어긋나는 표현 '{bad}'")
    missing = [m for m in MONTHS_DE if m not in text]
    add("annual", chart, "PASS" if not missing else "FAIL", "12개월 모두 언급" if not missing else f"누락된 월: {missing}")
    try:
        import report_facts
        year = calc["monthly"]["year"]
        res = report_facts.solar_month_boundaries(year, "de")
        bounds = res[0] if isinstance(res, tuple) else res
        miss = []
        for b in bounds:
            d = b["start"]
            if not re.search(rf"\b{d.day}\.\s*{MONTHS_DE[d.month - 1]}", text):
                miss.append(f"{d.day}.{d.month}.")
        add("annual", chart, "PASS" if len(miss) <= 3 else "WARN",
            "절기 시작일이 본문에 언급됨" if not miss else f"본문에 없는 절기 시작일 {miss}(월 머리말에 'ab N. Monat'로 쓰라는 규칙)")
    except Exception as e:  # noqa: BLE001
        add("annual", chart, "WARN", f"절기 날짜 점검 실패: {e!r}")
    if re.search(r"\b(sehr gut|schlecht|Note [A-F1-5]|Stufe \d|Punkte)\b", text):
        add("annual", chart, "WARN", "월별 등급/점수로 보이는 표현 - 원문 확인(등급은 비활성 상태여야 함)")


def lifetime_checks(chart, text, calc):
    entries = calc["daewoon"]["entries"]
    exp_years = {e["start_year"] for e in entries}
    found = {int(y) for y in re.findall(r"\b(19\d\d|20\d\d|21\d\d)\b", text)}
    birth_year = int(calc["input"].get("birth_date", "0000")[:4]) if isinstance(calc.get("input"), dict) else 0
    stray = sorted(y for y in found if y != birth_year and all(abs(y - s) > 1 for s in exp_years)
                   and not (2024 <= y <= 2030))
    add("lifetime", chart, "PASS" if not stray else "WARN",
        f"본문 연도 {sorted(found)} / 계산된 시작 연도 {sorted(exp_years)}" + (f" / 계산과 무관해 보이는 연도 {stray}" if stray else ""))
    miss_age = [e["start_age"] for e in entries if not re.search(rf"\b{e['start_age']}\s*[–-]\s*{e['end_age']}\b", text)]
    add("lifetime", chart, "PASS" if not miss_age else "FAIL",
        "모든 대운 구간 소제목이 본문에 있음" if not miss_age else f"소제목 누락 시작나이 {miss_age}")
    cur = [e for e in entries if e.get("is_current")]
    if cur:
        add("lifetime", chart, "PASS", f"계산상 현재 대운: {cur[0]['pillar']['hanja']} ({cur[0]['start_age']}~{cur[0]['end_age']}세, 약 {cur[0]['start_year']}년경~) - 본문의 '현재' 구간과 일치하는지 사람이 확인")


def compat_checks(chart, text, calc_a, calc_b):
    for bad in ("Sie ", "Ihnen"):
        if bad in text:
            add("compat", chart, "WARN", f"격식체 의심 '{bad.strip()}'")
    for key in ("Auf einen Blick", "So haben wir gerechnet"):
        if key not in text:
            add("compat", chart, "FAIL", f"필수 섹션 '{key}' 없음")
    for name in (calc_a.get("_name"), calc_b.get("_name")):
        if name and name not in text:
            add("compat", chart, "WARN", f"이름 '{name}'이 본문에 없음")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--products", default="free,annual,lifetime,compat")
    ap.add_argument("--charts", type=int, default=3, help="사용할 서로 다른 차트 수(1~3). 반복 실행은 --repeat")
    ap.add_argument("--repeat", action="store_true", help="첫 차트를 한 번 더 생성해 변동·중복을 비교")
    ap.add_argument("--dry", action="store_true", help="API 호출 없이 계산 입력만 점검")
    args = ap.parse_args()

    if not args.dry and not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("ANTHROPIC_API_KEY가 없습니다. 본인 환경에서 설정한 뒤 실행하세요(운영 서버 금지).")
    os.makedirs(args.out, exist_ok=True)

    os.environ.setdefault("BREVO_API_KEY", "not-used")
    os.environ.setdefault("FROM_EMAIL", "noreply@example.invalid")
    import app as A
    import report_pipeline as RP

    captured = {}

    def fake_send_email(*, to_email, subject, html_body, attachment_path=None, attachment_name=None, **kw):
        captured["pdf"] = None
        if attachment_path and os.path.exists(attachment_path):
            keep = os.path.join(args.out, "_last.pdf")
            shutil.copy(attachment_path, keep)
            captured["pdf"] = keep
        captured["html"] = html_body
        captured["subject"] = subject

    RP.send_email = fake_send_email
    products = [p.strip() for p in args.products.split(",") if p.strip()]
    charts = CHARTS[: max(1, min(args.charts, len(CHARTS)))]
    runs = [(c, "") for c in charts] + ([(charts[0], "_rep")] if args.repeat else [])
    texts = {}
    dest = "verify@example.invalid"

    for product, (chart, suffix) in itertools.product(products, runs):
        cid = chart["id"] + suffix
        label = f"{product}_{cid}"
        base = {"name": chart["name"], "birth_date": chart["birth_date"], "birth_time": chart["birth_time"],
                "birth_city": chart["birth_city"] or "Berlin", "email": dest, "lang": "de"}
        if args.dry:
            calc = A.run_calculation({**base, "gender": chart["gender"], "monthly_year": 2027})
            print(f"[dry] {label}: 계산 OK, 대운 시작연도 {[e['start_year'] for e in calc['daewoon']['entries']]}")
            continue
        t0 = time.time()
        captured.clear()
        try:
            if product == "free":
                calc = A.run_calculation(base)
                RP.run_free_signup(payload=base, calc_result=calc)
            elif product == "annual":
                calc = A.run_calculation({**base, "monthly_year": 2027})
                RP.run_paid_signup(payload={**base, "monthly_year": 2027}, calc_result=calc)
            elif product == "lifetime":
                calc = A.run_calculation({**base, "gender": chart["gender"]})
                RP.run_premium_signup(payload={**base, "gender": chart["gender"]}, calc_result=calc)
            elif product == "compat":
                other = CHARTS[(CHARTS.index(chart) + 1) % len(CHARTS)]
                pa = {"name": chart["name"], "birth_date": chart["birth_date"], "birth_time": chart["birth_time"],
                      "birth_city": chart["birth_city"] or "Berlin", "lang": "de"}
                pb = {"name": other["name"], "birth_date": other["birth_date"], "birth_time": other["birth_time"],
                      "birth_city": other["birth_city"] or "Berlin", "lang": "de"}
                ca, cb = A.run_calculation(pa), A.run_calculation(pb)
                ca["_name"], cb["_name"] = chart["name"], other["name"]
                RP.run_compatibility_signup(
                    payload={"email": dest, "name_a": chart["name"], "name_b": other["name"],
                             "birth_time_a": chart["birth_time"], "birth_time_b": other["birth_time"], "lang": "de"},
                    calc_result_a=ca, calc_result_b=cb)
            else:
                continue
        except Exception as e:  # noqa: BLE001
            add(product, cid, "FAIL", f"생성 실패: {type(e).__name__}: {e}")
            continue
        text = RP.LAST_REPORT_TEXT or ""
        texts[(product, cid)] = text
        with open(os.path.join(args.out, label + ".txt"), "w", encoding="utf-8") as f:
            f.write(text)
        if captured.get("pdf"):
            os.replace(captured["pdf"], os.path.join(args.out, label + ".pdf"))
            add(product, cid, "PASS", f"PDF 생성 ({os.path.getsize(os.path.join(args.out, label + '.pdf')) // 1024} KB)")
        else:
            add(product, cid, "FAIL", "PDF가 생성되지 않음")
        common_checks(product, cid, text)
        if product == "annual":
            annual_checks(cid, text, calc)
        elif product == "lifetime":
            lifetime_checks(cid, text, calc)
        elif product == "compat":
            compat_checks(cid, text, ca, cb)
        print(f"[{label}] {time.time() - t0:.0f}초, {len(words(text))}단어")

    # 유사도: (1) 같은 차트 반복 (2) 서로 다른 차트 (3) 같은 차트의 연간 vs 일생
    sim_rows = []
    for p in products:
        keys = [k for k in texts if k[0] == p]
        for (ka, kb) in itertools.combinations(keys, 2):
            kind = "같은 차트 반복" if ka[1].rstrip("_rep") == kb[1].rstrip("_rep") else "다른 차트"
            sim_rows.append((p, ka[1], kb[1], kind, jaccard(texts[ka], texts[kb])))
    for c in {k[1].rstrip("_rep") for k in texts}:
        if ("annual", c) in texts and ("lifetime", c) in texts:
            sim_rows.append(("annual↔lifetime", c, c, "상품 간 중복", jaccard(texts[("annual", c)], texts[("lifetime", c)])))

    lines = ["# AI 생성 검증 요약", "", "| 상품 | 차트 | 결과 | 내용 |", "|---|---|---|---|"]
    for p, c, lv, m in results:
        lines.append(f"| {p} | {c} | {lv} | {m} |")
    if sim_rows:
        lines += ["", "## 5단어 구문 중복도(Jaccard)", "", "| 비교 | A | B | 종류 | 중복도 |", "|---|---|---|---|---|"]
        lines += [f"| {p} | {a} | {b} | {k} | {s:.2f} |" for p, a, b, k, s in sim_rows]
        lines += ["", "해석 기준(참고): 다른 차트·상품 간 0.10 이하면 충분히 다름, 0.25 이상이면 문장 틀이 반복됨(원문 확인)."]
    lines += ["", "자동 점검은 명백한 오류만 잡는다. 문장 품질, 전통 해석의 적절성, 개인화 정도는 txt/pdf를 직접 읽고 판단할 것."]
    with open(os.path.join(args.out, "summary.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    with open(os.path.join(args.out, "summary.json"), "w", encoding="utf-8") as f:
        json.dump({"checks": results, "similarity": sim_rows}, f, ensure_ascii=False, indent=2)
    print("\n".join(lines))
    fails = [r for r in results if r[2] == "FAIL"]
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
