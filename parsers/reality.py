import httpx
import re
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urljoin

BASE = "https://www.reality.cz"
LISTING_PATH = "/pronajem/byty/Praha/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


def _fetch_detail_images(url: str) -> list[str]:
    try:
        r = httpx.get(url, headers=HEADERS, timeout=10, follow_redirects=True)
        soup = BeautifulSoup(r.text, "html.parser")
        imgs = []
        for img in soup.select("#galerie img"):
            src = img.get("src", "")
            if src and "no-image" not in src and "data:" not in src:
                imgs.append(src if src.startswith("http") else BASE + src)
        return list(dict.fromkeys(imgs))[:10]
    except Exception:
        return []


def fetch(s: dict) -> list[dict]:
    pmax = s.get("price_max", 0)
    results = []

    for page in range(1, 6):
        url = BASE + LISTING_PATH
        params = {"page": page} if page > 1 else {}
        try:
            r = httpx.get(url, params=params, headers=HEADERS, timeout=20, follow_redirects=True)
            soup = BeautifulSoup(r.text, "html.parser")
        except Exception as e:
            print(f"[reality.cz] {e}")
            break

        cards = soup.select(".xvypis")
        if not cards:
            break

        page_items = []
        for card in cards:
            try:
                link_el  = card.select_one(".vypisnaz a")
                thumb_el = card.select_one(".thumbnail img")
                price_el = card.select_one(".vypiscena strong")
                type_el  = card.select_one(".lokalita")

                href = link_el.get("href", "") if link_el else ""
                href = href.split("?")[0]
                href = urljoin(str(r.url), href) if href else ""

                addr       = link_el.get_text(strip=True) if link_el else ""
                type_txt   = type_el.get_text(strip=True) if type_el else ""
                price_text = price_el.get_text(strip=True) if price_el else ""
                price      = int(re.sub(r"[^\d]", "", price_text) or "0")

                thumb = ""
                if thumb_el:
                    src = thumb_el.get("src", "")
                    thumb = src if src.startswith("http") else (BASE + src if src else "")

                lat, lon = None, None
                for cls in card.get("class", []):
                    if cls.startswith("gpsx"):
                        try: lat = float(cls[4:])
                        except: pass
                    elif cls.startswith("gpsy"):
                        try: lon = float(cls[4:])
                        except: pass

                card_id = card.get("id", "")
                uid = card_id[2:] if card_id.startswith("id") else (card_id or addr)

                if pmax and price and price > pmax:
                    continue

                area = None
                m = re.search(r"(\d+)\s*m", type_txt)
                if m:
                    area = int(m.group(1))

                title = f"{type_txt} — {addr}" if type_txt else addr

                page_items.append({
                    "id":             f"reality_{uid}",
                    "source":         "Reality.cz",
                    "title":          title,
                    "price":          price,
                    "locality":       addr,
                    "url":            href,
                    "lat":            lat,
                    "lon":            lon,
                    "image":          thumb,
                    "images":         [thumb] if thumb else [],
                    "area_m2":        area,
                    "available_from": None,
                })
            except Exception:
                continue

        if page_items:
            detail_map = {i: it["url"] for i, it in enumerate(page_items) if it.get("url")}
            with ThreadPoolExecutor(max_workers=8) as pool:
                futures = {pool.submit(_fetch_detail_images, url): idx for idx, url in detail_map.items()}
                for fut in as_completed(futures):
                    idx  = futures[fut]
                    imgs = fut.result()
                    if imgs:
                        page_items[idx]["images"] = imgs
                        page_items[idx]["image"]  = imgs[0]

        results.extend(page_items)

        if len(cards) < 10:
            break

    return results
