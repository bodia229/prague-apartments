import asyncio
import threading
import time
import settings as cfg
import database
import mapgen_html
from i18n import T, get_lang, LANGS
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import BadRequest
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes,
)
from config import TG_BOT_TOKEN
import monitor as mon

# ── state ───────────────────────────────────────────────────
WAITING_PRICE       = {}   # user_id → message_id
WAITING_SKIP_KW     = {}   # user_id → True
WAITING_WORK_ADDR   = {}   # user_id → True
REVIEW_QUEUE        = {}   # user_id → list[dict]
REVIEW_CURRENT      = {}   # user_id → dict

# ── background threads ───────────────────────────────────────
_monitor_thread = None
_digest_thread  = None
_stop_event     = threading.Event()


def _monitor_loop():
    database.init()
    while not _stop_event.is_set():
        s = cfg.load()
        if s.get("active"):
            try:
                mon.run_once_with_settings(s)
            except Exception as e:
                print(f"[monitor] {e}")
        interval = cfg.load().get("check_interval", 1800)
        for _ in range(interval):
            if _stop_event.is_set():
                break
            time.sleep(1)


def _digest_loop():
    """Sends the daily digest at the configured hour."""
    _sent_today: set[int] = set()   # set of hours already sent
    while not _stop_event.is_set():
        try:
            import datetime as _dt
            now = _dt.datetime.now()
            s   = cfg.load()
            if s.get("digest_mode") and s.get("active"):
                dh = s.get("digest_hour", 9)
                key = now.date().toordinal() * 100 + dh
                if now.hour == dh and key not in _sent_today:
                    _sent_today.add(key)
                    listings = database.get_digest_listings()
                    if listings:
                        L = s.get("lang", "en")
                        import bot as _bot
                        header = T("digest_sent", L).format(n=len(listings))
                        def _line(fl):
                            u = fl.get("url", "")
                            t = fl.get("title", "?")[:60]
                            p = f"{fl.get('price',0):,}".replace(",", " ")
                            return f"• <a href='{u}'>{t}</a> — {p} Kč"
                        links = "\n".join(_line(fl) for fl in listings[:50])
                        _bot.send_text(header + links + "\n\n/menu")
                        database.clear_digest()
        except Exception as e:
            print(f"[digest] {e}")
        for _ in range(60):
            if _stop_event.is_set():
                break
            time.sleep(1)


def start_monitor():
    global _monitor_thread, _digest_thread, _stop_event
    _stop_event.clear()
    _monitor_thread = threading.Thread(target=_monitor_loop, daemon=True)
    _monitor_thread.start()
    _digest_thread = threading.Thread(target=_digest_loop, daemon=True)
    _digest_thread.start()


# ── keyboards ───────────────────────────────────────────────

def kb_language() -> InlineKeyboardMarkup:
    items = list(LANGS.items())
    rows = []
    for i in range(0, len(items), 2):
        row = []
        for code, label in items[i:i+2]:
            row.append(InlineKeyboardButton(label, callback_data=f"lang_{code}"))
        rows.append(row)
    return InlineKeyboardMarkup(rows)


def _summary_deal(s, L):
    return T("rent", L) if s.get("deal_type", "rent") == "rent" else T("sale", L)

def _summary_rooms(s, L):
    rooms = s.get("rooms") or []
    return ", ".join(rooms) if rooms else T("any_rooms", L)

def _summary_price(s, L):
    pmin = s.get("price_min", 0)
    pmax = s.get("price_max", 0)
    if pmin and pmax: return f"{pmin:,}–{pmax:,} Kč".replace(",", " ")
    if pmax:          return f"≤ {pmax:,} Kč".replace(",", " ")
    if pmin:          return f"≥ {pmin:,} Kč".replace(",", " ")
    return "∞"

def _summary_metro(s, L):
    v = s.get("max_metro_m", 0)
    if not v: return T("metro_any", L)
    return f"< {v} m" if v < 1000 else f"< {v/1000:.1f} km"

def _summary_districts(s, L):
    dists = s.get("districts") or []
    if not dists: return T("all_districts", L)
    return ", ".join(d.replace("Praha ", "P") for d in dists)


def kb_main(s: dict) -> InlineKeyboardMarkup:
    L = get_lang(s)
    active = s.get("active", False)
    n_unreacted = len(database.get_unreacted_listings(200))
    n_liked     = len(database.get_liked_listings())
    badge_review = f" ({n_unreacted})" if n_unreacted else ""
    badge_liked  = f" ({n_liked})"     if n_liked     else ""

    toggle_label = (
        f"⏸ 🟢 {T('active', L)}" if active
        else f"▶️ 🔴 {T('stopped', L)}"
    )
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(toggle_label, callback_data="toggle_active")],
        [InlineKeyboardButton(f"🏠 {_summary_deal(s,L)}",        callback_data="menu_deal"),
         InlineKeyboardButton(f"🛏 {_summary_rooms(s,L)}",       callback_data="menu_rooms")],
        [InlineKeyboardButton(f"💰 {_summary_price(s,L)}",       callback_data="menu_price"),
         InlineKeyboardButton(f"📍 {_summary_districts(s,L)}",   callback_data="menu_districts")],
        [InlineKeyboardButton(f"🚇 {_summary_metro(s,L)}",       callback_data="menu_metro"),
         InlineKeyboardButton(T("btn_extra", L),                  callback_data="menu_extra")],
        [InlineKeyboardButton(f"🔍 {T('btn_review',L)}{badge_review}", callback_data="review_start")],
        [InlineKeyboardButton(f"❤️ {T('btn_liked',L)}{badge_liked}",   callback_data="liked_list"),
         InlineKeyboardButton(T("btn_map", L),                    callback_data="show_map")],
        [InlineKeyboardButton(T("btn_skip_kw",  L), callback_data="menu_skip_kw"),
         InlineKeyboardButton(T("btn_commute",  L), callback_data="menu_commute"),
         InlineKeyboardButton(T("btn_digest",   L), callback_data="menu_digest")],
        [InlineKeyboardButton(T("btn_clear_db", L), callback_data="clear_db"),
         InlineKeyboardButton(T("btn_settings", L), callback_data="show_settings")],
        [InlineKeyboardButton(f"{T('btn_language',L)}: {LANGS.get(L,'🌍')}", callback_data="menu_language")],
    ])


def kb_deal(s: dict) -> InlineKeyboardMarkup:
    L = get_lang(s)
    r = s.get("deal_type", "rent")
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(f"{'✅' if r=='rent' else '⬜'} {T('rent', L)}", callback_data="deal_rent"),
            InlineKeyboardButton(f"{'✅' if r=='sale' else '⬜'} {T('sale', L)}", callback_data="deal_sale"),
        ],
        [InlineKeyboardButton(T("btn_back", L), callback_data="back_main")],
    ])


ROOM_OPTIONS = ["1+kk", "1+1", "2+kk", "2+1", "3+kk", "3+1", "4+kk", "4+1", "5+"]

def kb_rooms(s: dict) -> InlineKeyboardMarkup:
    L = get_lang(s)
    selected = s.get("rooms", [])
    rows = []
    row = []
    for r in ROOM_OPTIONS:
        mark = "✅" if r in selected else "⬜"
        row.append(InlineKeyboardButton(f"{mark} {r}", callback_data=f"room_{r}"))
        if len(row) == 3:
            rows.append(row); row = []
    if row:
        rows.append(row)
    rows.append([InlineKeyboardButton(T("btn_back", L), callback_data="back_main")])
    return InlineKeyboardMarkup(rows)


DISTRICTS = [f"Praha {i}" for i in range(1, 11)]

def kb_districts(s: dict) -> InlineKeyboardMarkup:
    L = get_lang(s)
    selected = s.get("districts", [])
    rows = []
    row = []
    for d in DISTRICTS:
        mark = "✅" if d in selected else "⬜"
        row.append(InlineKeyboardButton(f"{mark} {d}", callback_data=f"dist_{d.replace(' ', '_')}"))
        if len(row) == 2:
            rows.append(row); row = []
    if row:
        rows.append(row)
    rows.append([InlineKeyboardButton(T("btn_all_districts", L), callback_data="dist_all")])
    rows.append([InlineKeyboardButton(T("btn_back", L),          callback_data="back_main")])
    return InlineKeyboardMarkup(rows)


METRO_OPTIONS = [("metro_any", 0), ("< 300 m", 300), ("< 500 m", 500),
                 ("< 800 m", 800), ("< 1.5 km", 1500), ("< 2 km", 2000)]

def kb_metro(s: dict) -> InlineKeyboardMarkup:
    L = get_lang(s)
    cur = s.get("max_metro_m", 800)
    rows = []
    for label, val in METRO_OPTIONS:
        display = T("metro_any", L) if val == 0 else label
        mark = "✅" if cur == val else "⬜"
        rows.append([InlineKeyboardButton(f"{mark} {display}", callback_data=f"metro_{val}")])
    rows.append([InlineKeyboardButton(T("btn_back", L), callback_data="back_main")])
    return InlineKeyboardMarkup(rows)


def _tri_btn(key: str, s: dict, cb_prefix: str, lang: str):
    cur = s.get(key)
    return [
        InlineKeyboardButton(f"{'✅' if cur is True  else '⬜'} {T('tri_yes', lang)}", callback_data=f"{cb_prefix}_yes"),
        InlineKeyboardButton(f"{'✅' if cur is False else '⬜'} {T('tri_no',  lang)}", callback_data=f"{cb_prefix}_no"),
        InlineKeyboardButton(f"{'✅' if cur is None  else '⬜'} {T('tri_any', lang)}", callback_data=f"{cb_prefix}_any"),
    ]


def kb_extra(s: dict) -> InlineKeyboardMarkup:
    L = get_lang(s)
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(T("lbl_furniture", L), callback_data="noop")],
        _tri_btn("furnished", s, "furn", L),
        [InlineKeyboardButton(T("lbl_pets", L),      callback_data="noop")],
        _tri_btn("pets", s, "pets", L),
        [InlineKeyboardButton(T("lbl_balcony", L),   callback_data="noop")],
        _tri_btn("balcony", s, "balc", L),
        [InlineKeyboardButton(T("btn_back", L),      callback_data="back_main")],
    ])


# ── skip-keywords keyboard ──────────────────────────────────

def kb_skip_keywords(s: dict) -> InlineKeyboardMarkup:
    L    = get_lang(s)
    kws  = s.get("skip_keywords") or []
    rows = []
    for kw in kws:
        rows.append([InlineKeyboardButton(f"🗑 {kw}", callback_data=f"skipkw_del_{kw[:30]}")])
    rows.append([InlineKeyboardButton(T("btn_add_kw", L), callback_data="skipkw_add")])
    rows.append([InlineKeyboardButton(T("btn_back",   L), callback_data="back_main")])
    return InlineKeyboardMarkup(rows)


def _skip_kw_text(s: dict) -> str:
    L   = get_lang(s)
    kws = s.get("skip_keywords") or []
    body = T("skip_kw_empty", L) if not kws else "\n".join(f"• <code>{k}</code>" for k in kws)
    return T("skip_kw_menu", L) + "\n\n" + body


# ── commute keyboard ─────────────────────────────────────────

COMMUTE_OPTIONS = [20, 30, 45, 60]

def kb_commute(s: dict) -> InlineKeyboardMarkup:
    L   = get_lang(s)
    cur = s.get("max_commute_min", 0)
    rows = []
    row  = []
    for v in COMMUTE_OPTIONS:
        mark = "✅" if cur == v else "⬜"
        row.append(InlineKeyboardButton(f"{mark} < {v} min", callback_data=f"commute_min_{v}"))
        if len(row) == 2:
            rows.append(row); row = []
    if row:
        rows.append(row)
    dis_mark = "✅" if cur == 0 else "⬜"
    rows.append([InlineKeyboardButton(f"{dis_mark} {T('commute_disabled', L)}", callback_data="commute_min_0")])
    rows.append([InlineKeyboardButton(T("btn_set_addr", L), callback_data="commute_set_addr")])
    rows.append([InlineKeyboardButton(T("btn_back",     L), callback_data="back_main")])
    return InlineKeyboardMarkup(rows)


def _commute_text(s: dict) -> str:
    L = get_lang(s)
    addr = s.get("work_address", "")
    addr_line = T("commute_addr", L).format(a=addr) if addr else T("commute_no_addr", L)
    return T("commute_menu", L) + "\n\n" + addr_line


# ── digest keyboard ──────────────────────────────────────────

DIGEST_HOURS = [6, 7, 8, 9, 10, 12, 18, 19, 20, 21]

def kb_digest(s: dict) -> InlineKeyboardMarkup:
    L    = get_lang(s)
    on   = s.get("digest_mode", False)
    cur  = s.get("digest_hour", 9)
    rows = []
    if on:
        rows.append([InlineKeyboardButton(T("btn_digest_on", L), callback_data="digest_toggle")])
    else:
        rows.append([InlineKeyboardButton(T("btn_digest_off", L), callback_data="digest_toggle")])
    if on:
        row = []
        for h in DIGEST_HOURS:
            mark = "✅" if cur == h else "⬜"
            row.append(InlineKeyboardButton(f"{mark} {h:02d}:00", callback_data=f"digest_hour_{h}"))
            if len(row) == 4:
                rows.append(row); row = []
        if row:
            rows.append(row)
    rows.append([InlineKeyboardButton(T("btn_back", L), callback_data="back_main")])
    return InlineKeyboardMarkup(rows)


def _digest_text(s: dict) -> str:
    L  = get_lang(s)
    on = s.get("digest_mode", False)
    h  = s.get("digest_hour", 9)
    status = T("digest_status_on", L).format(h=f"{h:02d}") if on else T("digest_status_off", L)
    return T("digest_menu", L) + "\n\n" + status


# ── settings display ────────────────────────────────────────

def fmt_settings(s: dict) -> str:
    L = get_lang(s)
    def tri(v):
        if v is True:  return T("tri_yes", L)
        if v is False: return T("tri_no",  L)
        return T("tri_any", L)
    rooms = ", ".join(s.get("rooms") or [T("any_rooms", L)])
    dists = ", ".join(s.get("districts") or [T("all_districts", L)])
    metro = f"{s['max_metro_m']} m" if s.get("max_metro_m") else T("metro_any", L)
    pmin  = f"{s['price_min']:,}".replace(",", " ") if s.get("price_min") else "0"
    pmax  = f"{s['price_max']:,}".replace(",", " ") if s.get("price_max") else "∞"
    deal  = T("rent", L) if s.get("deal_type") == "rent" else T("sale", L)
    mins  = s.get("check_interval", 1800) // 60
    status = T("monitor_on", L) if s.get("active") else T("monitor_off", L)
    return (
        T("settings_title", L)
        + T("settings_type", L)     + deal + "\n"
        + T("settings_rooms", L)    + rooms + "\n"
        + T("settings_price", L)    + f"{pmin} – {pmax} Kč\n"
        + T("settings_districts", L)+ dists + "\n"
        + T("settings_metro", L)    + metro + "\n"
        + T("settings_furn", L)     + tri(s.get("furnished")) + "\n"
        + T("settings_pets", L)     + tri(s.get("pets")) + "\n"
        + T("settings_balcony", L)  + tri(s.get("balcony")) + "\n"
        + T("settings_interval", L).format(m=mins)
        + status
    )


# ── image fetch ─────────────────────────────────────────────

async def _fetch_image(url: str) -> bytes | None:
    import httpx, io
    from PIL import Image

    def _download():
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        r = httpx.get(url, timeout=10, follow_redirects=True, headers=headers)
        if r.status_code != 200 or len(r.content) < 500:
            return None
        ct = r.headers.get("content-type", "")
        if "avif" in ct or "webp" in ct or url.endswith((".avif", ".webp")):
            try:
                img = Image.open(io.BytesIO(r.content))
                buf = io.BytesIO()
                img.convert("RGB").save(buf, "JPEG", quality=85)
                return buf.getvalue()
            except Exception:
                return None
        return r.content

    try:
        return await asyncio.get_event_loop().run_in_executor(None, _download)
    except Exception:
        return None


# ── review helpers ──────────────────────────────────────────

async def _send_review_item(ctx, chat_id: int, flat: dict):
    import json as _json
    s  = cfg.load()
    L  = get_lang(s)
    from bot import format_listing as _fmt
    REVIEW_CURRENT[chat_id] = flat
    text = _fmt(flat, lang=L, settings=s)
    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton(T("btn_like",        L), callback_data="review_like"),
        InlineKeyboardButton(T("btn_dislike",     L), callback_data="review_dislike"),
    ], [
        InlineKeyboardButton(T("btn_skip",        L), callback_data="review_skip"),
        InlineKeyboardButton(T("btn_stop_review", L), callback_data="review_stop"),
    ]])

    raw_images = []
    if flat.get("images_json"):
        try:
            raw_images = _json.loads(flat["images_json"])
        except Exception:
            pass
    if not raw_images and flat.get("image"):
        raw_images = [flat["image"]]
    raw_images = [u for u in raw_images if u][:10]

    if not raw_images:
        await ctx.bot.send_message(chat_id=chat_id, text=text, parse_mode="HTML", reply_markup=kb)
        return

    photo_bytes = []
    for url in raw_images:
        b = await _fetch_image(url)
        if b:
            photo_bytes.append(b)

    if not photo_bytes:
        await ctx.bot.send_message(chat_id=chat_id, text=text, parse_mode="HTML", reply_markup=kb)
        return

    if len(photo_bytes) == 1:
        await ctx.bot.send_photo(chat_id=chat_id, photo=photo_bytes[0],
                                 caption=text, parse_mode="HTML", reply_markup=kb)
    else:
        from telegram import InputMediaPhoto
        media = [InputMediaPhoto(media=b) for b in photo_bytes]
        await ctx.bot.send_media_group(chat_id=chat_id, media=media)
        await ctx.bot.send_message(chat_id=chat_id, text=text, parse_mode="HTML", reply_markup=kb)


async def _next_review(ctx, chat_id: int):
    s = cfg.load()
    L = get_lang(s)
    queue = REVIEW_QUEUE.get(chat_id, [])
    if queue:
        flat = queue.pop(0)
        remaining = len(queue)
        total = REVIEW_QUEUE.get(f"{chat_id}_total", remaining + 1)
        current_n = total - remaining
        await _send_review_item(ctx, chat_id, flat)
        if remaining > 0:
            await ctx.bot.send_message(
                chat_id=chat_id,
                text=f"<i>{current_n} / {total}</i>",
                parse_mode="HTML",
            )
    else:
        REVIEW_CURRENT.pop(chat_id, None)
        await ctx.bot.send_message(
            chat_id=chat_id,
            text=T("review_done", L),
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton(T("btn_favourites", L), callback_data="liked_list"),
                InlineKeyboardButton(T("btn_menu",       L), callback_data="back_main"),
            ]]),
        )


# ── command handlers ────────────────────────────────────────

async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    s = cfg.load()
    if not s.get("lang"):
        await update.message.reply_text(
            "🌍 <b>Choose your language / Выберите язык / Оберіть мову / Vyberte jazyk:</b>",
            parse_mode="HTML",
            reply_markup=kb_language(),
        )
    else:
        L = get_lang(s)
        active = s.get("active", False)
        hint = ""
        if not active:
            hint = "\n\n▶️ " + ("Press the green button to start monitoring." if L=="en"
                   else "Нажми зелёную кнопку чтобы запустить мониторинг." if L=="ru"
                   else "Натисни зелену кнопку щоб запустити моніторинг." if L=="uk"
                   else "")
        await update.message.reply_text(
            T("welcome", L) + hint,
            parse_mode="HTML",
            reply_markup=kb_main(s),
        )


async def cmd_menu(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    s = cfg.load()
    L = get_lang(s)
    await update.message.reply_text(
        T("menu_title", L),
        parse_mode="HTML",
        reply_markup=kb_main(s),
    )


async def cmd_map(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    s = cfg.load()
    L = get_lang(s)
    await update.message.reply_text(T("map_generating", L))
    listings = database.get_listings_with_coords(500, rooms=s.get("rooms"))
    if not listings:
        await update.message.reply_text(T("map_empty", L), parse_mode="HTML")
        return
    try:
        html_bytes = await asyncio.get_event_loop().run_in_executor(
            None, mapgen_html.generate_map_html, listings
        )
        await ctx.bot.send_document(
            chat_id=update.effective_chat.id,
            document=html_bytes,
            filename="apartments_map.html",
            caption=T("map_caption", L).format(n=len(listings)),
            parse_mode="HTML",
        )
    except Exception as e:
        print(f"[map] {e}")
        await update.message.reply_text(T("map_error", L))


# ── callback router ─────────────────────────────────────────

async def on_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    data = q.data
    s = cfg.load()
    try:
        await _handle_callback(q, data, s, ctx)
    except BadRequest as e:
        if "not modified" not in str(e).lower():
            raise


async def _handle_callback(q, data: str, s: dict, ctx):
    L = get_lang(s)

    # ── language selection ──
    if data == "menu_language":
        await q.edit_message_text(T("choose_lang", L), parse_mode="HTML",
                                  reply_markup=kb_language())
        return

    if data.startswith("lang_"):
        code = data[5:]
        if code in LANGS:
            s["lang"] = code
            cfg.save(s)
            L = code
            await q.edit_message_text(T("welcome", L), parse_mode="HTML",
                                      reply_markup=kb_main(s))
        return

    # ── toggle active ──
    if data == "toggle_active":
        s["active"] = not s.get("active", False)
        cfg.save(s)
        msg = T("monitor_started", L) if s["active"] else T("monitor_stopped", L)
        await q.edit_message_text(msg, parse_mode="HTML", reply_markup=kb_main(s))
        return

    # ── navigation ──
    if data == "back_main":
        await q.edit_message_text(T("menu_title", L), parse_mode="HTML",
                                  reply_markup=kb_main(s))
        return
    if data == "menu_deal":
        await q.edit_message_text(T("deal_menu", L), parse_mode="HTML",
                                  reply_markup=kb_deal(s))
        return
    if data == "menu_rooms":
        await q.edit_message_text(T("rooms_menu", L), parse_mode="HTML",
                                  reply_markup=kb_rooms(s))
        return
    if data == "menu_price":
        WAITING_PRICE[q.from_user.id] = q.message.message_id
        await q.edit_message_text(T("price_menu", L), parse_mode="HTML")
        return
    if data == "menu_districts":
        await q.edit_message_text(T("districts_menu", L), parse_mode="HTML",
                                  reply_markup=kb_districts(s))
        return
    if data == "menu_metro":
        await q.edit_message_text(T("metro_menu", L), parse_mode="HTML",
                                  reply_markup=kb_metro(s))
        return
    if data == "menu_extra":
        await q.edit_message_text(T("extra_menu", L), parse_mode="HTML",
                                  reply_markup=kb_extra(s))
        return
    if data == "show_settings":
        await q.edit_message_text(fmt_settings(s), parse_mode="HTML",
                                  reply_markup=InlineKeyboardMarkup([[
                                      InlineKeyboardButton(T("btn_back", L), callback_data="back_main")
                                  ]]))
        return

    # ── skip keywords ──
    if data == "menu_skip_kw":
        await q.edit_message_text(_skip_kw_text(s), parse_mode="HTML",
                                  reply_markup=kb_skip_keywords(s))
        return

    if data == "skipkw_add":
        WAITING_SKIP_KW[q.from_user.id] = True
        await q.edit_message_text(T("skip_kw_hint", L), parse_mode="HTML")
        return

    if data.startswith("skipkw_del_"):
        kw = data[11:]
        kws = s.get("skip_keywords") or []
        # kw may be truncated to 30 chars; match exact OR full-length prefix
        s["skip_keywords"] = [k for k in kws if k != kw and not (len(kw) >= 30 and k.startswith(kw))]
        cfg.save(s)
        await q.edit_message_text(_skip_kw_text(s), parse_mode="HTML",
                                  reply_markup=kb_skip_keywords(s))
        return

    # ── commute ──
    if data == "menu_commute":
        await q.edit_message_text(_commute_text(s), parse_mode="HTML",
                                  reply_markup=kb_commute(s))
        return

    if data == "commute_set_addr":
        WAITING_WORK_ADDR[q.from_user.id] = True
        await q.edit_message_text(T("commute_addr_hint", L), parse_mode="HTML")
        return

    if data.startswith("commute_min_"):
        s["max_commute_min"] = int(data[12:])
        cfg.save(s)
        await q.edit_message_text(_commute_text(s), parse_mode="HTML",
                                  reply_markup=kb_commute(s))
        return

    # ── digest ──
    if data == "menu_digest":
        await q.edit_message_text(_digest_text(s), parse_mode="HTML",
                                  reply_markup=kb_digest(s))
        return

    if data == "digest_toggle":
        s["digest_mode"] = not s.get("digest_mode", False)
        cfg.save(s)
        await q.edit_message_text(_digest_text(s), parse_mode="HTML",
                                  reply_markup=kb_digest(s))
        return

    if data.startswith("digest_hour_"):
        s["digest_hour"] = int(data[12:])
        cfg.save(s)
        await q.edit_message_text(_digest_text(s), parse_mode="HTML",
                                  reply_markup=kb_digest(s))
        return

    # ── map ──
    if data == "show_map":
        await q.edit_message_text(T("map_generating", L), parse_mode="HTML")
        listings = database.get_listings_with_coords(500, rooms=s.get("rooms"))
        if not listings:
            await q.edit_message_text(
                T("map_empty", L), parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton(T("btn_back", L), callback_data="back_main")
                ]]),
            )
            return
        try:
            html_bytes = await asyncio.get_event_loop().run_in_executor(
                None, mapgen_html.generate_map_html, listings
            )
            await q.delete_message()
            await ctx.bot.send_document(
                chat_id=q.from_user.id,
                document=html_bytes,
                filename="apartments_map.html",
                caption=T("map_caption", L).format(n=len(listings)),
                parse_mode="HTML",
            )
        except Exception as e:
            print(f"[map] {e}")
            await ctx.bot.send_message(chat_id=q.from_user.id,
                                       text=T("map_error", L), reply_markup=kb_main(s))
        return

    # ── clear db ──
    if data == "clear_db":
        await q.edit_message_text(
            T("clear_confirm", L), parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(T("clear_yes", L), callback_data="clear_db_confirm")],
                [InlineKeyboardButton(T("clear_no",  L), callback_data="back_main")],
            ]),
        )
        return
    if data == "clear_db_confirm":
        database.clear_listings()
        await q.edit_message_text(T("clear_done", L), parse_mode="HTML",
                                  reply_markup=kb_main(cfg.load()))
        return

    if data == "noop":
        return

    # ── review ──
    if data == "review_start":
        listings = database.get_unreacted_listings(200)
        if not listings:
            await q.edit_message_text(
                T("review_empty", L), parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton(T("btn_back", L), callback_data="back_main")
                ]]),
            )
            return
        REVIEW_QUEUE[q.from_user.id]                     = list(listings)
        REVIEW_QUEUE[f"{q.from_user.id}_total"] = len(listings)
        await q.edit_message_text(
            T("review_start_msg", L).format(n=len(listings)),
            parse_mode="HTML",
        )
        await _next_review(ctx, q.from_user.id)
        return

    if data in ("review_like", "review_dislike", "review_skip"):
        flat = REVIEW_CURRENT.get(q.from_user.id)
        if flat:
            if data == "review_like":
                database.set_reaction(flat["id"], "like")
            elif data == "review_dislike":
                database.set_reaction(flat["id"], "dislike")
        await _next_review(ctx, q.from_user.id)
        return

    if data == "review_stop":
        REVIEW_QUEUE.pop(q.from_user.id, None)
        REVIEW_CURRENT.pop(q.from_user.id, None)
        s2 = cfg.load()
        await ctx.bot.send_message(
            chat_id=q.from_user.id,
            text=T("review_stopped", get_lang(s2)),
            parse_mode="HTML",
            reply_markup=kb_main(s2),
        )
        return

    # ── liked ──
    if data == "liked_list":
        liked = database.get_liked_listings()
        if not liked:
            await q.edit_message_text(
                T("liked_empty", L), parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton(T("btn_review_start", L), callback_data="review_start"),
                    InlineKeyboardButton(T("btn_back",         L), callback_data="back_main"),
                ]]),
            )
            return
        from bot import format_listing as _fmt
        await q.edit_message_text(T("liked_header", L).format(n=len(liked)), parse_mode="HTML")
        for flat in liked[:20]:
            text  = _fmt(flat, lang=L, settings=s)
            image = flat.get("image") or ""
            kb_l  = InlineKeyboardMarkup([[
                InlineKeyboardButton(T("btn_unlike", L), callback_data=f"unlike_{flat['id'][:40]}"),
            ]])
            try:
                if image:
                    await ctx.bot.send_photo(chat_id=q.from_user.id, photo=image,
                                             caption=text, parse_mode="HTML", reply_markup=kb_l)
                else:
                    await ctx.bot.send_message(chat_id=q.from_user.id, text=text,
                                               parse_mode="HTML", reply_markup=kb_l)
            except Exception:
                await ctx.bot.send_message(chat_id=q.from_user.id, text=text,
                                           parse_mode="HTML", reply_markup=kb_l)
        await ctx.bot.send_message(
            chat_id=q.from_user.id,
            text=T("liked_footer", L).format(n=len(liked)),
            reply_markup=kb_main(cfg.load()),
        )
        return

    if data.startswith("unlike_"):
        lid = data[7:]
        for flat in database.get_liked_listings():
            if flat["id"].startswith(lid) or flat["id"][:40] == lid:
                database.set_reaction(flat["id"], "dislike")
                break
        try:
            await q.edit_message_reply_markup(reply_markup=None)
        except Exception:
            pass
        await ctx.bot.send_message(chat_id=q.from_user.id, text=T("unlike_done", L))
        return

    # ── deal type ──
    if data in ("deal_rent", "deal_sale"):
        s["deal_type"] = "rent" if data == "deal_rent" else "sale"
        cfg.save(s)
        await q.edit_message_text(T("deal_menu", L), parse_mode="HTML",
                                  reply_markup=kb_deal(s))
        return

    # ── rooms ──
    if data.startswith("room_"):
        r = data[5:]
        rooms = s.get("rooms", [])
        if r in rooms: rooms.remove(r)
        else:          rooms.append(r)
        s["rooms"] = rooms
        cfg.save(s)
        await q.edit_message_text(T("rooms_menu", L), parse_mode="HTML",
                                  reply_markup=kb_rooms(s))
        return

    # ── districts ──
    if data == "dist_all":
        s["districts"] = []
        cfg.save(s)
        await q.edit_message_text(T("districts_menu", L), parse_mode="HTML",
                                  reply_markup=kb_districts(s))
        return
    if data.startswith("dist_"):
        d = data[5:].replace("_", " ")
        dists = s.get("districts", [])
        if d in dists: dists.remove(d)
        else:          dists.append(d)
        s["districts"] = dists
        cfg.save(s)
        await q.edit_message_text(T("districts_menu", L), parse_mode="HTML",
                                  reply_markup=kb_districts(s))
        return

    # ── metro ──
    if data.startswith("metro_"):
        s["max_metro_m"] = int(data[6:])
        cfg.save(s)
        await q.edit_message_text(T("metro_menu", L), parse_mode="HTML",
                                  reply_markup=kb_metro(s))
        return

    # ── extra ──
    def set_tri(key, val_str):
        s[key] = True if val_str == "yes" else (False if val_str == "no" else None)
        cfg.save(s)

    if data.startswith("furn_"): set_tri("furnished", data[5:])
    if data.startswith("pets_"): set_tri("pets",      data[5:])
    if data.startswith("balc_"): set_tri("balcony",   data[5:])
    if data.startswith(("furn_", "pets_", "balc_")):
        await q.edit_message_text(T("extra_menu", L), parse_mode="HTML",
                                  reply_markup=kb_extra(s))
        return


# ── text message handler ────────────────────────────────────

async def on_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid  = update.effective_user.id
    text = update.message.text.strip()
    s    = cfg.load()
    L    = get_lang(s)

    # ── skip keyword input ──
    if uid in WAITING_SKIP_KW:
        del WAITING_SKIP_KW[uid]
        word = text.lower().strip()
        if word:
            kws = s.get("skip_keywords") or []
            if word not in kws:
                kws.append(word)
            s["skip_keywords"] = kws
            cfg.save(s)
            await update.message.reply_text(
                T("skip_kw_added", L).format(w=word),
                parse_mode="HTML", reply_markup=kb_skip_keywords(cfg.load()),
            )
        return

    # ── work address input ──
    if uid in WAITING_WORK_ADDR:
        del WAITING_WORK_ADDR[uid]
        await update.message.reply_text(T("commute_geocoding", L))
        from commute import geocode
        result = await asyncio.get_event_loop().run_in_executor(None, geocode, text)
        if result:
            lat, lon = result
            s["work_address"] = text
            s["work_lat"]     = lat
            s["work_lon"]     = lon
            cfg.save(s)
            await update.message.reply_text(
                T("commute_addr_ok", L).format(a=text, lat=lat, lon=lon),
                parse_mode="HTML", reply_markup=kb_commute(cfg.load()),
            )
        else:
            await update.message.reply_text(
                T("commute_addr_fail", L), parse_mode="HTML",
            )
        return

    if uid in WAITING_PRICE:
        del WAITING_PRICE[uid]
        parts = text.split()
        try:
            if len(parts) == 2:
                s["price_min"] = int(parts[0])
                s["price_max"] = int(parts[1])
                cfg.save(s)
                pmin = f"{s['price_min']:,}".replace(",", " ")
                pmax = f"{s['price_max']:,}".replace(",", " ")
                await update.message.reply_text(
                    T("price_set", L).format(min=pmin, max=pmax),
                    parse_mode="HTML", reply_markup=kb_main(cfg.load()),
                )
            else:
                await update.message.reply_text(T("price_error", L), parse_mode="HTML")
        except ValueError:
            await update.message.reply_text(T("price_error", L), parse_mode="HTML")


# ── error handler ───────────────────────────────────────────

async def on_error(update: object, ctx: ContextTypes.DEFAULT_TYPE):
    from telegram.error import Conflict, NetworkError, TimedOut, RetryAfter
    err = ctx.error
    if isinstance(err, Conflict):
        print("\n[ERROR] Another bot instance is already running.")
        print("        Close all other tg_bot.py windows and restart.\n")
        return
    if isinstance(err, RetryAfter):
        print(f"[bot] Rate limit — retry after {err.retry_after}s")
        return
    if isinstance(err, (NetworkError, TimedOut)):
        return  # transient, ignore silently
    print(f"[bot error] {err}")


# ── entry point ─────────────────────────────────────────────

def main():
    start_monitor()
    app = Application.builder().token(TG_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start",    cmd_start))
    app.add_handler(CommandHandler("menu",     cmd_menu))
    app.add_handler(CommandHandler("settings", cmd_menu))
    app.add_handler(CommandHandler("map",      cmd_map))
    app.add_handler(CallbackQueryHandler(on_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_message))
    app.add_error_handler(on_error)
    print("🤖 Bot started. Ctrl+C to stop.")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
