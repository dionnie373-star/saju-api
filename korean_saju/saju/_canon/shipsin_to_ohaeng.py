"""십신(十神) → 오행(五行) 변환 — 일간 의존.

십신은 일간과의 관계 라벨이라 오행이 일간에 따라 달라진다.
예: 일간 甲(木) 기준 정관 = 辛(金), 일간 庚(金) 기준 정관 = 丁(火).
"""

from __future__ import annotations

from ..cheon_gan import CheonGan
from ..o_haeng import OHaeng
from ..shipsin import Shipsin

_GEN_CHAIN: tuple[OHaeng, ...] = (
    OHaeng.MOK, OHaeng.HWA, OHaeng.TO, OHaeng.GEUM, OHaeng.SU,
)
_OVR_CHAIN: tuple[OHaeng, ...] = (
    OHaeng.MOK, OHaeng.TO, OHaeng.SU, OHaeng.HWA, OHaeng.GEUM,
)


def _generated_by(o: OHaeng) -> OHaeng:
    return _GEN_CHAIN[(_GEN_CHAIN.index(o) + 1) % 5]


def _generating_of(o: OHaeng) -> OHaeng:
    return _GEN_CHAIN[(_GEN_CHAIN.index(o) - 1 + 5) % 5]


def _overcoming_of(o: OHaeng) -> OHaeng:
    return _OVR_CHAIN[(_OVR_CHAIN.index(o) + 1) % 5]


def _overcoming_from(o: OHaeng) -> OHaeng:
    return _OVR_CHAIN[(_OVR_CHAIN.index(o) - 1 + 5) % 5]


def shipsin_to_ohaeng(day_stem: CheonGan, shipsin: Shipsin) -> OHaeng:
    """일간 [day_stem] 기준 [shipsin] 십신의 오행."""
    day_oh = day_stem.o_haeng
    if shipsin in (Shipsin.BIGYEON, Shipsin.GEOPJAE):
        return day_oh
    if shipsin in (Shipsin.SIKSIN, Shipsin.SANGGWAN):
        return _generated_by(day_oh)
    if shipsin in (Shipsin.PYEONJAE, Shipsin.JEONGJAE):
        return _overcoming_of(day_oh)
    if shipsin in (Shipsin.PYEONGWAN, Shipsin.JEONGGWAN):
        return _overcoming_from(day_oh)
    if shipsin in (Shipsin.PYEONIN, Shipsin.JEONGIN):
        return _generating_of(day_oh)
    raise ValueError(f"unknown Shipsin: {shipsin}")
