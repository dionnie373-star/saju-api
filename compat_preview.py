"""궁합 무료 미리보기: AI·메일 없이 계산 결과만으로 만든 요약(두 사람의 오행 분포 + 관계 별명 + 개수).
이름·생일·출생지는 결과에 담지 않는다. 구체적인 장면·해석은 유료 리포트에만 있다."""
import pair_relations
import pair_scenes
import profile_view


def build(calc_a, calc_b, lang="de"):
    result = pair_relations.compare(calc_a["pillars"], calc_b["pillars"])
    codes = set(pair_scenes._codes_present(result))
    sel = pair_scenes.select(result, lang)

    def side(calc):
        v = profile_view.build_profile_view(calc, lang)
        day = v["pillars"]["day"]
        return {"counts": [{"key": c["key"], "name": c["name"], "n": int(c["n"])} for c in v["counts"]],
                "day_key": day["stem"], "day_name": day["stem_name"]}

    return {
        "pattern_name": sel["pattern_name"],
        "a": side(calc_a), "b": side(calc_b),
        "n_connections": len(codes & pair_scenes.CONNECTION_CODES),
        "n_frictions": len(codes & pair_scenes.TENSION_CODES),
        "n_scenes": len(sel["scenes"]),
        "lang": lang,
    }
