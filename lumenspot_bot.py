"""
LUMENSPOT — Billboard & OOH Advertising Telegram Bot (with images)
====================================================================
Interactive Telegram bot for browsing and "reserving" billboard / DOOH ad
placements around the world. Built with python-telegram-bot v20+.

WHAT'S NEW IN THIS VERSION
--------------------------
- The welcome screen now sends a photo (images/welcome.jpg) + caption + buttons.
- Every city → every spot detail screen sends that spot's own photo, with the
  location, price, and description in the caption underneath.
- Because Telegram cannot edit a text message into a photo message (or a
  photo into a different photo cleanly across all clients), every screen
  transition deletes the previous bot message and sends a fresh one. Back
  buttons are rebuilt to work correctly with this approach.

SETUP
-----
1. Install dependencies:
       pip install -r requirements.txt --break-system-packages

2. Create an "images" folder next to this script and drop your image files
   in it, matching the filenames referenced in the SPOTS dictionary below
   (see the "image" field on each spot) plus "welcome.jpg" for the hero.

3. Set your bot token and admin contact below (or via environment variables).

4. Run it:
       python lumenspot_bot.py

NOTE: This demo does not process real payments. The "Contact Support" step
shows your admin's Telegram @username / phone so a human finalizes payment.
"""

import os
import random
import logging

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputFile,
)
from telegram.constants import ParseMode
from telegram.error import BadRequest
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

# ======================================================================
# CONFIG — EDIT THESE
# ======================================================================

BOT_TOKEN = os.environ.get("LUMENSPOT_BOT_TOKEN", "PUT_YOUR_BOT_TOKEN_HERE")

ADMIN_CONTACT_USERNAME = os.environ.get("LUMENSPOT_ADMIN_USERNAME", "@your_support_username")
ADMIN_CONTACT_PHONE = os.environ.get("LUMENSPOT_ADMIN_PHONE", "+1 (212) 555-0142")

# Folder where your image files live (relative to this script)
IMAGES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "images")
WELCOME_IMAGE = "welcome.jpg"

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("lumenspot")

# ======================================================================
# DATA — Billboard / OOH inventory
# Each spot needs an "image" filename that must exist inside IMAGES_DIR.
# ======================================================================

SPOTS = {
    "piccadilly": {
        "city": "London, UK",
        "name": "Piccadilly Lights",
        "tag": "Iconic · Digital Spectacular",
        "image": "piccadilly.jpg",
        "desc": (
            "The most photographed billboard on earth. Curved 4K LED wrapping "
            "the busiest corner of the West End — global brands rotate here "
            "for a reason: 100M+ annual footfall."
        ),
        "price": 325000,
        "unit": "per 2-week flight",
        "dims": "780 m² curved LED",
        "reach": "~100M annual footfall",
        "format": "Digital · 10-sec spot",
        "min_flight": "2 weeks",
        "quote": "Piccadilly doesn't sell space, it sells arrival.",
        "avail": "Limited dates",
    },
    "timessquare": {
        "city": "New York, USA",
        "name": "Times Square Spectacular",
        "tag": "Iconic · Digital Spectacular",
        "image": "timessquare.jpg",
        "desc": (
            "Wraparound LED towers above 7th Avenue, the backdrop of every "
            "New Year's Eve broadcast. Your creative shares a skyline with "
            "the world's biggest media moments, 24/7."
        ),
        "price": 410000,
        "unit": "per 2-week flight",
        "dims": "1,200 m² wraparound LED",
        "reach": "~330K daily pedestrians",
        "format": "Digital · 8-sec spot",
        "min_flight": "2 weeks",
        "quote": "If Times Square notices you, the internet notices you thirty seconds later.",
        "avail": "Limited dates",
    },
    "sunset": {
        "city": "Los Angeles, USA",
        "name": "Sunset Strip Static",
        "tag": "Premium · Static Bulletin",
        "image": "sunset.jpg",
        "desc": (
            "A classic static bulletin over Sunset Boulevard — the launchpad "
            "for major beauty and fragrance drops. Slow traffic, long dwell "
            "time, unmissable golden-hour energy."
        ),
        "price": 85000,
        "unit": "per 4-week flight",
        "dims": "14 x 48 ft bulletin",
        "reach": "~62K daily vehicles",
        "format": "Static vinyl",
        "min_flight": "4 weeks",
        "quote": "Sunset doesn't move fast, which means people actually look up.",
        "avail": "Open dates",
    },
    "amsterdam": {
        "city": "Amsterdam, Netherlands",
        "name": "P.C. Hooftstraat Column",
        "tag": "Boutique · Street Furniture",
        "image": "amsterdam.jpg",
        "desc": (
            "A street column on Amsterdam's luxury shopping mile. Moody, "
            "editorial, built for a single striking portrait — perfect for "
            "a fragrance, jewelry, or fashion exclusive."
        ),
        "price": 14500,
        "unit": "per 2-week flight",
        "dims": "2.0 x 1.5 m backlit column",
        "reach": "~40K daily foot traffic",
        "format": "Backlit poster",
        "min_flight": "2 weeks",
        "quote": "Small format, big intimacy — luxury whispers instead of shouts.",
        "avail": "Open dates",
    },
    "soho": {
        "city": "New York, USA",
        "name": "SoHo Building Wrap",
        "tag": "Statement · Building Wrap",
        "image": "soho.jpg",
        "desc": (
            "A full building-facade wrap over a SoHo intersection — massive "
            "scale, maximum cultural conversation."
        ),
        "price": 260000,
        "unit": "per 4-week flight",
        "dims": "~2,800 m² mesh wrap",
        "reach": "~85K daily foot + vehicle",
        "format": "Printed mesh wrap",
        "min_flight": "4 weeks",
        "quote": "A wrap this size doesn't get walked past — it gets walked into, camera-first.",
        "avail": "Filling fast",
    },
    "penn": {
        "city": "New York, USA",
        "name": "Penn Plaza Tower Screen",
        "tag": "Premium · Digital Tower",
        "image": "penn.jpg",
        "desc": (
            "A vertical portrait-format LED tower facing Penn Station — one "
            "of the highest-traffic transit gateways in North America."
        ),
        "price": 95000,
        "unit": "per 2-week flight",
        "dims": "9 x 12 m vertical LED",
        "reach": "~600K weekly transit riders",
        "format": "Digital · portrait",
        "min_flight": "2 weeks",
        "quote": "Commuters look up exactly once. Make it count.",
        "avail": "Open dates",
    },
    "sanjose": {
        "city": "San José, Costa Rica",
        "name": "Centro Corner Wrap",
        "tag": "Regional · Corner Static",
        "image": "sanjose.jpg",
        "desc": (
            "An unmissable corner wrap in the heart of downtown San José — "
            "dense retail foot traffic at one of the city's busiest crossings."
        ),
        "price": 9200,
        "unit": "per 4-week flight",
        "dims": "Two-panel corner wrap",
        "reach": "~30K daily foot traffic",
        "format": "Static vinyl",
        "min_flight": "4 weeks",
        "quote": "Corner placements own two streets at once — twice the eyes, one booking.",
        "avail": "Open dates",
    },
    "alps": {
        "city": "Swiss Alps, Switzerland",
        "name": "Alpine Piste-Side Panel",
        "tag": "Niche · Resort Placement",
        "image": "alps.jpg",
        "desc": (
            "A static panel at the base of a groomed ski run — an audience "
            "of high-net-worth travelers automotive and watch brands chase all winter."
        ),
        "price": 38000,
        "unit": "per season (12 weeks)",
        "dims": "18 x 6 m piste-side panel",
        "reach": "~9K daily skiers in-season",
        "format": "Static vinyl, weatherproofed",
        "min_flight": "12 weeks",
        "quote": "No audience is more captive than someone waiting for the lift.",
        "avail": "Filling fast",
    },
    "hamburg": {
        "city": "Hamburg, Germany",
        "name": "Altstadt Scaffold Wrap",
        "tag": "Value · Construction Wrap",
        "image": "hamburg.jpg",
        "desc": (
            "A large-format wrap across active scaffolding in Hamburg's old "
            "town — high dwell-time crossing at a fraction of tower pricing."
        ),
        "price": 22000,
        "unit": "per 6-week flight",
        "dims": "~900 m² scaffold wrap",
        "reach": "~52K daily foot + transit",
        "format": "Printed PVC wrap",
        "min_flight": "6 weeks",
        "quote": "Scaffolding is temporary. The impression it leaves doesn't have to be.",
        "avail": "Open dates",
    },
    "volgograd": {
        "city": "Volgograd, Russia",
        "name": "Ring Road Bulletin",
        "tag": "Regional · Highway Bulletin",
        "image": "volgograd.jpg",
        "desc": (
            "A classic elevated highway bulletin on a major commuter ring "
            "road — warm, emotional creative performs best here."
        ),
        "price": 6400,
        "unit": "per 4-week flight",
        "dims": "12 x 5 m bulletin",
        "reach": "~44K daily vehicles",
        "format": "Static vinyl",
        "min_flight": "4 weeks",
        "quote": "On a ring road, nobody's scrolling past you. They're stuck in traffic, looking right at you.",
        "avail": "Open dates",
    },
    "hollywood": {
        "city": "Los Angeles, USA",
        "name": "Hollywood Hills Approach",
        "tag": "Premium · Static Bulletin",
        "image": "hollywood.jpg",
        "desc": (
            "The dramatic downhill approach bulletin with a skyline backdrop "
            "— a favorite for golden-hour, editorial-style beauty creative."
        ),
        "price": 72000,
        "unit": "per 4-week flight",
        "dims": "14 x 48 ft bulletin",
        "reach": "~55K daily vehicles",
        "format": "Static vinyl",
        "min_flight": "4 weeks",
        "quote": "Golden hour is free. This view of it isn't — but it's close.",
        "avail": "Filling fast",
    },
}

COMPLIMENTS = [
    "Good taste, by the way — you clearly know a landmark spot when you see one. ✦",
    "Most people scroll past this part. You didn't. That's a marketer's instinct. ✦",
    "You're early. The best flight dates go fast — smart move checking now. ✦",
    "This is the part where most brands play it safe. You're clearly not most brands. ✦",
]

TICKER_FACTS = [
    "14 cities live",
    "Bookings up 32% this quarter",
    "Piccadilly Lights — 2 slots left this month",
    "Times Square — high demand",
    "New: Swiss Alpine seasonal panel",
    "Avg. campaign launch time: 4 days",
]

# Conversation states for the reservation flow
ASK_BRAND, ASK_NAME, ASK_EMAIL, ASK_PHONE = range(4)


def get_cities():
    cities = []
    for spot in SPOTS.values():
        if spot["city"] not in cities:
            cities.append(spot["city"])
    return cities


def fmt_price(n: int) -> str:
    return f"${n:,}"


def image_path(filename: str) -> str:
    return os.path.join(IMAGES_DIR, filename)


def image_exists(filename: str) -> bool:
    return os.path.isfile(image_path(filename))


# ======================================================================
# CORE HELPER — swap the current bot message for a new photo message
# ======================================================================

async def send_photo_screen(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    image_filename: str,
    caption: str,
    keyboard: InlineKeyboardMarkup,
):
    """
    Deletes the previous bot message (if this was triggered by a button
    click) and sends a fresh photo + caption + keyboard. This is the
    reliable way to move between photo screens and text screens in
    Telegram, since you cannot edit a text message into a photo message.

    Falls back to a text-only message (with a warning logged) if the
    image file is missing, so the bot never silently breaks.
    """
    chat_id = update.effective_chat.id

    # If this came from a button press, remove the old message first.
    if update.callback_query:
        try:
            await update.callback_query.message.delete()
        except BadRequest:
            pass  # message too old to delete, or already gone — safe to ignore

    path = image_path(image_filename)
    if image_exists(image_filename):
        with open(path, "rb") as photo_file:
            await context.bot.send_photo(
                chat_id=chat_id,
                photo=InputFile(photo_file, filename=image_filename),
                caption=caption,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=keyboard,
            )
    else:
        logger.warning(
            "Image file not found: %s — sending text-only fallback. "
            "Add this file to the images/ folder to fix.",
            path,
        )
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"⚠️ _(image '{image_filename}' not found — showing text only)_\n\n{caption}",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=keyboard,
        )


async def send_text_screen(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    text: str,
    keyboard: InlineKeyboardMarkup,
):
    """Same delete-and-resend approach, but for text-only screens
    (How It Works, Support) so navigation stays consistent either way."""
    chat_id = update.effective_chat.id
    if update.callback_query:
        try:
            await update.callback_query.message.delete()
        except BadRequest:
            pass
    await context.bot.send_message(
        chat_id=chat_id, text=text, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard
    )


# ======================================================================
# HANDLERS — Welcome
# ======================================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    ticker = "  •  ".join(random.sample(TICKER_FACTS, 3))
    compliment = random.choice(COMPLIMENTS)

    caption = (
        "🎬 *LUMENSPOT* — Global OOH & Billboard Network\n\n"
        "*Your brand, impossible to scroll past.*\n\n"
        "From Piccadilly Circus to Times Square, Sunset Boulevard to "
        "Amsterdam's P.C. Hooftstraat — book the billboards and digital "
        "spectaculars that stop a city in its tracks. Real inventory, "
        "real prices, booked in minutes.\n\n"
        f"📡 _{ticker}_\n\n"
        f"{compliment}"
    )

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🌍 Explore Spots", callback_data="explore")],
        [InlineKeyboardButton("❓ How It Works", callback_data="how_it_works")],
        [InlineKeyboardButton("💬 Contact Support", callback_data="support")],
    ])

    if update.callback_query:
        await update.callback_query.answer()

    await send_photo_screen(update, context, WELCOME_IMAGE, caption, keyboard)


async def how_it_works(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    text = (
        "*How LUMENSPOT works*\n\n"
        "1️⃣ *Explore Spots* — browse billboards by city, see specs & pricing.\n"
        "2️⃣ *Reserve* — pick a placement, choose your flight length, share your details.\n"
        "3️⃣ *Confirmation* — get a booking reference, held for 48 hours.\n"
        "4️⃣ *Contact Support* — our media desk finalizes the insertion order and payment with you directly.\n\n"
        "No payment is ever taken automatically — a human confirms everything."
    )
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="back_to_start")]])
    await send_text_screen(update, context, text, keyboard)


async def back_to_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await start(update, context)


# ======================================================================
# HANDLERS — Explore (city list -> spots -> detail)
# ======================================================================

async def explore(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    cities = get_cities()
    keyboard_rows = [[InlineKeyboardButton(f"📍 {city}", callback_data=f"city:{city}")] for city in cities]
    keyboard_rows.append([InlineKeyboardButton("⬅️ Back", callback_data="back_to_start")])

    text = (
        "*Explore live spots* 🌍\n\n"
        "Pick a city to see available billboard placements, specs, and rate cards."
    )
    await send_text_screen(update, context, text, InlineKeyboardMarkup(keyboard_rows))


async def show_city_spots(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    city = query.data.split("city:", 1)[1]

    spots_in_city = {k: v for k, v in SPOTS.items() if v["city"] == city}

    keyboard_rows = []
    for spot_id, spot in spots_in_city.items():
        label = f"{spot['name']} — {fmt_price(spot['price'])}"
        keyboard_rows.append([InlineKeyboardButton(label, callback_data=f"spot:{spot_id}")])
    keyboard_rows.append([InlineKeyboardButton("⬅️ Back to Cities", callback_data="explore")])

    text = f"*{city}* 📍\n\nAvailable placements:"
    await send_text_screen(update, context, text, InlineKeyboardMarkup(keyboard_rows))


async def show_spot_detail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    spot_id = query.data.split("spot:", 1)[1]
    spot = SPOTS[spot_id]

    caption = (
        f"📍 *{spot['city']}*\n"
        f"🖼 *{spot['name']}*\n"
        f"_{spot['tag']}_\n\n"
        f"{spot['desc']}\n\n"
        f"📐 *Format:* {spot['format']}\n"
        f"📏 *Dimensions:* {spot['dims']}\n"
        f"👥 *Reach:* {spot['reach']}\n"
        f"🗓 *Min. flight:* {spot['min_flight']}\n"
        f"🟢 *Availability:* {spot['avail']}\n\n"
        f"_\"{spot['quote']}\"_\n\n"
        f"💰 *{fmt_price(spot['price'])}* {spot['unit']}"
    )

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Reserve This Spot", callback_data=f"reserve:{spot_id}")],
        [InlineKeyboardButton("⬅️ Back", callback_data=f"city:{spot['city']}")],
    ])

    await send_photo_screen(update, context, spot["image"], caption, keyboard)


# ======================================================================
# HANDLERS — Reservation flow (ConversationHandler)
# ======================================================================

async def reserve_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    spot_id = query.data.split("reserve:", 1)[1]
    spot = SPOTS[spot_id]

    context.user_data["spot_id"] = spot_id

    text = (
        f"🎟 *Reserving: {spot['name']}, {spot['city']}*\n\n"
        f"Let's lock in your flight dates. A media strategist will confirm "
        f"artwork specs and payment with you directly.\n\n"
        f"First — what's your *brand or company name*?"
    )
    # This screen has no keyboard — the next step is a plain text reply.
    await send_text_screen(update, context, text, InlineKeyboardMarkup([]))
    return ASK_BRAND


async def ask_brand(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["brand"] = update.message.text.strip()
    await update.message.reply_text("Great. What's your *full name*?", parse_mode=ParseMode.MARKDOWN)
    return ASK_NAME


async def ask_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["name"] = update.message.text.strip()
    await update.message.reply_text("And your *email address*?", parse_mode=ParseMode.MARKDOWN)
    return ASK_EMAIL


async def ask_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["email"] = update.message.text.strip()
    await update.message.reply_text(
        "Last one — a *phone number* we can reach you on? (or type `skip`)",
        parse_mode=ParseMode.MARKDOWN,
    )
    return ASK_PHONE


async def ask_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone = update.message.text.strip()
    context.user_data["phone"] = "" if phone.lower() == "skip" else phone

    spot_id = context.user_data["spot_id"]
    spot = SPOTS[spot_id]

    prod = round(spot["price"] * 0.06)
    fee = round(spot["price"] * 0.03)
    total = spot["price"] + prod + fee

    booking_ref = f"LMS-{random.randint(100000, 999999)}"
    context.user_data["booking_ref"] = booking_ref

    summary = (
        f"✅ *Reservation held — {booking_ref}*\n\n"
        f"🖼 *Spot:* {spot['name']}\n"
        f"📍 *Location:* {spot['city']}\n"
        f"🗓 *Flight:* {spot['min_flight']}\n\n"
        f"🏢 *Brand:* {context.user_data['brand']}\n"
        f"👤 *Contact:* {context.user_data['name']}\n"
        f"✉️ *Email:* {context.user_data['email']}\n"
        f"📞 *Phone:* {context.user_data['phone'] or '—'}\n\n"
        f"💵 *Placement rate:* {fmt_price(spot['price'])}\n"
        f"🛠 *Production & install:* {fmt_price(prod)}\n"
        f"🧾 *Media desk service fee:* {fmt_price(fee)}\n"
        f"———————————\n"
        f"💰 *Total due:* {fmt_price(total)}\n\n"
        f"⏳ Your spot is held for *48 hours*. To lock it in and finalize "
        f"payment, contact our media desk below with your booking reference."
    )

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💬 Contact Support to Pay", callback_data="support")],
        [InlineKeyboardButton("🌍 Explore More Spots", callback_data="explore")],
    ])

    # This message is a direct reply to plain text, not a button click,
    # so we send fresh rather than trying to delete anything.
    await update.message.reply_text(summary, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard)
    return ConversationHandler.END


async def cancel_reservation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Reservation cancelled. Type /start to explore spots again any time."
    )
    return ConversationHandler.END


# ======================================================================
# HANDLERS — Support
# ======================================================================

async def support(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    booking_ref = context.user_data.get("booking_ref")
    ref_line = f"\n\n🎟 *Your booking reference:* `{booking_ref}`" if booking_ref else ""

    text = (
        "💬 *Contact the LUMENSPOT media desk*\n\n"
        "Payments, invoices, and contract paperwork are finalized by our "
        "media desk directly — not automated — so nothing gets billed you "
        "didn't approve.\n\n"
        f"👤 *Telegram:* {ADMIN_CONTACT_USERNAME}\n"
        f"📞 *Phone / WhatsApp:* {ADMIN_CONTACT_PHONE}"
        f"{ref_line}\n\n"
        "Message us your booking reference and preferred payment method "
        "(wire, ACH, or card). We respond within one business hour, "
        "Monday–Saturday, 8am–8pm local to your campaign market."
    )

    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="back_to_start")]])
    await send_text_screen(update, context, text, keyboard)


async def support_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Allows /support as a direct text command too."""
    booking_ref = context.user_data.get("booking_ref")
    ref_line = f"\n\n🎟 *Your booking reference:* `{booking_ref}`" if booking_ref else ""
    text = (
        "💬 *Contact the LUMENSPOT media desk*\n\n"
        f"👤 *Telegram:* {ADMIN_CONTACT_USERNAME}\n"
        f"📞 *Phone / WhatsApp:* {ADMIN_CONTACT_PHONE}"
        f"{ref_line}"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


# ======================================================================
# Fallback for unrecognized text
# ======================================================================

async def unknown_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "I didn't quite catch that. Type /start to explore billboard spots, "
        "or /support to reach our media desk."
    )


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error("Update %s caused error %s", update, context.error)


# ======================================================================
# MAIN
# ======================================================================

def main():
    if BOT_TOKEN == "PUT_YOUR_BOT_TOKEN_HERE" or not BOT_TOKEN:
        raise SystemExit(
            "ERROR: Set your bot token first.\n"
            "Either edit BOT_TOKEN at the top of this file, or run:\n"
            "  export LUMENSPOT_BOT_TOKEN='your:token'   (Mac/Linux)\n"
            "  set LUMENSPOT_BOT_TOKEN=your:token        (Windows)\n"
        )

    os.makedirs(IMAGES_DIR, exist_ok=True)

    app = Application.builder().token(BOT_TOKEN).build()

    # Reservation conversation
    reserve_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(reserve_start, pattern=r"^reserve:")],
        states={
            ASK_BRAND: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_brand)],
            ASK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_name)],
            ASK_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_email)],
            ASK_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_phone)],
        },
        fallbacks=[CommandHandler("cancel", cancel_reservation)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("support", support_command))
    app.add_handler(reserve_conv)

    app.add_handler(CallbackQueryHandler(explore, pattern=r"^explore$"))
    app.add_handler(CallbackQueryHandler(how_it_works, pattern=r"^how_it_works$"))
    app.add_handler(CallbackQueryHandler(back_to_start, pattern=r"^back_to_start$"))
    app.add_handler(CallbackQueryHandler(show_city_spots, pattern=r"^city:"))
    app.add_handler(CallbackQueryHandler(show_spot_detail, pattern=r"^spot:"))
    app.add_handler(CallbackQueryHandler(support, pattern=r"^support$"))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, unknown_text))
    app.add_error_handler(error_handler)

    if not image_exists(WELCOME_IMAGE):
        logger.warning(
            "Welcome image not found at %s — the bot will still run, "
            "but /start will show a text-only fallback until you add it.",
            image_path(WELCOME_IMAGE),
        )

    logger.info("LUMENSPOT bot starting — polling for updates...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
