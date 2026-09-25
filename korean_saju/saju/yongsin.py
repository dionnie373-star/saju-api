"""용신(用神) v5 — 억부(Stage 1·2) + 조후(Stage 3) 결합.

Stage 1: 지지 환경 전처리 (합화·묘지·왕지)
Stage 2: 위치 카운트 → 억부 분류 (신강/중화/신약)
Stage 3: 계절성 조후 분류 (한습/난조/평탄)

조후 우선 결합:
  한습 → 용신 火, 희신 木
  난조 → 용신 水, 희신 金
  평탄 → 억부 용신·희신:
    신강 → 식상·재성 / 중화 → 관성·재성 / 신약 → 인성·비겁
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from .cheon_gan import CheonGan
from .gyeokguk import GyeokgukResult
from .ilgan_strength import IlganStrengthBreakdown, IlganStrengthLevel
from .ji_ji import JiJi
from .johu import JohuAnalysis
from .o_haeng import OHaeng
from .oegyeok import OegyeokResult, OegyeokType, OegyeokVerdict
from .saju import Saju


class YongsinRole(Enum):
    YONG = ("用神", "용신", "사주를 가장 좋게 하는 오행")
    HEE = ("喜神", "희신", "용신을 보좌·생조하는 오행")
    HAN = ("閑神", "한신", "중립 — 길흉 약함")
    GU = ("仇神", "구신", "기신을 도와주는 오행")
    GI = ("忌神", "기신", "용신을 극하는 오행 — 가장 흉")

    def __init__(self, hanja: str, hangul: str, description: str) -> None:
        self.hanja = hanja
        self.hangul = hangul
        self.description = description


class YongsinMethod(Enum):
    JEONWANG = ("全旺", "전왕")
    EOKBU = ("抑扶", "억부")
    JOHU = ("調候", "조후")
    GYEOKGUK = ("格局", "격국")
    TONGKWAN = ("通關", "통관")
    BYEONGYAK = ("病藥", "병약")
    PENDING = ("未定", "미정")

    def __init__(self, hanja: str, hangul: str) -> None:
        self.hanja = hanja
        self.hangul = hangul


class JohuState(Enum):
    HANSEUP = ("寒濕", "한습")
    NANJO = ("暖燥", "난조")
    PYEONGTAN = ("平坦", "평탄")

    def __init__(self, hanja: str, hangul: str) -> None:
        self.hanja = hanja
        self.hangul = hangul


@dataclass(frozen=True, slots=True)
class JohuClassification:
    """Stage 3 조후 분류 결과."""
    state: JohuState
    season_label: str
    hanseup_count: int
    nanjo_count: int
    by_taegwa: bool
    reason: str


@dataclass(frozen=True, slots=True)
class EokbuClassification:
    """Stage 1·2 억부 분류 결과."""
    level: IlganStrengthLevel
    deuk_ryeong: bool
    deuk_ji: bool
    ally_count: int
    wang_ji_premium: bool
    reason: str


@dataclass(frozen=True, slots=True)
class YongsinResult:
    yong_o_haeng: OHaeng
    method: YongsinMethod
    classifications: dict[OHaeng, YongsinRole]
    reason: str
    bo_o_haeng: OHaeng | None = None
    bo_method: YongsinMethod | None = None
    ilgan_strength: IlganStrengthBreakdown | None = None
    johu: JohuAnalysis | None = None
    gyeokguk: GyeokgukResult | None = None
    eokbu: EokbuClassification | None = None
    johu_class: JohuClassification | None = None
    element_counts: dict[OHaeng, int] = field(default_factory=dict)
    neutralized: frozenset[OHaeng] = field(default_factory=frozenset)

    def role_for(self, o: OHaeng) -> YongsinRole:
        return self.classifications[o]

    @property
    def has_bo_o_haeng(self) -> bool:
        return self.bo_o_haeng is not None

    @property
    def hee_o_haeng(self) -> OHaeng:
        """희신 오행 — classifications에서 HEE 자리."""
        return next(o for o, r in self.classifications.items()
                    if r is YongsinRole.HEE)

    def __str__(self) -> str:
        base = f"용신={self.yong_o_haeng.hangul}[{self.method.hangul}]"
        if self.has_bo_o_haeng and self.bo_method is not None:
            return f"{base} / 보조={self.bo_o_haeng.hangul}[{self.bo_method.hangul}]"  # type: ignore[union-attr]
        return base


# ============================================================================
# Stage 1 helpers
# ============================================================================

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

_WANG_JI = frozenset({JiJi.JA, JiJi.O, JiJi.MYO, JiJi.YU})
_MYO_JI = frozenset({JiJi.JIN, JiJi.SUL, JiJi.CHUK, JiJi.MI})

# Stage 3 그룹
_HANSEUP_GROUP = frozenset({JiJi.SIN, JiJi.YU, JiJi.HAE, JiJi.JA, JiJi.CHUK})
_NANJO_GROUP = frozenset({JiJi.IN, JiJi.O, JiJi.SUL, JiJi.SA, JiJi.MI})
_WINTER = frozenset({JiJi.HAE, JiJi.JA, JiJi.CHUK})
_SUMMER = frozenset({JiJi.SA, JiJi.O, JiJi.MI})
_SPRING = frozenset({JiJi.IN, JiJi.MYO, JiJi.JIN})

_GEN_CHAIN: tuple[OHaeng, ...] = (
    OHaeng.MOK, OHaeng.HWA, OHaeng.TO, OHaeng.GEUM, OHaeng.SU,
)
_OVR_CHAIN: tuple[OHaeng, ...] = (
    OHaeng.MOK, OHaeng.TO, OHaeng.SU, OHaeng.HWA, OHaeng.GEUM,
)


def _generates(a: OHaeng, b: OHaeng) -> bool:
    return (_GEN_CHAIN.index(a) + 1) % 5 == _GEN_CHAIN.index(b)


def _generated_by(o: OHaeng) -> OHaeng:
    return _GEN_CHAIN[(_GEN_CHAIN.index(o) + 1) % 5]


def _generating_of(o: OHaeng) -> OHaeng:
    return _GEN_CHAIN[(_GEN_CHAIN.index(o) - 1 + 5) % 5]


def _overcoming_of(o: OHaeng) -> OHaeng:
    return _OVR_CHAIN[(_OVR_CHAIN.index(o) + 1) % 5]


def _overcoming_from(o: OHaeng) -> OHaeng:
    return _OVR_CHAIN[(_OVR_CHAIN.index(o) - 1 + 5) % 5]


def _hap_effective_o_haeng(
    target: JiJi, saju_branches: frozenset[JiJi],
) -> OHaeng | None:
    for members, hwa in (*_SAM_HAPS, *_BANG_HAPS):
        if target not in members:
            continue
        if all(m in saju_branches for m in members):
            return hwa
    return None


def _myo_ji_blocked(day_oh: OHaeng, branch: JiJi) -> bool:
    if day_oh is OHaeng.HWA:
        return branch in (JiJi.CHUK, JiJi.JIN)
    if day_oh is OHaeng.SU:
        return branch in (JiJi.JIN, JiJi.SUL, JiJi.CHUK, JiJi.MI)
    return False


def _is_ally(oh: OHaeng, day_oh: OHaeng) -> bool:
    return oh is day_oh or _generates(oh, day_oh)


# ============================================================================
# Stage 2: 억부 분류
# ============================================================================

class EokbuClassifier:
    """사용자 정의 2단계 억부 분류."""

    @staticmethod
    def classify(saju: Saju) -> EokbuClassification:
        day_oh = saju.day_stem.o_haeng
        month_branch = saju.month_pillar.ji_ji
        day_branch = saju.day_pillar.ji_ji

        branches_list = [
            saju.year_pillar.ji_ji, saju.month_pillar.ji_ji,
            saju.day_pillar.ji_ji,
        ]
        if saju.hour_pillar is not None:
            branches_list.append(saju.hour_pillar.ji_ji)
        branches = frozenset(branches_list)

        # Stage 1.1: 합화
        month_hap = _hap_effective_o_haeng(month_branch, branches)
        day_hap = _hap_effective_o_haeng(day_branch, branches)
        effective_month_oh = month_hap or month_branch.o_haeng
        effective_day_oh = day_hap or day_branch.o_haeng

        deuk_ryeong = _is_ally(effective_month_oh, day_oh)
        deuk_ji = _is_ally(effective_day_oh, day_oh)

        # Stage 1.2: 묘지 필터
        if month_hap is None and _myo_ji_blocked(day_oh, month_branch):
            deuk_ryeong = False
        if day_hap is None and _myo_ji_blocked(day_oh, day_branch):
            deuk_ji = False

        # Stage 1.3: 왕지 프리미엄
        wang_ji_premium = (
            month_branch in _WANG_JI and day_branch in _WANG_JI and
            _is_ally(month_branch.o_haeng, day_oh) and
            _is_ally(day_branch.o_haeng, day_oh)
        )

        # Stage 2: 5자 인비 카운트
        ally_count = 0
        stems: list[CheonGan] = [
            saju.year_pillar.cheon_gan, saju.month_pillar.cheon_gan,
        ]
        if saju.hour_pillar is not None:
            stems.append(saju.hour_pillar.cheon_gan)
        for s in stems:
            if _is_ally(s.o_haeng, day_oh):
                ally_count += 1
        other_branches: list[JiJi] = [saju.year_pillar.ji_ji]
        if saju.hour_pillar is not None:
            other_branches.append(saju.hour_pillar.ji_ji)
        for b in other_branches:
            if _is_ally(b.o_haeng, day_oh):
                ally_count += 1

        # 6글자 모드 보정
        samju_mode = saju.hour_pillar is None
        if samju_mode:
            ally_count += 1

        # 분류
        if deuk_ryeong and deuk_ji:
            case_desc = 'Case1(득령+득지)'
            if ally_count >= 1:
                level = IlganStrengthLevel.SINKANG
            elif wang_ji_premium:
                level = IlganStrengthLevel.SINKANG
            else:
                level = IlganStrengthLevel.JUNGHWA
        elif deuk_ryeong and not deuk_ji:
            case_desc = 'Case2(득령+실지)'
            if ally_count >= 2:
                level = (IlganStrengthLevel.JUNGHWA
                         if month_branch in _MYO_JI
                         else IlganStrengthLevel.SINKANG)
            elif ally_count == 1:
                level = IlganStrengthLevel.JUNGHWA
            else:
                level = IlganStrengthLevel.SINYAK
        elif not deuk_ryeong and deuk_ji:
            case_desc = 'Case3(실령+득지)'
            if ally_count >= 4:
                level = IlganStrengthLevel.SINKANG
            elif ally_count == 3:
                level = IlganStrengthLevel.JUNGHWA
            else:
                level = IlganStrengthLevel.SINYAK
        else:
            case_desc = 'Case4(실령+실지)'
            level = (IlganStrengthLevel.JUNGHWA if ally_count >= 3
                     else IlganStrengthLevel.SINYAK)

        month_hap_tag = f"({month_hap.hangul}국 합화)" if month_hap else ""
        day_hap_tag = f"({day_hap.hangul}국 합화)" if day_hap else ""
        samju_tag = " (6글자 +1 보정)" if samju_mode else ""
        reason_parts = [
            case_desc,
            f"월지 {month_branch.hangul}{month_hap_tag} "
            f"{'득령' if deuk_ryeong else '실령'}",
            f"일지 {day_branch.hangul}{day_hap_tag} "
            f"{'득지' if deuk_ji else '실지'}",
            f"인비 {ally_count}개{samju_tag}",
        ]
        if wang_ji_premium:
            reason_parts.append("★왕지 프리미엄")

        return EokbuClassification(
            level=level, deuk_ryeong=deuk_ryeong, deuk_ji=deuk_ji,
            ally_count=ally_count, wang_ji_premium=wang_ji_premium,
            reason=' / '.join(reason_parts),
        )


# ============================================================================
# Stage 3: 조후 분류
# ============================================================================

class JohuClassifier:
    """계절성 기반 조후 분류 — 태과 우선, 그 다음 월지 계절."""

    @staticmethod
    def classify(saju: Saju) -> JohuClassification:
        month_branch = saju.month_pillar.ji_ji
        branches: list[JiJi] = [
            saju.year_pillar.ji_ji, saju.month_pillar.ji_ji,
            saju.day_pillar.ji_ji,
        ]
        if saju.hour_pillar is not None:
            branches.append(saju.hour_pillar.ji_ji)

        # 생지 동반 보정 — 寅(화국 생지)은 午/戌 동반 시만, 申(수국 생지)은
        # 子/辰 동반 시만 그룹 카운트. 생지 단독 다수는 원래 오행이라 제외.
        hanseup_count = JohuClassifier._count_group(
            branches, _HANSEUP_GROUP, JiJi.SIN, frozenset({JiJi.JA, JiJi.JIN}))
        nanjo_count = JohuClassifier._count_group(
            branches, _NANJO_GROUP, JiJi.IN, frozenset({JiJi.O, JiJi.SUL}))
        hanseup_taegwa = hanseup_count >= 3
        nanjo_taegwa = nanjo_count >= 3

        season = JohuClassifier._season_label(month_branch)

        if nanjo_taegwa and not hanseup_taegwa:
            return JohuClassification(
                state=JohuState.NANJO, season_label=season,
                hanseup_count=hanseup_count, nanjo_count=nanjo_count,
                by_taegwa=True,
                reason=f"난조 — 寅午戌巳未 {nanjo_count}개 태과",
            )
        if hanseup_taegwa and not nanjo_taegwa:
            return JohuClassification(
                state=JohuState.HANSEUP, season_label=season,
                hanseup_count=hanseup_count, nanjo_count=nanjo_count,
                by_taegwa=True,
                reason=f"한습 — 申酉亥子丑 {hanseup_count}개 태과",
            )

        if month_branch in _WINTER:
            return JohuClassification(
                state=JohuState.HANSEUP, season_label=season,
                hanseup_count=hanseup_count, nanjo_count=nanjo_count,
                by_taegwa=False,
                reason=f"한습 — 월지 {month_branch.hangul}({season}) 동월생",
            )
        if month_branch in _SUMMER:
            return JohuClassification(
                state=JohuState.NANJO, season_label=season,
                hanseup_count=hanseup_count, nanjo_count=nanjo_count,
                by_taegwa=False,
                reason=f"난조 — 월지 {month_branch.hangul}({season}) 하월생",
            )

        return JohuClassification(
            state=JohuState.PYEONGTAN, season_label=season,
            hanseup_count=hanseup_count, nanjo_count=nanjo_count,
            by_taegwa=False,
            reason=f"평탄 — 월지 {month_branch.hangul}({season}), 태과 없음",
        )

    @staticmethod
    def _season_label(m: JiJi) -> str:
        if m in _WINTER:
            return '冬'
        if m in _SUMMER:
            return '夏'
        if m in _SPRING:
            return '春'
        return '秋'

    @staticmethod
    def _count_group(
        branches: list[JiJi],
        group: frozenset[JiJi],
        saeng_ji: JiJi,
        companions: frozenset[JiJi],
    ) -> int:
        """조후 그룹 카운트 — 생지는 왕지·고지 동반 시만 인정."""
        has_companion = any(b in companions for b in branches)
        count = 0
        for b in branches:
            if b not in group:
                continue
            if b is saeng_ji and not has_companion:
                continue
            count += 1
        return count


# ============================================================================
# YongsinDeriver — 억부 + 조후 결합
# ============================================================================

def _is_sinyak_conflict(
    day_oh: OHaeng, johu_yong: OHaeng, level: IlganStrengthLevel,
) -> bool:
    """신약 + 조후용신 충돌 — 신약인데 조후용신이 인비가 아니면(식재관) 충돌."""
    if level not in (IlganStrengthLevel.SINYAK, IlganStrengthLevel.GEUKSINYAK):
        return False
    inbi = {day_oh, _generating_of(day_oh)}  # 비겁 + 인성
    return johu_yong not in inbi


def _core_o_haeng_of_oegyeok(type_: OegyeokType, day_oh: OHaeng) -> OHaeng:
    """외격 type → 전왕 핵심 오행."""
    fixed: dict[OegyeokType, OHaeng] = {
        OegyeokType.HWA_GI_GAP_GI_TO: OHaeng.TO,
        OegyeokType.HWA_GI_EUL_GYEONG_GEUM: OHaeng.GEUM,
        OegyeokType.HWA_GI_BYEONG_SIN_SU: OHaeng.SU,
        OegyeokType.HWA_GI_JEONG_IM_MOK: OHaeng.MOK,
        OegyeokType.HWA_GI_MU_GYE_HWA: OHaeng.HWA,
        OegyeokType.GOK_JIK: OHaeng.MOK,
        OegyeokType.YEOM_SANG: OHaeng.HWA,
        OegyeokType.GA_SAEK: OHaeng.TO,
        OegyeokType.JONG_HYEOK: OHaeng.GEUM,
        OegyeokType.YUN_HA: OHaeng.SU,
    }
    if type_ in fixed:
        return fixed[type_]
    if type_ in (OegyeokType.JONG_WANG, OegyeokType.JONG_GANG,
                 OegyeokType.YANG_SIN_SEONG_SANG):
        return day_oh
    if type_ is OegyeokType.JONG_JAE:
        return _overcoming_of(day_oh)
    if type_ is OegyeokType.JONG_GWAN_SAL:
        return _overcoming_from(day_oh)
    if type_ is OegyeokType.JONG_A:
        return _generated_by(day_oh)
    raise ValueError(f"unknown OegyeokType: {type_}")


def _classify_with(yong: OHaeng, hee: OHaeng) -> dict[OHaeng, YongsinRole]:
    """용신·희신 명시 + 기·구·한신 표준 룰."""
    gi = _overcoming_from(yong)
    gu = _generating_of(gi)
    result: dict[OHaeng, YongsinRole] = {o: YongsinRole.HAN for o in OHaeng}
    result[gu] = YongsinRole.GU
    result[gi] = YongsinRole.GI
    result[hee] = YongsinRole.HEE
    result[yong] = YongsinRole.YONG
    return result


class YongsinDeriver:
    """억부(Stage 1·2) + 조후(Stage 3) 결합 용신 도출."""

    @staticmethod
    def derive(
        *,
        saju: Saju,
        gyeokguk: GyeokgukResult,
        strength: IlganStrengthBreakdown,
        johu: JohuAnalysis,
        oegyeok: list[OegyeokResult],
    ) -> YongsinResult:
        day_oh = saju.day_stem.o_haeng
        eokbu = EokbuClassifier.classify(saju)
        johu_c = JohuClassifier.classify(saju)

        # === 0순위: 외격 진격 → 전왕 용신 ===
        genuine = [r for r in oegyeok if r.verdict is OegyeokVerdict.GENUINE]
        if genuine:
            type_ = genuine[0].type
            core = _core_o_haeng_of_oegyeok(type_, day_oh)
            jw_hee = _generating_of(core)
            return YongsinResult(
                yong_o_haeng=core,
                method=YongsinMethod.JEONWANG,
                classifications=_classify_with(core, jw_hee),
                reason=(
                    f"[외격 우선] {type_.hangul} 진격 → 전왕 용신 {core.hangul}, "
                    f"희신 {jw_hee.hangul} (억부·조후 불문)"
                ),
                ilgan_strength=strength,
                johu=johu,
                gyeokguk=gyeokguk,
                eokbu=eokbu,
                johu_class=johu_c,
            )

        if johu_c.state is JohuState.HANSEUP:
            yong = OHaeng.HWA
            method = YongsinMethod.JOHU
            if _is_sinyak_conflict(day_oh, OHaeng.HWA, eokbu.level):
                hee = _generating_of(day_oh)  # 인성
                merge_reason = (
                    f"[조후 우선·신약보정] {johu_c.reason} → "
                    f"용신 火, 희신 {hee.hangul}(인성 — 신약 충돌 보정)"
                )
            else:
                hee = OHaeng.MOK
                merge_reason = (
                    f"[조후 우선] {johu_c.reason} → 용신 火, 희신 木 "
                    f"(억부 {eokbu.level.hangul} 불문)"
                )
        elif johu_c.state is JohuState.NANJO:
            yong = OHaeng.SU
            method = YongsinMethod.JOHU
            if _is_sinyak_conflict(day_oh, OHaeng.SU, eokbu.level):
                hee = _generating_of(day_oh)  # 인성
                merge_reason = (
                    f"[조후 우선·신약보정] {johu_c.reason} → "
                    f"용신 水, 희신 {hee.hangul}(인성 — 신약 충돌 보정)"
                )
            else:
                hee = OHaeng.GEUM
                merge_reason = (
                    f"[조후 우선] {johu_c.reason} → 용신 水, 희신 金 "
                    f"(억부 {eokbu.level.hangul} 불문)"
                )
        else:  # PYEONGTAN
            method = YongsinMethod.EOKBU
            if eokbu.level in (IlganStrengthLevel.SINKANG,
                               IlganStrengthLevel.GEUKSINKANG):
                yong = _generated_by(day_oh)   # 식상
                hee = _overcoming_of(day_oh)   # 재성
                merge_reason = (
                    f"[억부] {johu_c.reason} → 신강 → "
                    f"용신 식상({yong.hangul}), 희신 재성({hee.hangul})"
                )
            elif eokbu.level is IlganStrengthLevel.JUNGHWA:
                yong = _overcoming_from(day_oh)  # 관성
                hee = _overcoming_of(day_oh)     # 재성
                merge_reason = (
                    f"[억부] {johu_c.reason} → 중화 → "
                    f"용신 관성({yong.hangul}), 희신 재성({hee.hangul})"
                )
            else:  # SINYAK, GEUKSINYAK
                yong = _generating_of(day_oh)  # 인성
                hee = day_oh                    # 비겁
                merge_reason = (
                    f"[억부] {johu_c.reason} → 신약 → "
                    f"용신 인성({yong.hangul}), 희신 비겁({hee.hangul})"
                )

        return YongsinResult(
            yong_o_haeng=yong,
            method=method,
            classifications=_classify_with(yong, hee),
            reason=f"{eokbu.reason} → 억부 {eokbu.level.hangul}. {merge_reason}",
            ilgan_strength=strength,
            johu=johu,
            gyeokguk=gyeokguk,
            eokbu=eokbu,
            johu_class=johu_c,
        )
