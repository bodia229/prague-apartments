import httpx
from config import DEAL_TYPE, PRICE_MIN, PRICE_MAX, ROOMS, AREA_MIN, AREA_MAX

GQL_URL = "https://api.bezrealitky.cz/graphql/"
HEADERS = {"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}

OFFER_TYPE = "PRONAJEM" if DEAL_TYPE == "rent" else "PRODEJ"

ROOM_MAP = {
    "1+kk": "DISP_1_KK", "1+1": "DISP_1_1",
    "2+kk": "DISP_2_KK", "2+1": "DISP_2_1",
    "3+kk": "DISP_3_KK", "3+1": "DISP_3_1",
    "4+kk": "DISP_4_KK", "4+1": "DISP_4_1",
}

QUERY = """
query ListAdverts($offerType: OfferType, $estateType: [EstateType], $disposition: [Disposition],
                  $priceMax: Int, $priceMin: Int, $surfaceMin: Int, $surfaceMax: Int,
                  $regionOsmIds: [ID], $limit: Int, $offset: Int) {
  listAdverts(
    offerType: $offerType, estateType: $estateType, disposition: $disposition,
    priceMax: $priceMax, priceMin: $priceMin, surfaceMin: $surfaceMin, surfaceMax: $surfaceMax,
    regionOsmIds: $regionOsmIds, limit: $limit, offset: $offset
  ) {
    list {
      id
      uri
      price
      surface
      disposition
      mainImage { url }
      address { city street }
      gps { lat lng }
    }
    totalCount
  }
}
"""


def fetch() -> list[dict]:
    dispositions = [ROOM_MAP[r] for r in ROOMS if r in ROOM_MAP]
    variables = {
        "offerType":    OFFER_TYPE,
        "estateType":   ["BYT"],
        "disposition":  dispositions or None,
        "priceMin":     PRICE_MIN or None,
        "priceMax":     PRICE_MAX or None,
        "surfaceMin":   AREA_MIN or None,
        "surfaceMax":   AREA_MAX or None,
        "regionOsmIds": ["439539818"],  # Praha OSM ID
        "limit":        50,
        "offset":       0,
    }

    results = []
    while True:
        try:
            r = httpx.post(GQL_URL, json={"query": QUERY, "variables": variables},
                           headers=HEADERS, timeout=15)
            data = r.json().get("data", {}).get("listAdverts", {})
        except Exception as e:
            print(f"[bezrealitky] error: {e}")
            break

        items = data.get("list", [])
        if not items:
            break

        for item in items:
            gps = item.get("gps") or {}
            addr = item.get("address") or {}
            results.append({
                "id":       f"bezrealitky_{item['id']}",
                "source":   "Bezrealitky",
                "title":    f"{item.get('disposition','')} — {addr.get('street','')} {addr.get('city','')}",
                "price":    item.get("price", 0),
                "locality": f"{addr.get('street','')} {addr.get('city','')}".strip(),
                "url":      f"https://www.bezrealitky.cz/nemovitosti-byty-domy/{item.get('uri','')}",
                "lat":      gps.get("lat"),
                "lon":      gps.get("lng"),
                "image":    (item.get("mainImage") or {}).get("url", ""),
                "area_m2":  item.get("surface"),
                "floor":    None,
                "furnished": None,
            })

        total = data.get("totalCount", 0)
        variables["offset"] += 50
        if variables["offset"] >= total:
            break

    return results
