# 🏠 Prague Apartment Monitor — Telegram Bot

**Stop refreshing real estate sites. Get notified automatically.**

A ready-to-run Telegram bot that monitors 6 Czech real estate platforms 24/7 and alerts you the moment a new apartment matching your criteria appears.

---

## 🎯 Who is this for?

- People **moving to Prague** who don't want to miss listings
- **Expats** searching for rentals without speaking Czech
- Anyone tired of **refreshing Sreality, Bezrealitky, and Expats.cz manually**

---

## ✅ What it does

**Monitors 6 sources simultaneously:**
- Sreality.cz — largest Czech real estate portal
- Bezrealitky.cz — apartments directly from owners (no agency fee)
- Expats.cz — English-language listings
- iDnes Reality — news portal real estate section
- Reality.cz — established Czech portal
- Flatio.com — furnished mid-term rentals

**Smart filtering:**
- Price range (min / max in CZK)
- Number of rooms (1+kk, 2+kk, 3+kk etc.)
- Prague district (Praha 1–10)
- Metro distance (< 300m, 500m, 800m, 1.5km, 2km)
- Furnished / pets / balcony filters
- Automatically skips sublets

**For each new listing it shows:**
- Up to 10 photos (high-res, fetched directly)
- Price, area, address
- Move-in date
- Direct link to the listing

**Review mode (like Tinder for apartments):**
- See all new apartments one by one
- 👍 Like / 👎 Dislike / ⏭ Skip
- Saved "Favourites" list for liked apartments
- Progress counter (5 / 47)

**Interactive map:**
- All found apartments plotted on Leaflet.js map
- Prague metro stations overlay
- Click on any point to see listing details
- Sent as HTML file — opens in any browser

**8 language interface:**
🇬🇧 English · 🇷🇺 Русский · 🇺🇦 Українська · 🇨🇿 Čeština
🇩🇪 Deutsch · 🇵🇱 Polski · 🇸🇰 Slovenčina · 🇪🇸 Español

---

## 📦 What you get

- Complete Python source code (8 files, ~1,500 lines)
- Setup guide (5 minutes to deploy)
- `requirements.txt` with all dependencies
- SQLite database — no external services needed
- Works on Windows, Mac, Linux, any VPS

**Requirements:**
- Python 3.10+
- A free Telegram bot token (create in 1 minute via @BotFather)
- Internet connection

---

## ⚡ Setup in 5 minutes

```
1. pip install -r requirements.txt
2. Add your Telegram bot token to config.py
3. python tg_bot.py
4. Open your bot → choose language → press ▶️ Start
```

That's it. The bot starts monitoring and will message you when apartments appear.

---

## 💬 FAQ

**Do I need a server?**
No. Runs on your PC while it's on. For 24/7 monitoring, a $5/month VPS (e.g. Hetzner) is enough.

**Will it work after sites update their design?**
The parsers use robust selectors and have been tested. If a site breaks, the bot skips it and continues with others.

**Can I use it for other cities?**
The code is structured to support it. Prague-specific parts are clearly marked.

**Is there a monthly fee?**
No. One-time purchase, runs locally.

---

## 🔄 Licence

Personal use. You may modify for your own use. Resale not permitted.

---

*Built by a developer who moved to Prague and got tired of refreshing Sreality every morning.*
