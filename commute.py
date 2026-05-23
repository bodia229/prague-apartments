from math import radians, cos, sin, sqrt, atan2
import httpx


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6_371_000
    p = radians
    a = sin(p(lat2 - lat1) / 2) ** 2 + cos(p(lat1)) * cos(p(lat2)) * sin(p(lon2 - lon1) / 2) ** 2
    return R * 2 * atan2(sqrt(a), sqrt(1 - a))


def estimate_commute_min(flat_lat: float, flat_lon: float,
                         work_lat: float, work_lon: float) -> int:
    """
    Straight-line distance / 400 m per minute.
    400 m/min ≈ door-to-door speed in Prague (metro ~500 m/min + walking legs).
    Good enough for a filter; real time ±30%.
    """
    dist = haversine_m(flat_lat, flat_lon, work_lat, work_lon)
    return max(1, int(dist / 400))


def geocode(address: str) -> tuple[float, float] | None:
    """Geocode an address string using Nominatim (OSM). Returns (lat, lon) or None."""
    try:
        r = httpx.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": address, "format": "json", "limit": 1, "countrycodes": "cz"},
            headers={"User-Agent": "PragueApartmentMonitor/1.0 contact@example.com"},
            timeout=10,
        )
        data = r.json()
        if data:
            return float(data[0]["lat"]), float(data[0]["lon"])
    except Exception as e:
        print(f"[geocode] {e}")
    return None
