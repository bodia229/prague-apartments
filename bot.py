import httpx
from datetime import datetime, date
from config import TG_BOT_TOKEN, TG_CHAT_ID
from metro import nearest_metro

LINE_EMOJI = {"A": "🟢", "B": "🟡", "C": "🔴"}

# Labels indexed by lang for the few translatable strings in format_listing
_FMT = {
    "price_eur":  {"en": "~{n} €/night (see site)", "ru": "~{n} €/ночь (на сайте)",
                   "uk": "~{n} €/ніч (на сайті)",   "cs": "~{n} €/noc (na webu)",
                   "de": "~{n} €/Nacht (Website)",   "pl": "~{n} €/noc (na stronie)",
                   "sk": "~{n} €/noc (na webe)",     "es": "~{n} €/noche (en web)"},
    "price_site": {"en": "price on site", "ru": "цена на сайте",
                   "uk": "ціна на сайті", "cs": "cena na webu",
                   "de": "Preis auf Website", "pl": "cena na stronie",
                   "sk": "cena na webe",     "es": "precio en web"},
    "metro":      {"en": "Metro", "ru": "Метро", "uk": "Метро",
                   "cs": "Metro", "de": "U-Bahn", "pl": "Metro",
                   "sk": "Metro", "es": "Metro"},
    "move_in":    {"en": "Move-in", "ru": "Въезд", "uk": "Заїзд",
                   "cs": "Nastěhování", "de": "Einzug", "pl": "Wprowadzka",
                   "sk": "Nasťahovanie", "es": "Entrada"},
    "avail_now":  {"en": "Available now", "ru": "Свободна сейчас",
                   "uk": "Вільна зараз",  "cs": "Volný nyní",
                   "de": "Sofort frei",   "pl": "Wolne teraz",
                   "sk": "Voľný teraz",   "es": "Disponible ahora"},
    "commute":    {"en": "🚶 To work: ~{n} min", "ru": "🚶 До работы: ~{n} мин",
                   "uk": "🚶 До роботи: ~{n} хв", "cs": "🚶 Do práce: ~{n} min",
                   "de": "🚶 Zur Arbeit: ~{n} Min", "pl": "🚶 Do pracy: ~{n} min",
                   "sk": "🚶 Do práce: ~{n} min",   "es": "🚶 Al trabajo: ~{n} min"},
}


def _t(key: str, lang: str, **kwargs) -> str:
    row = _FMT.get(key, {})
    txt = row.get(lang) or row.get("en") or key
    return txt.format(**kwargs) if kwargs else txt


def format_listing(flat: dict, lang: str = "uk", settings: dict | None = None) -> str:
    source = flat.get("source", "")
    title  = flat.get("title", "—")
    price  = flat.get("price", 0)
    area   = flat.get("area_m2")
    loc    = flat.get("locality", "")
    url    = flat.get("url", "")

    price_eur = flat.get("price_eur")
    if price_eur:
        price_line = f"💰 <b>{_t('price_eur', lang, n=price_eur)}</b>"
    elif price:
        price_line = f"💰 <b>{price:,} Kč/мес</b>".replace(",", " ")
    else:
        price_line = f"💰 <b>{_t('price_site', lang)}</b>"

    lines = [f"🏠 <b>{title}</b>", price_line]
    if area:
        lines.append(f"📐 {area} m²")
    if loc:
        lines.append(f"📍 {loc}")

    lat, lon = flat.get("lat"), flat.get("lon")
    if lat and lon:
        metro = nearest_metro(lat, lon)
        em    = LINE_EMOJI.get(metro["line"], "🚇")
        lines.append(f"{em} {_t('metro', lang)}: <b>{metro['station']}</b> — {metro['distance_m']} m")

        # Commute time if work address is set
        if settings:
            wlat = settings.get("work_lat")
            wlon = settings.get("work_lon")
            max_c = settings.get("max_commute_min", 0)
            if wlat and wlon:
                from commute import estimate_commute_min
                mins = estimate_commute_min(lat, lon, wlat, wlon)
                lines.append(_t("commute", lang, n=mins))

    avail = flat.get("available_from")
    if avail:
        try:
            d = datetime.fromisoformat(str(avail)[:10])
            today = date.today()
            avail_str = _t("avail_now", lang) if d.date() <= today else d.strftime("%d.%m.%Y")
            lines.append(f"📅 {_t('move_in', lang)}: <b>{avail_str}</b>")
        except Exception:
            lines.append(f"📅 {_t('move_in', lang)}: <b>{avail}</b>")

    lines.append(f"🔗 <a href='{url}'>{source}</a>")
    return "\n".join(lines)


def _post(method: str, **kwargs) -> dict:
    try:
        r = httpx.post(
            f"https://api.telegram.org/bot{TG_BOT_TOKEN}/{method}",
            timeout=15, **kwargs,
        )
        return r.json()
    except Exception as e:
        print(f"[bot] {method}: {e}")
        return {}


def send_text(text: str):
    _post("sendMessage", json={
        "chat_id": TG_CHAT_ID, "text": text, "parse_mode": "HTML",
    })


def send_document(data: bytes, filename: str, caption: str = ""):
    try:
        httpx.post(
            f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendDocument",
            data={"chat_id": TG_CHAT_ID, "caption": caption, "parse_mode": "HTML"},
            files={"document": (filename, data, "text/html")},
            timeout=30,
        )
    except Exception as e:
        print(f"[bot] send_document: {e}")
