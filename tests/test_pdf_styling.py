"""PDF 리포트가 사이트 브랜드(세리프 헤딩 + 테라코타 액센트)를 유지하는지,
그리고 마크다운 불릿 줄이 실제 글머리 기호로 변환되는지 확인하는 회귀 테스트.

배경: 예전엔 PDF가 전부 Helvetica(무채색 산세리프)로만 렌더링돼서 사이트의
세리프 헤딩(Fraunces)+테라코타 액센트 브랜드와 완전히 동떨어져 보였다. 실제로
PDF를 렌더링해서 눈으로 봐야만 알 수 있는 문제라 기존 테스트로는 못 잡았음
(report_pipeline의 배선만 검증했지, 렌더링 결과는 안 봤음). 이 테스트는 PDF를
실제로 픽셀 단위로 검사하진 않지만, 스타일 정의 자체가 실수로 다시 Helvetica로
되돌아가거나 불릿 처리가 깨지는 걸 최소한으로 막는다.

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
    def test_title_and_headings_use_serif_font_not_generic_helvetica(self):
        self.assertEqual(rp._PDF_STYLES["title"].fontName, "Times-Bold")
        self.assertEqual(rp._PDF_STYLES["subtitle"].fontName, "Times-Italic")
        self.assertEqual(rp._PDF_STYLES["h2"].fontName, "Times-Bold")

    def test_body_text_stays_readable_sans_serif(self):
        # 세리프는 헤딩에만 — 본문까지 세리프로 바꾸면 긴 리포트는 오히려 읽기
        # 힘들어지므로, 사이트와 같은 세리프 헤딩 + 산세리프 본문 조합을 유지한다.
        self.assertEqual(rp._PDF_STYLES["body"].fontName, "Helvetica")

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


if __name__ == "__main__":
    unittest.main()
