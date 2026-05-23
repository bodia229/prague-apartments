import httpx
import re
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE    = "https://www.expats.cz"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
}


def _parse_price(text: str) -> int:
    text = text.strip()
    digits = re.sub(r"[^\d]", "", text)
    price = int(digits) if digits else 0
    if "eur" in text.lower() and price:
        price = int(price * 25)
    return price


def _fetch_detail_images(url: str) -> list[str]:
    try:
        r = httpx.get(url, headers=HEADERS, timeout=10, follow_redirects=True)
        soup = BeautifulSoup(r.text, "html.parser")
        imgs = []
        for img in soup.select(".gallery img"):
            src = img.get("src", "") or img.get("data-src", "")
            if src and "data:" not in src:
                imgs.append(src if src.startswith("http") else BASE + src)
        return list(dict.fromkeys(imgs))[:10]
    except Exception:
        return []


def fetch(s: dict) -> list[dict]:
    pmax = s.get("price_max", 0)
    results = []

    for page in range(1, 6):
        url = f"{BASE}/praguerealestate/apartments/for-rent"
        params = {"page": page} if page > 1 else {}
        try:
            r = httpx.get(url, params=params, headers=HEADERS, timeout=15, follow_redirects=True)
            soup = BeautifulSoup(r.text, "html.parser")
        except Exception as e:
            print(f"[expats] {e}")
            break

        lst = soup.select_one(".list")
        if not lst:
            break

        items = lst.find_all("div", recursive=False)
        if not items:
            break

        page_items = []
        for item in items:
            try:
                link_el  = item.select_one(".photos a")
                title_el = item.select_one("h2 a")
                loc_el   = item.select_one("h3")
                price_el = item.select_one("strong")

                if not link_el:
                    continue

                href     = link_el.get("href", "")
                full_url = href if href.startswith("http") else BASE + href
                uid      = href.split("/")[-1] or href

                title    = title_el.get_text(strip=True) if title_el else ""
                locality = loc_el.get_text(strip=True)  if loc_el  else ""
                price    = _parse_price(price_el.get_text(strip=True)) if price_el else 0

                images = []
                for img_el in item.select(".photos img"):
                    src = img_el.get("src") or img_el.get("data-src") or ""
                    if src:
                        images.append(src if src.startswith("http") else BASE + src)
                image = images[0] if images else ""

                if pmax and price and price > pmax:
                    continue

                area = None
                m = re.search(r"(\d+)\s*m", title)
                if m:
                    area = int(m.group(1))

                page_items.append({
                    "id":             f"expats_{uid}",
                    "source":         "Expats.cz",
                    "title":          title,
                    "price":          price,
                    "locality":       locality,
                    "url":            full_url,
                    "lat":            None,
                    "lon":            None,
                    "image":          image,
                    "images":         images,
                    "area_m2":        area,
                    "available_from": None,
                    "_detail_url":    full_url,
                })
            except Exception:
                continue

        if page_items:
            detail_map = {i: it["_detail_url"] for i, it in enumerate(page_items)}
            with ThreadPoolExecutor(max_workers=8) as pool:
                futures = {pool.submit(_fetch_detail_images, url): idx for idx, url in detail_map.items()}
                for fut in as_completed(futures):
                    idx  = futures[fut]
                    imgs = fut.result()
                    if imgs:
                        page_items[idx]["images"] = imgs
                        page_items[idx]["image"]  = imgs[0]

        for it in page_items:
            it.pop("_detail_url", None)

        results.extend(page_items)

        if len(items) < 5:
            break

    return results
