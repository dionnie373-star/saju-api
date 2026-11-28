import report_facts as rf


def test_boundaries_follow_reader_timezone():
    de = rf.solar_month_boundaries(2027, "de")
    # 입춘 2027-02-04 10:42 KST == 02:42 Berlin (같은 순간, 표시만 다름)
    assert de[1]["name"] == "입춘" and (de[1]["start"].month, de[1]["start"].day) == (2, 4)
    # 경칩은 KST 3/6 04:36 이지만 베를린에서는 3/5
    assert (de[2]["start"].month, de[2]["start"].day) == (3, 5)
    assert len(de) == 12 and de[11]["end"].year == 2028
    assert de[0]["end"] == de[1]["start"]
