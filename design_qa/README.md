# Palja 디자인 QA 자료 (2026-09-28)

이 폴더는 ChatGPT가 Palja의 실제 구현 결과물을 시각적으로 검토할 수 있도록
준비한 자료다. 디자인/코드는 수정하지 않았고, 실제 화면/PDF를 그대로 캡처·렌더링했다.

## 랜딩페이지 캡처 (production, 실제 브라우저 렌더링)

| 파일 | 내용 |
|---|---|
| `landing_01_hero.jpg` | Hero 영역 (헤드라인 + 무료 프로필 신청 폼 전체) |
| `landing_02_how_it_works_and_preview_intro.jpg` | "So funktioniert's" 하단 + "Ein Blick hinein" 도입부 |
| `landing_03_preview_pdf_sample.jpg` | "Ein Blick hinein"의 PDF 미리보기 이미지 + 캡션 |
| `landing_04_products_free_and_paid.jpg` | 상품 섹션: Kostenloses Profil(0€) + Jahresreport(9,90€) 카드 |
| `landing_05_products_premium_and_table.jpg` | Premium-Lebenskarte(24,90€) 카드 + 비교표 시작 |
| `landing_06_products_table_full.jpg` | 상품 비교표(Inhalt/Kostenlos/Jahresreport) |
| `landing_07_kompatibilitaet.jpg` | "Wie gut passt du..." 궁합 섹션 헤드라인 + 입력 폼 |
| `landing_08_footer.jpg` | 궁합 폼 하단 + Footer(PALJA 로고, 법적 고지, Impressum/Datenschutz/AGB/Widerruf 링크) |

## PDF 렌더링

`palja_test_report.pdf` — 실제 production 렌더링 함수(`build_pdf`,
`_report_text_to_flowables`, `_build_daewoon_timeline_drawing`,
`_draw_branded_footer`)를 그대로 호출해서 생성. AI 생성/이메일 발송/결제는
전혀 실행하지 않았고, 본문 텍스트만 형식(##/-/>)이 동일한 예시 텍스트로
대체했다 — **디자인/레이아웃은 실제 고객이 받는 PDF와 동일**하다.

| 파일 | 내용 |
|---|---|
| `pdf_01_cover_and_toc_and_lifeline.png` | 표지 + Lebenslinie(대운 타임라인 그래픽) + 목차(Inhalt) — 현재 레이아웃에서는 세 요소가 한 페이지에 같이 나온다 |
| `pdf_02_first_chapter_and_quote.png` | 첫 번째 챕터(Einleitung) + pull quote 예시 |
| `pdf_03_body_monthly.png` | 일반 본문/월별 챕터 페이지 |
| `pdf_04_monthly_and_quote.png` | 월별 챕터 + pull quote 예시 |
| `pdf_05_last_page.png` | 마지막 페이지(Daewoon 설명 + 맺음말) |
| `pdf_contact_sheet.png` | 전체 6페이지를 한 장에 모은 contact sheet (3x2 그리드) |

페이지 번호는 모든 페이지 하단에 "PALJA · 제목 / 숫자" 형식으로 이미 표시되어 있다(표지 제외).

## 텍스트 참고 자료

- **Landing page URL**: https://palja-api.onrender.com/ (production, 실제 배포본)
- **PDF 생성 명령**: `python3 gen_test_pdf.py` (스크립트는 `run_calculation()` → `compute_daewoon_facts()` → `build_pdf()` 순서로 기존 함수만 호출; 본문 텍스트는 예시 데이터)
- **생성된 테스트 PDF 위치**: `/home/claude/saju-api/design_qa/palja_test_report.pdf`
- **랜딩페이지 섹션 순서**: Hero(무료 신청 폼) → So funktioniert's(3단계) → Ein Blick hinein(PDF 미리보기) → Wie viel möchtest du über dich erfahren?(Kostenlos/Jahresreport/Premium-Lebenskarte 상품 카드 + 비교표) → Wie gut passt du mit jemand anderem zusammen?(궁합 폼) → Footer
- **주요 폰트**: 제목/헤딩 — `Fraunces`(serif), 본문 — `Work Sans`(sans-serif). PDF도 동일 계열(Fraunces 임베드 / WorkSans 임베드) 사용
- **주요 색상**: 배경 크림 `#FAF7F1`/`#F3EEE4`, 텍스트 다크 브라운 `#211D1A`/`#3B3630`, 포인트(테라코타) `#C1442E`, 그린(관계운 축) `#2F6F4E`, 골드(직업운 축) `#D4A017`, 뉴트럴 브라운(총운 축) `#8A6F5C`
