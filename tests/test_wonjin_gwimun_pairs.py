"""원진살과 귀문관살은 子·寅의 짝만 다르다 (원진 子未·寅酉 / 귀문 子酉·寅未)."""
from korean_saju.saju import sinsal
from korean_saju.saju.ji_ji import JiJi


def _has(pairs, a, b):
    return frozenset({a, b}) in pairs


def test_wonjin_pairs():
    p = sinsal._WONJIN_PAIRS
    assert len(p) == 6
    assert _has(p, JiJi.JA, JiJi.MI) and _has(p, JiJi.IN, JiJi.YU)
    assert not _has(p, JiJi.JA, JiJi.YU) and not _has(p, JiJi.IN, JiJi.MI)


def test_gwimun_pairs():
    p = sinsal._GWIMUN_PAIRS
    assert len(p) == 6
    assert _has(p, JiJi.JA, JiJi.YU) and _has(p, JiJi.IN, JiJi.MI)
    assert not _has(p, JiJi.JA, JiJi.MI) and not _has(p, JiJi.IN, JiJi.YU)


def test_shared_pairs_identical():
    shared = {frozenset({JiJi.CHUK, JiJi.O}), frozenset({JiJi.MYO, JiJi.SIN}),
              frozenset({JiJi.JIN, JiJi.HAE}), frozenset({JiJi.SA, JiJi.SUL})}
    assert shared <= set(sinsal._WONJIN_PAIRS)
    assert shared <= set(sinsal._GWIMUN_PAIRS)
