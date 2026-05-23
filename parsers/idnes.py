import httpx
import re
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urljoin

BASE = "https://reality.idnes.cz"
LISTING_URL = f"{BASE}/s/pronajem/byty/Praha/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


def _fetch_detail_images(url: str) -> list[str]:
    try:
        r = httpx.get(url, headers=HEADERS, timeout=10, follow_redirects=True)
        soup = BeautifulSoup(r.text, "html.parser")
        imgs = []
        for img in soup.select("[class*=gallery] img"):
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
        params = {"page": page} if page > 1 else {}
        try:
            r = httpx.get(LISTING_URL, params=params, headers=HEADERS, timeout=20, follow_redirects=True)
            soup = BeautifulSoup(r.text, "html.parser")
        except Exception as e:
            print(f"[idnes] {e}")
            break

        cards = soup.select("article")
        if not cards:
            break

        page_items = []
        for card in cards:
            try:
                link_el  = card.select_one("a.c-products__link")
                title_el = card.select_one(".c-products__title")
                price_el = card.select_one(".c-products__price")
                addr_el  = card.select_one(".c-products__info")
                img_el   = card.select_one("img[data-src], img[src]")

                href = link_el.get("href", "") if link_el else ""
                href = urljoin(str(r.url), href) if href else ""

                title      = title_el.get_text(separator=" ", strip=True).replace("\xa0", " ") if title_el else ""
                price_text = price_el.get_text(strip=True) if price_el else ""
                price      = int(re.sub(r"[^\d]", "", price_text) or "0")
                addr       = addr_el.get_text(strip=True) if addr_el else ""
                uid        = href.rstrip("/").split("/")[-1] if href else title

                thumb = ""
                if img_el:
                    thumb = img_el.get("data-src") or img_el.get("src", "")

                if pmax and price and price > pmax:
                    continue

                area = None
                m = re.search(r"(\d+)\s*m", title)
                if m:
                    area = int(m.group(1))

                page_items.append({
                    "id":             f"idnes_{uid}",
                    "source":         "iDnes Reality",
                    "title":          title,
                    "price":          price,
                    "locality":       addr,
                    "url":            href,
                    "lat":            None,
                    "lon":            None,
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

        if len(cards) < 5:
            break

    return results
