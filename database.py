import re
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "seen.db"

_ROOM_RE = re.compile(r"\b(\d\+(?:kk|\d))\b", re.IGNORECASE)


def _extract_rooms(flat: dict) -> str:
    if flat.get("rooms"):
        return str(flat["rooms"]).lower()
    m = _ROOM_RE.search(flat.get("title", ""))
    return m.group(1).lower() if m else ""


def init():
    with sqlite3.connect(DB_PATH) as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS seen (
                id      TEXT PRIMARY KEY,
                source  TEXT,
                seen_at TEXT DEFAULT (datetime('now'))
            )
        """)
        con.execute("""
            CREATE TABLE IF NOT EXISTS listings (
                id             TEXT PRIMARY KEY,
                source         TEXT,
                title          TEXT,
                price          INTEGER,
                locality       TEXT,
                url            TEXT,
                lat            REAL,
                lon            REAL,
                area_m2        INTEGER,
                image          TEXT,
                images_json    TEXT,
                available_from TEXT,
                found_at       TEXT DEFAULT (datetime('now'))
            )
        """)
        con.execute("""
            CREATE TABLE IF NOT EXISTS reactions (
                id          TEXT PRIMARY KEY,
                reaction    TEXT,
                reacted_at  TEXT DEFAULT (datetime('now'))
            )
        """)
        con.execute("""
            CREATE TABLE IF NOT EXISTS digest (
                id       TEXT PRIMARY KEY,
                added_at TEXT DEFAULT (datetime('now'))
            )
        """)
        # migrate existing DB — add columns if missing
        for col, typ in [("image", "TEXT"), ("available_from", "TEXT"),
                         ("images_json", "TEXT"), ("rooms", "TEXT")]:
            try:
                con.execute(f"ALTER TABLE listings ADD COLUMN {col} {typ}")
            except sqlite3.OperationalError:
                pass


def is_seen(listing_id: str) -> bool:
    with sqlite3.connect(DB_PATH) as con:
        row = con.execute("SELECT 1 FROM seen WHERE id=?", (listing_id,)).fetchone()
    return row is not None


def mark_seen(listing_id: str, source: str):
    with sqlite3.connect(DB_PATH) as con:
        con.execute("INSERT OR IGNORE INTO seen (id, source) VALUES (?,?)", (listing_id, source))


def save_listing(flat: dict):
    import json as _json
    images = flat.get("images") or []
    image  = flat.get("image") or (images[0] if images else None)
    images_json = _json.dumps(images) if images else None
    rooms = _extract_rooms(flat) or None
    with sqlite3.connect(DB_PATH) as con:
        con.execute("""
            INSERT INTO listings
                (id, source, title, price, locality, url, lat, lon, area_m2, image, images_json, available_from, rooms)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(id) DO UPDATE SET
                image          = COALESCE(excluded.image,       listings.image),
                images_json    = COALESCE(excluded.images_json, listings.images_json),
                available_from = COALESCE(excluded.available_from, listings.available_from),
                rooms          = COALESCE(excluded.rooms,       listings.rooms)
        """, (
            flat.get("id"), flat.get("source"), flat.get("title"),
            flat.get("price"), flat.get("locality"), flat.get("url"),
            flat.get("lat"), flat.get("lon"), flat.get("area_m2"),
            image, images_json, flat.get("available_from"), rooms,
        ))


def get_listings_with_coords(limit: int = 500, rooms: list | None = None) -> list[dict]:
    with sqlite3.connect(DB_PATH) as con:
        con.row_factory = sqlite3.Row
        if rooms:
            placeholders = ",".join("?" * len(rooms))
            rows = con.execute(f"""
                SELECT * FROM listings
                WHERE lat IS NOT NULL AND lon IS NOT NULL
                  AND (rooms IS NULL OR rooms IN ({placeholders}))
                ORDER BY found_at DESC LIMIT ?
            """, [r.lower() for r in rooms] + [limit]).fetchall()
        else:
            rows = con.execute("""
                SELECT * FROM listings
                WHERE lat IS NOT NULL AND lon IS NOT NULL
                ORDER BY found_at DESC LIMIT ?
            """, (limit,)).fetchall()
    return [dict(r) for r in rows]


def get_all_listings(limit: int = 50) -> list[dict]:
    with sqlite3.connect(DB_PATH) as con:
        con.row_factory = sqlite3.Row
        rows = con.execute("""
            SELECT * FROM listings ORDER BY found_at DESC LIMIT ?
        """, (limit,)).fetchall()
    return [dict(r) for r in rows]


def get_unreacted_listings(limit: int = 200) -> list[dict]:
    """Listings without a like/dislike reaction yet."""
    with sqlite3.connect(DB_PATH) as con:
        con.row_factory = sqlite3.Row
        rows = con.execute("""
            SELECT * FROM listings
            WHERE id NOT IN (SELECT id FROM reactions)
            ORDER BY found_at DESC LIMIT ?
        """, (limit,)).fetchall()
    return [dict(r) for r in rows]


def set_reaction(listing_id: str, reaction: str):
    with sqlite3.connect(DB_PATH) as con:
        con.execute(
            "INSERT OR REPLACE INTO reactions (id, reaction) VALUES (?,?)",
            (listing_id, reaction),
        )


def get_liked_listings() -> list[dict]:
    with sqlite3.connect(DB_PATH) as con:
        con.row_factory = sqlite3.Row
        rows = con.execute("""
            SELECT l.* FROM listings l
            JOIN reactions r ON l.id = r.id
            WHERE r.reaction = 'like'
            ORDER BY r.reacted_at DESC
        """).fetchall()
    return [dict(r) for r in rows]


def add_to_digest(listing_id: str):
    with sqlite3.connect(DB_PATH) as con:
        con.execute("INSERT OR IGNORE INTO digest (id) VALUES (?)", (listing_id,))


def get_digest_listings() -> list[dict]:
    with sqlite3.connect(DB_PATH) as con:
        con.row_factory = sqlite3.Row
        rows = con.execute("""
            SELECT l.* FROM listings l
            JOIN digest d ON l.id = d.id
            ORDER BY d.added_at ASC
        """).fetchall()
    return [dict(r) for r in rows]


def clear_digest():
    with sqlite3.connect(DB_PATH) as con:
        con.execute("DELETE FROM digest")


def clear_listings():
    with sqlite3.connect(DB_PATH) as con:
        con.execute("DELETE FROM listings")
        con.execute("DELETE FROM seen")
        con.execute("DELETE FROM reactions")
