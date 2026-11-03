import unittest
import pair_scenes
from i18n import MECHANICAL_ISSUES


class PairScenesFrTest(unittest.TestCase):
    def setUp(self):
        self.ov = pair_scenes.load_overlay("fr")

    def test_overlay_covers_bank(self):
        themes = {sc[0] for scs in pair_scenes.BANK.values() for sc in scs}
        self.assertEqual(themes - set(self.ov["scenes"]), set())

    def test_pattern_names(self):
        self.assertEqual(len(self.ov["pattern_names"]), 6)

    def test_texts_pass_mechanical(self):
        check = MECHANICAL_ISSUES["fr"]
        for th, v in self.ov["scenes"].items():
            issues = check(v["scene"] + " " + v["question"])
            bad = [i for i in issues if "mots" not in str(i).lower() and "word" not in str(i).lower()]
            self.assertEqual(bad, [], th)


if __name__ == "__main__":
    unittest.main()
