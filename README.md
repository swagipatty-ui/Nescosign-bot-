# Nescosign Billboard Bot 🏙️

An interactive, charming Telegram bot for showcasing and selling billboard /
urban-panel ad spots — from welcome message to manual payment confirmation.

## What's included

- `bot.py` — the bot
- `spots.json` — your billboard spot catalog (cities → spots → image, description, price)
- `requirements.txt` — Python dependencies

## ⚠️ Important: the demo data is placeholder — read this before launching

`spots.json` now contains **9 demo cities** — New York, London, Dubai, Oslo,
Paris, Berlin, Madrid, Monaco, and Moscow — with 7-8 spots each (Monaco has 3,
reflecting its actual size; padding a 2 km² principality with invented
landmarks wouldn't make the catalog more credible). All 61 spots use:
- **Placeholder images** (generic Unsplash city photos — not real installed
  billboards)
- **Estimated prices** based on 2026 industry rate research for comparable
  locations (e.g. Times Square, Piccadilly Lights, Sheikh Zayed Road) — not
  contracted rates
- **Estimated daily views / monthly impressions** based on published foot
  traffic and traffic-volume data for those areas — not measured ad-play data

**This is a mockup/template, not live sellable inventory.** Because you don't
yet have signed agreements with real billboard/panel owners, none of these
spots can currently be fulfilled if someone pays for them. Selling inventory
you don't control — even unintentionally — is a real legal and trust risk
once real money is involved.

**Before accepting real payments, you need to either:**
1. Sign agreements with real billboard/DOOH vendors (Broadsign resellers,
   local OOH companies, etc.) for specific spots, OR
2. Own/control physical panels yourself

**Then replace every entry in `spots.json` with:**
1. Real photos of the actual, contracted billboard/panel locations
2. Real negotiated prices
3. Real (or vendor-provided) daily view / impression figures
4. Descriptions in your own words (keep the warm tone if you like!)

Until then, treat this bot as a **pitch tool** — great for showing investors,
partners, or early customers what the experience will feel like — rather
than a live storefront.

## Setup

1. **Create your bot** with [@BotFather](https://t.me/BotFather) on Telegram
   → get your `BOT_TOKEN`.
2. **Get your admin chat ID** — message [@userinfobot](https://t.me/userinfobot)
   to get your own Telegram user ID. This is where new orders and payment
   notices will be sent.
3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
4. **Set environment variables:**
   ```bash
   export BOT_TOKEN="123456:ABC-your-real-token"
   export ADMIN_CHAT_ID="123456789"
   ```
5. **Run it:**
   ```bash
   python bot.py
   ```

## How it works

1. `/start` → warm welcome message + main menu
2. Customer taps **"Explore Billboard Spots"** → picks a city
3. Picks a spot → sees photo, charming description, and price
4. Taps **"Order This Spot"** → order summary with a unique order ID
5. Taps **"Confirm Order"** → bot shows payment instructions (edit these in
   `PAYMENT_INSTRUCTIONS` inside `bot.py`) and notifies **you** (the admin)
6. Customer pays, taps **"I've Paid"**, and can send a screenshot of proof
   — this gets forwarded straight to you
7. You verify payment and run `/confirm <order_id>` in your own chat with the
   bot → customer automatically gets a celebratory confirmation message

## Customizing

- **Welcome banner:** `images/welcome_banner.png` is shown right after
  `/start` for a strong first impression. Regenerate it by editing and
  re-running `generate_banner.py`, or simply replace the PNG with your own
  logo/banner design (same filename, same folder).
- **Payment details:** edit `PAYMENT_INSTRUCTIONS` in `bot.py`
- **Brand tone/wording:** edit the text strings throughout `bot.py` — they're
  written in plain English, easy to tweak
- **Adding more cities/spots:** just add more entries to `spots.json` following
  the existing structure — no code changes needed
- **Orders storage:** orders are currently stored in memory (`ORDERS` dict) —
  they reset if the bot restarts. For production, swap this for a real
  database (SQLite is an easy first upgrade)

## Hosting

This runs anywhere Python runs 24/7 — a cheap VPS (DigitalOcean, Hetzner),
Railway, Render, or even a Raspberry Pi. Just make sure it keeps running
continuously so customers can reach it any time.
