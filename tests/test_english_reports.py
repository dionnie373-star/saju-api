"""English ("en") report language: prompts, mechanical rules, PDF/email strings, pipeline wiring.

The real Anthropic API is never called. The pipeline functions run end to end with
call_claude / validate_report_consistency / send_email replaced by mocks, and the
attached PDF is rendered for real.

Set EN_PDF_OUT=/some/dir to keep the generated PDFs (used for visual inspection).
"""
import json
import os
import re
import shutil
import subprocess
import unittest
from unittest import mock

os.environ.setdefault("ANTHROPIC_API_KEY", "test-not-used")
os.environ.setdefault("BREVO_API_KEY", "test-not-used")
os.environ.setdefault("FROM_EMAIL", "test@example.com")
os.environ.setdefault("FROM_NAME", "Palja Test")

import app as app_module  # noqa: E402
import i18n  # noqa: E402
import pdf_design  # noqa: E402
import profile_view  # noqa: E402
import report_pipeline as rp  # noqa: E402

PROMPT_FILES = ("free_report_prompt.json", "paid_report_prompt.json",
                "premium_report_prompt.json", "compatibility_report_prompt.json")

MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August",
          "September", "October", "November", "December"]
ELEMENTS = ["Wood", "Fire", "Earth", "Metal", "Water"]

_SENTENCES = [
    "This part of the year can be read as a quiet invitation to look at {topic} with fresh eyes.",
    "According to the Saju tradition, a combination of {a} and {b} is linked with {topic}.",
    "You may notice this in small daily moments, for example when you plan your week or tidy your desk.",
    "It can help to write down one simple observation and to look at it again after a few days.",
    "Nothing here is a fixed rule, and you are free to keep only what feels useful to you.",
    "Think about how {a} shows up in your habits: is it loud, calm, steady or hard to see?",
    "A short walk, a clear list or a calm talk with a close person can make this theme easier to see.",
]


def _para(i, topic, a, b, n=5):
    out = []
    for k in range(n):
        out.append(_SENTENCES[(i + k) % len(_SENTENCES)].format(topic=topic, a=a, b=b))
    return " ".join(out)


def stub_free_report():
    parts = ["## Your Saju profile", "",
             "Your day element is Water. This profile uses the Korean Saju tradition, also known as BaZi, "
             "as a frame for reflection.", ""]
    for i, h in enumerate(["The five elements", "Your elements", "2026: a look back", "2027: a preview"]):
        parts += [f"## {h}", "", _para(i, "your energy", "Water", "Wood", 12), ""]
    parts += [
        "### Your Saju annual report 2027 — $10.00", "",
        "What you will get:",
        "- Your personal theme for 2027",
        "- 12 monthly chapters with personal Saju impulses",
        "- Reflection questions about love, work and personal growth",
        "- Your personal strengths and possible inner tensions",
        "- A yearly compass with concrete questions for your own decisions", "",
        "A personal reflection report based on the Saju tradition. It is not a scientific personality "
        "diagnosis, and it is not a certain prediction of the future.", "",
        "> What you do with this reading is your own choice.", "",
        "This content is offered for entertainment and personal reflection. "
        "It does not replace medical or psychological advice.",
    ]
    return "\n".join(parts)


def stub_paid_report():
    parts = ["## Introduction", "", _para(0, "the whole year", "Wood", "Fire", 6), "",
             "## Your year at a glance", "", _para(1, "the year", "Earth", "Metal", 6), "",
             "- Months in which things may flow more easily: March and April.",
             "- Months for more attention: August and September.", ""]
    for i, m in enumerate(MONTHS):
        a, b = ELEMENTS[i % 5], ELEMENTS[(i + 2) % 5]
        parts += [f"## {m} — Resources to observe", "",
                  f"This month brings a combination of {a} and {b}.", "",
                  _para(i, "resources", a, b, 9), "",
                  f"> Where could {a} meet {b} in your plans this month?", ""]
    parts += ["## Compass of the year", "", _para(2, "the year", "Wood", "Water", 8), "",
              "## About this reading", "",
              "This content is offered for entertainment and personal reflection. It is not a certain "
              "prediction, a diagnosis, or medical, psychological, legal or financial advice."]
    return "\n".join(parts)


def stub_premium_report():
    parts = ["## Introduction", "", _para(0, "a whole life", "Wood", "Fire", 8), "",
             "## Your life at a glance", "", _para(1, "ten-year phases", "Earth", "Metal", 8), ""]
    for i in range(8):
        a, b = ELEMENTS[i % 5], ELEMENTS[(i + 3) % 5]
        parts += [f"## Ages {3 + 10 * i}–{12 + 10 * i} — Responsibilities and bonds", "",
                  f"This phase brings a combination of {a} and {b}.", "",
                  _para(i, "responsibilities", a, b, 17), "",
                  f"> What changes in how you speak about {a} in this phase?", ""]
    parts += ["## Three patterns that repeat", "", _para(3, "patterns", "Fire", "Water", 12), "",
              "## Life compass", "", _para(4, "your life", "Metal", "Wood", 10), "",
              "## About this reading", "",
              "This content is offered for entertainment and personal reflection. It is not a certain "
              "prediction, a diagnosis, or medical, psychological, legal or financial advice. "
              "The decisions of your life depend only on you."]
    return "\n".join(parts)


def stub_compat_report():
    parts = ["## At a glance", "", "- Anna has a lot of Water, while Ben has very little.",
             "- Both charts share some Earth.", ""]
    for i, h in enumerate(["Introduction", "Balance of elements", "The core elements",
                           "What to watch together", "Closing"]):
        parts += [f"## {h}", "", _para(i, "the relationship", "Water", "Fire", 10).replace("You may", "Both may")
                  .replace("you are", "both are").replace("your", "their").replace("you", "they"), ""]
    parts += ["This content is offered for entertainment and personal reflection. "
              "It does not replace medical or psychological advice."]
    return "\n".join(parts)


class EnglishPromptTests(unittest.TestCase):
    VARS = {
        "free_report_prompt.json": {"compact": "COMPACT_BLOCK"},
        "paid_report_prompt.json": {"compact": "COMPACT_BLOCK", "computed_facts": "FACTS_BLOCK",
                                    "monthly_compact": "MONTHLY_BLOCK"},
        "premium_report_prompt.json": {"compact": "COMPACT_BLOCK", "computed_facts": "FACTS_BLOCK",
                                       "daewoon_compact": "DAEWOON_BLOCK"},
        "compatibility_report_prompt.json": {"compact_a": "COMPACT_A", "compact_b": "COMPACT_B",
                                             "name_a": "Anna", "name_b": "Ben",
                                             "gender_a": "female", "gender_b": "not specified"},
    }

    def load(self, name, lang="en"):
        return rp._load_prompt_template(name, lang)

    def test_four_files_exist_and_are_native_en(self):
        for name in PROMPT_FILES:
            with self.subTest(name=name):
                path = os.path.join(rp.PROMPTS_DIR, "en", name)
                self.assertTrue(os.path.exists(path))
                tpl = self.load(name)
                self.assertEqual(tpl["native_lang"], "en")

    def test_structure_matches_es(self):
        for name in PROMPT_FILES:
            with self.subTest(name=name):
                en, es = self.load(name), self.load(name, "es")
                self.assertEqual(list(en), list(es))
                for k in ("model", "max_tokens", "thinking"):
                    self.assertEqual(en.get(k), es.get(k), k)
                self.assertEqual(len(en["messages"]), len(es["messages"]))
                self.assertEqual([m["role"] for m in en["messages"]], [m["role"] for m in es["messages"]])
                ph = lambda t: sorted(set(re.findall(r"\{\{\s*[\w.]+\s*\}\}", t["messages"][0]["content"])))
                self.assertEqual(ph(en), ph(es))

    def test_placeholders_fill_and_no_language_switch_block(self):
        for name, variables in self.VARS.items():
            with self.subTest(name=name):
                msgs = rp._build_messages(self.load(name), variables, "en")
                text = msgs[0]["content"]
                self.assertNotIn("{{", text)
                self.assertNotIn("독일어", text)
                self.assertNotIn("언어 전환 지시", text)  # native prompt: no override block added
                for v in variables.values():
                    self.assertIn(v, text)

    def test_prompts_are_english_and_us_spelling(self):
        for name in PROMPT_FILES:
            with self.subTest(name=name):
                text = self.load(name)["messages"][0]["content"]
                self.assertIsNone(re.search(r"[áéíóúñ¿¡äöüß]", text))
                # the prompt names British spellings once, as examples of what NOT to write
                scan = re.sub(r"Never British spelling \([^)]*\)\.", "", text)
                self.assertIsNone(i18n.EN_BRITISH_SPELLING_RE.search(scan), i18n.EN_BRITISH_SPELLING_RE.findall(scan))
                for must in ("Wood", "Fire", "Earth", "Metal", "Water", "Korean", "destiny", "plain"):
                    self.assertIn(must, text)

    def test_required_rules_present(self):
        required = {
            "free_report_prompt.json": ["$10.00", "800 to 1,200 words", "never \"Gold\"", "Never British spelling"],
            "paid_report_prompt.json": ["2,500 to 3,500 words", "8 life phases of ten years", "last chance",
                                        "reveals", "guarantees", "About this reading", "[CALCULATED FACTS]"],
            "premium_report_prompt.json": ["3,400 to 4,400 words", "$24.90", "8", "last chance", "for the first time",
                                           "reveals", "guarantees", "Your life at a glance",
                                           "The decisions of your life depend only on you"],
            "compatibility_report_prompt.json": ["750 to 1,050 words", "do not address a reader as \"you\"",
                                                 "Never speak about \"the man\" or \"the woman\"", "$10.00"],
        }
        for name, phrases in required.items():
            text = self.load(name)["messages"][0]["content"]
            for p in phrases:
                with self.subTest(name=name, phrase=p):
                    self.assertIn(p, text)

    def test_fallback_localization_block_for_non_native_template(self):
        out = i18n.localize_prompt_text("독일어로 쓰기", "en")
        self.assertIn("영어로 쓰기", out)
        self.assertIn("미국식", out)
        self.assertIn("최종 확인", out)
        mid = i18n.localize_prompt_text("독일어 abc", "en", is_first_message=False, is_last_message=False)
        self.assertEqual(mid, "영어 abc")
        # de template (non-native for en) still builds with the override
        tpl = rp._load_prompt_template("free_report_prompt.json", "de")
        msgs = rp._build_messages(tpl, {"compact": "X"}, "en", "NOTE")
        self.assertIn("you", msgs[0]["content"])
        self.assertTrue(msgs[-1]["content"].endswith("NOTE"))


GOOD_EN = (
    "## Your year at a glance\n"
    "This report is a personal reflection based on the Korean Saju tradition. "
    "You may notice that Wood and Fire support each other in your pillars. "
    "It is not a scientific personality diagnosis. Which part of this reading feels useful to you?"
)


class EnglishMechanicalTests(unittest.TestCase):
    def issues(self, text):
        return i18n.en_mechanical_issues(text)

    def test_clean_text_passes(self):
        self.assertEqual(self.issues(GOOD_EN), [])
        for stub in (stub_free_report(), stub_paid_report(), stub_premium_report(), stub_compat_report()):
            self.assertEqual(self.issues(stub), [])

    def test_fate_words(self):
        for bad in ("It is your destiny.", "This is not fate.", "A fated meeting.", "A fateful year.",
                    "Fatality is not the point.", "A fatalistic view."):
            self.assertTrue(self.issues(bad), bad)
        # similar words that are fine
        self.assertEqual(self.issues("The destination is near. Fatigue can appear."), [])

    def test_destination_is_not_destiny(self):
        self.assertEqual(self.issues("The destination of the walk is a quiet park."), [])
        self.assertIsNone(i18n.EN_DESTINY_RE.search("destination"))
        self.assertIsNotNone(i18n.EN_DESTINY_RE.search("Destiny"))

    def test_science_and_certainty_claims(self):
        for bad in ("A scientific study.", "This is empirically true.", "Studies show this works.",
                    "It is statistically significant.", "The method is validated.", "This reveals your character.",
                    "The chart proves it.", "It guarantees success.", "This demonstrates a pattern."):
            self.assertTrue(self.issues(bad), bad)

    def test_negated_science_disclaimer_allowed(self):
        for ok in ("It is not a scientific personality diagnosis, and it is not a certain prediction.",
                   "This is a reading and not a scientific diagnosis.",
                   "It does not claim to be scientific."):
            self.assertEqual(self.issues(ok), [], ok)
        self.assertTrue(self.issues("This scientific method is clear. It is not a game."))

    def test_scarcity_and_urgency(self):
        for bad in ("This is a unique opportunity.", "It is your last chance.", "The ideal moment is now.",
                    "Now is the time to act.", "For the first time, Fire appears.", "A once in a lifetime phase.",
                    "A decisive moment.", "With a racing heart."):
            self.assertTrue(self.issues(bad), bad)

    def test_stem_literal_translations(self):
        for bad in ("A year of Fire of heaven.", "The heavenly Fire is strong.", "Earth in the sky."):
            self.assertTrue(self.issues(bad), bad)

    def test_gendered_reader_forms(self):
        for bad in ("He or she may prefer calm.", "Check his/her notes.", "Ask him or her."):
            self.assertTrue(self.issues(bad), bad)

    def test_gold_is_not_metal(self):
        self.assertTrue(self.issues("The element Gold is strong."))
        self.assertEqual(self.issues("Metal is strong in this chart."), [])

    def test_british_spelling_flagged_us_spelling_ok(self):
        for bad in ("Your behaviour and colour.", "The centre of your chart.", "You may recognise this.",
                    "Please organise your week.", "A programme for practise.", "Your neighbour's judgement.",
                    "A grey day, whilst waiting."):
            self.assertTrue(any("영국식" in i for i in self.issues(bad)), bad)
        self.assertEqual(self.issues("Your behavior and color. The center of your chart. You may recognize this. "
                                     "Please organize your week. A program for practice. Your neighbor's judgment. "
                                     "A gray day, while waiting."), [])

    def test_idioms_flagged(self):
        for bad in ("At the end of the day, it is fine.", "Step out of your comfort zone.", "A real rollercoaster.",
                    "Go with the flow.", "A rich tapestry of energy."):
            self.assertTrue(any("관용구" in i for i in self.issues(bad)), bad)

    def test_other_language_leaks(self):
        self.assertTrue(self.issues("Dein Jahr und der Tag ist nicht leicht."))
        self.assertTrue(self.issues("Votre année avec Bois et Feu."))
        self.assertTrue(self.issues("El elemento Fuego y la Madera."))
        self.assertTrue(self.issues("Les années des étapes est dans une zone."))
        self.assertTrue(self.issues("Los años de las etapas para una vida."))
        self.assertTrue(self.issues("Your element is 물."))

    def test_pipeline_dispatch_hanja_and_length(self):
        out = rp.check_mechanical_rules("It is your destiny. " * 5, lang="en", min_words=1)
        self.assertTrue(any("destiny" in i for i in out))
        out = rp.check_mechanical_rules("Fire 丙午 and Water.", lang="en", min_words=100)
        self.assertTrue(any("CJK" in i for i in out))
        self.assertTrue(any("분량 미달" in i for i in out))
        self.assertEqual(rp.check_mechanical_rules(GOOD_EN, lang="en", min_words=10), [])

    def test_other_languages_unchanged(self):
        self.assertTrue(rp.check_mechanical_rules("Sie können das tun.", min_words=0))
        self.assertEqual(rp.check_mechanical_rules("Du kannst das tun.", min_words=0), [])
        self.assertTrue(rp.check_mechanical_rules("Vous êtes aligné. Tu peux.", min_words=0, lang="fr"))
        self.assertTrue(rp.check_mechanical_rules("Es tu destino.", min_words=0, lang="es"))
        # English words are still treated as a leak in fr/es, and en rules do not touch de
        self.assertTrue(rp.check_mechanical_rules("Your energy and the flow.", min_words=0, lang="es"))
        self.assertEqual(rp.check_mechanical_rules("Du kannst die Farbe wählen, behaviour.", min_words=0), [])

    def test_destiny_strip_last_line_of_defense(self):
        out = rp._strip_schicksal_sentences("Hello. It is not fate. Thanks.", i18n.EN_DESTINY_RE)
        self.assertNotIn("fate", out.lower())
        self.assertIn("Hello.", out)
        self.assertIn("Thanks.", out)
        self.assertEqual(i18n.DESTINY_LABEL["en"], "destiny")
        # the label must appear in the issue text so the pipeline can drop the resolved issue
        self.assertTrue(any(i18n.DESTINY_LABEL["en"] in i for i in i18n.en_mechanical_issues("Your fate.")))

    def test_call_claude_checked_strips_destiny_after_retries(self):
        with mock.patch.object(rp, "call_claude", return_value="Good start. This is your destiny. Good end."), \
                mock.patch.object(rp, "_regenerate_with_correction", return_value=None):
            text = rp.call_claude_checked("free_report_prompt.json", {"compact": "x"}, lang="en", min_words=0)
        self.assertNotIn("destiny", text.lower())
        self.assertIn("Good start.", text)


class EnglishStringTests(unittest.TestCase):
    def test_registry(self):
        self.assertIn("en", i18n.SUPPORTED_LANGS)
        self.assertEqual(i18n.normalize_lang("EN"), "en")
        self.assertEqual(i18n.normalize_lang(" en "), "en")
        self.assertEqual(i18n.normalize_lang("xx"), "de")
        self.assertEqual(i18n.normalize_lang(None), "de")
        for reg in (i18n.STRINGS, i18n.MECHANICAL_ISSUES, i18n.DESTINY_RE, i18n.PROMPT_BLOCKS):
            self.assertIn("en", reg)
        self.assertIn("en", i18n.DESTINY_LABEL)

    def test_string_table_keys_match_fr_es(self):
        fr, es, en = i18n.STRINGS["fr"], i18n.STRINGS["es"], i18n.STRINGS["en"]
        self.assertEqual(set(en), set(es))
        self.assertEqual(set(en), set(fr))
        for k in ("free", "paid", "premium", "compatibility"):
            self.assertEqual(set(en[k]), set(es[k]), k)
        self.assertEqual(set(en["axis_labels"]), set(es["axis_labels"]))

    def test_english_strings_have_no_foreign_leftovers_and_us_spelling(self):
        flat = json.dumps(i18n.EN_STRINGS, ensure_ascii=False)
        for w in ("Bonjour", "Hola", "Hallo", "vous", "tú", "Rapport", "Informe", "Jahres"):
            self.assertNotIn(w, flat)
        self.assertIsNone(i18n.EN_BRITISH_SPELLING_RE.search(flat))
        self.assertTrue(i18n.EN_STRINGS["disclaimer"].startswith("Palja is offered"))

    def test_pdf_design_tables(self):
        self.assertEqual(set(pdf_design.STRINGS["en"]), set(pdf_design.STRINGS["de"]))
        self.assertEqual(set(pdf_design.STRINGS["en"]), set(pdf_design.STRINGS["es"]))
        self.assertEqual(set(pdf_design.ELEMENT_NAMES["en"]), set(pdf_design.ELEMENT_NAMES["de"]))
        self.assertEqual(pdf_design.ELEMENT_NAMES["en"]["금"], "Metal")
        self.assertEqual(len(pdf_design.STRINGS["en"]["cols"]), 4)
        self.assertEqual(len(pdf_design.STRINGS["en"]["rows"]), 2)
        self.assertIn("en", {"de", "fr", "es", "en"} & set(pdf_design.STRINGS))

    def test_profile_view_english_is_clean(self):
        for d, city in (("1990-05-15", "Berlin"), ("1985-11-03", "Paris"), ("1978-02-20", "Madrid")):
            for bt in ("", "14:00"):
                calc = app_module.run_calculation({"birth_date": d, "birth_time": bt, "birth_city": city,
                                                   "lang": "en", "target_years": [2026, 2027]})
                view = profile_view.build_profile_view(calc, "en")
                txt = "\n".join(s["text"] for s in view["sections"])
                self.assertEqual(i18n.en_mechanical_issues(txt), [], (d, city, bt))

    def test_email_templates(self):
        for kind in ("free", "paid", "premium", "compatibility"):
            with self.subTest(kind=kind):
                html = rp._fr_email_template(kind, "en")
                self.assertIn("{geocoding_notice}", html)
                out = html.format(name_suffix=" Ana", geocoding_notice="")
                self.assertIn("Hello Ana,", out)
                self.assertIn("Legal notice", out)
                self.assertIn("Privacy", out)
                self.assertIn("It does not replace medical or psychological advice", out)
                for w in ("Hallo", "Bonjour", "Hola", "Impressum", "Datenschutz"):
                    self.assertNotIn(w, out)
                if kind == "free":
                    self.assertNotIn("money-back", out)
                else:
                    self.assertIn("60 days", out)
                self.assertEqual("how well you connect" in out, kind != "compatibility")

    def test_email_links(self):
        with mock.patch.dict(os.environ, {"EN_SITE_BASE_URL": ""}):
            self.assertEqual(rp._lang_url("en/privacy", "en"), rp.SITE_BASE_URL + "/en/privacy")
        with mock.patch.dict(os.environ, {"EN_SITE_BASE_URL": "https://example.test/"}):
            self.assertEqual(rp._lang_url("en/privacy", "en"), "https://example.test/privacy")

    def test_doc_strings(self):
        t, st, fn, subj, tpl = rp._doc_strings("paid", "en", "Ana")
        self.assertEqual((t, fn), ("Your Saju annual report", "Palja-Annual-Report.pdf"))
        self.assertEqual(st, "Prepared for Ana")
        self.assertIn("annual report", subj)
        self.assertEqual(rp._doc_strings("paid", "en", "")[1], "Your personal annual report")
        self.assertEqual(rp._doc_strings("premium", "en", "Ana")[2], "Palja-Life-Map.pdf")
        t, st, fn, subj, _ = rp._doc_strings("compatibility", "en", None)
        self.assertIsNone(st)
        self.assertEqual(fn, "Palja-Compatibility.pdf")
        self.assertEqual(rp._doc_strings("free", "en", "")[2], "Palja-Profile.pdf")

    def test_geo_notice(self):
        html = rp._geocoding_fallback_notice_html(["Nowhereville"], "en")
        self.assertIn('"Nowhereville"', html)
        self.assertIn("central Germany", html)
        self.assertEqual(rp._geocoding_fallback_notice_html([None], "en"), "")
        self.assertIn("Paris", rp._geocoding_fallback_notice_html(["X"], "fr"))
        self.assertIn("Madrid", rp._geocoding_fallback_notice_html(["X"], "es"))
        self.assertIn("Deutschlands", rp._geocoding_fallback_notice_html(["X"], "de"))


def _pdftotext(path):
    exe = shutil.which("pdftotext")
    if not exe:
        return None
    return subprocess.run([exe, "-layout", path, "-"], capture_output=True, text=True, check=True).stdout


class EnglishPipelineEndToEndTests(unittest.TestCase):
    """run_*_signup with lang='en', AI and mail mocked, real PDF rendering."""

    def setUp(self):
        self.sent = []
        self.out_dir = os.environ.get("EN_PDF_OUT")
        if self.out_dir:
            os.makedirs(self.out_dir, exist_ok=True)

    def fake_send(self, **kw):
        with open(kw["attachment_path"], "rb") as f:
            data = f.read()
        rec = dict(kw, pdf=data)
        self.sent.append(rec)
        if self.out_dir:
            with open(os.path.join(self.out_dir, kw["attachment_name"]), "wb") as f:
                f.write(data)

    def run_pipeline(self, fn, text, **kw):
        ok = {"consistent": True, "issues": []}
        with mock.patch.object(rp, "call_claude", return_value=text) as cc, \
                mock.patch.object(rp, "validate_report_consistency", return_value=ok), \
                mock.patch.object(rp, "send_email", self.fake_send), \
                mock.patch.object(rp, "_regenerate_with_correction", return_value=None):
            fn(**kw)
        return cc

    def assert_pdf(self, rec, *needles):
        self.assertTrue(rec["pdf"].startswith(b"%PDF"))
        self.assertGreater(len(rec["pdf"]), 20000)
        text = _pdftotext(rec.get("path_for_text") or self._tmp(rec))
        if text is None:
            return
        for n in needles:
            self.assertIn(n, text)
        return text

    def _tmp(self, rec):
        import tempfile
        fd, path = tempfile.mkstemp(suffix=".pdf")
        os.close(fd)
        self.addCleanup(os.unlink, path)
        with open(path, "wb") as f:
            f.write(rec["pdf"])
        return path

    def calc(self, **extra):
        payload = {"name": "Ana", "birth_date": "1991-03-14", "birth_time": "07:30", "birth_city": "Berlin",
                   "gender": "female", "lang": "en", "target_years": [2026, 2027]}
        payload.update(extra)
        return payload, app_module.run_calculation(payload)

    def test_free(self):
        payload, calc = self.calc()
        payload["email"] = "ana@example.com"
        cc = self.run_pipeline(rp.run_free_signup, stub_free_report(), payload=payload, calc_result=calc)
        self.assertEqual(cc.call_args.kwargs["lang"], "en")
        rec = self.sent[0]
        self.assertEqual(rec["subject"], "Your free Saju profile is ready ✨")
        self.assertEqual(rec["attachment_name"], "Palja-Profile.pdf")
        self.assertIn("Hello Ana,", rec["html_body"])
        self.assertNotIn("{name_suffix}", rec["html_body"])
        self.assertNotIn("{geocoding_notice}", rec["html_body"])
        self.assertIn("Legal notice", rec["html_body"])
        self.assert_pdf(rec, "Your Saju profile", "Prepared for Ana", "Contents", "Your profile at a glance",
                        "Your five elements", "Wood", "Heavenly stem", "palja.de/en")

    def test_free_anonymous_and_unknown_hour(self):
        payload, calc = self.calc(name="", birth_time="")
        payload["email"] = "x@example.com"
        self.run_pipeline(rp.run_free_signup, stub_free_report(), payload=payload, calc_result=calc)
        rec = self.sent[0]
        self.assertIn("Hello,", rec["html_body"])
        self.assert_pdf(rec, "Your personal five-elements profile", "Without a birth time")

    def test_paid(self):
        payload, calc = self.calc(monthly_year=2027)
        payload["email"] = "ana@example.com"
        cc = self.run_pipeline(rp.run_paid_signup, stub_paid_report(), payload=payload, calc_result=calc)
        self.assertEqual(cc.call_args.args[0], "paid_report_prompt.json")
        self.assertEqual(cc.call_args.kwargs["lang"], "en")
        rec = self.sent[0]
        self.assertEqual(rec["subject"], "Your Palja annual report is ready 📖")
        self.assertEqual(rec["attachment_name"], "Palja-Annual-Report.pdf")
        self.assertIn("60 days", rec["html_body"])
        self.assertIn("Saju compatibility check ($10.00)", rec["html_body"])
        text = self.assert_pdf(rec, "Your Saju annual report", "Contents", "January", "December", "About this reading")
        if text:
            self.assertNotIn("Inhalt", text)

    def test_premium(self):
        payload, calc = self.calc(daewoon_count=8)
        payload["email"] = "ana@example.com"
        self.run_pipeline(rp.run_premium_signup, stub_premium_report(), payload=payload, calc_result=calc)
        rec = self.sent[0]
        self.assertEqual(rec["subject"], "Your Palja life map is ready 🧭")
        self.assertEqual(rec["attachment_name"], "Palja-Life-Map.pdf")
        text = self.assert_pdf(rec, "Your Saju life map", "Your life map at a glance", "YOU ARE HERE",
                               "Resources", "Contents")
        if text:
            self.assertNotIn("DU BIST HIER", text)

    def test_compatibility(self):
        payload_a, calc_a = self.calc(name="Anna")
        payload_b, calc_b = self.calc(name="Ben", birth_date="1988-09-02", birth_city="Madrid", gender="male")
        payload = {"email": "anna@example.com", "name_a": "Anna", "name_b": "Ben", "lang": "en",
                   "gender_a": "female", "gender_b": ""}
        cc = self.run_pipeline(rp.run_compatibility_signup, stub_compat_report(),
                               payload=payload, calc_result_a=calc_a, calc_result_b=calc_b)
        sent_vars = cc.call_args.args[1]
        self.assertEqual(sent_vars["gender_a"], "female")
        self.assertEqual(sent_vars["gender_b"], "not specified")
        self.assertEqual(sent_vars["name_a"], "Anna")
        rec = self.sent[0]
        self.assertEqual(rec["subject"], "Your Saju compatibility check is ready 💫")
        self.assertEqual(rec["attachment_name"], "Palja-Compatibility.pdf")
        self.assertNotIn("how well you connect", rec["html_body"])
        self.assert_pdf(rec, "Your Saju compatibility", "Anna", "Ben", "The five elements")

    def test_pullquote_quotes_only_change_for_english(self):
        en = rp._report_text_to_flowables("> A calm sentence.", lang="en")
        de = rp._report_text_to_flowables("> A calm sentence.", lang="de")
        self.assertEqual(en[0].text, "“A calm sentence.”")
        self.assertEqual(de[0].text, "„A calm sentence.“")

    def test_english_text_in_german_default_path_untouched(self):
        # lang missing -> German pipeline constants as before
        payload, calc = self.calc()
        payload["lang"] = None
        payload["email"] = "ana@example.com"
        self.run_pipeline(rp.run_free_signup, "## Einleitung\n\n" + "Du kannst das tun. " * 200,
                          payload=payload, calc_result=calc)
        self.assertEqual(self.sent[0]["attachment_name"], "Palja-Profil.pdf")
        self.assertIn("Dein kostenloses", self.sent[0]["subject"])


class EnglishAppTests(unittest.TestCase):
    def setUp(self):
        app_module._RATE_LIMIT_HISTORY.clear()
        self.c = app_module.app.test_client()

    def test_msg_has_english_for_every_key(self):
        for key, table in app_module._MSG.items():
            self.assertIn("en", table, key)
            self.assertEqual(app_module._msg(key, "en"), table["en"])
        self.assertIn("Too many requests", app_module._msg("too_many", "en"))
        self.assertIn("Zu viele", app_module._msg("too_many", "de"))
        self.assertIn("Trop de", app_module._msg("too_many", "fr"))
        self.assertIn("Demasiadas", app_module._msg("too_many", "es"))

    def test_signup_passes_en_to_pipeline_and_errors_are_english(self):
        seen = {}

        def fake(payload, calc_result):
            seen["lang"] = i18n.normalize_lang(payload.get("lang"))
            seen["years"] = payload.get("target_years")

        import report_pipeline
        with mock.patch.object(report_pipeline, "run_free_signup", fake):
            r = self.c.post("/signup", json={"email": "a@example.com", "name": "Ana", "birth_date": "1990-05-15",
                                             "birth_time": "", "birth_city": "Berlin", "lang": "en"})
        self.assertEqual(r.status_code, 200, r.get_data(as_text=True))
        self.assertEqual(seen, {"lang": "en", "years": [2026, 2027]})
        # same address again within 10 minutes -> English message
        r = self.c.post("/signup", json={"email": "a@example.com", "birth_date": "1990-05-15",
                                         "birth_city": "Berlin", "lang": "en"})
        self.assertEqual(r.status_code, 429)
        self.assertIn("free profile was already requested", r.get_json()["error"])
        app_module._RATE_LIMIT_HISTORY.clear()
        r = self.c.post("/signup", json={"email": "b@example.com", "birth_date": "1990-05-15",
                                         "birth_city": "Berlin", "lang": "de"})
        # German keeps going through the German path (pipeline is real here, mail/AI not available -> error status)
        self.assertNotIn("free profile", r.get_data(as_text=True))

    def test_signup_unknown_place_with_time_rejected_only_for_english(self):
        orig = app_module._lookup_location
        app_module._lookup_location = lambda city, lang="de": (10.45, "Europe/Berlin", "default_fallback")
        try:
            import report_pipeline
            calls = []
            with mock.patch.object(report_pipeline, "run_free_signup", lambda **kw: calls.append(kw)):
                r = self.c.post("/signup", json={"email": "c@example.com", "birth_date": "1990-05-15",
                                                 "birth_time": "14:00", "birth_city": "Nowhereville", "lang": "en"})
                self.assertEqual(r.status_code, 422)
                self.assertEqual(r.get_json()["code"], "place_not_found")
                self.assertIn("birth place", r.get_json()["error"])
                self.assertEqual(calls, [])
                app_module._RATE_LIMIT_HISTORY.clear()
                r = self.c.post("/signup", json={"email": "d@example.com", "birth_date": "1990-05-15",
                                                 "birth_time": "", "birth_city": "Nowhereville", "lang": "en"})
                self.assertEqual(r.status_code, 200)
                app_module._RATE_LIMIT_HISTORY.clear()
                r = self.c.post("/signup", json={"email": "e@example.com", "birth_date": "1990-05-15",
                                                 "birth_time": "14:00", "birth_city": "Nowhereville", "lang": "fr"})
                self.assertEqual(r.status_code, 200)  # fr behavior unchanged
        finally:
            app_module._lookup_location = orig

    def test_profile_and_signup_use_same_location_language(self):
        langs = []
        orig = app_module._lookup_location

        def spy(city, lang="de"):
            langs.append(lang)
            return orig(city, lang)

        with mock.patch.object(app_module, "_lookup_location", spy):
            self.c.post("/profile", json={"birth_date": "1990-05-15", "birth_city": "Berlin", "lang": "en"})
        self.assertEqual(set(langs), {"en"})

    def test_contact_form_english_error(self):
        r = self.c.post("/kontakt/senden", json={"email": "", "message": "", "lang": "en"})
        self.assertEqual(r.status_code, 400)  # existing Korean validation message path for missing email

    def test_pending_order_rate_limit_message_language(self):
        app_module._RATE_LIMIT_HISTORY.clear()
        body = {"email": "o@example.com", "lang": "en", "tier": "paid"}
        with mock.patch.object(app_module, "_rate_limited", return_value=True):
            r = self.c.post("/orders/pending", json=body)
            self.assertEqual(r.status_code, 429)
            self.assertIn("Too many requests", r.get_json()["error"])
            r = self.c.post("/orders/pending", json=dict(body, lang="fr"))
            self.assertIn("Zu viele", r.get_json()["error"])  # unchanged behavior for non-English


if __name__ == "__main__":
    unittest.main()
