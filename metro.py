import math

# Всі станції метро Праги з координатами
METRO_STATIONS = [
    # Лінія A (зелена)
    {"name": "Depo Hostivař",      "line": "A", "lat": 50.0714, "lon": 14.5151},
    {"name": "Skalka",             "line": "A", "lat": 50.0737, "lon": 14.4933},
    {"name": "Strašnická",         "line": "A", "lat": 50.0755, "lon": 14.4769},
    {"name": "Želivského",         "line": "A", "lat": 50.0773, "lon": 14.4607},
    {"name": "Flora",              "line": "A", "lat": 50.0789, "lon": 14.4467},
    {"name": "Náměstí Míru",       "line": "A", "lat": 50.0754, "lon": 14.4358},
    {"name": "Jiřího z Poděbrad",  "line": "A", "lat": 50.0779, "lon": 14.4504},
    {"name": "Muzeum",             "line": "A", "lat": 50.0785, "lon": 14.4310},
    {"name": "Můstek",             "line": "A", "lat": 50.0836, "lon": 14.4239},
    {"name": "Staroměstská",       "line": "A", "lat": 50.0877, "lon": 14.4167},
    {"name": "Malostranská",       "line": "A", "lat": 50.0889, "lon": 14.4036},
    {"name": "Hradčanská",         "line": "A", "lat": 50.0956, "lon": 14.3942},
    {"name": "Dejvická",           "line": "A", "lat": 50.1003, "lon": 14.3939},
    {"name": "Bořislavka",         "line": "A", "lat": 50.1017, "lon": 14.3787},
    {"name": "Nádraží Veleslavín", "line": "A", "lat": 50.1021, "lon": 14.3622},
    {"name": "Petřiny",            "line": "A", "lat": 50.0998, "lon": 14.3472},
    {"name": "Nemocnice Motol",    "line": "A", "lat": 50.0772, "lon": 14.3515},
    # Лінія B (жовта)
    {"name": "Zličín",             "line": "B", "lat": 50.0598, "lon": 14.2915},
    {"name": "Stodůlky",           "line": "B", "lat": 50.0594, "lon": 14.3076},
    {"name": "Luka",               "line": "B", "lat": 50.0609, "lon": 14.3219},
    {"name": "Lužiny",             "line": "B", "lat": 50.0618, "lon": 14.3344},
    {"name": "Hůrka",              "line": "B", "lat": 50.0625, "lon": 14.3474},
    {"name": "Nové Butovice",      "line": "B", "lat": 50.0609, "lon": 14.3596},
    {"name": "Jinonice",           "line": "B", "lat": 50.0609, "lon": 14.3709},
    {"name": "Radlická",           "line": "B", "lat": 50.0651, "lon": 14.3848},
    {"name": "Smíchovské nádraží", "line": "B", "lat": 50.0591, "lon": 14.4039},
    {"name": "Anděl",              "line": "B", "lat": 50.0714, "lon": 14.4033},
    {"name": "Karlovo náměstí",    "line": "B", "lat": 50.0758, "lon": 14.4189},
    {"name": "Národní třída",      "line": "B", "lat": 50.0816, "lon": 14.4181},
    {"name": "Můstek",             "line": "B", "lat": 50.0836, "lon": 14.4239},
    {"name": "Náměstí Republiky",  "line": "B", "lat": 50.0878, "lon": 14.4314},
    {"name": "Florenc",            "line": "B", "lat": 50.0916, "lon": 14.4389},
    {"name": "Křižíkova",          "line": "B", "lat": 50.0941, "lon": 14.4475},
    {"name": "Invalidovna",        "line": "B", "lat": 50.0961, "lon": 14.4601},
    {"name": "Palmovka",           "line": "B", "lat": 50.0981, "lon": 14.4708},
    {"name": "Českomoravská",      "line": "B", "lat": 50.1001, "lon": 14.4829},
    {"name": "Vysočanská",         "line": "B", "lat": 50.1033, "lon": 14.4944},
    {"name": "Kolbenova",          "line": "B", "lat": 50.1064, "lon": 14.5044},
    {"name": "Hloubětín",          "line": "B", "lat": 50.1089, "lon": 14.5166},
    {"name": "Rajská zahrada",     "line": "B", "lat": 50.1106, "lon": 14.5311},
    {"name": "Černý Most",         "line": "B", "lat": 50.1135, "lon": 14.5469},
    # Лінія C (червона)
    {"name": "Letňany",            "line": "C", "lat": 50.1367, "lon": 14.5133},
    {"name": "Prosek",             "line": "C", "lat": 50.1261, "lon": 14.4972},
    {"name": "Střížkov",           "line": "C", "lat": 50.1189, "lon": 14.4850},
    {"name": "Ládví",              "line": "C", "lat": 50.1129, "lon": 14.4749},
    {"name": "Kobylisy",           "line": "C", "lat": 50.1087, "lon": 14.4618},
    {"name": "Nádraží Holešovice", "line": "C", "lat": 50.1033, "lon": 14.4453},
    {"name": "Vltavská",           "line": "C", "lat": 50.0974, "lon": 14.4367},
    {"name": "Florenc",            "line": "C", "lat": 50.0916, "lon": 14.4389},
    {"name": "Hlavní nádraží",     "line": "C", "lat": 50.0832, "lon": 14.4352},
    {"name": "Muzeum",             "line": "C", "lat": 50.0785, "lon": 14.4310},
    {"name": "I. P. Pavlova",      "line": "C", "lat": 50.0741, "lon": 14.4330},
    {"name": "Vyšehrad",           "line": "C", "lat": 50.0650, "lon": 14.4275},
    {"name": "Pankrác",            "line": "C", "lat": 50.0591, "lon": 14.4322},
    {"name": "Budějovická",        "line": "C", "lat": 50.0486, "lon": 14.4425},
    {"name": "Kačerov",            "line": "C", "lat": 50.0371, "lon": 14.4500},
    {"name": "Roztyly",            "line": "C", "lat": 50.0264, "lon": 14.4558},
    {"name": "Chodov",             "line": "C", "lat": 50.0162, "lon": 14.4869},
    {"name": "Opatov",             "line": "C", "lat": 50.0097, "lon": 14.4997},
    {"name": "Háje",               "line": "C", "lat": 50.0028, "lon": 14.5122},
]


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Відстань між двома точками в метрах."""
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def nearest_metro(lat: float, lon: float) -> dict:
    """Повертає найближчу станцію метро і відстань до неї."""
    best = None
    best_dist = float("inf")
    for st in METRO_STATIONS:
        d = haversine(lat, lon, st["lat"], st["lon"])
        if d < best_dist:
            best_dist = d
            best = st
    return {"station": best["name"], "line": best["line"], "distance_m": int(best_dist)}
