# Palja 라이브 배포 런북

> 목표: 사용자가 명시한 "2주 안에 배포" 데드라인. 병목은 Paddle 라이브 계정
> KYC 심사 기간이므로, 아래 순서대로 최대한 빨리 착수할 것. 계좌/도메인은
> 2026-09-28(내일) 사용자가 직접 진행 예정.

## 0. 지금 상태 (2026-09-27 기준)

- 코드/사이트/이메일/PDF: 라이브 전환 외에는 **전부 준비 완료** (샌드박스로
  end-to-end 검증됨, 테스트 31개 통과).
- 막고 있는 것: (1) Paddle 라이브 계정 KYC 승인 대기, (2) palja.de 도메인 미구매.
- 최소 조건: **KYC 승인 하나만 있으면** 그날 안에 라이브 결제 전환 가능.
  도메인은 없어도 palja-api.onrender.com으로 서비스 자체는 완전히 동작함.

## 1. 사용자가 직접 해야 하는 것 (Claude가 대신 못 함 — 결제/계정 인증 포함)

이 순서로, 최대한 이른 시각에 시작할 것 (심사 대기 시간이 제일 긴 병목):

1. **Paddle 라이브 계정 신청**
   - 사업자 계좌 정보 입력 + KYC 서류 제출 (사업자등록증명 385-09-03139 등)
   - 신청 즉시 접수되지만 심사에 수일 걸릴 수 있음 — 이걸 제일 먼저 할 것
2. **palja.de 도메인 구매** (united-domains.de, ~5€/1년차)
   - 구매만 사용자가 하면 됨. 구매 후 "네임서버/DNS 관리" 화면 링크나 로그인
     정보를 알려주면, DNS 레코드 추가는 Claude가 안내하거나 직접 처리 가능한
     범위에서 도와줄 수 있음 (단, 도메인 등록업체 계정 로그인 자체는 안 함 —
     사용자가 화면 보고 값 입력, Claude는 정확히 뭘 입력해야 하는지 알려줌)
3. (선택, 급하지 않음) 사업자등록에 디지털 콘텐츠 업종 추가 — 세무사 확인 권장

## 2. Paddle KYC 승인 나는 즉시 Claude가 처리할 것

1. **라이브 상품/가격 3종 생성** (Paddle 대시보드, live 모드)
   - Jahresreport — EUR 9.90 (샌드박스 `pri_01m3f98f0s27hjx0xy4bc9em4d`와 동일 스펙)
   - Premium-Lebenskarte — EUR 24.90 (샌드박스 `pri_01m3f9bjxx7sgpr1wvm5g8k61r`)
   - Kompatibilitäts-Check — EUR 4.90 (샌드박스 `pri_01m3g7k8hqa7dggxxj8x5vnh1n`)
   - (`paddle:catalog-setup` 스킬로 MCP/Node SDK 시도, 안 되면 대시보드 수기 안내)
2. **라이브 웹훅 destination 등록**, `transaction.completed` 구독,
   URL은 그대로 `https://palja-api.onrender.com/webhooks/paddle`
   (도메인 연결 전이면 onrender.com URL 유지, 연결 후 palja.de로 바꿀 수도 있음
   — 웹훅 URL 자체는 Render가 서빙하는 한 어느 쪽이든 동작)
3. **Render 환경변수 교체** (live 값으로):
   - `PADDLE_WEBHOOK_SECRET` → 라이브 웹훅 시크릿
   - `COMPATIBILITY_PADDLE_PRICE_ID` → 라이브 price ID
4. **Render 환경변수 `ALLOWED_ORIGIN`을 실제 도메인으로 좁히기** — 지금은
   `*`(전체 허용)로 열려있음(app.py 주석에 이미 "실사용자 결제 전에 좁히는 걸
   권장"이라고 적어둠). palja.de가 붙기 전이면 `https://palja-api.onrender.com`으로,
   붙은 뒤엔 `https://palja.de`로 설정.
5. **`static_site/index.html`의 Paddle 클라이언트 스크립트 수정** (지금 TODO
   주석 표시돼 있음):
   - `PADDLE_CLIENT_TOKEN` → 라이브 토큰
   - `PADDLE_PRICE_IDS` (paid/premium/compatibility) → 라이브 price ID 3개
   - `Paddle.Environment.set('sandbox')` → 이 줄 제거 (라이브가 기본값)
6. **실제 라이브 결제 1건 직접 테스트** (사용자 본인 카드로 최소 금액,
   예: Kompatibilitäts-Check 4.90€) — 웹훅 200 확인 + 실제 이메일/PDF 수신
   확인까지 완료해야 "라이브 전환 완료"로 간주.
7. `PROJECT_STATUS.md`의 "Paddle 라이브 계정 전환" 섹션을 완료로 갱신.

## 3. palja.de 도메인 구매 후 Claude가 처리할 것 (KYC와 무관, 병행 가능)

1. Render 대시보드에 palja.de 커스텀 도메인 연결 (Render가 안내하는 CNAME/A
   레코드 값을 사용자에게 전달 → 사용자가 도메인 등록업체 DNS 설정에 입력)
2. Brevo 발신 도메인 인증 (SPF/DKIM 레코드도 같은 방식으로 DNS에 추가)
   — 이거 안 하면 이메일이 스팸함으로 갈 확률이 높아짐, 라이브 전환만큼 중요
3. 코드 내 TODO 3곳을 palja.de 기준으로 일괄 갱신:
   - `report_pipeline.py`의 `SITE_BASE_URL` 상수
   - `static_site/index.html`의 `og:url`/`og:image`
   - `static_site/robots.txt`, `static_site/sitemap.xml`의 URL
4. DNS 전파 대기(수 시간~하루) 후 https://palja.de 로 브라우저 재검증

## 4. 2주 데드라인 관점 타임라인 제안

- **Day 0 (내일, 9/28)**: KYC 신청 + 도메인 구매 동시 착수
- **Day 0~수일**: KYC 심사 대기 중에도 서비스는 지금 URL로 계속 운영 가능
  (완전히 막혀있는 상태 아님 — 이미 라이브 서비스 중, 궁합 등 실결제도 이미
  검증됨. "배포"가 새 결제 라인을 라이브로 튼다는 의미라면 이게 진짜 병목)
- **KYC 승인 당일**: 위 2번 항목 전부 그날 안에 끝낼 수 있음
- **도메인 DNS 전파 완료 시**: 위 3번 항목 처리, 최종 palja.de 라이브 확인

## 5. 주의사항 / 하지 말 것

- Claude는 Paddle/도메인 등록업체에 결제하거나 KYC 서류를 대신 제출하지 않음
  (금융/신원 인증 행위는 사용자 본인만 가능)
- 라이브 전환 시 샌드박스 값을 실수로 섞어 쓰지 않도록, 전환 커밋은 한 번에
  스크립트/체크리스트로 처리하고 곧바로 실결제 테스트로 검증할 것
- `gunicorn app:app --timeout 150`의 `--timeout 150`은 절대 빠지면 안 됨
  (AI 리포트 생성 30~90초 걸리는데 기본 30초 타임아웃이면 웹훅이 500남)
