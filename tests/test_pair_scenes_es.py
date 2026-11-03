"""Spanische Szenen-Overlay (prompts/scenes/es.json): Abdeckung, Regeln, Auswahl."""
import re
import unittest

import i18n
import pair_relations
import pair_scenes

PATTERN_KEYS = {"both", "connection", "tension", "trine_only", "same_only", "none"}
A = {"year": {"hanja": "甲子"}, "month": {"hanja": "乙酉"}, "day": {"hanja": "甲子"}}
B = {"year": {"hanja": "乙丑"}, "day": {"hanja": "甲寅"}}


def _overlay():
    ov = pair_scenes.load_overlay("es")
    assert ov
    return ov


def test_overlay_covers_every_bank_theme():
    ov = _overlay()
    themes = {i[0] for items in pair_scenes.BANK.values() for i in items}
    assert set(ov["scenes"]) == themes
    for t, v in ov["scenes"].items():
        assert v["scene"].strip() and v["question"].strip(), t


def test_pattern_names_complete():
    names = _overlay()["pattern_names"]
    assert set(names) == PATTERN_KEYS
    assert len(set(names.values())) == len(names)


def test_all_texts_pass_spanish_mechanical_checks():
    ov = _overlay()
    texts = list(ov["pattern_names"].values())
    for v in ov["scenes"].values():
        texts += [v["scene"], v["question"]]
    cjk = re.compile(r"[぀-ヿ㐀-鿿가-힯]")
    for t in texts:
        assert not i18n.es_mechanical_issues(t), t
        assert not cjk.search(t), t


def test_select_returns_spanish_text():
    sel = pair_scenes.select(pair_relations.compare(A, B), "es")
    assert sel["scenes"]
    ov = _overlay()
    allowed = {v["scene"] for v in ov["scenes"].values()}
    for s in sel["scenes"]:
        assert s["scene"] in allowed
    assert sel["pattern_name"] in ov["pattern_names"].values()


class PairScenesEsTests(unittest.TestCase):
    def test_all(self):
        test_overlay_covers_every_bank_theme()
        test_pattern_names_complete()
        test_all_texts_pass_spanish_mechanical_checks()
        test_select_returns_spanish_text()
