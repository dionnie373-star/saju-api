"""격국 × 일간 강약 → 상신(相神) 후보 십신 매핑.

출처: 자평진전 順用·逆用 원칙 + 한국 실무 명리 절충.
順用 (財·官·印·食): 격을 보호·생조
逆用 (殺·傷·刃)   : 격을 제압·견제
"""

from __future__ import annotations

from ..gyeokguk import Gyeokguk
from ..ilgan_strength import IlganStrengthLevel
from ..shipsin import Shipsin

# 신강·신약 단순 분기 표. 중화·극신강·극신약은 forLevel에서 매핑.
_BASE: dict[tuple[Gyeokguk, IlganStrengthLevel], tuple[Shipsin, ...]] = {
    # === 順用 4길신 ===
    # 정관격
    (Gyeokguk.JEONGGWAN_GYEOK, IlganStrengthLevel.SINKANG):
        (Shipsin.PYEONJAE, Shipsin.JEONGJAE),
    (Gyeokguk.JEONGGWAN_GYEOK, IlganStrengthLevel.SINYAK):
        (Shipsin.JEONGIN, Shipsin.PYEONIN, Shipsin.BIGYEON),
    # 정인격
    (Gyeokguk.JEONGIN_GYEOK, IlganStrengthLevel.SINKANG):
        (Shipsin.PYEONJAE, Shipsin.JEONGJAE),
    (Gyeokguk.JEONGIN_GYEOK, IlganStrengthLevel.SINYAK):
        (Shipsin.JEONGGWAN, Shipsin.PYEONGWAN),
    # 편인격
    (Gyeokguk.PYEONIN_GYEOK, IlganStrengthLevel.SINKANG):
        (Shipsin.PYEONJAE, Shipsin.JEONGJAE),
    (Gyeokguk.PYEONIN_GYEOK, IlganStrengthLevel.SINYAK):
        (Shipsin.JEONGGWAN, Shipsin.PYEONGWAN),
    # 식신격
    (Gyeokguk.SIKSIN_GYEOK, IlganStrengthLevel.SINKANG):
        (Shipsin.PYEONJAE, Shipsin.JEONGJAE),
    (Gyeokguk.SIKSIN_GYEOK, IlganStrengthLevel.SINYAK):
        (Shipsin.BIGYEON, Shipsin.GEOPJAE, Shipsin.JEONGIN),
    # 정재격
    (Gyeokguk.JEONGJAE_GYEOK, IlganStrengthLevel.SINKANG):
        (Shipsin.JEONGGWAN, Shipsin.PYEONGWAN),
    (Gyeokguk.JEONGJAE_GYEOK, IlganStrengthLevel.SINYAK):
        (Shipsin.BIGYEON, Shipsin.GEOPJAE),
    # 편재격
    (Gyeokguk.PYEONJAE_GYEOK, IlganStrengthLevel.SINKANG):
        (Shipsin.JEONGGWAN, Shipsin.PYEONGWAN),
    (Gyeokguk.PYEONJAE_GYEOK, IlganStrengthLevel.SINYAK):
        (Shipsin.BIGYEON, Shipsin.GEOPJAE),
    # === 逆用 흉신 ===
    # 칠살격(편관)
    (Gyeokguk.PYEONGWAN_GYEOK, IlganStrengthLevel.SINKANG):
        (Shipsin.SIKSIN, Shipsin.GEOPJAE),
    (Gyeokguk.PYEONGWAN_GYEOK, IlganStrengthLevel.SINYAK):
        (Shipsin.JEONGIN, Shipsin.PYEONIN),
    # 상관격
    (Gyeokguk.SANGGWAN_GYEOK, IlganStrengthLevel.SINKANG):
        (Shipsin.PYEONJAE, Shipsin.JEONGJAE),
    (Gyeokguk.SANGGWAN_GYEOK, IlganStrengthLevel.SINYAK):
        (Shipsin.JEONGIN,),
    # === 비겁 별격 ===
    (Gyeokguk.GEON_ROK_GYEOK, IlganStrengthLevel.SINKANG):
        (Shipsin.JEONGGWAN, Shipsin.PYEONGWAN, Shipsin.SIKSIN),
    (Gyeokguk.GEON_ROK_GYEOK, IlganStrengthLevel.SINYAK): (),
    (Gyeokguk.YANG_IN_GYEOK, IlganStrengthLevel.SINKANG):
        (Shipsin.PYEONGWAN, Shipsin.JEONGGWAN),
    (Gyeokguk.YANG_IN_GYEOK, IlganStrengthLevel.SINYAK): (),
}


def sanggwan_for_level(
    gyeokguk: Gyeokguk, level: IlganStrengthLevel,
) -> tuple[Shipsin, ...]:
    """격국·강약에 해당하는 상신 후보 우선순위 tuple.

    빈 tuple이면 표준 처방 없음 (모순 케이스 또는 별격).
    중화는 신강 처방 차용, 극신강/극신약은 동일 처방.
    """
    if level in (IlganStrengthLevel.GEUKSINKANG, IlganStrengthLevel.SINKANG,
                 IlganStrengthLevel.JUNGHWA):
        mapped = IlganStrengthLevel.SINKANG
    else:  # SINYAK, GEUKSINYAK
        mapped = IlganStrengthLevel.SINYAK
    return _BASE.get((gyeokguk, mapped), ())
