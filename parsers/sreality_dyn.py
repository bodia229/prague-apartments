import httpx

ROOM_MAP = {
    "1+kk": 2, "1+1": 3, "2+kk": 4, "2+1": 5,
    "3+kk": 6, "3+1": 7, "4+kk": 8, "4+1": 9, "5+": 10,
}
TYPE_MAP = {"rent": 2, "sale": 1}
BASE    = "https://www.sreality.cz/api/cs/v2/estates"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}


def fetch(s: dict) -> list[dict]:
    deal   = s.get("deal_type", "rent")
    rooms  = s.get("rooms", [])
    pmin   = s.get("price_min", 0)
    pmax   = s.get("price_max", 0)
    area_min = s.get("area_min", 0)
    area_max = s.get("area_max", 0)

    room_codes = [str(ROOM_MAP[r]) for r in rooms if r in ROOM_MAP]
    params = {
        "category_main_cb": 1,
        "category_type_cb": TYPE_MAP.get(deal, 2),
        "locality_region_id": 10,
        "per_page": 60,
    }
    if pmin:   params["price_min"] = pmin
    if pmax:   params["price_max"] = pmax
    if area_min or area_max:
        params["usable_area"] = f"{area_min}_{area_max}"
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
            print(f"[sreality] {e}")
            break

        estates = data.get("_embedded", {}).get("estates", [])
        if not estates:
            break

        for e in estates:
            gps  = e.get("gps") or {}
            name = e.get("name", "")
            loc  = e.get("locality", "")
            results.append({
                "id":       f"sreality_{e.get('hash_id')}",
                "source":   "Sreality",
                "title":    name if isinstance(name, str) else name.get("value", ""),
                "price":    e.get("price", 0),
                "locality": loc  if isinstance(loc,  str) else loc.get("value", ""),
                "url":      f"https://www.sreality.cz/detail/{'pronajem' if deal=='rent' else 'prodej'}/byt/{e.get('hash_id')}",
                "lat":      gps.get("lat"),
                "lon":      gps.get("lon"),
                "image":    (e.get("_links", {}).get("images") or [{}])[0].get("href", ""),
                "images":   [img.get("href","") for img in (e.get("_links",{}).get("images") or []) if img.get("href")][:10],
                "area_m2":       None,
                "available_from": None,
            })

        if page * 60 >= data.get("result_size", 0):
            break
        page += 1

    return results
