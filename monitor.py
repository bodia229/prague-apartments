import re
import time
import database
import bot
import mapgen_html
import settings as cfg
from metro import nearest_metro
from commute import estimate_commute_min


_SUBRENT_KEYWORDS = ("podnájem", "podnáj", "podnaj", "sub-let", "sublet", "субаренд")
_ROOM_RE = re.compile(r"\b(\d\+(?:kk|\d))\b", re.IGNORECASE)


def passes_filter(flat: dict, s: dict) -> bool:
    price = flat.get("price", 0)
    if s.get("price_min") and price and price < s["price_min"]:
        return False
    if s.get("price_max") and price and price > s["price_max"]:
        return False

    # Rooms — safety net in case a parser returns wrong-room listings
    rooms_filter = [r.lower() for r in (s.get("rooms") or [])]
    if rooms_filter:
        flat_rooms = flat.get("rooms", "")
        if not flat_rooms:
            m = _ROOM_RE.search(flat.get("title", ""))
            flat_rooms = m.group(1).lower() if m else ""
        if flat_rooms and flat_rooms not in rooms_filter:
            return False

    # Always exclude subrents
    title = (flat.get("title") or "").lower()
    url   = (flat.get("url")   or "").lower()
    if any(kw in title or kw in url for kw in _SUBRENT_KEYWORDS):
        return False

    # User-defined auto-skip keywords
    skip_kws = [kw.lower() for kw in (s.get("skip_keywords") or []) if kw]
    if skip_kws and any(kw in title for kw in skip_kws):
        return False

    # Metro distance
    max_m = s.get("max_metro_m", 0)
    if max_m and flat.get("lat") and flat.get("lon"):
        metro = nearest_metro(flat["lat"], flat["lon"])
        if metro["distance_m"] > max_m:
            return False

    # Commute time
    max_commute = s.get("max_commute_min", 0)
    work_lat    = s.get("work_lat")
    work_lon    = s.get("work_lon")
    if max_commute and work_lat and work_lon and flat.get("lat") and flat.get("lon"):
        mins = estimate_commute_min(flat["lat"], flat["lon"], work_lat, work_lon)
        if mins > max_commute:
            return False

    return True


def run_once_with_settings(s: dict):
    sources = {
        "sreality":    True,
        "bezrealitky": True,
        "idnes":       True,
        "reality":     True,
        "flatio":      True,
        "expats":      True,
    }
    all_listings = []

    if sources.get("sreality"):
        try:
            from parsers.sreality_dyn import fetch
            items = fetch(s)
            print(f"[sreality] {len(items)}")
            all_listings.extend(items)
        except Exception as e:
            print(f"[sreality] {e}")

    if sources.get("bezrealitky"):
        try:
            from parsers.bezrealitky_dyn import fetch
            items = fetch(s)
            print(f"[bezrealitky] {len(items)}")
            all_listings.extend(items)
        except Exception as e:
            print(f"[bezrealitky] {e}")

    if sources.get("idnes"):
        try:
            from parsers.idnes import fetch
            items = fetch(s)
            print(f"[idnes] {len(items)}")
            all_listings.extend(items)
        except Exception as e:
            print(f"[idnes] {e}")

    if sources.get("reality"):
        try:
            from parsers.reality import fetch
            items = fetch(s)
            print(f"[reality.cz] {len(items)}")
            all_listings.extend(items)
        except Exception as e:
            print(f"[reality.cz] {e}")

    if sources.get("flatio"):
        try:
            from parsers.flatio import fetch
            items = fetch(s)
            print(f"[flatio] {len(items)}")
            all_listings.extend(items)
        except Exception as e:
            print(f"[flatio] {e}")

    if sources.get("expats"):
        try:
            from parsers.expats import fetch
            items = fetch(s)
            print(f"[expats] {len(items)}")
            all_listings.extend(items)
        except Exception as e:
            print(f"[expats] {e}")

    new_count = 0
    for flat in all_listings:
        uid = flat.get("id", "")
        if not uid or database.is_seen(uid):
            continue
        if not passes_filter(flat, s):
            continue
        database.mark_seen(uid, flat.get("source", ""))
        database.save_listing(flat)
        new_count += 1
        if s.get("digest_mode"):
            database.add_to_digest(uid)

    print(f"[monitor] нових: {new_count}")

    if new_count > 0 and not s.get("digest_mode"):
        bot.send_text(f"🔔 Знайдено <b>{new_count}</b> нових квартир\nНатисни 🔍 Переглянути — /menu")
        try:
            listings = database.get_listings_with_coords(500, rooms=s.get("rooms"))
            if listings:
                html = mapgen_html.generate_map_html(listings)
                bot.send_document(
                    html,
                    filename="apartments_map.html",
                    caption=f"🗺 Оновлена карта — {len(listings)} квартир",
                )
        except Exception as e:
            print(f"[monitor] map: {e}")


def run_once():
    run_once_with_settings(cfg.load())


def main():
    database.init()
    print("🏠 Monitor запущено (без бота)")
    while True:
        s = cfg.load()
        if s.get("active", True):
            run_once_with_settings(s)
        time.sleep(s.get("check_interval", 1800))


if __name__ == "__main__":
    main()
