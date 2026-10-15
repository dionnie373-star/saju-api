"""FR/ES 프리미엄 전용 프롬프트(prompts/<lang>/premium_report_prompt.json)의 구조 검증.

API를 호출하지 않는다. 플레이스홀더, native_lang(=언어 전환 블록이 덧씌워지지 않음),
핵심 금지어/규칙 문구가 빠지지 않았는지만 확인한다.
"""
import unittest

import report_pipeline as rp

VARS = {"computed_facts": "FACTS_BLOCK", "compact": "COMPACT_BLOCK", "daewoon_compact": "DAEWOON_BLOCK"}

# 기계적 검사(i18n.*_BANNED_REGEXES)가 잡는 표현을 프롬프트가 미리 금지하는지
REQUIRED_PHRASES = {
    "fr": ["pour la première fois", "dernière chance", "révèle", "garantit", "vous êtes aligné", "3 400 mots", "Métal"],
    "es": ["por primera vez", "última oportunidad", "revela", "garantiza", "estás preparado", "3.400 palabras", "Metal"],
}


class PremiumPromptTests(unittest.TestCase):
    def test_templates_load_native_and_fill_placeholders(self):
        for lang in ("fr", "es"):
            with self.subTest(lang=lang):
                tpl = rp._load_prompt_template("premium_report_prompt.json", lang)
                self.assertEqual(tpl.get("native_lang"), lang)
                self.assertGreaterEqual(tpl.get("max_tokens", 0), 14000)
                msgs = rp._build_messages(tpl, VARS, lang)
                self.assertEqual(len(msgs), 1)
                text = msgs[0]["content"]
                for block in ("FACTS_BLOCK", "COMPACT_BLOCK", "DAEWOON_BLOCK"):
                    self.assertIn(block, text)
                self.assertNotIn("{{", text)
                self.assertNotIn("독일어", text)  # 언어 전환 치환이 적용되지 않았음

    def test_required_rules_present(self):
        for lang, phrases in REQUIRED_PHRASES.items():
            tpl = rp._load_prompt_template("premium_report_prompt.json", lang)
            text = tpl["messages"][0]["content"]
            for p in phrases:
                with self.subTest(lang=lang, phrase=p):
                    self.assertIn(p, text)


if __name__ == "__main__":
    unittest.main()
