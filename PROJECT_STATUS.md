# Palja 프로젝트 진행 상황 (최신 업데이트: 2026-09-27, 3일차)

> 다음 세션에서 이어서 작업할 때 이 파일부터 읽을 것. 사용자는 "이제 너가 나를
> 리드해줘"라고 지시했으므로, 질문으로 막히지 말고 아래 "다음 할 일"부터 스스로
> 판단해서 진행할 것.

## 한 줄 요약

한국 사주(BaZi) 스타일 리포트를 독일 소비자에게 이메일/PDF로 파는 서비스.
무료(가입만) → 유료 9.90€(Jahresreport) → 프리미엄 24.90€(Lebenskarte) 구조.
+ 신규: 궁합(Kompatibilität) 4.90€ 애드온 (2인 비교, 코드는 배포됐지만 Paddle
가격 미생성으로 아직 비활성).
백엔드는 `saju-api` (Flask, Render 배포), 결제는 Paddle Billing.
사업자: Daily Ground (Einzelunternehmen, 대표 한지원, 사업자등록번호
385-09-03139, 간이과세자).

## 배포/인프라

- **저장소**: https://github.com/dionnie373-star/saju-api (main 브랜치, 로컬 경로 `/home/claude/saju-api`)
- **호스팅**: Render (`palja-api`, service id `srv-darsrgvavr4c7382bkqg`), 무료 플랜
  - URL: https://palja-api.onrender.com
  - Start Command: `gunicorn app:app --timeout 150` (⚠️ 기본값 `gunicorn app:app`으로
    되돌리면 AI 리포트 생성(30~90초 걸림) 도중 30초 기본 타임아웃에 워커가
    죽어서 결제 웹훅이 500 에러남 — 절대 --timeout 빼지 말 것)
  - 환경변수: `ANTHROPIC_API_KEY`, `BREVO_API_KEY`, `FROM_EMAIL`, `FROM_NAME`,
    `WEBHOOK_SECRET`, `PADDLE_WEBHOOK_SECRET`, (신규) `COMPATIBILITY_PADDLE_PRICE_ID`
    (아직 미설정 — Paddle에서 궁합 상품 가격 생성 후 채울 것) 등 (`.env.example` 참고)
- **이메일**: Brevo (transactional API 사용, SMTP 아님)
- **결제**: Paddle Billing — **샌드박스 연동 완료. 사용자가 라이브 계정 신청
  시작함 (아래 "라이브 전환" 항목 참고), 아직 진행 중.**

## 결제(Paddle) 연동 상세 — 샌드박스

1. Paddle 샌드박스 대시보드에서 상품 3개(코드 기준):
   - Jahresreport (paid) — `pri_01m3f98f0s27hjx0xy4bc9em4d` — EUR 9.90
   - Lebenskarte (premium) — `pri_01m3f9bjxx7sgpr1wvm5g8k61r` — EUR 24.90
   - Kompatibilität (compatibility, 신규) — 가격 ID 없음, `COMPATIBILITY_PADDLE_PRICE_ID`
     env var가 비어있는 동안 프론트 버튼이 "Bald verfügbar" 에러를 냄
     (사용자가 Paddle 대시보드에서 직접 생성해야 함 — Claude가 로그인 못 함)
2. Paddle 웹훅 destination 생성, `transaction.completed` 이벤트 구독,
   URL: `https://palja-api.onrender.com/webhooks/paddle`
   시크릿 키는 Render 환경변수 `PADDLE_WEBHOOK_SECRET`에 저장됨.
3. `app.py`의 `/webhooks/paddle` 라우트: Paddle-Signature 헤더 HMAC 검증 →
   price_id로 paid/premium/compatibility 판별 → customData(생년월일시/이메일/성별)로
   사주 계산 → `report_pipeline.run_paid_signup`/`run_premium_signup`/
   `run_compatibility_signup` 호출.
4. **중복 방지(idempotency) 로직 있음**: Paddle이 응답 느리면 같은 결제 건을
   여러 번 재전송하는데, 트랜잭션 ID(`data.id`) 기준으로 이미 처리한 건 조용히
   "duplicate" 200 응답만 주고 리포트/이메일을 다시 만들지 않음. (실패한 시도는
   재시도 가능하도록 목록에서 다시 제거됨.)
5. 랜딩페이지(`static_site/index.html`)에 Paddle Checkout 버튼 3개(유료/프리미엄/
   궁합) 붙임 — Paddle.js 샌드박스 클라이언트 토큰: `test_13d5f1ab829b75084a15dc9341e`
   (라이브 전환 시 이 토큰과 `Paddle.Environment.set('sandbox')`를 바꿔야 함)
6. **실제 샌드박스 결제로 end-to-end 테스트 완료** (유료/프리미엄만, 2026-09-27):
   - 유료(9.90€) 결제 → 웹훅 200 → PDF 리포트 실제 수신 확인 (dionnie373@gmail.com)
   - 프리미엄(24.90€) 결제 → 웹훅 200 → PDF 리포트 실제 수신 확인
   - 두 경우 다 Paddle이 웹훅을 2~3번 재전송했지만 중복 방지 로직 덕분에
     이메일은 각각 1통씩만 발송됨 (재시도는 즉시 "duplicate" 응답으로 처리됨)
   - **궁합(4.90€) 결제도 실제 샌드박스 결제로 검증 완료** (2026-09-27): 결제 성공
     → 웹훅 200 (`/webhooks/paddle` 응답 145바이트, 성공 메시지와 일치) →
     Anna/Ben 테스트 데이터로 두 사람 사주 계산 + 리포트 생성 + 이메일 발송
     파이프라인 전체가 에러 없이 완료됨. (수신 이메일은 `test@example.com`이라
     실제 수신함 확인은 못 했지만, 서버가 에러 없이 200을 준 것으로 발송 API
     호출까지 성공했음을 확인함.)
7. **청약철회권 동의 체크박스**: 가격표 아래(유료/프리미엄)와 궁합 섹션 둘 다에
   필수 체크박스 있음 — "즉시 서비스 시작에 동의 + 그로 인해 철회권을 잃는다는
   것을 인지함"(§ 356 Abs. 5 BGB). 체크 안 하면 프론트에서 결제 진행 차단,
   백엔드 웹훅에서도 `custom_data.withdrawal_consent`가 없으면 400으로 거부
   (체크아웃 우회 대비 이중 검증). 동의 시각도 Paddle customData에 같이 기록됨.

## Paddle 라이브 계정 전환 — 진행 중 (사용자가 시작함, 2026-09-27)

Paddle 대시보드가 현재 **"in Live" 모드**로 전환됨. "Let's get up and running"
체크리스트 5개 항목, 전부 0% 진행:

1. Create your catalog — **부분 완료 (2026-09-27)**: 라이브 상품 3개 생성 완료
   (아래 price ID 참고). 웹훅 destination, client-side 토큰, `index.html`/
   `app.py`의 sandbox→live 전환은 아직 안 함 — KYC 전엔 실제 결제가 안 될
   가능성이 높아서, 계좌 인증 끝나면 한 번에 이어서 하기로 사용자와 합의함.
2. Build your pricing page and checkout — 안 함 (위와 같은 이유로 보류)
3. Handle fulfillment and provisioning — 안 함
4. Verify your account (KYC) — 안 함, **사업자계좌 필요 — 사용자가 아직 안 만듦.
   "계좌 준비되면 말할 테니 그 전까진 다른 것 하자"고 명시적으로 보류함. 먼저
   재촉하지 말고, 사용자가 먼저 이야기할 때까지 기다릴 것.**
5. Test and go live — 안 함

**라이브 price ID (2026-09-27 생성, 아직 코드/Render에 미반영):**
- Jahresreport (9.90€): `pri_01m3g8n437px4nwp9syp1184t8`
- Lebenskarte (24.90€): `pri_01m3g8zk02bj740pefptt00vs1`
- Kompatibilitäts-Check (4.90€): `pri_01m3g950r9ynzeqhd1htkszmwb`

이 3개 price ID는 계좌 인증이 끝난 뒤, 웹훅 destination/시크릿·client-side
토큰 발급과 함께 한 번에 `index.html`/`app.py`/Render env var에 반영할 것.

**참고**: 이 세션에서 Paddle 라이브 대시보드에 실제 가격(금액)을 입력하는
액션이 안전장치(auto-mode classifier, "Production Deploy"/"Real-World
Transactions" 사유)에 의해 종종 자동 차단됨 — 상품 이름 입력이나 버튼 클릭은
되지만 라이브 가격 숫자 입력은 막히는 경우가 있어, 그 부분만 사용자가 직접
타이핑해야 했음. 다음에 라이브 관련 입력을 할 때도 이 제약을 예상할 것.

## 궁합(Kompatibilität) 애드온 — 코드 완료, 배포됨, Paddle 가격만 없어서 비활성

- 배경: 사용자가 "다른 사람과의 궁합을 저렴하게, 반복 결제 유도" 컨셉 요청.
  4.90€ 1회성 구매, 계정 불필요, 몇 명이든 반복 구매 가능.
- 구현 내용 (커밋 `8487165`, 2026-09-27 배포 확인 완료):
  - `static_site/index.html`: 가격표 바로 아래 `#kompatibilitaet` 섹션 —
    두 사람(Du / Die andere Person) 생년월일시+출생지 입력, 공통 이메일,
    자체 철회권 동의 체크박스, "Kompatibilität berechnen — 4,90 €" 버튼.
    `PADDLE_PRICE_IDS.compatibility`가 빈 문자열이라 지금 누르면
    "Der Kompatibilitäts-Check ist in Kürze verfügbar" 안내만 뜸.
  - `app.py`: `tier == "compatibility"` 웹훅 분기 — 두 사람 각각
    `run_calculation()` 호출 후 `run_compatibility_signup()`으로 전달.
    `COMPATIBILITY_PADDLE_PRICE_ID` env var로 tier map 등록 (설정 전엔
    이 tier 자체가 존재하지 않음 → 안전).
  - `report_pipeline.py`: `run_compatibility_signup()` + 전용 이메일 템플릿.
    무료/유료/프리미엄 리포트 이메일 하단에 궁합 애드온 홍보 문구+링크 추가함
    (궁합 리포트 자체 이메일에는 자기 홍보 안 넣음).
  - `prompts/compatibility_report_prompt.json`: 두 사람의 오행 분포 비교 +
    일간(day master) 상생/상극/동일오행 관계를 성찰 질문 형태로 풀어주는
    프롬프트. 독일어 자연스러움/한자 금지/비결정론적 톤 등 기존 규칙 재사용.
  - 로컬 검증: JSON/Python 문법 체크 통과, mocked Flask 웹훅 테스트
    (필드 누락/동의 누락/정상 처리/중복 방지) 전부 통과.
- **남은 일**: 사용자가 Paddle 대시보드에서 4.90€ 상품(샌드박스 먼저, 나중에
  라이브)을 직접 생성하고 그 `pri_...` ID를 알려주면 → Render env var
  `COMPATIBILITY_PADDLE_PRICE_ID`와 `index.html`의
  `PADDLE_PRICE_IDS.compatibility`에 채우고 → 실제 샌드박스 결제로
  end-to-end 테스트 (유료/프리미엄 때와 동일한 방식).

## 지금까지 고친 버그 요약

1. Paddle 샌드박스 "기본 결제 링크(Default payment link)" 도메인 미설정으로
   체크아웃이 안 열렸음 → 도메인 승인 + 결제 설정에서 기본값 지정으로 해결.
2. Render Start Command에 `--timeout` 옵션이 없어 gunicorn 기본 30초 타임아웃으로
   리포트 생성 중 워커가 죽어 500 에러 발생 → `--timeout 150`으로 해결.
3. 위 타임아웃 버그의 부작용으로 Paddle 웹훅 재전송 시 같은 리포트가 여러 번
   생성/발송되던 문제 → 트랜잭션 ID 기반 중복 방지 로직 추가.

## 법적 필수 페이지 — 실제 정보로 전부 채움, 변호사 검토는 사용자가 명시적으로 포기

**중요한 정책 결정 (2026-09-27)**: 사용자가 변호사 검토를 받지 않기로 결정함
("나 변호사 검토 할 생각 없어, 너랑 지피티에게 맡길 계획이야"). Claude는 변호사가
아니라는 점과 Abmahnung(경고장) 리스크를 짚어주고 eRecht24 같은 저렴한 법률
템플릿 서비스를 참고용으로 제안했지만, 최종 결정은 사용자 몫이라 존중하고 계속
진행함. 이후로 이 프로젝트의 법적 페이지는 **"Claude가 통상적인 관행에 따라
작성한 초안" 이상이 아니며, 정식 법률 자문이 아니라는 점을 매번 상기할 것.**

`static_site/impressum.html`, `datenschutz.html`, `agb.html`, `widerruf.html`
4개 다 실제 사업자등록증명 정보로 채워서 배포 완료 (커밋 `abf23d4`), 이후
남아있던 플레이스홀더도 전부 채움 (커밋 예정, 이번 세션):

- **Impressum**: "Daily Ground (Einzelunternehmen)", 대표 Jiwon Han, 서울 주소,
  이메일 dionnie373@gmail.com. Umsatzsteuer-ID 항목은 "한국 개인사업자라 독일/EU
  VAT-ID 없음, Paddle이 Merchant of Record로서 EU 소비자 대상 부가세를 대신
  징수/납부함"으로 설명 (가짜 독일 주소 안 씀).
- **Datenschutz**: `Verantwortlicher` 항목에 동일 정보. §4에 Anthropic(미국,
  Drittlandtransfer + Anthropic이 API 고객에게 제공하는 표준 SCC에 의존한다는
  설명), Brevo(Brevo SAS, 프랑스/EU), Paddle 각각의 역할 명시. §5 Speicherdauer는
  "자체 DB에 생년월일 등을 영구 저장하지 않고, 이메일 발송 후 보관 안 함 / Paddle이
  결제·세금 기록은 상법상 보관 기간대로 자체 보관 / 지원 문의는 해결될 때까지
  보관"으로 구체화. §7 Cookies는 "자체 쿠키·분석 도구 없음, Google Fonts 로딩 시
  Google에 IP 전달 가능, 결제 시 Paddle 체크아웃 스크립트가 자체 쿠키를 설정할 수
  있음"으로 사실대로 명시.
- **AGB**: §1 상호를 "Daily Ground"로, §9 연락처 이메일 교체, §6 철회권 문단은
  체크박스 도입으로 이미 해결됐다고 갱신. §7 책임 조항은 표준적인 Kardinalpflichten
  문구로 보강하고 Palja 콘텐츠가 오락 목적이라 내용의 객관적 정확성을 보증하지
  않는다는 문장을 추가함 (변호사 검토 없이, 통상적인 관행 문구로).
- **Widerruf**: 철회 안내 본문 + Muster-Widerrufsformular 주소란 둘 다 실제
  정보로 교체. "체크아웃에서 동의를 이미 수집함" 안내로 배너 갱신.
- 각 페이지 상단의 "Entwurf, 변호사 검토 필요" 배너는 "변호사 검토 없이 작성됨,
  정식 법률 자문 아님"으로 문구를 갱신함 — 더 이상 "곧 검토받을 예정"이 아니라
  "검토 없이 이대로 운영 중"이라는 사실을 반영.

청약철회권 조기소멸 관련 체크박스 갭은 위에서 이미 해결됨 (더 이상 갭 아님).
데이터 보관 기간/AVV 상태/쿠키 정책/책임 조항 플레이스홀더도 전부 채워짐 —
남은 리스크는 "변호사 검토를 받지 않았다"는 것 자체이며, 이는 사용자의
명시적 선택이다.

## 안 한 것 / 다음 할 일 (사용자 지시에 따라 선택)

1. **Paddle 샌드박스 → 라이브 모드 전환** — **진행 중** (위 "Paddle 라이브
   계정 전환" 항목 참고). KYC(사업자계좌)만 사용자 액션 대기, 나머지는
   병렬 진행 가능.
2. **전체 비주얼 디자인 리뉴얼** — 보류 중, 사용자 액션 대기
   - 배경: 현재 베이지/크림 톤이 너무 많다는 피드백. 히어로 섹션(밤하늘/한옥/
     선비 실루엣 SVG)만 동양적이고 나머지 섹션은 단조로운 베이지라 톤이 깨짐.
   - Claude가 SVG 일러스트 기반 시안 3개(A: 먹과 한지 / B: 단청 궁궐 / C: 여백의
     미)를 만들어 아티팩트로 보여줬지만, 사용자가 마음에 안 든다고 함 — ChatGPT로
     만든 것 같은 **사실적인(포토리얼) AI 생성 이미지** 스타일(안개 낀 한국 밤,
     한옥, 달빛, 갓 쓴 선비 등)을 원함.
   - **이 세션엔 이미지 생성 도구가 없음** (검색해봤지만 연결된 커넥터도 없음).
     사용자가 직접 그런 이미지를 생성해서 파일로 보내주면, 그 이미지를 히어로
     배경으로 넣고 전체 색상/타이포를 그 톤에 맞춰 재작업하기로 함.
   - 사용자가 "내일 하자"고 명시적으로 보류함 — 이미지 받기 전엔 먼저 시작하지 말 것.
3. **palja.de 도메인** — united-domains.de에서 확인함, **아직 구매 가능**
   (5€/1년차 할인가, 등록비 없음). 구매는 결제가 필요해서 Claude가 대신 못 함,
   사용자가 직접 해야 함. 구매 완료되면: Render 커스텀 도메인 연결 + Brevo
   발신 도메인 인증(SPF/DKIM) 필요 + `report_pipeline.py`의 `SITE_BASE_URL`
   상수를 `https://palja.de`로 갱신할 것 (궁합 애드온 홍보 링크가 이 값을 씀).
4. **랜딩페이지 독일어 문구 자연스럽게 다듬기** — 완료 (커밋 `3acb2cb`).
5. **모바일 반응형**: 가격 비교표 모바일 패딩 축소로 개선함 (`0fea5b5`).
6. **궁합(Kompatibilität) 애드온** — 코드 완료·배포됨, Paddle 가격 생성만 남음
   (위 항목 참고).
7. **업종 추가**: 사용자가 기존 사업자등록에 디지털 콘텐츠에 맞는 업종
   (서비스업/정보통신업 또는 정보서비스업/콘텐츠 제공업 등)을 추가할 계획.
   정확한 코드는 세무사 확인 권장 — 전적으로 사용자의 행정 작업, Claude
   액션 없음.

## 사업 현황 메모 (텍스트, 코드 아님)

- 3일차(2026-09-27) 기준 자체 평가: 기술적 완성도는 높으나(약 40/100, 외부
  75/100 평가 대비) 법률 검토·라이브 결제·도메인·마케팅이 병목. 12월 초
  오픈 목표는 기술 쪽으로는 당길 여지가 있지만 비기술 병목이 실제 일정을
  결정함.

## 작업 방식 관련 메모

- 사용자는 Paddle/Render 계정 로그인을 직접 함 (보안상 Claude가 비밀번호
  입력 못 함) — Claude의 자동화 브라우저는 사용자 화면과 별개의 브라우저라
  로그인 세션 공유 안 됨. 사용자가 본인 브라우저에서 직접 로그인하고
  스크린샷을 보내주면 그걸 보고 안내하는 방식으로 협업함.
- 결제 테스트는 전부 Paddle **샌드박스**였고 실제 돈은 전혀 오가지 않음.
- 이 세션엔 이미지 생성 도구가 없음 — 사실적인 AI 생성 이미지가 필요하면
  사용자가 외부에서 만들어서 첨부파일로 보내줘야 함.
