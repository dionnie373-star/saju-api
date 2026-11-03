"""English scene overlay tests."""
import pair_scenes
from i18n import en_mechanical_issues


def _ov():
    ov = pair_scenes.load_overlay("en")
    assert ov, "prompts/scenes/en.json missing"
    return ov


def test_overlay_covers_every_bank_theme():
    ov = _ov()
    themes = {t for items in pair_scenes.BANK.values() for (t, _f, _s, _q) in items}
    assert themes <= set(ov["scenes"]), themes - set(ov["scenes"])


def test_six_pattern_names():
    names = _ov()["pattern_names"]
    assert set(names) == {"both", "connection", "tension", "trine_only", "same_only", "none"}
    assert all(names.values())


def test_texts_pass_english_mechanical_checks():
    ov = _ov()
    texts = list(ov["pattern_names"].values())
    for v in ov["scenes"].values():
        texts += [v["scene"], v["question"]]
    for t in texts:
        assert not en_mechanical_issues(t), (t, en_mechanical_issues(t))
        assert " you " not in f" {t.lower()} ", t


def test_select_returns_english():
    import re
    for code, items in pair_scenes.BANK.items():
        theme, _f, de_scene, _q = items[0]
        assert _ov()["scenes"][theme]["scene"] != de_scene
        assert not re.search(r"\b(einer|nicht|und)\b", _ov()["scenes"][theme]["scene"])
