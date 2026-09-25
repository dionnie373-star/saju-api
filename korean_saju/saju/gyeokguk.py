"""격국(格局) — 자평진전 표준 8정격 + 건록격(建祿格)·양인격(羊刃格).

결정 흐름:
  0. 월지가 일간 록(祿) 위치 → 건록격 (모든 일간)
  1. 월지가 일간 양인(羊刃) 위치 → 양인격
     - 자평진전 정통: 양일간(갑·병·무·경·임) 제왕 위치만 양인격
     - 음일간 양인은 정론에서 불인정 (한국 학파 일부만)
  2. 그 외: 월지 본기→중기→여기 순서로 천간 4자리(연·월·시 — 일간 제외)에
     투간된 첫 글자의 십신 → 8정격 (단, 일간 비겁 제외)
  3. 모두 투간 안 됐으면 월지 본기 십신 fallback (성격 X)
     - 본기가 일간 비겁이면 잡기재관(雜氣財官) 케이스: 중기·여기 차용

결과 GyeokgukResult에는 성격(成格) 여부와 병약(病藥) 라벨이 함께 담긴다.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .cheon_gan import CheonGan
from .ji_jang_gan import JiJangGanComponent, JiJangGanRole
from .ji_ji import JiJi
from .o_haeng import OHaeng
from .saju import Saju
from .shipsin import Shipsin, ShipsinCalculator


class Gyeokguk(Enum):
    SIKSIN_GYEOK = ("食神格", "식신격")
    SANGGWAN_GYEOK = ("傷官格", "상관격")
    PYEONJAE_GYEOK = ("偏財格", "편재격")
    JEONGJAE_GYEOK = ("正財格", "정재격")
    PYEONGWAN_GYEOK = ("偏官格", "편관격")
    JEONGGWAN_GYEOK = ("正官格", "정관격")
    PYEONIN_GYEOK = ("偏印格", "편인격")
    JEONGIN_GYEOK = ("正印格", "정인격")
    GEON_ROK_GYEOK = ("建祿格", "건록격")
    YANG_IN_GYEOK = ("羊刃格", "양인격")
    JIJI_HAPHWA_GYEOK = ("地支合化格", "지지합화격")

    def __init__(self, hanja: str, hangul: str) -> None:
        self.hanja = hanja
        self.hangul = hangul

    @classmethod
    def from_shipsin(cls, s: Shipsin) -> Gyeokguk:
        return _SHIPSIN_TO_GYEOKGUK[s]


_SHIPSIN_TO_GYEOKGUK: dict[Shipsin, Gyeokguk] = {
    Shipsin.BIGYEON: Gyeokguk.GEON_ROK_GYEOK,
    Shipsin.GEOPJAE: Gyeokguk.YANG_IN_GYEOK,
    Shipsin.SIKSIN: Gyeokguk.SIKSIN_GYEOK,
    Shipsin.SANGGWAN: Gyeokguk.SANGGWAN_GYEOK,
    Shipsin.PYEONJAE: Gyeokguk.PYEONJAE_GYEOK,
    Shipsin.JEONGJAE: Gyeokguk.JEONGJAE_GYEOK,
    Shipsin.PYEONGWAN: Gyeokguk.PYEONGWAN_GYEOK,
    Shipsin.JEONGGWAN: Gyeokguk.JEONGGWAN_GYEOK,
    Shipsin.PYEONIN: Gyeokguk.PYEONIN_GYEOK,
    Shipsin.JEONGIN: Gyeokguk.JEONGIN_GYEOK,
}

_ROK_POSITION: dict[CheonGan, JiJi] = {
    CheonGan.GAP: JiJi.IN, CheonGan.EUL: JiJi.MYO,
    CheonGan.BYEONG: JiJi.SA, CheonGan.JEONG: JiJi.O,
    CheonGan.MU: JiJi.SA, CheonGan.GI: JiJi.O,
    CheonGan.GYEONG: JiJi.SIN, CheonGan.SIN: JiJi.YU,
    CheonGan.IM: JiJi.HAE, CheonGan.GYE: JiJi.JA,
}

# 자평진전 정통: 양일간만 12운성 제왕(帝旺) → 양인격.
# 음일간 양인은 정론에서 불인정 (사용자 결정: 정통 채택).
_YANG_IN_POSITION: dict[CheonGan, JiJi] = {
    CheonGan.GAP: JiJi.MYO,
    CheonGan.BYEONG: JiJi.O,
    CheonGan.MU: JiJi.O,
    CheonGan.GYEONG: JiJi.YU,
    CheonGan.IM: JiJi.JA,
}


@dataclass(frozen=True, slots=True)
class GyeokgukResult:
    gyeokguk: Gyeokguk
    basis_stem: CheonGan
    basis: str
    is_seonggyeok: bool
    """성격(成格) 여부 — 월지 투간 또는 별격(건록·양인)으로 명확히 결정됐는가."""
    byeong: Shipsin | None
    """격국의 병(病) — 사주에 존재 시 격국을 깨는 십신. 별격은 None."""
    yak_sin: Shipsin
    """약신(藥神) — 병을 제압·견제하는 십신."""
    byeong_yak_reason: str

    def __str__(self) -> str:
        seong = "成格" if self.is_seonggyeok else "未成格"
        byeong_str = self.byeong.hangul if self.byeong else "없음"
        return (
            f"{self.gyeokguk.hangul}({self.gyeokguk.hanja}) {seong} — {self.basis} "
            f"[병={byeong_str} 약={self.yak_sin.hangul}]"
        )


def _stems_in(saju: Saju) -> set[CheonGan]:
    result = {saju.year_pillar.cheon_gan, saju.month_pillar.cheon_gan}
    if saju.hour_pillar is not None:
        result.add(saju.hour_pillar.cheon_gan)
    return result


def _bongi_first_order(components: list[JiJangGanComponent]) -> list[JiJangGanComponent]:
    bongi = next(c for c in components if c.role is JiJangGanRole.BONGI)
    junggi = [c for c in components if c.role is JiJangGanRole.JUNGGI]
    yeogi = [c for c in components if c.role is JiJangGanRole.YEOGI]
    return [bongi, *junggi, *yeogi]


# 삼합/방합 — (멤버 3개, 화 오행).
_SAM_HAPS: tuple[tuple[tuple[JiJi, ...], OHaeng], ...] = (
    ((JiJi.SIN, JiJi.JA, JiJi.JIN), OHaeng.SU),
    ((JiJi.IN, JiJi.O, JiJi.SUL), OHaeng.HWA),
    ((JiJi.SA, JiJi.YU, JiJi.CHUK), OHaeng.GEUM),
    ((JiJi.HAE, JiJi.MYO, JiJi.MI), OHaeng.MOK),
)
_BANG_HAPS: tuple[tuple[tuple[JiJi, ...], OHaeng], ...] = (
    ((JiJi.IN, JiJi.MYO, JiJi.JIN), OHaeng.MOK),
    ((JiJi.SA, JiJi.O, JiJi.MI), OHaeng.HWA),
    ((JiJi.SIN, JiJi.YU, JiJi.SUL), OHaeng.GEUM),
    ((JiJi.HAE, JiJi.JA, JiJi.CHUK), OHaeng.SU),
)

_YANG_STEM: dict[OHaeng, CheonGan] = {
    OHaeng.MOK: CheonGan.GAP,
    OHaeng.HWA: CheonGan.BYEONG,
    OHaeng.TO: CheonGan.MU,
    OHaeng.GEUM: CheonGan.GYEONG,
    OHaeng.SU: CheonGan.IM,
}


def _yang_stem_of(o: OHaeng) -> CheonGan:
    return _YANG_STEM[o]


def _month_branch_hap_hwa(saju: Saju) -> OHaeng | None:
    """월지가 삼합/방합으로 합화된 오행. 합화 안 됐으면 None."""
    month_branch = saju.month_pillar.ji_ji
    branches = {
        saju.year_pillar.ji_ji, saju.month_pillar.ji_ji,
        saju.day_pillar.ji_ji,
    }
    if saju.hour_pillar is not None:
        branches.add(saju.hour_pillar.ji_ji)
    for members, hwa in (*_SAM_HAPS, *_BANG_HAPS):
        if month_branch not in members:
            continue
        if all(m in branches for m in members):
            return hwa
    return None


def _label_byeong_yak(
    *, gyeokguk: Gyeokguk, basis_stem: CheonGan, basis: str, is_seonggyeok: bool,
) -> GyeokgukResult:
    """격국 후처리 — 병약 라벨링."""
    # 순환 import 회피 — runtime import.
    from ._canon.byeong_table import byeong_for_gyeokguk

    by = byeong_for_gyeokguk(gyeokguk)
    return GyeokgukResult(
        gyeokguk=gyeokguk,
        basis_stem=basis_stem,
        basis=basis,
        is_seonggyeok=is_seonggyeok,
        byeong=by.byeong if by else None,
        yak_sin=by.yak if by else Shipsin.BIGYEON,
        byeong_yak_reason=by.reason if by else "정의 없음",
    )


class GyeokgukCalculator:
    """격국 결정."""

    @staticmethod
    def determine(saju: Saju) -> GyeokgukResult:
        month_branch = saju.month_pillar.ji_ji
        day_stem = saju.day_stem

        # 0. 월지가 일간 록 위치 → 건록격
        if _ROK_POSITION[day_stem] is month_branch:
            return _label_byeong_yak(
                gyeokguk=Gyeokguk.GEON_ROK_GYEOK,
                basis_stem=day_stem,
                basis=f"월지 {month_branch.hangul}이 일간 {day_stem.hangul}의 록(祿) 위치",
                is_seonggyeok=True,
            )

        # 1. 월지가 일간 양인 위치 (양일간만) → 양인격
        if _YANG_IN_POSITION.get(day_stem) is month_branch:
            return _label_byeong_yak(
                gyeokguk=Gyeokguk.YANG_IN_GYEOK,
                basis_stem=day_stem,
                basis=f"월지 {month_branch.hangul}이 일간 {day_stem.hangul}의 양인(제왕) 위치",
                is_seonggyeok=True,
            )

        # 2. 8정격 — 월지 본기→중기→여기 투간 검사 (일간 제외)
        stems_in_saju = _stems_in(saju)
        for component in _bongi_first_order(month_branch.ji_jang_gan):
            if component.stem in stems_in_saju:
                shipsin = ShipsinCalculator.for_cheon_gan(day_stem, component.stem)
                if shipsin in (Shipsin.BIGYEON, Shipsin.GEOPJAE):
                    continue
                return _label_byeong_yak(
                    gyeokguk=Gyeokguk.from_shipsin(shipsin),
                    basis_stem=component.stem,
                    basis=f"월지 {component.role.hangul} 투간",
                    is_seonggyeok=True,
                )

        # 3. 불투 — 월지가 삼합/방합으로 합화되면 지지합화격.
        month_hwa = _month_branch_hap_hwa(saju)
        if month_hwa is not None:
            return _label_byeong_yak(
                gyeokguk=Gyeokguk.JIJI_HAPHWA_GYEOK,
                basis_stem=_yang_stem_of(month_hwa),
                basis=f"월지 {month_branch.hangul} → {month_hwa.hangul}국 "
                f"지지합화 (투간 없음)",
                is_seonggyeok=True,
            )

        # 4. fallback — 월지 본기 십신 (성격 X)
        #   - 본기 십신이 일간 비겁이면 잡기재관 케이스: 중기·여기로 차용.
        bongi = month_branch.bongi
        bongi_shipsin = ShipsinCalculator.for_cheon_gan(day_stem, bongi)

        if bongi_shipsin in (Shipsin.BIGYEON, Shipsin.GEOPJAE):
            for c in _bongi_first_order(month_branch.ji_jang_gan):
                if c.role is JiJangGanRole.BONGI:
                    continue
                s = ShipsinCalculator.for_cheon_gan(day_stem, c.stem)
                if s in (Shipsin.BIGYEON, Shipsin.GEOPJAE):
                    continue
                return _label_byeong_yak(
                    gyeokguk=Gyeokguk.from_shipsin(s),
                    basis_stem=c.stem,
                    basis=f"월지 본기 비겁 — {c.role.hangul} {c.stem.hangul} 차용 (잡기재관)",
                    is_seonggyeok=False,
                )

        return _label_byeong_yak(
            gyeokguk=Gyeokguk.from_shipsin(bongi_shipsin),
            basis_stem=bongi,
            basis="월지 본기 (투간 없음)",
            is_seonggyeok=False,
        )
