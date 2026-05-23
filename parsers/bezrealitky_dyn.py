import httpx
from datetime import datetime, timezone

GQL_URL = "https://api.bezrealitky.cz/graphql/"
HEADERS  = {
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Origin": "https://www.bezrealitky.cz",
    "Referer": "https://www.bezrealitky.cz/",
}
ROOM_MAP = {
    "1+kk": "DISP_1_KK", "1+1": "DISP_1_1",
    "2+kk": "DISP_2_KK", "2+1": "DISP_2_1",
    "3+kk": "DISP_3_KK", "3+1": "DISP_3_1",
    "4+kk": "DISP_4_KK", "4+1": "DISP_4_1",
}
DISP_LABEL = {v: k for k, v in ROOM_MAP.items()}

# Prague centre GPS + 15 km radius covers all city districts
PRAGUE_GPS = {"lat": 50.0755, "lng": 14.4378}
PRAGUE_RADIUS = 15000

QUERY = """
query ListAdverts(
    $offerType:[OfferType],$estateType:[EstateType],$disposition:[Disposition],
    $priceFrom:Int,$priceTo:Int,$locationPoint:GPSPointInput,$locationRadius:Int,
    $limit:Int,$offset:Int
){
  listAdverts(
    offerType:$offerType,estateType:$estateType,disposition:$disposition,
    priceFrom:$priceFrom,priceTo:$priceTo,
    locationPoint:$locationPoint,locationRadius:$locationRadius,
    limit:$limit,offset:$offset
  ){
    list{
      id uri price surface disposition availableFrom street
      city(locale:CS) cityDistrict(locale:CS)
      gps{lat lng}
      mainImage{url(filter:RECORD_MAIN)}
      publicImages{url(filter:RECORD_MAIN)}
    }
    totalCount
  }
}
"""


def fetch(s: dict) -> list[dict]:
    deal  = s.get("deal_type", "rent")
    rooms = s.get("rooms", [])
    pmin  = s.get("price_min", 0)
    pmax  = s.get("price_max", 0)

    dispositions = [ROOM_MAP[r] for r in rooms if r in ROOM_MAP]
    variables = {
        "offerType":      ["PRONAJEM"] if deal == "rent" else ["PRODEJ"],
        "estateType":     ["BYT"],
        "disposition":    dispositions or None,
        "priceFrom":      pmin or None,
        "priceTo":        pmax or None,
        "locationPoint":  PRAGUE_GPS,
        "locationRadius": PRAGUE_RADIUS,
        "limit":          50,
        "offset":         0,
    }

    results = []
    while True:
        try:
            r = httpx.post(GQL_URL, json={"query": QUERY, "variables": variables},
                           headers=HEADERS, timeout=15)
            data = r.json().get("data", {}).get("listAdverts", {})
        except Exception as e:
            print(f"[bezrealitky] {e}")
            break

        items = data.get("list") or []
        if not items:
            break

        for item in items:
            gps  = item.get("gps") or {}
            city = item.get("city", "") or ""
            dist = item.get("cityDistrict", "") or ""
            street = item.get("street", "") or ""
            locality = dist or city
            if street:
                locality = f"{street}, {locality}" if locality else street

            main_img = (item.get("mainImage") or {}).get("url", "")
            pub_imgs = [(img.get("url") or "") for img in (item.get("publicImages") or []) if img.get("url")]
            images   = pub_imgs or ([main_img] if main_img else [])

            avail_ts  = item.get("availableFrom")
            avail_str = None
            if avail_ts:
                try:
                    avail_str = datetime.fromtimestamp(avail_ts, tz=timezone.utc).strftime("%Y-%m-%d")
                except Exception:
                    pass

            results.append({
                "id":             f"bezrealitky_{item['id']}",
                "source":         "Bezrealitky",
                "title":          f"{DISP_LABEL.get(item.get('disposition',''), item.get('disposition',''))} — {locality}".strip(" —"),
                "price":          item.get("price", 0),
                "locality":       locality,
                "url":            f"https://www.bezrealitky.cz/nemovitosti-byty-domy/{item.get('uri', '')}",
                "lat":            gps.get("lat"),
                "lon":            gps.get("lng"),
                "image":          images[0] if images else "",
                "images":         images,
                "area_m2":        item.get("surface"),
                "available_from": avail_str,
            })

        variables["offset"] += 50
        if variables["offset"] >= (data.get("totalCount") or 0):
            break

    return results
