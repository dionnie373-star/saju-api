"""궁합 리포트의 선택적 성별(gender_a/gender_b) 처리에 대한 회귀 테스트.

배경: 궁합 계산 자체(오행/일간 비교)에는 성별이 전혀 쓰이지 않는다 — 성별은
daewoon(대운) 계산에만 필요하고 궁합 리포트엔 daewoon이 없다. 그래서 성별
필드는 순전히 "리포트 문장에서 자연스러운 독일어 대명사(sie/er)를 쓸지"를
결정하는 선택 입력으로 추가했다. "divers"를 고르거나 아예 선택하지 않으면
성별을 추측하지 않고 이름 반복 등 중립적인 표현으로 안전하게 대체되도록
프롬프트에 "keine Angabe"로 전달되어야 한다 (제3의 성을 배제하지 않으면서도,
독일어에 널리 합의된 성별 중립 대명사가 없다는 현실적 한계를 존중하는 절충안).

이 테스트는 Anthropic/Brevo를 전혀 호출하지 않는다 — call_claude와
send_email을 monkeypatch로 가짜 함수로 바꿔서 run_compatibility_signup이
프롬프트에 넘기는 변수만 검증한다.

실행: cd /home/claude/saju-api && python3 -m unittest discover tests -v
"""
import os
import unittest

os.environ.setdefault("ANTHROPIC_API_KEY", "test-not-used")
os.environ.setdefault("BREVO_API_KEY", "test-not-used")
os.environ.setdefault("FROM_EMAIL", "test@example.com")
os.environ.setdefault("FROM_NAME", "Palja Test")

import report_pipeline as rp  # noqa: E402


class CompatibilityGenderTests(unittest.TestCase):
    def setUp(self):
        self._orig_call_claude = rp.call_claude
        self._orig_send_email = rp.send_email
        self.captured_variables = None
        rp.call_claude = self._fake_call_claude
        rp.send_email = lambda **kw: None

    def tearDown(self):
        rp.call_claude = self._orig_call_claude
        rp.send_email = self._orig_send_email

    def _fake_call_claude(self, prompt_template_name, variables, **kw):
        self.captured_variables = variables
        return "Test-Reportinhalt."

    def _run(self, gender_a=None, gender_b=None):
        payload = {
            "email": "test@example.com",
            "name_a": "Anna",
            "name_b": "Ben",
        }
        if gender_a is not None:
            payload["gender_a"] = gender_a
        if gender_b is not None:
            payload["gender_b"] = gender_b

        calc_result_a = {"compact": "Person A 사주 데이터"}
        calc_result_b = {"compact": "Person B 사주 데이터"}

        rp.run_compatibility_signup(payload=payload, calc_result_a=calc_result_a, calc_result_b=calc_result_b)
        return self.captured_variables

    def test_explicit_female_and_male_pass_through_as_german_labels(self):
        variables = self._run(gender_a="female", gender_b="male")
        self.assertEqual(variables["gender_a"], "weiblich")
        self.assertEqual(variables["gender_b"], "männlich")

    def test_missing_gender_falls_back_to_no_assumption(self):
        variables = self._run(gender_a=None, gender_b=None)
        self.assertEqual(variables["gender_a"], "keine Angabe")
        self.assertEqual(variables["gender_b"], "keine Angabe")

    def test_empty_string_gender_falls_back_to_no_assumption(self):
        """폼에서 '선택 안 함' 옵션은 빈 문자열로 전송된다."""
        variables = self._run(gender_a="", gender_b="")
        self.assertEqual(variables["gender_a"], "keine Angabe")
        self.assertEqual(variables["gender_b"], "keine Angabe")

    def test_divers_does_not_get_mapped_to_a_binary_gender(self):
        """'divers'를 선택해도 male/female로 잘못 추측되면 안 된다 — 이름 기반
        중립 표현으로 안전하게 처리되도록 'keine Angabe'와 동일하게 취급한다."""
        variables = self._run(gender_a="divers", gender_b="female")
        self.assertEqual(variables["gender_a"], "keine Angabe")
        self.assertEqual(variables["gender_b"], "weiblich")

    def test_mixed_one_specified_one_not_handled_independently(self):
        variables = self._run(gender_a="male", gender_b=None)
        self.assertEqual(variables["gender_a"], "männlich")
        self.assertEqual(variables["gender_b"], "keine Angabe")

    def test_gender_is_case_insensitive(self):
        variables = self._run(gender_a="FEMALE", gender_b="Male")
        self.assertEqual(variables["gender_a"], "weiblich")
        self.assertEqual(variables["gender_b"], "männlich")


if __name__ == "__main__":
    unittest.main()
