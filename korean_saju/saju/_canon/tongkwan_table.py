"""통관(通關) 용신 — 두 오행이 강력 대립 시 중재 오행.

정론: 두 오행이 상극 관계로 동일하게 강할 때, 그 사이를 生하여 흐름을 잇는 오행.
木剋土: 木·土 → 火 (木生火, 火生土)
土剋水: 土·水 → 金
水剋火: 水·火 → 木
火剋金: 火·金 → 土
金剋木: 金·木 → 水
"""

from __future__ import annotations

from dataclasses import dataclass

from ..o_haeng import OHaeng

# 정렬된 (a, b) tuple → 통관 오행. a.index < b.index 보장.
_PAIR: dict[tuple[OHaeng, OHaeng], OHaeng] = {
    (OHaeng.MOK, OHaeng.TO): OHaeng.HWA,
    (OHaeng.TO, OHaeng.SU): OHaeng.GEUM,
    (OHaeng.HWA, OHaeng.SU): OHaeng.MOK,
    (OHaeng.HWA, OHaeng.GEUM): OHaeng.TO,
    (OHaeng.MOK, OHaeng.GEUM): OHaeng.SU,
}


@dataclass(frozen=True, slots=True)
class TongkwanMatch:
    opposing_a: OHaeng
    opposing_b: OHaeng
    mediator: OHaeng
    count_a: int
    count_b: int

    def __str__(self) -> str:
        return (
            f"{self.opposing_a.hangul}({self.count_a}) vs "
            f"{self.opposing_b.hangul}({self.count_b}) → 통관 {self.mediator.hangul}"
        )


def _ohaeng_idx(o: OHaeng) -> int:
    """OHaeng의 정렬용 index — mok=0, hwa=1, to=2, geum=3, su=4."""
    order = (OHaeng.MOK, OHaeng.HWA, OHaeng.TO, OHaeng.GEUM, OHaeng.SU)
    return order.index(o)


def mediator(a: OHaeng, b: OHaeng) -> OHaeng | None:
    """[a]와 [b] 사이를 통관할 오행. 상극 관계가 아니면 None."""
    if _ohaeng_idx(a) < _ohaeng_idx(b):
        first, second = a, b
    else:
        first, second = b, a
    return _PAIR.get((first, second))


def find_if_applicable(
    counts: dict[OHaeng, int], threshold: int = 3,
) -> TongkwanMatch | None:
    """사주 5오행 카운트에서 통관 후보 검색.

    임계 [threshold] 이상 두 오행이 상극 관계면 그 쌍의 통관 오행 반환.
    """
    strong = [o for o, c in counts.items() if c >= threshold]
    for i in range(len(strong)):
        for j in range(i + 1, len(strong)):
            a, b = strong[i], strong[j]
            med = mediator(a, b)
            if med is not None:
                return TongkwanMatch(
                    opposing_a=a, opposing_b=b, mediator=med,
                    count_a=counts[a], count_b=counts[b],
                )
    return None
