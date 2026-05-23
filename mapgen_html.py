import json
from datetime import date, datetime

SOURCE_COLORS = {
    "Sreality":      "#7c5cfc",
    "Bezrealitky":   "#22d3ee",
    "iDnes Reality": "#f59e0b",
    "Reality.cz":    "#4ade80",
}
DEFAULT_COLOR = "#f87171"

METRO_STATIONS = [
    # Linka A
    {"name": "Nemocnice Motol",   "lat": 50.0689, "lon": 14.3234, "line": "A"},
    {"name": "Petřiny",           "lat": 50.0722, "lon": 14.3390, "line": "A"},
    {"name": "Nádraží Veleslavín","lat": 50.0803, "lon": 14.3621, "line": "A"},
    {"name": "Bořislavka",        "lat": 50.0837, "lon": 14.3750, "line": "A"},
    {"name": "Dejvická",          "lat": 50.1006, "lon": 14.3932, "line": "A"},
    {"name": "Hradčanská",        "lat": 50.0994, "lon": 14.3875, "line": "A"},
    {"name": "Malostranská",      "lat": 50.0880, "lon": 14.4037, "line": "A"},
    {"name": "Staroměstská",      "lat": 50.0869, "lon": 14.4161, "line": "A"},
    {"name": "Můstek",            "lat": 50.0828, "lon": 14.4238, "line": "A"},
    {"name": "Muzeum",            "lat": 50.0786, "lon": 14.4317, "line": "A"},
    {"name": "Náměstí Míru",      "lat": 50.0754, "lon": 14.4380, "line": "A"},
    {"name": "Jiřího z Poděbrad", "lat": 50.0773, "lon": 14.4508, "line": "A"},
    {"name": "Flora",             "lat": 50.0764, "lon": 14.4619, "line": "A"},
    {"name": "Želivského",        "lat": 50.0752, "lon": 14.4750, "line": "A"},
    {"name": "Strašnická",        "lat": 50.0738, "lon": 14.4880, "line": "A"},
    {"name": "Skalka",            "lat": 50.0723, "lon": 14.5013, "line": "A"},
    {"name": "Depo Hostivař",     "lat": 50.0711, "lon": 14.5153, "line": "A"},
    # Linka B
    {"name": "Zličín",            "lat": 50.0666, "lon": 14.2977, "line": "B"},
    {"name": "Stodůlky",          "lat": 50.0671, "lon": 14.3117, "line": "B"},
    {"name": "Luka",              "lat": 50.0660, "lon": 14.3257, "line": "B"},
    {"name": "Lužiny",            "lat": 50.0648, "lon": 14.3382, "line": "B"},
    {"name": "Hůrka",             "lat": 50.0641, "lon": 14.3513, "line": "B"},
    {"name": "Nové Butovice",     "lat": 50.0605, "lon": 14.3647, "line": "B"},
    {"name": "Jinonice",          "lat": 50.0562, "lon": 14.3748, "line": "B"},
    {"name": "Radlická",          "lat": 50.0542, "lon": 14.3897, "line": "B"},
    {"name": "Smíchovské nádraží","lat": 50.0510, "lon": 14.4046, "line": "B"},
    {"name": "Anděl",             "lat": 50.0717, "lon": 14.4034, "line": "B"},
    {"name": "Karlovo náměstí",   "lat": 50.0749, "lon": 14.4181, "line": "B"},
    {"name": "Národní třída",     "lat": 50.0809, "lon": 14.4175, "line": "B"},
    {"name": "Můstek",            "lat": 50.0828, "lon": 14.4238, "line": "B"},
    {"name": "Náměstí Republiky", "lat": 50.0883, "lon": 14.4296, "line": "B"},
    {"name": "Florenc",           "lat": 50.0901, "lon": 14.4397, "line": "B"},
    {"name": "Křižíkova",         "lat": 50.0929, "lon": 14.4470, "line": "B"},
    {"name": "Invalidovna",       "lat": 50.0958, "lon": 14.4610, "line": "B"},
    {"name": "Palmovka",          "lat": 50.0975, "lon": 14.4706, "line": "B"},
    {"name": "Českomoravská",     "lat": 50.0987, "lon": 14.4842, "line": "B"},
    {"name": "Vysočanská",        "lat": 50.1013, "lon": 14.4972, "line": "B"},
    {"name": "Kolbenova",         "lat": 50.1049, "lon": 14.5101, "line": "B"},
    {"name": "Hloubětín",         "lat": 50.1072, "lon": 14.5259, "line": "B"},
    {"name": "Rajská zahrada",    "lat": 50.1080, "lon": 14.5455, "line": "B"},
    {"name": "Černý Most",        "lat": 50.1082, "lon": 14.5604, "line": "B"},
    # Linka C
    {"name": "Letňany",           "lat": 50.1338, "lon": 14.5235, "line": "C"},
    {"name": "Prosek",            "lat": 50.1271, "lon": 14.5043, "line": "C"},
    {"name": "Střížkov",          "lat": 50.1181, "lon": 14.4921, "line": "C"},
    {"name": "Ládví",             "lat": 50.1114, "lon": 14.4833, "line": "C"},
    {"name": "Kobylisy",          "lat": 50.1045, "lon": 14.4642, "line": "C"},
    {"name": "Nádraží Holešovice","lat": 50.1000, "lon": 14.4408, "line": "C"},
    {"name": "Vltavská",          "lat": 50.0976, "lon": 14.4244, "line": "C"},
    {"name": "Florenc",           "lat": 50.0901, "lon": 14.4397, "line": "C"},
    {"name": "Hlavní nádraží",    "lat": 50.0830, "lon": 14.4352, "line": "C"},
    {"name": "Muzeum",            "lat": 50.0786, "lon": 14.4317, "line": "C"},
    {"name": "I. P. Pavlova",     "lat": 50.0742, "lon": 14.4330, "line": "C"},
    {"name": "Vyšehrad",          "lat": 50.0656, "lon": 14.4283, "line": "C"},
    {"name": "Pankrác",           "lat": 50.0609, "lon": 14.4316, "line": "C"},
    {"name": "Budějovická",       "lat": 50.0483, "lon": 14.4403, "line": "C"},
    {"name": "Kačerov",           "lat": 50.0359, "lon": 14.4493, "line": "C"},
    {"name": "Roztyly",           "lat": 50.0264, "lon": 14.4607, "line": "C"},
    {"name": "Chodov",            "lat": 50.0156, "lon": 14.4706, "line": "C"},
    {"name": "Opatov",            "lat": 50.0055, "lon": 14.4797, "line": "C"},
    {"name": "Háje",              "lat": 49.9967, "lon": 14.4873, "line": "C"},
]

LINE_COLOR = {"A": "#00a650", "B": "#f7c300", "C": "#e3000f"}


def _fmt_price(p) -> str:
    if not p:
        return "не вказано"
    try:
        return f"{int(p):,} Kč".replace(",", " ")
    except Exception:
        return str(p)


def _fmt_avail(avail) -> str:
    if not avail:
        return ""
    try:
        d = datetime.fromisoformat(str(avail)[:10])
        if d.date() <= date.today():
            return "Вільна зараз"
        return d.strftime("%d.%m.%Y")
    except Exception:
        return str(avail)


def generate_map_html(listings: list[dict]) -> bytes:
    features = []
    for f in listings:
        lat, lon = f.get("lat"), f.get("lon")
        if not lat or not lon:
            continue
        avail = _fmt_avail(f.get("available_from"))
        features.append({
            "lat":    lat,
            "lon":    lon,
            "title":  f.get("title", ""),
            "price":  _fmt_price(f.get("price")),
            "loc":    f.get("locality", ""),
            "area":   f.get("area_m2"),
            "url":    f.get("url", ""),
            "source": f.get("source", ""),
            "color":  SOURCE_COLORS.get(f.get("source", ""), DEFAULT_COLOR),
            "avail":  avail,
        })

    data_js   = json.dumps(features,       ensure_ascii=False)
    metro_js  = json.dumps(METRO_STATIONS, ensure_ascii=False)
    colors_js = json.dumps(SOURCE_COLORS,  ensure_ascii=False)
    total     = len(features)

    counts = {}
    for f in features:
        counts[f["source"]] = counts.get(f["source"], 0) + 1
    legend_items = "".join(
        f'<span style="display:inline-flex;align-items:center;gap:5px;margin-right:12px">'
        f'<span style="width:12px;height:12px;border-radius:50%;background:{SOURCE_COLORS.get(src, DEFAULT_COLOR)};display:inline-block"></span>'
        f'{src}: <b>{cnt}</b></span>'
        for src, cnt in counts.items()
    )

    html = f"""<!DOCTYPE html>
<html lang="uk">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Квартири у Празі — {total} оголошень</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background: #0d0d1a; color: #e2e8f0; }}
  #map {{ height: calc(100vh - 52px); width: 100%; }}
  #bar {{ height: 52px; background: #1a1a2e; display: flex; align-items: center; padding: 0 16px; gap: 16px; overflow-x: auto; white-space: nowrap; border-bottom: 1px solid #2d2d4e; }}
  #bar .ttl {{ font-size: 15px; font-weight: 700; color: #a78bfa; flex-shrink: 0; }}
  #bar .leg {{ font-size: 13px; color: #94a3b8; }}
  .popup {{ min-width: 220px; max-width: 280px; font-size: 13px; line-height: 1.5; }}
  .popup-title {{ font-weight: 700; font-size: 14px; margin-bottom: 4px; color: #1e293b; }}
  .popup-price {{ font-size: 15px; font-weight: 700; color: #7c5cfc; margin-bottom: 4px; }}
  .popup-row {{ color: #475569; margin-bottom: 2px; }}
  .popup-avail {{ color: #059669; font-weight: 600; }}
  .popup-link {{ display: inline-block; margin-top: 8px; padding: 5px 12px; background: #7c5cfc; color: #fff !important; border-radius: 6px; text-decoration: none; font-size: 12px; font-weight: 600; }}
  .popup-link:hover {{ background: #6d47e8; }}
  .metro-popup {{ font-size: 12px; color: #334155; }}
  .leaflet-popup-content-wrapper {{ border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,.2); }}
</style>
</head>
<body>
<div id="bar">
  <span class="ttl">🏠 Квартири у Празі</span>
  <span class="leg">{legend_items}</span>
</div>
<div id="map"></div>
<script>
const listings = {data_js};
const metroStations = {metro_js};
const sourceColors = {colors_js};
const lineColor = {{"A":"#00a650","B":"#f7c300","C":"#e3000f"}};

const map = L.map('map', {{zoomControl: true}}).setView([50.0755, 14.4378], 12);

L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
  attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
  maxZoom: 19,
}}).addTo(map);

// Метро
const metroLayer = L.layerGroup();
metroStations.forEach(s => {{
  const col = lineColor[s.line] || '#888';
  L.circleMarker([s.lat, s.lon], {{
    radius: 5, fillColor: col, color: '#fff',
    weight: 1.5, opacity: 1, fillOpacity: 0.85,
  }}).bindPopup(`<div class="metro-popup"><b>${{s.name}}</b><br>Лінія ${{s.line}}</div>`).addTo(metroLayer);
}});
metroLayer.addTo(map);

// Квартири
const aptLayer = L.layerGroup();
listings.forEach(f => {{
  const m = L.circleMarker([f.lat, f.lon], {{
    radius: 11, fillColor: f.color, color: '#fff',
    weight: 2.5, opacity: 1, fillOpacity: 0.92,
  }});
  let popup = `<div class="popup">
    <div class="popup-title">${{f.title}}</div>
    <div class="popup-price">${{f.price}}</div>`;
  if (f.loc)  popup += `<div class="popup-row">📍 ${{f.loc}}</div>`;
  if (f.area) popup += `<div class="popup-row">📐 ${{f.area}} м²</div>`;
  if (f.avail) popup += `<div class="popup-avail">📅 Заїзд: ${{f.avail}}</div>`;
  popup += `<div class="popup-row" style="margin-top:4px">🏷 ${{f.source}}</div>`;
  if (f.url)  popup += `<a class="popup-link" href="${{f.url}}" target="_blank">Відкрити →</a>`;
  popup += `</div>`;
  m.bindPopup(popup, {{maxWidth: 300}}).addTo(aptLayer);
}});
aptLayer.addTo(map);

// Layers control
L.control.layers(null, {{
  '🏠 Квартири': aptLayer,
  '🚇 Метро': metroLayer,
}}, {{collapsed: false, position: 'topright'}}).addTo(map);

// Auto-fit
if (listings.length > 0) {{
  const pts = listings.map(f => [f.lat, f.lon]);
  map.fitBounds(L.latLngBounds(pts).pad(0.15));
}}
</script>
</body>
</html>"""

    return html.encode("utf-8")
