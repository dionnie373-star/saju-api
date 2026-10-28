"""전 세계 영어권 사용자용 주요 도시 표(경도, IANA 시간대). 네트워크 지오코딩이 실패해도 시간대를 맞추기 위함.

키는 소문자 도시명(별칭 포함). "City, Country" 입력은 쉼표 앞부분으로 조회한다.
영국·미국·캐나다·호주·뉴질랜드는 일부러 넣지 않았다(온라인 지오코딩이 처리, 주 대상 아님).
"""

_ROWS = [
    # (이름들, 경도, 시간대)
    # South Asia
    (("mumbai", "bombay"), 72.8777, "Asia/Kolkata"), (("delhi", "new delhi"), 77.2090, "Asia/Kolkata"),
    (("bengaluru", "bangalore"), 77.5946, "Asia/Kolkata"), (("chennai", "madras"), 80.2707, "Asia/Kolkata"),
    (("kolkata", "calcutta"), 88.3639, "Asia/Kolkata"), (("hyderabad",), 78.4867, "Asia/Kolkata"),
    (("pune",), 73.8567, "Asia/Kolkata"), (("ahmedabad",), 72.5714, "Asia/Kolkata"), (("jaipur",), 75.7873, "Asia/Kolkata"),
    (("lucknow",), 80.9462, "Asia/Kolkata"), (("kochi", "cochin"), 76.2673, "Asia/Kolkata"),
    (("karachi",), 67.0011, "Asia/Karachi"), (("lahore",), 74.3587, "Asia/Karachi"), (("islamabad",), 73.0479, "Asia/Karachi"),
    (("dhaka",), 90.4125, "Asia/Dhaka"), (("colombo",), 79.8612, "Asia/Colombo"), (("kathmandu",), 85.3240, "Asia/Kathmandu"),
    (("kabul",), 69.2075, "Asia/Kabul"),
    # Southeast Asia
    (("manila",), 120.9842, "Asia/Manila"), (("quezon city",), 121.0437, "Asia/Manila"), (("cebu", "cebu city"), 123.8854, "Asia/Manila"),
    (("davao", "davao city"), 125.4553, "Asia/Manila"),
    (("jakarta",), 106.8456, "Asia/Jakarta"), (("surabaya",), 112.7521, "Asia/Jakarta"), (("bandung",), 107.6191, "Asia/Jakarta"),
    (("medan",), 98.6722, "Asia/Jakarta"), (("denpasar", "bali"), 115.2167, "Asia/Makassar"),
    (("kuala lumpur",), 101.6869, "Asia/Kuala_Lumpur"), (("george town", "penang"), 100.3288, "Asia/Kuala_Lumpur"),
    (("singapore",), 103.8198, "Asia/Singapore"),
    (("bangkok",), 100.5018, "Asia/Bangkok"), (("chiang mai",), 98.9853, "Asia/Bangkok"),
    (("ho chi minh city", "ho chi minh", "saigon"), 106.6297, "Asia/Ho_Chi_Minh"), (("hanoi",), 105.8342, "Asia/Bangkok"),
    (("phnom penh",), 104.9282, "Asia/Phnom_Penh"), (("yangon", "rangoon"), 96.1951, "Asia/Yangon"),
    # East Asia
    (("beijing",), 116.4074, "Asia/Shanghai"), (("shanghai",), 121.4737, "Asia/Shanghai"), (("guangzhou",), 113.2644, "Asia/Shanghai"),
    (("shenzhen",), 114.0579, "Asia/Shanghai"), (("chengdu",), 104.0665, "Asia/Shanghai"),
    (("hong kong",), 114.1694, "Asia/Hong_Kong"), (("taipei",), 121.5654, "Asia/Taipei"),
    (("tokyo",), 139.6917, "Asia/Tokyo"), (("osaka",), 135.5023, "Asia/Tokyo"),
    # Central Asia
    (("almaty",), 76.8512, "Asia/Almaty"), (("tashkent",), 69.2401, "Asia/Tashkent"),
    # Middle East
    (("dubai",), 55.2708, "Asia/Dubai"), (("abu dhabi",), 54.3773, "Asia/Dubai"),
    (("riyadh",), 46.6753, "Asia/Riyadh"), (("jeddah",), 39.1925, "Asia/Riyadh"), (("doha",), 51.5310, "Asia/Qatar"),
    (("kuwait city", "kuwait"), 47.9774, "Asia/Kuwait"), (("tel aviv",), 34.7818, "Asia/Jerusalem"), (("jerusalem",), 35.2137, "Asia/Jerusalem"),
    (("amman",), 35.9106, "Asia/Amman"), (("baghdad",), 44.3661, "Asia/Baghdad"), (("tehran",), 51.3890, "Asia/Tehran"),
    (("istanbul",), 28.9784, "Europe/Istanbul"), (("ankara",), 32.8597, "Europe/Istanbul"), (("izmir",), 27.1428, "Europe/Istanbul"),
    # Africa
    (("cairo",), 31.2357, "Africa/Cairo"), (("alexandria",), 29.9187, "Africa/Cairo"),
    (("lagos",), 3.3792, "Africa/Lagos"), (("abuja",), 7.3986, "Africa/Lagos"), (("ibadan",), 3.9470, "Africa/Lagos"),
    (("port harcourt",), 7.0498, "Africa/Lagos"), (("accra",), -0.1870, "Africa/Accra"), (("nairobi",), 36.8219, "Africa/Nairobi"),
    (("addis ababa",), 38.7578, "Africa/Addis_Ababa"), (("dar es salaam",), 39.2083, "Africa/Dar_es_Salaam"),
    (("kampala",), 32.5825, "Africa/Kampala"), (("kigali",), 30.0619, "Africa/Kigali"),
    (("johannesburg",), 28.0473, "Africa/Johannesburg"), (("pretoria",), 28.1881, "Africa/Johannesburg"),
    (("cape town",), 18.4241, "Africa/Johannesburg"), (("durban",), 31.0218, "Africa/Johannesburg"),
    (("harare",), 31.0522, "Africa/Harare"), (("lusaka",), 28.2871, "Africa/Lusaka"), (("luanda",), 13.2344, "Africa/Luanda"),
    (("maputo",), 32.5732, "Africa/Maputo"), (("gaborone",), 25.9231, "Africa/Gaborone"), (("windhoek",), 17.0832, "Africa/Windhoek"),
    (("khartoum",), 32.5599, "Africa/Khartoum"), (("tripoli",), 13.1913, "Africa/Tripoli"),
    # Latin America & Caribbean (English speakers)
    (("sao paulo", "são paulo"), -46.6333, "America/Sao_Paulo"), (("rio de janeiro", "rio"), -43.1729, "America/Sao_Paulo"),
    (("brasilia", "brasília"), -47.8825, "America/Sao_Paulo"), (("fortaleza",), -38.5434, "America/Fortaleza"), (("belo horizonte",), -43.9378, "America/Sao_Paulo"),
    (("curitiba",), -49.2733, "America/Sao_Paulo"), (("porto alegre",), -51.2177, "America/Sao_Paulo"),
    (("kingston",), -76.7936, "America/Jamaica"), (("port of spain",), -61.5167, "America/Port_of_Spain"),
    (("nassau",), -77.3554, "America/Nassau"), (("bridgetown",), -59.6167, "America/Barbados"),
    # Europe (non-UK)
    (("moscow",), 37.6173, "Europe/Moscow"), (("saint petersburg", "st petersburg", "st. petersburg"), 30.3351, "Europe/Moscow"),
    (("kyiv", "kiev"), 30.5234, "Europe/Kyiv"), (("warsaw",), 21.0122, "Europe/Warsaw"), (("prague",), 14.4378, "Europe/Prague"),
    (("budapest",), 19.0402, "Europe/Budapest"), (("bucharest",), 26.1025, "Europe/Bucharest"), (("sofia",), 23.3219, "Europe/Sofia"),
    (("athens",), 23.7275, "Europe/Athens"), (("lisbon",), -9.1393, "Europe/Lisbon"), (("porto",), -8.6291, "Europe/Lisbon"),
    (("rome",), 12.4964, "Europe/Rome"), (("milan",), 9.1900, "Europe/Rome"), (("amsterdam",), 4.9041, "Europe/Amsterdam"),
    (("dublin",), -6.2603, "Europe/Dublin"), (("stockholm",), 18.0686, "Europe/Stockholm"), (("oslo",), 10.7522, "Europe/Oslo"),
    (("copenhagen",), 12.5683, "Europe/Copenhagen"), (("helsinki",), 24.9384, "Europe/Helsinki"),
    (("belgrade",), 20.4489, "Europe/Belgrade"), (("zagreb",), 15.9819, "Europe/Zagreb"),
]

WORLD_CITIES = {}
for _names, _lon, _tz in _ROWS:
    for _n in _names:
        WORLD_CITIES[_n] = (_lon, _tz)


def lookup_world_city(city_name):
    """'Lagos' 또는 'Lagos, Nigeria' -> (경도, 시간대) 또는 None."""
    key = " ".join((city_name or "").strip().lower().split())
    if key in WORLD_CITIES:
        return WORLD_CITIES[key]
    head = key.split(",")[0].strip()
    return WORLD_CITIES.get(head)
