# 출생 시각 처리 구조 (Time Handling)

**이 문서의 목적**: 이후 다른 기능을 추가하는 개발자가 아래 파이프라인을 잘못 건드리거나
"이중 보정"처럼 보이는 부분을 실수로 고치지 않도록, 현재 구조와 그 이유를 명확히 기록한다.

> 관련 코드: `app.py`의 `_lookup_location()` / `_to_kst_equivalent_moment()` / `run_calculation()`,
> `korean_saju/solar_time/solar_time_correction.py`, `korean_saju/saju/saju.py::Saju.from_birth()`.
> 관련 테스트: `tests/test_calculation.py`의 `TimezoneBugFixTests` (2026-09-28 시간대 버그
> 수정 및 2026-09-28 감사에서 고정된 regression 값들).

## 파이프라인 (5단계)

```
① 사용자 입력 (출생지 현지 civil time, naive)
        │  예: "1991-03-14 07:30", birth_city="Berlin"
        ▼
② IANA timezone 적용 → UTC 절대시각
        │  app.py: _lookup_location() 로 도시 -> IANA tz 이름(예: "Europe/Berlin")을 찾고,
        │  _to_kst_equivalent_moment() 1~2단계에서 zoneinfo.ZoneInfo(tz_name)로 aware
        │  datetime을 만든 뒤 .astimezone(UTC) → 절대시각(UTC instant).
        │  ※ 이 단계에서 서머타임(DST) 여부가 자동으로 반영된다 (아래 "DST" 절 참고).
        ▼
③ UTC + 9시간 = KST-equivalent moment (naive)
        │  app.py: _to_kst_equivalent_moment() 3단계.
        │  "이 절대 순간을 한국에서는 몇 시라고 부르는가"를 계산한 것일 뿐,
        │  아직 진태양시 보정은 전혀 들어가지 않은 순수한 시간대 표기 변환이다.
        ▼
④ korean_saju에 kst_moment로 전달 (app.py: Saju.from_birth(kst_moment=..., longitude=...))
        ▼
⑤ korean_saju 내부에서 longitude 기반 진태양시(AST) 보정 수행
        │  korean_saju/solar_time/solar_time_correction.py:
        │  ast = kst_moment + (longitude - 135.0) * 4분
        │  이 ast로 일주 날짜 경계(자시 판별)와 시주 지지를 결정한다.
        │  (korean_saju/saju/saju.py, hour_pillar.py)
```

## 핵심 불변식: 중복 보정 아님

②~③(시간대/DST 변환)과 ⑤(진태양시/경도 보정)은 **서로 다른 레이어에서 각각 정확히
한 번씩만** 적용된다. `app.py`는 진태양시 공식을 절대 복제하지 않고, `korean_saju`는
timezone/DST를 전혀 모른다 — 서로의 영역을 침범하지 않는다.

그런데 왜 "중복 보정처럼" 보일 수 있는가? `kst_moment = UTC_instant + 9h` 이고, 그 위에
`ast = kst_moment + (longitude-135)/15h`가 얹히므로, 대수적으로 정리하면:

```
ast = UTC_instant + 9h + (longitude - 135)/15h
    = UTC_instant + longitude/15h        (9h와 -135°/15h 항이 정확히 상쇄됨)
```

즉 결과적으로 `ast = UTC + longitude/15시간` — 이것이 바로 **보편적인 "지방 평균 태양시"
공식**이다. `korean_saju`의 `(경도-135°)×4분` 공식은 원래 "서울 기준 진태양시"를 위해
설계된 것이지만, 입력을 KST-equivalent로 먼저 환산해주기만 하면 **어느 나라 사용자든
그 나라 경도 기준의 올바른 진태양시가 자동으로 나온다** — 그래서 `korean_saju` 라이브러리
자체는 한 줄도 수정할 필요가 없었다.

**따라서**: ②~③ 단계를 없애거나 ⑤ 단계를 "중복이니 생략"하면 안 된다. 생략하면 다시
2026-09-27/28에 발견됐던 원래 버그(독일 등 해외 사용자의 시주가 항상 자시 근처로
잘못 나오는 문제)로 되돌아간다.

## DST(서머타임) 처리

DST는 **①→② 단계에서 `zoneinfo` + `tzdata`가 전적으로 처리**한다. 코드에 서머타임
시작/종료일을 하드코딩한 부분은 없다 — `ZoneInfo("Europe/Berlin")`이 해당 연도의
실제(역사적) 서머타임 여부를 자동으로 반영해서 올바른 UTC 오프셋(CET=+1 / CEST=+2)을
계산해준다. `requirements.txt`에 `tzdata`가 명시적으로 들어있는 이유도 이것 —
배포 환경에 OS 레벨 tzdata가 없어도 항상 정확히 동작하도록 보장하기 위함이다.

## 한국(Seoul) 사용자는 왜 안전한가

한국은 실제로 UTC+9(=KST)이고 서머타임도 쓰지 않으므로, `Asia/Seoul`에 대해
②~③ 단계는 **수학적으로 항등변환(no-op)**이다 — 즉 `kst_equivalent_moment ==
사용자가 입력한 원본 시각`. 이 때문에 한국 사용자에 대해서는 이번 timezone 수정
전후로 `korean_saju`에 전달되는 값이 100% 동일하며, 계산 결과(사주)도 전혀 바뀌지
않는다. 이는 `tests/test_calculation.py`의
`test_run_calculation_seoul_pillars_are_the_known_good_regression_values`로
고정되어 있다 — 이 테스트가 깨지면 한국 사용자 계산에 회귀가 생긴 것이다.

## 새 기능을 추가할 때 지켜야 할 것

- 새로운 국가/도시를 추가할 때는 `KNOWN_CITY_LONGITUDE`와 `KNOWN_CITY_TIMEZONE`에
  **반드시 함께** 항목을 추가해야 한다. 경도만 추가하고 시간대를 빠뜨리면
  `DEFAULT_TIMEZONE`("Europe/Berlin")으로 폴백되어 조용히 틀린 결과가 나온다.
- `korean_saju`에 넘기는 값은 항상 "KST-equivalent moment"여야 한다. 사용자의
  원본 현지 시각(`birth_local_dt`)을 실수로 그대로 넘기면 안 된다 — 단, 나이 계산
  (대운의 `current_age` 등)에는 반드시 `birth_local_dt`(현지 달력 날짜)를 써야
  한다. 이 둘을 혼동하면 자정 근처 출생자의 나이가 하루 어긋날 수 있다
  (`_compute_daewoon_forecast`의 `birth_local_date` 파라미터 참고).
- `korean_saju` 내부의 `SolarTimeCorrection` 공식이나 호출 위치를 건드리지 말 것 —
  위 "핵심 불변식" 절의 대수적 상쇄 관계가 깨진다.

## Regression 테스트 목록 (tests/test_calculation.py::TimezoneBugFixTests)

| 케이스 | 확인 내용 |
|---|---|
| Berlin 1991-03-14 07:30 | timezone/kst_equivalent + 4주 전체(年辛未/月辛卯/日癸未/時丙辰) 고정 |
| Berlin 겨울 (1991-01-14) vs 여름 (1991-07-14) | DST로 kst_equivalent와 시주가 서로 다르게 나옴을 end-to-end로 확인 |
| Berlin 자정 rollover (23:30 vs 다음날 00:30) | local/KST 날짜와 일주가 함께 논리적으로 넘어감, 둘 다 子時인 것은 정상 |
| Seoul 1991-03-14 07:30 | timezone 변환이 항등변환이며 4주 값이 기존과 동일(회귀 없음) |
| 도시→timezone 매핑 | 독일/오스트리아/스위스/한국 주요 도시가 올바른 IANA 이름으로 매핑됨 |
| 잘못된 timezone 문자열 | 예외로 죽지 않고 DEFAULT_TIMEZONE으로 안전하게 폴백 |
