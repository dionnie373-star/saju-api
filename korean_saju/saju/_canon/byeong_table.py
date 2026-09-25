"""격국별 병(病) → 약신(藥神) 매핑.

자평진전 "유병유약 시위귀명(有病有藥 始爲貴命)" — 병이 있고 약이 있으면 귀명.

검출 흐름:
  1. 격국 결정 후 사주 천간/지장간 본기에 byeong이 강하게 있는지 검사
  2. 존재하면 yak_sin을 용신 후보에 가산점 부여 (Deriver 측)
"""

from __future__ import annotations

from dataclasses import dataclass

from ..gyeokguk import Gyeokguk
from ..shipsin import Shipsin


@dataclass(frozen=True, slots=True)
class ByeongYak:
    byeong: Shipsin | None
    yak: Shipsin
    reason: str


_TABLE: dict[Gyeokguk, ByeongYak] = {
    Gyeokguk.JEONGGWAN_GYEOK: ByeongYak(
        byeong=Shipsin.SANGGWAN, yak=Shipsin.JEONGIN,
        reason="상관견관(傷官見官) → 인수제상(印綬制傷)",
    ),
    Gyeokguk.PYEONGWAN_GYEOK: ByeongYak(
        byeong=Shipsin.JEONGJAE, yak=Shipsin.SIKSIN,
        reason="재생살(財生殺) 過 → 식신제살(食神制殺)",
    ),
    Gyeokguk.JEONGIN_GYEOK: ByeongYak(
        byeong=Shipsin.JEONGJAE, yak=Shipsin.BIGYEON,
        reason="재극인(財剋印) → 비견 분재(分財)",
    ),
    Gyeokguk.PYEONIN_GYEOK: ByeongYak(
        byeong=Shipsin.JEONGJAE, yak=Shipsin.BIGYEON,
        reason="재극인 → 비견 분재",
    ),
    Gyeokguk.SIKSIN_GYEOK: ByeongYak(
        byeong=Shipsin.PYEONIN, yak=Shipsin.PYEONJAE,
        reason="도식(倒食) — 편인이 식신 탈취 → 재극인",
    ),
    Gyeokguk.SANGGWAN_GYEOK: ByeongYak(
        byeong=Shipsin.JEONGGWAN, yak=Shipsin.PYEONJAE,
        reason="상관견관 — 재성으로 통관 (상관생재→재생관)",
    ),
    Gyeokguk.JEONGJAE_GYEOK: ByeongYak(
        byeong=Shipsin.GEOPJAE, yak=Shipsin.JEONGGWAN,
        reason="군겁쟁재(群劫爭財) → 관성으로 비겁 제압",
    ),
    Gyeokguk.PYEONJAE_GYEOK: ByeongYak(
        byeong=Shipsin.GEOPJAE, yak=Shipsin.JEONGGWAN,
        reason="군겁쟁재 → 관성 제압",
    ),
    Gyeokguk.GEON_ROK_GYEOK: ByeongYak(
        byeong=None, yak=Shipsin.JEONGGWAN,
        reason="비겁 旺 → 관살로 설기·제압",
    ),
    Gyeokguk.YANG_IN_GYEOK: ByeongYak(
        byeong=None, yak=Shipsin.PYEONGWAN,
        reason="양인 旺 → 칠살로 합살·제인",
    ),
}


def byeong_for_gyeokguk(gyeokguk: Gyeokguk) -> ByeongYak | None:
    return _TABLE.get(gyeokguk)
