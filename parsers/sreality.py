import httpx
from config import DEAL_TYPE, PRICE_MIN, PRICE_MAX, ROOMS, AREA_MIN, AREA_MAX

ROOM_MAP = {
    "1+kk": 2, "1+1": 3, "2+kk": 4, "2+1": 5,
    "3+kk": 6, "3+1": 7, "4+kk": 8, "4+1": 9, "5+": 10,
}
TYPE_MAP = {"rent": 2, "sale": 1}

BASE = "https://www.sreality.cz/api/cs/v2/estates"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}


def fetch() -> list[dict]:
    room_codes = [str(ROOM_MAP[r]) for r in ROOMS if r in ROOM_MAP]
    params = {
        "category_main_cb": 1,
        "category_type_cb": TYPE_MAP.get(DEAL_TYPE, 2),
        "locality_region_id": 10,  # Praha
        "per_page": 60,
        "price_min": PRICE_MIN if PRICE_MIN else "",
        "price_max": PRICE_MAX if PRICE_MAX else "",
        "usable_area": f"{AREA_MIN}_{AREA_MAX}" if AREA_MIN or AREA_MAX else "",
    }
    if room_codes:
        params["category_sub_cb"] = "|".join(room_codes)

    results = []
    page = 1
    while True:
        params["page"] = page
        try:
            r = httpx.get(BASE, params=params, headers=HEADERS, timeout=15)
            data = r.json()
        except Exception as e:
            print(f"[sreality] error: {e}")
            break

        estates = data.get("_embedded", {}).get("estates", [])
        if not estates:
            break

        for e in estates:
            gps = e.get("gps") or {}
            results.append({
                "id":       f"sreality_{e.get('hash_id')}",
                "source":   "Sreality",
                "title":    e.get("name", "") if isinstance(e.get("name"), str) else e.get("name", {}).get("value", ""),
                "price":    e.get("price", 0),
                "locality": e.get("locality", "") if isinstance(e.get("locality"), str) else e.get("locality", {}).get("value", ""),
                "url":      f"https://www.sreality.cz/detail/{'pronajem' if DEAL_TYPE=='rent' else 'prodej'}/byt/{e.get('hash_id')}",
                "lat":      gps.get("lat"),
                "lon":      gps.get("lon"),
                "image":    (e.get("_links", {}).get("images", [{}])[0] or {}).get("href", ""),
                "area_m2":  None,
                "floor":    None,
                "furnished": None,
            })

        if page * 60 >= data.get("result_size", 0):
            break
        page += 1

    return results
