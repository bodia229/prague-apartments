# 🏠 Prague Apartment Monitor — Setup & Usage Guide

A Telegram bot that watches 6 Czech real estate sites 24/7 and alerts you the moment a new apartment matching your criteria appears. No subscription, no cloud — runs on your computer or a cheap VPS.

---

## Table of Contents

1. [Requirements](#1-requirements)
2. [Create a Telegram Bot](#2-create-a-telegram-bot)
3. [Installation & First Start](#3-installation--first-start)
4. [Configuration](#4-configuration)
5. [How to Use the Bot](#5-how-to-use-the-bot)
   - [First Launch — Language](#first-launch--language)
   - [Main Menu](#main-menu)
   - [Filters: Deal, Rooms, Price, Districts, Metro](#filters)
   - [Extra Filters](#extra-filters)
   - [Browse & Review Apartments](#browse--review-apartments)
   - [Favourites](#favourites)
   - [Interactive Map](#interactive-map)
   - [Auto-skip Keywords](#auto-skip-keywords)
   - [Commute Filter](#commute-filter)
   - [Daily Digest Mode](#daily-digest-mode)
6. [Monitoring Sources](#6-monitoring-sources)
7. [Running 24/7 on a VPS](#7-running-247-on-a-vps)
8. [Troubleshooting](#8-troubleshooting)
9. [FAQ](#9-faq)

---

## 1. Requirements

| What | Details |
|------|---------|
| **Python** | 3.10 or newer — [python.org/downloads](https://www.python.org/downloads/) |
| **OS** | Windows 10/11 · macOS · Linux |
| **Internet** | Required while the bot is running |
| **Telegram account** | Free — to receive notifications |

---

## 2. Create a Telegram Bot

You need a free bot token and your Chat ID. Takes about 2 minutes.

### Get a Bot Token

1. Open Telegram, search for **@BotFather**
2. Send `/newbot`
3. Enter a display name, e.g. `Prague Apartments`
4. Enter a username ending in `bot`, e.g. `my_prague_bot`
5. BotFather replies with your token:
   ```
   7412503891:AAHs_Jf82nMkLxZzO3CtfpsFspfgZ6soVJo
   ```
   Copy it — you will paste it into `config.py`.

### Find your Chat ID

1. Send **any message** to your new bot
2. Open this URL in a browser — replace `TOKEN` with your actual token:
   ```
   https://api.telegram.org/botTOKEN/getUpdates
   ```
3. In the response, find `"chat"` and copy the `"id"` number inside it:
   ```json
   "chat": { "id": 874093938, "type": "private" }
   ```
   That number is your Chat ID.

---

## 3. Installation & First Start

### Windows — double-click to start

1. Open `config.py` in Notepad and fill in your token and Chat ID (see section 2)
2. Save the file
3. Double-click **`start.bat`**

The script will check Python, install all dependencies automatically, and start the bot. On subsequent launches, just double-click `start.bat` again.

### macOS / Linux

```bash
# Make the script executable (once)
chmod +x start.sh

# Run
./start.sh
```

The script checks Python, installs dependencies, and starts the bot. If config.py is not filled in, it tells you exactly what is missing.

### Manual start (any OS)

```bash
pip install -r requirements.txt
python tg_bot.py
```

---

## 4. Configuration

Open `config.py` in any text editor and set **two required values**:

```python
TG_BOT_TOKEN = "7412503891:AAHs_Jf82nMkLxZzO3CtfpsFspfgZ6soVJo"  # from BotFather
TG_CHAT_ID   = 874093938                                             # your Chat ID (no quotes)
```

Everything else — filters, intervals, which rooms and districts to search — is configured inside the Telegram bot itself. You do not need to touch `config.py` again after the initial setup.

---

## 5. How to Use the Bot

### First Launch — Language

Send `/start` to your bot. On first launch it asks you to pick a language:

```
🌍 Choose your language:

🇬🇧 English    🇷🇺 Русский
🇺🇦 Українська  🇨🇿 Čeština
🇩🇪 Deutsch    🇵🇱 Polski
🇸🇰 Slovenčina  🇪🇸 Español
```

Tap your language. The entire bot interface switches to it immediately. You can change it at any time from the main menu.

---

### Main Menu

All current settings are shown directly in the buttons. You always see what is active without opening submenus:

```
⚙️ Search settings

[⏸ 🟢 Active]

[🏠 Rent]              [🛏 2+kk, 2+1]
[💰 10 000–25 000 Kč]  [📍 P2, P3, P6]
[🚇 < 800 m]           [🔧 Extra filters]

[🔍 Browse (12)]       [❤️ Favourites (3)]
[🗺 Map]               [🗑 Clear database]

[📵 Auto-skip words]   [🚶 Commute]   [📰 Daily digest]

[🗑 Clear database]    [📋 Settings]
[🌍 Language: 🇬🇧 English]
```

The `(12)` badge on Browse means 12 new apartments are waiting to be reviewed.

---

### Filters

Tap any filter button to open it. Changes are saved instantly.

#### 🏠 Deal Type
Choose **Rent** or **Sale**.

#### 🛏 Rooms
Select one or more types. Czech notation:

| Type | Meaning |
|------|---------|
| `1+kk` | Studio / room with kitchenette |
| `1+1` | One room + separate kitchen |
| `2+kk` | Two rooms + kitchenette |
| `2+1` | Two rooms + kitchen |
| `3+kk` | Three rooms + kitchenette |
| `3+1` | Three rooms + kitchen |
| `4+kk` / `4+1` | Four rooms |
| `5+` | Five or more rooms |

Tap to select, tap again to deselect. Multiple selections are allowed.

#### 💰 Price
Type two numbers in the chat — minimum and maximum in CZK per month:
```
10000 25000
```
- Maximum only: `0 25000`
- Remove the filter: `0 0`

#### 📍 Districts
Praha 1 through Praha 10. Tap to select multiple. Leave all unchecked = search all districts.

#### 🚇 Metro Distance
Maximum walking distance from the apartment to the nearest metro station:
- Any distance
- ≤ 300 m
- ≤ 500 m
- ≤ 800 m *(about 10 min walk)*
- ≤ 1 500 m
- ≤ 2 000 m

---

### Extra Filters

Tap **🔧 Extra filters** for three optional toggles. Each has three states — Yes / No / Any:

- 🪑 **Furniture** — furnished / unfurnished / any
- 🐾 **Pets** — pets allowed / not allowed / any
- 🏗 **Balcony** — with balcony / without / any

---

### Browse & Review Apartments

When the monitor finds new apartments, the bot notifies you:
```
🔔 Found 8 new apartments
Tap 🔍 Browse — /menu
```

Press **🔍 Browse (8)** to enter review mode. Each apartment is shown one by one with its photos, followed by a details card:

```
🏠 Pronájem bytu 2+1, 58 m²
💰 18 500 Kč/month
📐 58 m²
📍 Praha 2 – Vinohrady
🟢 Metro: Náměstí Míru — 320 m
🚶 To work: ~14 min
📅 Move-in: 01.06.2025
🔗 Sreality

[👍 Like]  [👎 No]  [⏭ Skip]  [✖️ Stop]
```

| Button | Action |
|--------|--------|
| **👍 Like** | Saves to Favourites — revisit later |
| **👎 No** | Marks as rejected — never shown again |
| **⏭ Skip** | Marks as seen, no rating |
| **✖️ Stop** | Exits review, returns to menu |

A counter at the bottom shows your progress, e.g. `3 / 47`.

---

### Favourites

Press **❤️ Favourites** to see all liked apartments. Each shows full details and a **🗑 Remove** button to un-like.

---

### Interactive Map

Press **🗺 Map** to receive an HTML file. Open it in any browser — Chrome, Firefox, Safari:

- All found apartments are plotted as coloured dots (colour = source site)
- All Prague metro stations are shown (green / yellow / red lines)
- Click any dot to see the title, price, area, move-in date, and a link
- Zoom, drag, and toggle layers freely
- The map only shows apartments matching your current room filter

The map is automatically regenerated and sent whenever new apartments are found.

---

### Auto-skip Keywords

Press **📵 Auto-skip words** to manage your keyword blocklist.

If a listing title contains any of these words, it is silently skipped — it never reaches your review queue. Useful examples:

| Keyword | Filters out |
|---------|-------------|
| `rekonstrukce` | Apartments under renovation |
| `student` | Student-only listings |
| `short term` | Short-term / vacation rentals |
| `garáž` | Garage listings mixed into results |
| `podnájem` | Sublets *(already filtered automatically)* |

**Add:** tap **➕ Add word**, then type in the chat.  
**Remove:** tap the **🗑 keyword** button in the list.

Keywords are case-insensitive. Phrases work too.

---

### Commute Filter

Press **🚶 Commute** to set a maximum commute time to your workplace.

Apartments that would take longer than your limit are filtered before you see them.

**Setup:**
1. Tap **📍 Set work address**
2. Type your address in the chat (include the city for best results):
   ```
   Václavské náměstí, Praha
   ```
   ```
   Florenc, Praha 8
   ```
3. The bot geocodes it via OpenStreetMap and confirms the coordinates
4. Select the maximum commute: **20 / 30 / 45 / 60 minutes**

To disable: select **🚫 Disabled**.

> **Note:** Commute time is estimated from straight-line distance ÷ Prague's average door-to-door transit speed. Actual commute can vary ±30%. This filter is a fast pre-screen, not a routing engine.

---

### Daily Digest Mode

Press **📰 Daily digest** to switch notification style.

**Default (instant):** a message is sent the moment each new apartment is found.

**Digest mode:** all new apartments are collected silently and sent as a single summary once per day at your chosen hour.

**Enable:**
1. Tap **🟢 Switch to daily digest**
2. Choose the send time: 6:00, 7:00, 8:00, 9:00, 10:00, 12:00, 18:00, 19:00, 20:00, or 21:00

**Disable:** tap **🔴 Switch to instant**.

The digest message contains titles, prices, and direct links for all apartments found since the previous digest.

---

## 6. Monitoring Sources

| Site | Type | Notes |
|------|------|-------|
| **Sreality.cz** | Largest Czech portal | Agencies + private owners |
| **Bezrealitky.cz** | Owner-to-owner | No agency fee listings |
| **Expats.cz** | English-language listings | Popular with international community |
| **iDnes Reality** | News portal real estate section | Good additional coverage |
| **Reality.cz** | Established Czech portal | GPS coordinates available |
| **Flatio.com** | Furnished mid-term rentals | 1–12 month stays, price in EUR |

- All 6 sources are checked every **30 minutes** by default
- Sublets (`podnájem`) are **always filtered out** regardless of settings
- If one source fails or is temporarily blocked, the rest continue unaffected

---

## 7. Running 24/7 on a VPS

The bot runs as long as the process is alive. To monitor around the clock without keeping your PC on, deploy to a small Linux server.

**Recommended providers:** Hetzner (~€4/mo), DigitalOcean (~$5/mo), any Ubuntu VPS.

```bash
# Upload the project folder to the server, then:
pip install -r requirements.txt

# Option A — nohup (simplest)
nohup python tg_bot.py > bot.log 2>&1 &
echo "Started, PID: $!"

# Option B — screen (easier to re-attach)
screen -S bot
python tg_bot.py
# Detach: Ctrl+A, then D
# Re-attach later: screen -r bot

# Check if running
ps aux | grep tg_bot

# View live logs
tail -f bot.log
```

---

## 8. Troubleshooting

**Bot does not respond to /start**
- Check that `tg_bot.py` is running — you should see `🤖 Bot started` in the terminal
- Verify `TG_BOT_TOKEN` and `TG_CHAT_ID` in `config.py` are correct
- Make sure you are messaging the right bot (the one you created with BotFather)

**0 results from a source**
- Sites occasionally update their layout. The bot skips broken sources and continues with the rest.
- Check terminal output — each source prints a count after every scan

**"pip" / "python" is not recognized (Windows)**
- During Python installation, the option **"Add Python to PATH"** must be checked
- Reinstall Python with that option enabled, or use the `start.bat` script which handles this

**"pip" not found (macOS / Linux)**
- Use `pip3` or `python3 -m pip install -r requirements.txt`

**Commute address not found**
- Always include the city: `Florenc, Praha` instead of `Florenc`
- Use Czech or English spelling of well-known places

**Bot stops after I close the terminal**
- Expected behaviour on a local PC. Keep the terminal open, or deploy to a VPS (section 7).

**Settings are reset**
- Settings are stored in `settings.json` in the project folder. Do not delete it while the bot is running.

---

## 9. FAQ

**Do I need a server?**
No. The bot runs on your local PC. For 24/7 monitoring without leaving your PC on, a $4–5/month VPS is sufficient.

**Is there a monthly fee?**
No. One-time purchase. Runs on your hardware with no external paid services.

**Can I use it for a Telegram group?**
Yes — set `TG_CHAT_ID` to the group's ID and make your bot an admin of the group.

**What if a site changes its layout?**
Each parser catches its own errors and logs them. The other 5 sources continue working. The code is plain Python and straightforward to update.

**Can I change the check interval?**
The default is 30 minutes. To change it, edit `settings.json` and set `"check_interval"` to any number of seconds (e.g. `900` for 15 min). Or restart the bot — interval can also be changed in the settings file.

**How do I start fresh?**
- **Reset settings:** delete `settings.json`
- **Clear apartment database:** use **🗑 Clear database** inside the bot, then confirm

**Can I modify the code?**
Yes. Clean Python, no obfuscation. Licensed for personal use and modification. Resale not permitted.

---

*Most setup problems come from an incorrect token or Chat ID in `config.py`. Double-check those first.*
