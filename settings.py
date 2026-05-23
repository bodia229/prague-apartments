import json
from pathlib import Path

FILE = Path(__file__).parent / "settings.json"

DEFAULTS = {
    "deal_type":        "rent",
    "rooms":            ["2+kk", "2+1"],
    "price_min":        0,
    "price_max":        25000,
    "districts":        [],
    "max_metro_m":      800,
    "furnished":        None,
    "pets":             None,
    "balcony":          None,
    "check_interval":   1800,
    "active":           False,
    # auto-skip keywords
    "skip_keywords":    [],
    # commute filter
    "work_address":     "",
    "work_lat":         None,
    "work_lon":         None,
    "max_commute_min":  0,
    # daily digest
    "digest_mode":      False,
    "digest_hour":      9,
}


def load() -> dict:
    if FILE.exists():
        try:
            return {**DEFAULTS, **json.loads(FILE.read_text(encoding="utf-8"))}
        except Exception:
            pass
    return dict(DEFAULTS)


def save(s: dict):
    FILE.write_text(json.dumps(s, ensure_ascii=False, indent=2), encoding="utf-8")
