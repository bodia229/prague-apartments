import io
from staticmap import StaticMap, CircleMarker, IconMarker
from PIL import Image, ImageDraw, ImageFont

# Кольори за джерелом
SOURCE_COLORS = {
    "Sreality":    "#7c5cfc",
    "Bezrealitky": "#22d3ee",
    "iDnes Reality": "#f59e0b",
    "Reality.cz":  "#4ade80",
}
DEFAULT_COLOR = "#f87171"

# Центр Праги
PRAGUE_LAT = 50.0755
PRAGUE_LON = 14.4378


def generate_map(listings: list[dict], width: int = 1200, height: int = 900) -> bytes:
    """
    Генерує PNG карту з маркерами квартир.
    Повертає bytes зображення.
    """
    m = StaticMap(width, height, url_template="https://tile.openstreetmap.org/{z}/{x}/{y}.png")

    if not listings:
        # Порожня карта центру Праги
        m.add_marker(CircleMarker((PRAGUE_LON, PRAGUE_LAT), "#7c5cfc", 8))
        img = m.render(zoom=12)
    else:
        for flat in listings:
            lat = flat.get("lat")
            lon = flat.get("lon")
            if not lat or not lon:
                continue
            color = SOURCE_COLORS.get(flat.get("source", ""), DEFAULT_COLOR)
            m.add_marker(CircleMarker((lon, lat), color, 14))
            m.add_marker(CircleMarker((lon, lat), "#ffffff", 6))

        # Автозум
        try:
            img = m.render()
        except Exception:
            img = m.render(zoom=12, center=(PRAGUE_LON, PRAGUE_LAT))

    # Додаємо легенду знизу
    img = _add_legend(img, listings)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _add_legend(img: Image.Image, listings: list[dict]) -> Image.Image:
    if not listings:
        return img

    # Рахуємо по джерелах
    counts = {}
    for f in listings:
        src = f.get("source", "?")
        counts[src] = counts.get(src, 0) + 1

    legend_h = 44
    new_img = Image.new("RGB", (img.width, img.height + legend_h), "#0d0d1a")
    new_img.paste(img, (0, 0))

    draw = ImageDraw.Draw(new_img)
    try:
        font = ImageFont.truetype("arial.ttf", 16)
        font_sm = ImageFont.truetype("arial.ttf", 13)
    except Exception:
        font = ImageFont.load_default()
        font_sm = font

    x = 16
    y = img.height + 8

    draw.text((x, y), f"Знайдено: {len(listings)}", fill="#ffffff", font=font)
    x += 160

    for src, cnt in counts.items():
        color = SOURCE_COLORS.get(src, DEFAULT_COLOR)
        draw.ellipse([x, y + 3, x + 12, y + 15], fill=color)
        draw.text((x + 16, y), f"{src}: {cnt}", fill="#e2e8f0", font=font_sm)
        x += len(f"{src}: {cnt}") * 9 + 30

    return new_img


def generate_price_chart(listings: list[dict]) -> bytes:
    """Генерує простий бар-чарт цін."""
    if not listings:
        return b""

    prices = sorted([f["price"] for f in listings if f.get("price")], reverse=True)[:20]
    if not prices:
        return b""

    w, h, pad = 800, 400, 60
    img = Image.new("RGB", (w, h), "#07070f")
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("arial.ttf", 13)
    except Exception:
        font = ImageFont.load_default()

    max_p = max(prices)
    bar_w = (w - pad * 2) // len(prices) - 4

    for i, price in enumerate(prices):
        bar_h = int((price / max_p) * (h - pad * 2))
        x0 = pad + i * (bar_w + 4)
        y0 = h - pad - bar_h
        draw.rectangle([x0, y0, x0 + bar_w, h - pad], fill="#7c5cfc")
        draw.text((x0, h - pad + 4), f"{price//1000}k", fill="#94a3b8", font=font)

    draw.text((pad, 10), "Розподіл цін (Kč)", fill="#ffffff", font=font)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()
