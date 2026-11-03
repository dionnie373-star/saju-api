"""두 사람 궁합 관계 계산(pair_relations) 테스트. 설계: Claude 문서 'Palja 두 사람 궁합 엔진 설계안'."""
import itertools
import json
import os
import re
import unittest

import pair_relations as pr

BRANCHES = "子丑寅卯辰巳午未申酉戌亥"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def pillars(year, month, day, hour=None):
    def p(s):
        return None if s is None else {"hanja": s}
    return {"year": p(year), "month": p(month), "day": p(day), "hour": p(hour)}


class TableIntegrityTests(unittest.TestCase):
    def test_every_pair_is_two_distinct_branches(self):
        for name, table in pr._BRANCH_TABLES:
            for pair in table:
                self.assertEqual(len(pair), 2, (name, pair))
                self.assertTrue(pair <= set(BRANCHES), (name, pair))

    def test_perfect_matchings_cover_all_12_branches_once(self):
        # 육합·충·파·해·원진·귀문은 각각 12지지를 6쌍으로 빠짐없이 한 번씩 묶는다.
        for name in ("yukhap", "chung", "pa", "hae", "wonjin", "gwimun"):
            table = dict(pr._BRANCH_TABLES)[name]
            self.assertEqual(len(table), 6, name)
            covered = [b for pair in table for b in pair]
            self.assertEqual(sorted(covered), sorted(BRANCHES), name)

    def test_wonjin_and_gwimun_differ_only_in_ja_and_in(self):
        wonjin, gwimun = set(pr.WONJIN), set(pr.GWIMUN)
        self.assertEqual(wonjin - gwimun, {frozenset("子未"), frozenset("寅酉")})
        self.assertEqual(gwimun - wonjin, {frozenset("子酉"), frozenset("寅未")})
        self.assertEqual(len(wonjin & gwimun), 4)

    def test_banhap_counts(self):
        self.assertEqual(len(pr.BANHAP_PRIMARY), 8)
        self.assertEqual(len(pr.SAME_TRINE_GROUP), 4)
        # 왕지(子午卯酉)를 포함한 쌍만 반합, 생지+고지 쌍은 포함하지 않는다.
        for pair in pr.BANHAP_PRIMARY:
            self.assertTrue(pair & set("子午卯酉"), pair)
        for pair in pr.SAME_TRINE_GROUP:
            self.assertFalse(pair & set("子午卯酉"), pair)
        # 반합 8쌍 + 같은 삼합 그룹 4쌍 = 삼합 4개 x 3쌍
        self.assertEqual(len(set(pr.BANHAP_PRIMARY) | set(pr.SAME_TRINE_GROUP)), 12)

    def test_confidence_and_names_cover_all_codes(self):
        codes = {c for c, _ in pr._BRANCH_TABLES} | {"stem_hap"}
        self.assertEqual(codes, set(pr.CONFIDENCE))
        self.assertEqual(codes, set(pr.KO_NAME))


class BranchRelationTests(unittest.TestCase):
    def test_symmetry_for_all_pairs(self):
        for a, b in itertools.product(BRANCHES, repeat=2):
            self.assertEqual(pr.branch_relations(a, b), pr.branch_relations(b, a), (a, b))

    def test_ja_mi_vs_ja_yu(self):
        self.assertEqual(pr.branch_relations("子", "未"), ["hae", "wonjin"])
        self.assertEqual(pr.branch_relations("子", "酉"), ["pa", "gwimun"])

    def test_in_yu_vs_in_mi(self):
        self.assertEqual(pr.branch_relations("寅", "酉"), ["wonjin"])
        self.assertEqual(pr.branch_relations("寅", "未"), ["gwimun"])

    def test_overlapping_relations_are_all_returned(self):
        self.assertEqual(pr.branch_relations("寅", "亥"), ["yukhap", "pa"])
        self.assertEqual(pr.branch_relations("巳", "申"), ["yukhap", "pa", "hyung_partial"])
        self.assertEqual(pr.branch_relations("丑", "午"), ["hae", "wonjin", "gwimun"])
        self.assertEqual(pr.branch_relations("丑", "未"), ["chung", "hyung_partial"])
        self.assertEqual(pr.branch_relations("寅", "申"), ["chung", "hyung_partial"])

    def test_pairs_without_relation(self):
        self.assertEqual(pr.branch_relations("子", "寅"), [])
        self.assertEqual(pr.branch_relations("午", "午"), [])  # 같은 지지: 관계 없음, 교차 자형 판정 안 함
        self.assertEqual(pr.branch_relations("", "子"), [])

    def test_hyung_partial_is_not_a_complete_samhyung(self):
        self.assertEqual(pr.branch_relations("寅", "巳"), ["hae", "hyung_partial"])
        self.assertNotIn("hyung", pr.branch_relations("寅", "巳"))
        self.assertEqual(pr.branch_relations("子", "卯"), ["hyung"])

    def test_banhap_vs_same_trine_group(self):
        self.assertEqual(pr.branch_relations("申", "子"), ["banhap"])
        self.assertEqual(pr.branch_relations("申", "辰"), ["same_trine_group"])
        self.assertEqual(pr.branch_relations("寅", "戌"), ["same_trine_group"])

    def test_stem_hap(self):
        self.assertEqual(pr.stem_relations("甲", "己"), ["stem_hap"])
        self.assertEqual(pr.stem_relations("己", "甲"), ["stem_hap"])
        self.assertEqual(pr.stem_relations("甲", "庚"), [])  # 천간충은 적용하지 않는다
        self.assertEqual(pr.stem_relations("甲", "甲"), [])


class CompareTests(unittest.TestCase):
    def test_day_day_is_primary_and_others_secondary(self):
        a = pillars("甲子", "乙丑", "丙寅", "丁卯")
        b = pillars("庚午", "辛未", "壬亥", "癸酉")
        res = pr.compare(a, b)
        primary = [i for i in res["branch_pairs"] if i["priority"] == "primary"]
        self.assertEqual(len(primary), 1)
        self.assertEqual((primary[0]["a"], primary[0]["b"]), ("寅", "亥"))
        self.assertEqual(primary[0]["relations"], ["yukhap", "pa"])
        self.assertTrue(all(i["priority"] == "secondary" for i in res["branch_pairs"] if i is not primary[0]))

    def test_every_cross_pair_is_checked_and_order_swap_gives_same_pairs(self):
        a = pillars("甲子", "乙丑", "丙寅", "丁卯")
        b = pillars("庚午", "辛未", "壬亥", "癸酉")
        ab = pr.compare(a, b)["branch_pairs"]
        ba = pr.compare(b, a)["branch_pairs"]
        key = lambda i: (tuple(sorted((i["a"], i["b"]))), tuple(i["relations"]))
        self.assertEqual(sorted(map(key, ab)), sorted(map(key, ba)))
        # 16개 교차 조합 중 관계 또는 같은 지지가 있는 것만 남는다
        a_br = ["子", "丑", "寅", "卯"]
        b_br = ["午", "未", "亥", "酉"]
        expected = sum(1 for x in a_br for y in b_br if pr.branch_relations(x, y) or x == y)
        self.assertEqual(len(ab), expected)

    def test_relation_inside_one_chart_is_not_reported(self):
        # B 안에 丑·未(충)이 모두 있어도 A에 丑/未가 없으면 두 사람 사이 관계가 아니다.
        a = pillars("甲子", "乙午", "丙寅", "丁卯")
        b = pillars("庚辰", "辛丑", "壬未", "癸巳")
        res = pr.compare(a, b)
        for item in res["branch_pairs"]:
            self.assertNotEqual(frozenset((item["a"], item["b"])), frozenset("丑未"))

    def test_same_branch_is_recorded_without_relation(self):
        a = pillars("甲辰", "乙丑", "丙午", "丁卯")
        b = pillars("庚辰", "辛巳", "壬午", "癸亥")
        res = pr.compare(a, b)
        same = [i for i in res["branch_pairs"] if i["same_branch"]]
        self.assertTrue(same)
        for i in same:
            self.assertEqual(i["relations"], [])  # 교차 자형(辰辰·午午) 판정 안 함

    def test_missing_hour_pillar_is_skipped(self):
        a = pillars("甲子", "乙丑", "丙寅", None)
        b = pillars("庚午", "辛未", "壬亥", "癸酉")
        res = pr.compare(a, b)
        self.assertTrue(all(i["person_a_position"] != "hour" for i in res["branch_pairs"]))
        self.assertTrue(any(i["person_b_position"] == "hour" for i in res["branch_pairs"]))

    def test_stem_hap_pairs(self):
        a = pillars("甲子", "乙丑", "丙寅", "丁卯")
        b = pillars("己午", "庚未", "辛亥", "壬酉")
        res = pr.compare(a, b)
        self.assertTrue(any(i["a"] == "甲" and i["b"] == "己" for i in res["stem_pairs"]))
        day_day = [i for i in res["stem_pairs"] if i["priority"] == "primary"]
        self.assertEqual([(i["a"], i["b"]) for i in day_day], [("丙", "辛")])


class FactsTextTests(unittest.TestCase):
    def test_primary_and_cap_on_secondary(self):
        a = pillars("甲子", "乙丑", "丙寅", "丁卯")
        b = pillars("庚午", "辛未", "壬亥", "癸酉")
        text = pr.build_facts_text(pr.compare(a, b), "Anna", "Ben")
        self.assertIn("핵심 관계", text)
        self.assertIn("Anna의 일지 寅 ↔ Ben의 일지 亥: 육합 + 파", text)
        secondary_lines = [l for l in text.splitlines() if l.startswith("- ") and "일지 寅 ↔ Ben의 일지 亥" not in l
                           and "천간" not in l]
        self.assertLessEqual(len(secondary_lines), pr.MAX_SECONDARY)
        self.assertNotIn("합화", text.replace("합화(오행이 바뀜)는 판단하지 않음", ""))

    def test_no_relations_message(self):
        a = pillars("甲子", "甲子", "甲子", "甲子")
        b = pillars("甲寅", "甲寅", "甲寅", "甲寅")
        text = pr.build_facts_text(pr.compare(a, b), "A", "B")
        self.assertIn("성립하는 관계 없음", text)
        self.assertIn("확인되지 않았습니다", text)

    def test_fallback_on_bad_input(self):
        self.assertEqual(pr.relations_for_report({"pillars": "bad"}, None, "A", "B"), pr.FALLBACK_FACTS)
        # 기둥 정보가 아예 없으면 예외 없이 "관계 없음" 사실 블록이 만들어진다
        self.assertIn("성립하는 관계 없음", pr.relations_for_report({}, {}, "A", "B"))


class PromptTests(unittest.TestCase):
    def setUp(self):
        with open(os.path.join(ROOT, "prompts", "compatibility_report_prompt.json"), encoding="utf-8") as f:
            self.text = json.load(f)["messages"][0]["content"]

    def test_placeholder_section_and_rules_present(self):
        self.assertIn("{{relations_facts}}", self.text)
        self.assertIn("3-2. 부딪히기 쉬운 순간들", self.text)
        self.assertIn("[지지 관계 서술 규칙 - 매우 중요]", self.text)

    def test_german_expressions_present_and_hanja_rule_kept(self):
        for term in ("harmonische Verbindung", "unterschiedliche Impulse", "Reibungspunkte",
                     "emotionale Spannungen", "ausgeprägte Sensibilität"):
            self.assertIn(term, self.text)
        self.assertIn("[한자 사용 금지]", self.text)

    def test_section_percentages_sum_unchanged(self):
        pcts = [int(x) for x in re.findall(r"\(~(\d+)%", self.text)]
        self.assertEqual(sum(pcts), 98)  # v3 구조(8+5+18+14+28+12+8+5=98)

    def test_fills_without_leftover_placeholders(self):
        try:
            import report_pipeline as rp
        except ImportError:
            self.skipTest("report_pipeline 의존 패키지가 없는 환경")
        tpl = rp._load_prompt_template("compatibility_report_prompt.json", "de")
        vars_ = {"name_a": "Anna", "name_b": "Ben", "gender_a": "x", "gender_b": "y",
                 "compact_a": "CA", "compact_b": "CB", "relations_facts": "FACTS_BLOCK",
                 "relation_type": "REL"}
        msg = rp._build_messages(tpl, vars_, "de")[0]["content"]
        self.assertNotIn("{{", msg)
        self.assertIn("FACTS_BLOCK", msg)


if __name__ == "__main__":
    unittest.main()
