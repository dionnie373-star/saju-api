"""일간(日干) 강약 분석 v3 — 실무 10점 만점 + 보정.

사용자 정의 배점 (일간 제외 7자리, 합계 10.0점):
  월지(月支)        3.5점  득령(得令)
  일지(日支)        1.5점  득지(得地)
  시지(時支)        1.0점
  연지(年支)        1.0점
  연간/월간/시간    각 1.0점 (총 3.0점)

가산 조건: 비겁(같은 오행) 또는 인성(생해주는 오행) 자리만.

등급 (5단계):
  극신강 ≥ 8.5 / 신강 5.5~8.4 / 중화 4.0~5.4 / 신약 2.0~3.9 / 극신약 < 2.0

보정:
  A. 월지 충 — 월지가 다른 지지와 충이면 -0.5
  B. 합화 변이 — 비겁/인성 천간이 합화로 외부 오행 변이하면 그 천간 0
  C. 통근 없는 천간 — 천간 비겁/인성이 지지 본기/중기/여기에 뿌리 없으면 ×0.5
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .cheon_gan import CheonGan
from .hapchung import HapChungAnalyzer, HapKind
from .ji_ji import JiJi
from .o_haeng import OHaeng
from .saju import Saju


class IlganStrengthLevel(Enum):
    GEUKSINKANG = ("極身強", "극신강")
    SINKANG = ("身強", "신강")
    JUNGHWA = ("中和", "중화")
    SINYAK = ("身弱", "신약")
    GEUKSINYAK = ("極身弱", "극신약")

    def __init__(self, hanja: str, hangul: str) -> None:
        self.hanja = hanja
        self.hangul = hangul


@dataclass(frozen=True, slots=True)
class IlganStrengthBreakdown:
    month_branch_score: float
    day_branch_score: float
    hour_branch_score: float
    year_branch_score: float
    year_stem_score: float
    month_stem_score: float
    hour_stem_score: float
    adjustment: float
    total: float
    level: IlganStrengthLevel
    reason: str

    # 기존 호출자 호환 alias.
    @property
    def deuk_ryeong(self) -> float:
        return self.month_branch_score

    @property
    def deuk_ji(self) -> float:
        return self.day_branch_score

    @property
    def deuk_sae(self) -> float:
        return (
            self.hour_branch_score + self.year_branch_score +
            self.year_stem_score + self.month_stem_score + self.hour_stem_score
        )

    @property
    def hap_chung_adjust(self) -> float:
        return self.adjustment

    def __str__(self) -> str:
        return (
            f"{self.level.hangul} ({self.total:.1f}/10) — 월지 {self.month_branch_score:.1f} "
            f"+ 일지 {self.day_branch_score:.1f} + 득세 {self.deuk_sae:.1f} "
            f"+ 보정 {self.adjustment:.1f}"
        )


_W_MONTH = 3.5
_W_DAY = 1.5
_W_HOUR = 1.0
_W_YEAR_BRANCH = 1.0
_W_STEM = 1.0


_GEN_CHAIN: tuple[OHaeng, ...] = (
    OHaeng.MOK, OHaeng.HWA, OHaeng.TO, OHaeng.GEUM, OHaeng.SU,
)


def _generates(a: OHaeng, b: OHaeng) -> bool:
    return (_GEN_CHAIN.index(a) + 1) % 5 == _GEN_CHAIN.index(b)


def _branch_score(day_oh: OHaeng, branch_oh: OHaeng, weight: float) -> float:
    if branch_oh is day_oh:
        return weight
    if _generates(branch_oh, day_oh):
        return weight
    return 0.0


def _stem_score_base(day_oh: OHaeng, stem_oh: OHaeng, weight: float) -> float:
    if stem_oh is day_oh:
        return weight
    if _generates(stem_oh, day_oh):
        return weight
    return 0.0


_CHUNG_OPPOSITE: dict[JiJi, JiJi] = {
    JiJi.JA: JiJi.O, JiJi.O: JiJi.JA,
    JiJi.CHUK: JiJi.MI, JiJi.MI: JiJi.CHUK,
    JiJi.IN: JiJi.SIN, JiJi.SIN: JiJi.IN,
    JiJi.MYO: JiJi.YU, JiJi.YU: JiJi.MYO,
    JiJi.JIN: JiJi.SUL, JiJi.SUL: JiJi.JIN,
    JiJi.SA: JiJi.HAE, JiJi.HAE: JiJi.SA,
}


def _level_of(total: float) -> IlganStrengthLevel:
    if total >= 8.5:
        return IlganStrengthLevel.GEUKSINKANG
    if total >= 5.5:
        return IlganStrengthLevel.SINKANG
    if total >= 4.0:
        return IlganStrengthLevel.JUNGHWA
    if total >= 2.0:
        return IlganStrengthLevel.SINYAK
    return IlganStrengthLevel.GEUKSINYAK


def _fmt(v: float) -> str:
    iv = int(v)
    return str(iv) if v == iv else f"{v:.1f}"


class IlganStrengthAnalyzer:
    """일간 강약 분석 — 10점 만점 실무 배점."""

    @staticmethod
    def analyze(saju: Saju) -> IlganStrengthBreakdown:
        day_oh = saju.day_stem.o_haeng

        # === 보정 B: 합화 변이 식별 ===
        hwaed_stems: set[CheonGan] = set()
        for h in HapChungAnalyzer.detect_hap(saju):
            if h.kind is not HapKind.CHEON_GAN_HAP:
                continue
            hwa = h.hwa_o_haeng
            if hwa is None:
                continue
            if hwa is not day_oh and not _generates(hwa, day_oh):
                for ch in h.members:
                    stem = CheonGan.from_hanja(ch)
                    if stem is not None:
                        hwaed_stems.add(stem)

        # === 지지 점수 ===
        month_branch_score = _branch_score(
            day_oh, saju.month_pillar.ji_ji.o_haeng, _W_MONTH)
        day_branch_score = _branch_score(
            day_oh, saju.day_pillar.ji_ji.o_haeng, _W_DAY)
        year_branch_score = _branch_score(
            day_oh, saju.year_pillar.ji_ji.o_haeng, _W_YEAR_BRANCH)
        hour_branch_score = (
            _branch_score(day_oh, saju.hour_pillar.ji_ji.o_haeng, _W_HOUR)
            if saju.hour_pillar is not None else 0.0
        )

        # === 천간 점수 (보정 B + 보정 C) ===
        all_branches: list[JiJi] = [
            saju.year_pillar.ji_ji,
            saju.month_pillar.ji_ji,
            saju.day_pillar.ji_ji,
        ]
        if saju.hour_pillar is not None:
            all_branches.append(saju.hour_pillar.ji_ji)

        def stem_score_for(stem: CheonGan) -> float:
            if stem in hwaed_stems:
                return 0.0
            raw = _stem_score_base(day_oh, stem.o_haeng, _W_STEM)
            if raw == 0.0:
                return 0.0
            # 통근: 본기/중기/여기 어디든 같은 오행 (정통 자평진전).
            has_root = any(
                b.o_haeng is stem.o_haeng or
                any(j.stem.o_haeng is stem.o_haeng for j in b.ji_jang_gan)
                for b in all_branches
            )
            return raw if has_root else raw * 0.5

        year_stem_score = stem_score_for(saju.year_pillar.cheon_gan)
        month_stem_score = stem_score_for(saju.month_pillar.cheon_gan)
        hour_stem_score = (
            stem_score_for(saju.hour_pillar.cheon_gan)
            if saju.hour_pillar is not None else 0.0
        )

        # === 보정 A: 월지 충 ===
        adjustment = 0.0
        if month_branch_score > 0:
            opposite = _CHUNG_OPPOSITE.get(saju.month_pillar.ji_ji)
            others = [saju.year_pillar.ji_ji, saju.day_pillar.ji_ji]
            if saju.hour_pillar is not None:
                others.append(saju.hour_pillar.ji_ji)
            if opposite is not None and opposite in others:
                adjustment -= 0.8

        # === 6글자(삼주) 모드 보정: 시주 기댓값 +1.0 ===
        # 시주 결손 사주는 base 8.0 만점이라 임계값 비도달. 통계 기댓값 +1.0.
        samju_mode = saju.hour_pillar is None
        expected_value_adjust = 1.0 if samju_mode else 0.0

        raw = (month_branch_score + day_branch_score + year_branch_score +
               hour_branch_score + year_stem_score + month_stem_score +
               hour_stem_score)
        total = max(0.0, min(10.0, raw + adjustment + expected_value_adjust))
        level = _level_of(total)

        parts = [
            f"월지({saju.month_pillar.ji_ji.hangul}) {_fmt(month_branch_score)}",
            f"일지({saju.day_pillar.ji_ji.hangul}) {_fmt(day_branch_score)}",
            f"연지 {_fmt(year_branch_score)}",
        ]
        if saju.hour_pillar is not None:
            parts.append(f"시지 {_fmt(hour_branch_score)}")
        parts.extend([
            f"연간 {_fmt(year_stem_score)}",
            f"월간 {_fmt(month_stem_score)}",
        ])
        if saju.hour_pillar is not None:
            parts.append(f"시간 {_fmt(hour_stem_score)}")
        reason = f"{' + '.join(parts)} = {_fmt(raw)}점"
        tags: list[str] = []
        if adjustment != 0:
            tags.append(f"월지충 {_fmt(adjustment)}")
        if expected_value_adjust != 0:
            tags.append(f"6글자 시주 기댓값 +{_fmt(expected_value_adjust)}")
        if tags:
            reason += f" / {', '.join(tags)} → {_fmt(total)}점"

        return IlganStrengthBreakdown(
            month_branch_score=month_branch_score,
            day_branch_score=day_branch_score,
            hour_branch_score=hour_branch_score,
            year_branch_score=year_branch_score,
            year_stem_score=year_stem_score,
            month_stem_score=month_stem_score,
            hour_stem_score=hour_stem_score,
            adjustment=adjustment,
            total=total,
            level=level,
            reason=reason,
        )
