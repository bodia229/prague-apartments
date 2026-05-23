import httpx
import json
from bs4 import BeautifulSoup

BASE    = "https://www.flatio.com"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}


def fetch(s: dict) -> list[dict]:
    pmax = s.get("price_max", 0)
    results = []
    seen_ids = set()

    for page in range(1, 6):
        url = f"{BASE}/s/Prague"
        params = {"page": page} if page > 1 else {}
        try:
            r = httpx.get(url, params=params, headers=HEADERS, timeout=20, follow_redirects=True)
            soup = BeautifulSoup(r.text, "html.parser")
        except Exception as e:
            print(f"[flatio] {e}")
            break

        cards = soup.select(".offer-card")
        if not cards:
            break

        for card in cards:
            # data-offer-data is on the inner wrapper div
            wrapper = card.select_one("[data-offer-data]")
            if not wrapper:
                continue
            try:
                d = json.loads(wrapper["data-offer-data"])
            except Exception:
                continue

            offer_id = str(d.get("id", ""))
            if not offer_id or offer_id in seen_ids:
                continue
            seen_ids.add(offer_id)

            if d.get("type") not in ("apartment", "flat", "studio"):
                continue

            # price in JSON is per-night short-term; medium-term monthly price only on listing page
            # store raw EUR value, skip price filtering for Flatio
            price_eur = d.get("price", 0) or 0
            price_czk = 0  # unknown monthly price — shown as EUR on listing page

            loc_data = d.get("location") or {}
            city = loc_data.get("city_just_name", "Prague")

            # URL: find the offer link
            link_el = card.select_one("a.offer-card__link")
            href = link_el["href"].split("?")[0] if link_el and link_el.get("href") else ""
            listing_url = href if href.startswith("http") else BASE + href

            # All carousel images (up to 10)
            images = []
            for img_el in card.select(".offer-carousel img, img.image"):
                src = img_el.get("src") or img_el.get("data-src") or ""
                if src and "data:" not in src:
                    images.append(src if src.startswith("http") else BASE + src)
            images = list(dict.fromkeys(images))[:10]  # deduplicate, max 10
            image = images[0] if images else ""

            # Available from
            booking = d.get("booking_date") or {}
            avail = booking.get("start")

            bedrooms = d.get("bedrooms_count", 0) or 0
            title = f"Квартира {bedrooms}BR — {city}" if bedrooms else f"Студіо — {city}"

            results.append({
                "id":             f"flatio_{offer_id}",
                "source":         "Flatio",
                "title":          title,
                "price":          price_czk,
                "price_eur":      price_eur,
                "locality":       city,
                "url":            listing_url,
                "lat":            None,
                "lon":            None,
                "image":          image,
                "images":         images,
                "area_m2":        None,
                "available_from": avail,
            })

        if len(cards) < 5:
            break

    return results
