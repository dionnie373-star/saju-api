"""PDF 리포트가 사이트 브랜드(Fraunces 세리프 헤딩 + Work Sans 산세리프 본문 +
테라코타 액센트)를 유지하는지, 마크다운 불릿/구분선이 제대로 변환되는지 확인.

배경: 처음엔 PDF가 전부 Helvetica(무채색 산세리프)로만 렌더링돼서 사이트
브랜드와 동떨어져 보였다 - reportlab 코어 폰트(Times-Bold/Times-Italic)로
"세리프 느낌"만 흉내 냈었음. 이후 챗지피티 디자인 리뷰에서 "웹사이트는
모던한 한국 웰니스 브랜드인데 PDF는 자동 생성된 문서처럼 보인다"는 지적을
받고(2026-09-27), 실제 웹사이트와 동일한 TTF 폰트(fonts/Fraunces-SemiBold.ttf,
fonts/WorkSans-*.ttf, 둘 다 OFL 라이선스)를 reportlab에 임베딩해서 웹↔PDF
폰트를 진짜로 통일했다. 이 테스트는 PDF를 픽셀 단위로 검사하진 않지만,
스타일 정의가 실수로 다시 코어 폰트(Helvetica/Times)로 되돌아가는 걸 막는다.

실행: cd /home/claude/saju-api && python3 -m unittest discover tests -v
"""
import os
import unittest

os.environ.setdefault("ANTHROPIC_API_KEY", "test-not-used")
os.environ.setdefault("BREVO_API_KEY", "test-not-used")
os.environ.setdefault("FROM_EMAIL", "test@example.com")
os.environ.setdefault("FROM_NAME", "Palja Test")

import report_pipeline as rp  # noqa: E402


class PdfStylingTests(unittest.TestCase):
    def test_title_and_headings_use_embedded_fraunces_not_core_font(self):
        self.assertEqual(rp._PDF_STYLES["title"].fontName, "Fraunces")
        self.assertEqual(rp._PDF_STYLES["subtitle"].fontName, "WorkSans-Italic")
        self.assertEqual(rp._PDF_STYLES["h2"].fontName, "Fraunces")

    def test_body_text_uses_embedded_work_sans_not_core_helvetica(self):
        # 세리프는 헤딩에만 — 본문까지 세리프로 바꾸면 긴 리포트는 오히려 읽기
        # 힘들어지므로, 사이트와 같은 세리프 헤딩 + 산세리프 본문 조합을 유지한다.
        self.assertEqual(rp._PDF_STYLES["body"].fontName, "WorkSans")

    def test_pdf_fonts_are_actually_registered_with_reportlab(self):
        # 스타일 딕셔너리에 폰트 "이름"만 맞아도, 실제로 reportlab에 등록이 안 돼
        # 있으면 렌더링 시점에 예외가 나거나 기본 폰트로 조용히 대체된다.
        from reportlab.pdfbase import pdfmetrics
        for font_name in ("Fraunces", "WorkSans", "WorkSans-Bold", "WorkSans-Italic", "WorkSans-BoldItalic"):
            self.assertIn(font_name, pdfmetrics.getRegisteredFontNames())

    def test_h2_rule_uses_brand_terracotta_color(self):
        self.assertEqual(rp._H2_RULE.color, "#C1442E")

    def test_dash_bullet_lines_become_real_bullets_not_literal_dashes(self):
        flowables = rp._report_text_to_flowables("- Erstes\n- Zweites")
        self.assertEqual(len(flowables), 2)
        for f in flowables:
            self.assertEqual(f.style.name, "PaljaBullet")
            # 텍스트 자체엔 더 이상 선행 "- "가 남아있으면 안 된다 (글머리 기호로
            # 대체됐으므로).
            self.assertFalse(f.text.startswith("- "))

    def test_heading_lines_are_followed_by_the_accent_rule(self):
        flowables = rp._report_text_to_flowables("## Ein Titel")
        self.assertEqual(len(flowables), 2)
        self.assertEqual(flowables[0].style.name, "PaljaH2")
        self.assertIs(flowables[1], rp._H2_RULE)

    def test_markdown_divider_becomes_a_rule_not_literal_dashes(self):
        # 실제 발견된 버그(2026-09-27): Claude가 챕터 구분에 마크다운 "---"를
        # 쓰는데, 예전엔 그게 그대로 평문 "---"로 PDF에 찍혔다.
        flowables = rp._report_text_to_flowables("Text davor\n---\nText danach")
        kinds = [type(f).__name__ for f in flowables]
        self.assertIn("HRFlowable", kinds)
        for f in flowables:
            if hasattr(f, "text"):
                self.assertNotIn("---", f.text)

    def test_blockquote_line_becomes_pull_quote_not_body_text(self):
        flowables = rp._report_text_to_flowables("> Ein wichtiger Satz.")
        self.assertEqual(len(flowables), 1)
        self.assertEqual(flowables[0].style.name, "PaljaPullQuote")
        self.assertNotIn(">", flowables[0].text)


class DaewoonTimelineDrawingTests(unittest.TestCase):
    """report_facts 기반 "Lebenslinie" 타임라인 그래픽이 죽지 않고 그려지는지 확인.

    실제 그림을 픽셀 단위로 검사하진 않지만, 실제 대운 데이터 구조로 호출했을 때
    예외 없이 Drawing을 반환하는지, 그리고 세그먼트/범례 개수가 데이터와
    맞는지는 확인한다.
    """

    def test_builds_drawing_with_one_segment_per_period_and_correct_axis_colors(self):
        from report_facts import compute_daewoon_facts

        daewoon = {
            "gender": "male",
            "forward": True,
            "current_age": 42,
            "entries": [
                {"index": 0, "start_age": 3, "end_age": 12, "start_year": 1987,
                 "pillar": {"cheon_gan_element": "목", "ji_ji_element": "수"}, "axis": "총운", "is_current": False},
                {"index": 1, "start_age": 13, "end_age": 22, "start_year": 1997,
                 "pillar": {"cheon_gan_element": "수", "ji_ji_element": "목"}, "axis": "재물운", "is_current": False},
                {"index": 2, "start_age": 23, "end_age": 32, "start_year": 2007,
                 "pillar": {"cheon_gan_element": "화", "ji_ji_element": "화"}, "axis": "직업운", "is_current": False},
                {"index": 3, "start_age": 33, "end_age": 42, "start_year": 2017,
                 "pillar": {"cheon_gan_element": "화", "ji_ji_element": "토"}, "axis": "재물운", "is_current": True},
            ],
        }
        facts = compute_daewoon_facts(daewoon)
        drawing = rp._build_daewoon_timeline_drawing(facts)
        self.assertEqual(drawing.__class__.__name__, "Drawing")
        # 세그먼트(Rect, 범례 제외) 개수 == 시기 개수
        from reportlab.graphics.shapes import Rect
        segment_rects = [c for c in drawing.contents if isinstance(c, Rect)]
        self.assertEqual(len(segment_rects), len(daewoon["entries"]) + len(set(e["axis"] for e in daewoon["entries"])))


if __name__ == "__main__":
    unittest.main()
