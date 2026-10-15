# 운영 런북 (최신: 2026-10-16)

> 예전 Paddle 기반 런북은 폐기됐다. 결제는 Digistore24, 서버는 Render.

## 서버
- Render 서비스 `palja-api`, main 푸시 → 자동 배포. 배포 중에는 몇 분간 재시작된다.
- **Start Command는 `gunicorn app:app --workers 1 --threads 8 --timeout 300`.**
  `--timeout`과 `--threads`는 빠지면 안 된다(유료 리포트 생성이 수 분, 무료 가입은 동기 호출).
  Procfile은 Render가 무시한다. 설정 변경은 Render 대시보드 Settings > Deploy.
- 필수 환경변수: ANTHROPIC_API_KEY, DATABASE_URL, Brevo 키, Digistore24 IPN passphrase,
  ADMIN_TEST_TOKEN(20자 이상, /admin/test-report용).

## 배포 후 확인 (2분)
1. palja.de / .fr / .es 가 열리는지.
2. Render Logs(최근 1시간)에서 `[claim]`, `[recovery]`, `[fulfill 실패]` 검색.
3. 가급적 트래픽이 적은 시간(한국 오전)에 배포. 푸시하면 생성 중이던 주문이 끊길 수 있으나
   12분 뒤 자동 복구가 재시도한다.

## 결제 문제 대응
- 운영자 메일(제목 `[Palja]`)이 오면: 
  - "리포트 생성 실패": 자동 복구가 2회까지 재시도. 그래도 실패하면 "자동 복구 포기" 메일이 온다 →
    Digistore24 주문 확인 후 `/admin/test-report`로 수동 발송하거나 고객에게 직접 안내.
  - "결제 알림 거부": Digistore24 IPN 설정(passphrase)과 상품 ID 매핑 확인.
- 환불은 Digistore24가 처리(60일 보증). 사이트/이메일에 철회권 포기 문구를 넣지 않는다.

## FR/ES 프리미엄 버튼 (승인 대기 중)
- Digistore24에서 746480(FR), 746751(ES) 승인되면 사이트 버튼을 복구한다.
  절차는 PROJECT_STATUS.md의 FR/ES 섹션 참고.

## 하지 않는 것
- 결제/카드/비밀번호/신분증 입력, 고객 대신 메일 발송, 공개 게시는 사장님 승인 없이 하지 않는다.
