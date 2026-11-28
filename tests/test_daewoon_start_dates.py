from datetime import date

import app


def test_start_dates_basic_case():
    d = app._daewoon_start_dates(date(1984, 9, 27), 3, 7, 8)
    assert (d[0].year, d[0].month) == (1988, 4)
    assert (d[4].year, d[4].month) == (2028, 4)


def test_start_dates_january_and_december_births():
    jan = app._daewoon_start_dates(date(1990, 1, 15), 5, 0, 3)
    assert (jan[0], jan[1], jan[2]) == (date(1995, 1, 15), date(2005, 1, 15), date(2015, 1, 15))
    dec = app._daewoon_start_dates(date(1990, 12, 31), 5, 2, 2)
    assert dec[0] == date(1996, 2, 29)
    assert dec[1] == date(2006, 2, 28)


def test_start_year_crosses_year_boundary_with_months():
    d = app._daewoon_start_dates(date(2000, 11, 10), 3, 6, 1)
    assert (d[0].year, d[0].month) == (2004, 5)


def test_forecast_end_to_end_1984_male():
    r = app.run_calculation({"birth_date": "1984-09-27", "birth_time": "20:00",
                             "birth_city": "Seoul", "gender": "male", "lang": "de"})
    e = r["daewoon"]["entries"]
    years = [x["start_year"] for x in e]
    assert all(b - a == 10 for a, b in zip(years, years[1:]))
    assert e[4]["pillar"]["hanja"] == "戊寅" and e[4]["start_year"] == 2028
