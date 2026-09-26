# Palja 프로젝트 진행 상황 (최신 업데이트: 2026-09-27)

> 다음 세션에서 이어서 작업할 때 이 파일부터 읽을 것. 사용자는 "이제 너가 나를
> 리드해줘"라고 지시했으므로, 질문으로 막히지 말고 아래 "다음 할 일"부터 스스로
> 판단해서 진행할 것.

## 한 줄 요약

한국 사주(BaZi) 스타일 리포트를 독일 소비자에게 이메일/PDF로 파는 서비스.
무료(가입만) → 유료 9.90€(Jahresreport) → 프리미엄 24.90€(Lebenskarte) 구조.
백엔드는 `saju-api` (Flask, Render 배포), 결제는 Paddle Billing.

## 배포/인프라

- **저장소**: https://github.com/dionnie373-star/saju-api (main 브랜치, 로컬 경로 `/home/claude/saju-api`)
- **호스팅**: Render (`palja-api`, service id `srv-darsrgvavr4c7382bkqg`), 무료 플랜
  - URL: https://palja-api.onrender.com
  - Start Command: `gunicorn app:app --timeout 150` (⚠️ 기본값 `gunicorn app:app`으로
    되돌리면 AI 리포트 생성(30~90초 걸림) 도중 30초 기본 타임아웃에 워커가
    죽어서 결제 웹훅이 500 에러남 — 절대 --timeout 빼지 말 것)
  - 환경변수: `ANTHROPIC_API_KEY`, `BREVO_API_KEY`, `FROM_EMAIL`, `FROM_NAME`,
    `WEBHOOK_SECRET`, `PADDLE_WEBHOOK_SECRET` 등 (`.env.example` 참고)
- **이메일**: Brevo (transactional API 사용, SMTP 아님)
- **결제**: Paddle Billing — **현재 샌드박스(sandbox) 모드만 연동됨. 라이브 아님.**

## 결제(Paddle) 연동 상세 — 지금까지 한 것

1. Paddle 샌드박스 대시보드에서 상품 2개 생성 완료:
   - Jahresreport (paid) — `pri_01m3f98f0s27hjx0xy4bc9em4d` — EUR 9.90
   - Lebenskarte (premium) — `pri_01m3f9bjxx7sgpr1wvm5g8k61r` — EUR 24.90
2. Paddle 웹훅 destination 생성, `transaction.completed` 이벤트 구독,
   URL: `https://palja-api.onrender.com/webhooks/paddle`
   시크릿 키는 Render 환경변수 `PADDLE_WEBHOOK_SECRET`에 저장됨.
3. `app.py`의 `/webhooks/paddle` 라우트: Paddle-Signature 헤더 HMAC 검증 →
   price_id로 paid/premium 판별 → customData(생년월일시/이메일/성별)로 사주 계산 →
   `report_pipeline.run_paid_signup`/`run_premium_signup` 호출.
4. **중복 방지(idempotency) 로직 있음**: Paddle이 응답 느리면 같은 결제 건을
   여러 번 재전송하는데, 트랜잭션 ID(`data.id`) 기준으로 이미 처리한 건 조용히
   "duplicate" 200 응답만 주고 리포트/이메일을 다시 만들지 않음. (실패한 시도는
   재시도 가능하도록 목록에서 다시 제거됨.)
5. 랜딩페이지(`static_site/index.html`)에 Paddle Checkout 버튼 2개(유료/프리미엄)
   붙임 — Paddle.js 샌드박스 클라이언트 토큰: `test_13d5f1ab829b75084a15dc9341e`
   (라이브 전환 시 이 토큰과 `Paddle.Environment.set('sandbox')`를 바꿔야 함)
6. **실제 샌드박스 결제로 end-to-end 테스트 완료** (2026-09-27):
   - 유료(9.90€) 결제 → 웹훅 200 → PDF 리포트 실제 수신 확인 (dionnie373@gmail.com)
   - 프리미엄(24.90€) 결제 → 웹훅 200 → PDF 리포트 실제 수신 확인
   - 두 경우 다 Paddle이 웹훅을 2~3번 재전송했지만 중복 방지 로직 덕분에
     이메일은 각각 1통씩만 발송됨 (재시도는 즉시 "duplicate" 응답으로 처리됨)

### 이번 세션에서 고친 버그 3개

1. Paddle 샌드박스 계정에 "기본 결제 링크(Default payment link)" 도메인이
   설정 안 되어 있어서 체크아웃 자체가 안 열렸음 → `palja-api.onrender.com`
   도메인 승인 요청 + 결제 설정에서 기본값으로 지정해서 해결.
2. Render Start Command에 `--timeout` 옵션이 없어서 gunicorn 기본 30초
   타임아웃으로 리포트 생성 중 워커가 죽어 500 에러 발생 → `--timeout 150`
   으로 고쳐서 해결.
3. 위 타임아웃 버그의 부작용으로 Paddle이 웹훅을 재전송하면서 같은 리포트가
   여러 번(최대 3번) 생성/발송되던 문제 → 트랜잭션 ID 기반 중복 방지 로직 추가.

## 안 한 것 / 다음 할 일 (우선순위 순 아님, 사용자 지시에 따라 선택)

1. **샌드박스 → 라이브 모드 전환** (실제 손님 결제를 받으려면 필수)
   - 라이브 API 키, 라이브 Client-side 토큰 발급
   - 라이브 상품/가격 다시 생성 (샌드박스 ID는 라이브에서 안 씀)
   - 라이브 웹훅 destination + 시크릿 키 다시 설정 → Render
     `PADDLE_WEBHOOK_SECRET` 갱신
   - `static_site/index.html`의 `PADDLE_CLIENT_TOKEN`, `PADDLE_PRICE_IDS`,
     `Paddle.Environment.set('sandbox')` → 라이브 값으로 교체
   - 아직 사용자가 명시적으로 "지금 하자"고 한 적 없음 — 시작 전에 확인할 것
2. **전체 비주얼 디자인 리뉴얼** (2026-09-27 사용자 피드백, "나중에 하자"고 함):
   - 현재 베이지/크림 톤이 너무 많아서 별로라는 피드백. 히어로 섹션(밤하늘/
     한옥/선비 실루엣)만 동양적이고 나머지 섹션(가격표, 비교표, 푸터)은
     단조로운 베이지 단색이라 톤이 깨짐.
   - 요청: 좀 더 동양적인(한국적인) 느낌이 전체적으로 들어갔으면 함.
   - 색 팔레트, 배경 문양/패턴, 섹션 디바이더 등 재검토 필요. 아직 시작 안 함.
3. **법적 문서** (Impressum/AGB/Datenschutzerklärung/Widerrufsbelehrung) —
   푸터에 텍스트만 있고 실제 내용/링크 없음. 독일 소비자 대상 실서비스 오픈
   전 필수. "맨 마지막에 하자"는 기존 지시 있음.
4. **palja.de 도메인 구매 + 인증** — `FROM_EMAIL` 발신 주소, Brevo 도메인 인증에
   필요. 아직 시작 안 함.
5. 모바일 반응형: 이번 세션에서 가격 비교표 모바일 패딩 축소로 개선함
   (`0fea5b5`). 페이지 전체 가로 스크롤/깨짐은 없음(직접 측정 확인).

## 작업 방식 관련 메모

- 사용자는 Paddle/Render 계정 로그인을 직접 함 (보안상 Claude가 비밀번호
  입력 못 함) — 브라우저 탭이 로그인된 상태로 남아있으면 재사용 가능.
- Paddle Claude Code 플러그인(MCP 서버)은 이 세션들에서 한 번도 tool로
  안 떴음 — 결국 브라우저 자동화(`Claude_Browser__*`)로 Paddle 대시보드를
  직접 조작해서 설정함. 새 세션에서 플러그인 MCP가 뜨면 그쪽이 더 편할 수 있음.
- 결제 테스트는 전부 Paddle **샌드박스**였고 실제 돈은 전혀 오가지 않음.
