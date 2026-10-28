"""시간대가 하나뿐인(또는 사실상 하나인) 나라의 대표 경도·시간대. 도시를 못 찾았을 때 나라 기준 근사값으로 쓴다.

여러 시간대에 걸친 나라(미국, 러시아, 브라질 등)는 일부러 넣지 않는다: 시간이 몇 시간씩 틀어질 수 있다.
"""
COUNTRIES = {
    "south korea": (127.0, "Asia/Seoul"), "japan": (138.0, "Asia/Tokyo"), "india": (78.0, "Asia/Kolkata"),
    "pakistan": (69.0, "Asia/Karachi"), "bangladesh": (90.4, "Asia/Dhaka"), "nepal": (84.0, "Asia/Kathmandu"),
    "sri lanka": (80.7, "Asia/Colombo"), "thailand": (101.0, "Asia/Bangkok"), "vietnam": (106.0, "Asia/Ho_Chi_Minh"),
    "philippines": (121.0, "Asia/Manila"), "singapore": (103.8, "Asia/Singapore"), "taiwan": (121.0, "Asia/Taipei"),
    "malaysia": (102.0, "Asia/Kuala_Lumpur"), "cambodia": (104.9, "Asia/Phnom_Penh"), "laos": (102.6, "Asia/Vientiane"),
    "myanmar": (96.0, "Asia/Yangon"), "mongolia": (106.9, "Asia/Ulaanbaatar"), "iran": (53.0, "Asia/Tehran"),
    "iraq": (44.0, "Asia/Baghdad"), "saudi arabia": (45.0, "Asia/Riyadh"), "united arab emirates": (54.4, "Asia/Dubai"),
    "israel": (35.0, "Asia/Jerusalem"), "jordan": (36.0, "Asia/Amman"), "lebanon": (35.8, "Asia/Beirut"),
    "turkey": (35.0, "Europe/Istanbul"), "egypt": (30.0, "Africa/Cairo"), "nigeria": (8.0, "Africa/Lagos"),
    "ghana": (-1.0, "Africa/Accra"), "kenya": (38.0, "Africa/Nairobi"), "ethiopia": (39.0, "Africa/Addis_Ababa"),
    "tanzania": (35.0, "Africa/Dar_es_Salaam"), "uganda": (32.0, "Africa/Kampala"), "south africa": (25.0, "Africa/Johannesburg"),
    "morocco": (-6.0, "Africa/Casablanca"), "algeria": (3.0, "Africa/Algiers"), "tunisia": (9.5, "Africa/Tunis"),
    "senegal": (-14.5, "Africa/Dakar"), "cameroon": (12.0, "Africa/Douala"), "zimbabwe": (30.0, "Africa/Harare"),
    "zambia": (28.0, "Africa/Lusaka"), "rwanda": (30.0, "Africa/Kigali"),
    "kazakhstan": (68.0, "Asia/Almaty"), "uzbekistan": (64.0, "Asia/Tashkent"), "colombia": (-74.0, "America/Bogota"),
    "peru": (-75.0, "America/Lima"), "chile": (-71.0, "America/Santiago"), "argentina": (-64.0, "America/Argentina/Buenos_Aires"),
    "venezuela": (-66.0, "America/Caracas"), "ecuador": (-78.5, "America/Guayaquil"), "bolivia": (-65.0, "America/La_Paz"),
    "uruguay": (-56.0, "America/Montevideo"), "paraguay": (-58.0, "America/Asuncion"), "cuba": (-79.0, "America/Havana"),
    "dominican republic": (-70.0, "America/Santo_Domingo"), "jamaica": (-77.3, "America/Jamaica"),
    "costa rica": (-84.0, "America/Costa_Rica"), "panama": (-80.0, "America/Panama"), "guatemala": (-90.5, "America/Guatemala"),
    "new zealand": (174.0, "Pacific/Auckland"), "poland": (19.0, "Europe/Warsaw"), "ukraine": (31.0, "Europe/Kyiv"),
    "romania": (25.0, "Europe/Bucharest"), "greece": (23.0, "Europe/Athens"), "portugal": (-8.0, "Europe/Lisbon"),
    "sweden": (16.0, "Europe/Stockholm"), "norway": (10.0, "Europe/Oslo"), "finland": (25.0, "Europe/Helsinki"),
    "ireland": (-8.0, "Europe/Dublin"), "italy": (12.5, "Europe/Rome"), "netherlands": (5.3, "Europe/Amsterdam"),
    "belgium": (4.5, "Europe/Brussels"), "switzerland": (8.2, "Europe/Zurich"), "austria": (14.5, "Europe/Vienna"),
    "czech republic": (15.5, "Europe/Prague"), "hungary": (19.5, "Europe/Budapest"), "serbia": (21.0, "Europe/Belgrade"),
    "croatia": (16.0, "Europe/Zagreb"), "bulgaria": (25.0, "Europe/Sofia"), "denmark": (10.0, "Europe/Copenhagen"),
    "france": (2.3, "Europe/Paris"), "germany": (10.0, "Europe/Berlin"), "spain": (-3.7, "Europe/Madrid"),
}
