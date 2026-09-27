# saju-api

## 테스트

의존성 설치 없이 표준 라이브러리 `unittest`만으로 돌아간다 (Anthropic/Brevo/Paddle에
실제로 접속하지 않음 — 웹훅 핸들러의 `run_*_signup` 호출은 monkeypatch로 가짜 함수로
교체해서 라우팅/검증 로직만 검증한다):

```bash
python3 -m unittest discover tests -v
```

`COMPATIBILITY_PADDLE_PRICE_ID` 환경변수가 없으면 궁합 관련 테스트 2개는 skip된다
(로컬에선 정상, Render에는 설정돼 있음).
