"""
saju-api: 사주(四柱) 계산 웹 API

POST /calculate
{
  "name": "홍길동",              // optional
  "birth_datetime": "1984-09-27T20:00:00",  // 필수, 양력 기준, 시간 모름이면 12:00 사용 권장
  "longitude": 126.9784,          // 필수, 출생지 경도 (서울=126.9784, 베를린=13.405, 프랑크푸르트=8.6821 등)
  "yaja_si_separated": true,      // 선택, 기본 true (야자시/조자시 구분)
  "target_year": 2027             // 선택, 특정 연도 세운(년주)까지 함께 계산하고 싶을 때
}

응답에는 사주 4주(년/월/일/시), 오행 개수, 그리고 AI 프롬프트에 바로 넣을 수 있는
"compact" 텍스트 요약이 포함됩니다.
"""

import os
import sys
from datetime import datetime

from flask import Flask, request, jsonify

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from korean_saju import Saju, SajuAnalysis, load_bundled_data  # noqa: E402

app = Flask(__name__)

_lunar, _solar_terms = load_bundled_data()

ELEMENT_HANJA = {
    "목": "木", "화": "火", "토": "土", "금": "金", "수": "水",
}


def _pillar_dict(pillar):
    return {
        "hanja": pillar.hanja,
        "hangul": pillar.hangul,
        "cheon_gan_element": pillar.cheon_gan.o_haeng.hangul,
        "ji_ji_element": pillar.ji_ji.o_haeng.hangul,
    }


def _count_elements(saju):
    counts = {"목": 0, "화": 0, "토": 0, "금": 0, "수": 0}
    for pillar in [saju.year_pillar, saju.month_pillar, saju.day_pillar, saju.hour_pillar]:
        counts[pillar.cheon_gan.o_haeng.hangul] += 1
        counts[pillar.ji_ji.o_haeng.hangul] += 1
    return counts


def _build_compact(name, saju, counts):
    pillars_str = (
        f"년주 {saju.year_pillar.hanja}({saju.year_pillar.hangul}) / "
        f"월주 {saju.month_pillar.hanja}({saju.month_pillar.hangul}) / "
        f"일주 {saju.day_pillar.hanja}({saju.day_pillar.hangul}) / "
        f"시주 {saju.hour_pillar.hanja}({saju.hour_pillar.hangul})"
    )
    counts_str = ", ".join(f"{el}{ELEMENT_HANJA[el]} {cnt}개" for el, cnt in counts.items())
    max_el = max(counts, key=counts.get)
    min_els = [el for el, cnt in counts.items() if cnt == min(counts.values())]
    lines = [
        f"이름: {name or '(미입력)'}",
        f"사주: {pillars_str}",
        f"오행 분포: {counts_str}",
        f"가장 많은 오행: {max_el}({ELEMENT_HANJA[max_el]})",
        f"가장 적은/없는 오행: {', '.join(f'{e}({ELEMENT_HANJA[e]})' for e in min_els)}",
    ]
    return "\n".join(lines)


@app.route("/", methods=["GET"])
def health():
    return jsonify({"ok": True, "service": "saju-api", "status": "running"})


@app.route("/calculate", methods=["POST"])
def calculate():
    try:
        payload = request.get_json(force=True, silent=False) or {}
    except Exception:
        return jsonify({"ok": False, "error": "잘못된 JSON 형식입니다."}), 400

    name = payload.get("name")
    birth_datetime_str = payload.get("birth_datetime")
    longitude = payload.get("longitude")
    yaja_si_separated = payload.get("yaja_si_separated", True)
    target_year = payload.get("target_year")

    if not birth_datetime_str:
        return jsonify({"ok": False, "error": "birth_datetime 값이 필요합니다. 예: '1984-09-27T20:00:00'"}), 400
    if longitude is None:
        return jsonify({"ok": False, "error": "longitude(경도) 값이 필요합니다."}), 400

    try:
        birth_dt = datetime.fromisoformat(birth_datetime_str)
    except ValueError:
        return jsonify({"ok": False, "error": "birth_datetime 형식이 올바르지 않습니다. 'YYYY-MM-DDTHH:MM:SS' 형식을 사용하세요."}), 400

    try:
        longitude = float(longitude)
    except (TypeError, ValueError):
        return jsonify({"ok": False, "error": "longitude 값은 숫자여야 합니다."}), 400

    try:
        saju = Saju.from_birth(
            kst_moment=birth_dt,
            solar_terms=_solar_terms,
            longitude=longitude,
            yaja_si_separated=bool(yaja_si_separated),
        )
        analysis = SajuAnalysis(saju)
    except Exception as e:
        return jsonify({"ok": False, "error": f"사주 계산 중 오류가 발생했습니다: {e}"}), 500

    counts = _count_elements(saju)

    result = {
        "ok": True,
        "input": {
            "name": name,
            "birth_datetime": birth_datetime_str,
            "longitude": longitude,
            "yaja_si_separated": bool(yaja_si_separated),
        },
        "pillars": {
            "year": _pillar_dict(saju.year_pillar),
            "month": _pillar_dict(saju.month_pillar),
            "day": _pillar_dict(saju.day_pillar),
            "hour": _pillar_dict(saju.hour_pillar),
        },
        "element_counts": counts,
        "jeonggyeok": getattr(analysis, "jeonggyeok", None) and str(analysis.jeonggyeok),
        "yongsin": getattr(analysis, "yongsin", None) and str(analysis.yongsin),
        "compact": _build_compact(name, saju, counts),
    }

    if target_year:
        try:
            target_year = int(target_year)
            year_moment = datetime(target_year, 7, 1, 12, 0)
            year_saju = Saju.from_birth(
                kst_moment=year_moment,
                solar_terms=_solar_terms,
                longitude=longitude,
                yaja_si_separated=bool(yaja_si_separated),
            )
            result["target_year"] = {
                "year": target_year,
                "year_pillar": _pillar_dict(year_saju.year_pillar),
            }
        except Exception as e:
            result["target_year_error"] = str(e)

    return jsonify(result)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
