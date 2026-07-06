"""
Nescosign Billboard Bot
------------------------
A warm, charming, interactive Telegram bot for browsing billboard/urban-panel
ad spots, picking one, and placing an order that ends in manual payment
confirmation by an admin.

Flow:
  /start -> Welcome (charming, personalized) -> "Explore Billboard Spots"
  -> Choose a City/State -> See spot image + charming description + price
  -> "Order This Spot" -> Confirm details -> Order submitted
  -> Bot shows payment instructions -> Customer sends proof
  -> Admin confirms payment manually via /confirm <order_id>

Run:
  pip install -r requirements.txt
  export BOT_TOKEN="your-telegram-bot-token"
  export ADMIN_CHAT_ID="your-telegram-user-id"   (get from @userinfobot)
  python bot.py
"""

import json
import logging
import os
import uuid
from datetime import datetime

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

BOT_TOKEN = os.environ.get("BOT_TOKEN", "PASTE_YOUR_BOT_TOKEN_HERE")
ADMIN_CHAT_ID = os.environ.get("ADMIN_CHAT_ID", "PASTE_YOUR_TELEGRAM_CHAT_ID_HERE")
BRAND_NAME = "Nescosign"
WELCOME_BANNER = os.path.join(os.path.dirname(__file__), "images", "welcome_banner.png")

# Manual payment details — edit these to your real bank/payment info
PAYMENT_INSTRUCTIONS = (
    "🏦 *Bank Transfer*\n"
    "Account Name: Nescosign Media Ltd\n"
    "Account Number: 012311789\n"
    "Bank: (contact support)\n\n"
    "💳 Or pay via your preferred method and send proof of payment here.\n\n"
    "Once you've paid, tap *\"I've Paid\"* below and our team will confirm "
    "your booking within a few hours."
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------

with open(os.path.join(os.path.dirname(__file__), "spots.json"), "r", encoding="utf-8") as f:
    SPOTS = json.load(f)

# in-memory order store (swap for a real DB in production)
ORDERS = {}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def cities_keyboard():
    rows = []
    for city in SPOTS.keys():
        rows.append([InlineKeyboardButton(f"📍 {city}", callback_data=f"city::{city}")])
    rows.append([InlineKeyboardButton("⬅️ Back to Menu", callback_data="menu")])
    return InlineKeyboardMarkup(rows)


def spots_keyboard(city):
    rows = []
    for idx, spot in enumerate(SPOTS[city]):
        rows.append(
            [InlineKeyboardButton(f"🖼️ {spot['name']}", callback_data=f"spot::{city}::{idx}")]
        )
    rows.append([InlineKeyboardButton("⬅️ Back to Cities", callback_data="explore")])
    return InlineKeyboardMarkup(rows)


def spot_detail_keyboard(city, idx):
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🛒 Order This Spot", callback_data=f"order::{city}::{idx}")],
            [InlineKeyboardButton("⬅️ Back to Spots", callback_data=f"city::{city}")],
        ]
    )


def main_menu_keyboard():
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🌍 Explore Billboard Spots", callback_data="explore")],
            [InlineKeyboardButton("💬 Talk to Our Team", callback_data="contact")],
            [InlineKeyboardButton("ℹ️ About Nescosign", callback_data="about")],
        ]
    )


def order_confirm_keyboard(order_id):
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("✅ Confirm Order", callback_data=f"confirmorder::{order_id}")],
            [InlineKeyboardButton("❌ Cancel", callback_data="explore")],
        ]
    )


def paid_keyboard(order_id):
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton("💸 I've Paid", callback_data=f"paid::{order_id}")]]
    )


# ---------------------------------------------------------------------------
# Handlers — Start / Menu
# ---------------------------------------------------------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    first_name = user.first_name or "there"

    welcome_text = (
        f"✨ *Welcome, {first_name}!* ✨\n\n"
        f"You've just walked into *{BRAND_NAME}* — where the world's busiest "
        f"streets become the stage for *your* brand.\n\n"
        f"We put businesses like yours in front of thousands — sometimes "
        f"millions — of eyes every single day, on premium digital billboards "
        f"and urban panels across the globe's most iconic cities.\n\n"
        f"Whether you're launching something new or scaling something great, "
        f"you're in exactly the right place. Let's find the perfect spot to "
        f"put your brand on the map. 🌍🚀"
    )

    # Send the branded banner first, if it exists, for a captivating first impression
    if os.path.exists(WELCOME_BANNER):
        with open(WELCOME_BANNER, "rb") as banner:
            await update.message.reply_photo(photo=banner)

    await update.message.reply_text(
        welcome_text, parse_mode=ParseMode.MARKDOWN, reply_markup=main_menu_keyboard()
    )


async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        f"✨ *{BRAND_NAME}* — where would you like to go?\n\n"
        f"Tap below to keep exploring, madam/sir. 😊",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=main_menu_keyboard(),
    )


async def about_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    text = (
        f"🏙️ *About {BRAND_NAME}*\n\n"
        f"We connect ambitious brands with premium digital billboard and "
        f"urban panel inventory in the world's most influential cities — "
        f"from Times Square to Piccadilly Circus, Sheikh Zayed Road to "
        f"Victoria Island.\n\n"
        f"When you advertise with {BRAND_NAME}, you're not just buying screen "
        f"time — you're buying *visibility, credibility, and momentum* for "
        f"your business. Let's get your brand seen. 💼✨"
    )
    await query.edit_message_text(
        text, parse_mode=ParseMode.MARKDOWN, reply_markup=main_menu_keyboard()
    )


async def contact_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    text = (
        "💬 *Talk to Our Team*\n\n"
        "Have a custom request, a big campaign in mind, or just want to chat "
        "with a real human first? Send your message right here in this chat "
        "and our team will personally get back to you shortly. We'd love to "
        "hear what you're building. 🤝"
    )
    await query.edit_message_text(
        text, parse_mode=ParseMode.MARKDOWN, reply_markup=main_menu_keyboard()
    )


# ---------------------------------------------------------------------------
# Handlers — Explore Cities / Spots
# ---------------------------------------------------------------------------

async def explore_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    text = (
        "🌍 *Access the Best Global Urban Panel Inventory*\n\n"
        "Reach people right where their attention already is — on their way "
        "to work, to lunch, to the biggest decisions of their day.\n\n"
        "Choose a city below to see what's available, madam. Every spot "
        "comes with real photos, real numbers, and real potential for your "
        "brand. 👇"
    )
    await query.edit_message_text(
        text, parse_mode=ParseMode.MARKDOWN, reply_markup=cities_keyboard()
    )


async def city_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    city = query.data.split("::", 1)[1]
    text = (
        f"📍 *{city}*\n\n"
        f"Beautiful choice. Here are the premium spots we have available in "
        f"{city} right now. Tap any spot to see it up close. ✨"
    )
    await query.edit_message_text(
        text, parse_mode=ParseMode.MARKDOWN, reply_markup=spots_keyboard(city)
    )


async def spot_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    _, city, idx = query.data.split("::")
    idx = int(idx)
    spot = SPOTS[city][idx]

    daily_views = spot.get("daily_views", "N/A")
    monthly_impressions = spot.get("monthly_impressions", "N/A")

    caption = (
        f"🖼️ *{spot['name']}*\n"
        f"📍 {city}\n\n"
        f"{spot['description']}\n\n"
        f"👀 *{daily_views}* daily views\n"
        f"📊 *{monthly_impressions}* monthly impressions\n"
        f"💰 *${spot['price_usd']:,}* {spot['unit']}\n\n"
        f"Imagine your brand right here, madam — this is where visibility "
        f"turns into revenue. Ready to make it yours?"
    )

    # Delete old message and send a fresh photo message (can't edit text->photo)
    await query.message.delete()
    await context.bot.send_photo(
        chat_id=query.message.chat_id,
        photo=spot["image"],
        caption=caption,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=spot_detail_keyboard(city, idx),
    )


# ---------------------------------------------------------------------------
# Handlers — Ordering
# ---------------------------------------------------------------------------

async def order_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    _, city, idx = query.data.split("::")
    idx = int(idx)
    spot = SPOTS[city][idx]

    order_id = str(uuid.uuid4())[:8]
    ORDERS[order_id] = {
        "user_id": query.from_user.id,
        "username": query.from_user.username or query.from_user.first_name,
        "city": city,
        "spot": spot["name"],
        "price": spot["price_usd"],
        "status": "pending_confirmation",
        "created_at": datetime.utcnow().isoformat(),
    }

    text = (
        f"🧾 *Order Summary*\n\n"
        f"Spot: *{spot['name']}*\n"
        f"City: {city}\n"
        f"Daily Views: {spot.get('daily_views', 'N/A')}\n"
        f"Price: *${spot['price_usd']:,}* {spot['unit']}\n"
        f"Order ID: `{order_id}`\n\n"
        f"You're one tap away from getting your brand on this billboard, "
        f"madam. Shall we lock it in? 😊"
    )
    await context.bot.send_message(
        chat_id=query.message.chat_id,
        text=text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=order_confirm_keyboard(order_id),
    )


async def confirm_order_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    order_id = query.data.split("::", 1)[1]
    order = ORDERS.get(order_id)

    if not order:
        await query.edit_message_text("Sorry, this order could not be found. Please start again with /start.")
        return

    text = (
        f"🎉 *Wonderful choice!*\n\n"
        f"Your order `{order_id}` for *{order['spot']}* in {order['city']} "
        f"is now reserved for you.\n\n"
        f"To complete your booking, please make payment using the details "
        f"below:\n\n{PAYMENT_INSTRUCTIONS}"
    )
    await query.edit_message_text(
        text, parse_mode=ParseMode.MARKDOWN, reply_markup=paid_keyboard(order_id)
    )

    # notify admin
    if ADMIN_CHAT_ID and "PASTE" not in ADMIN_CHAT_ID:
        try:
            await context.bot.send_message(
                chat_id=ADMIN_CHAT_ID,
                text=(
                    f"🆕 *New Order Placed*\n"
                    f"Order ID: `{order_id}`\n"
                    f"Customer: @{order['username']} (id: {order['user_id']})\n"
                    f"Spot: {order['spot']}\n"
                    f"City: {order['city']}\n"
                    f"Price: ${order['price']:,}\n\n"
                    f"Waiting for payment. Use /confirm {order_id} once verified."
                ),
                parse_mode=ParseMode.MARKDOWN,
            )
        except Exception as e:
            logger.warning(f"Could not notify admin: {e}")


async def paid_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    order_id = query.data.split("::", 1)[1]
    order = ORDERS.get(order_id)

    if not order:
        await query.edit_message_text("Sorry, this order could not be found. Please start again with /start.")
        return

    order["status"] = "awaiting_admin_confirmation"

    text = (
        "🙏 *Thank you!*\n\n"
        "We've received your payment notice and our team is verifying it "
        "now. You'll hear from us very shortly with final confirmation — "
        "and then it's showtime for your brand. ✨\n\n"
        "Feel free to send any payment proof (screenshot/receipt) right "
        "here in this chat to speed things up."
    )
    await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN)

    if ADMIN_CHAT_ID and "PASTE" not in ADMIN_CHAT_ID:
        try:
            await context.bot.send_message(
                chat_id=ADMIN_CHAT_ID,
                text=(
                    f"💸 Customer says they've paid for order `{order_id}` "
                    f"(@{order['username']}). Please verify and run "
                    f"/confirm {order_id} once confirmed."
                ),
                parse_mode=ParseMode.MARKDOWN,
            )
        except Exception as e:
            logger.warning(f"Could not notify admin: {e}")


# ---------------------------------------------------------------------------
# Handlers — Admin
# ---------------------------------------------------------------------------

async def confirm_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin-only: /confirm <order_id> marks an order as paid & notifies customer."""
    if str(update.effective_chat.id) != str(ADMIN_CHAT_ID):
        await update.message.reply_text("This command is for the Nescosign team only.")
        return

    if not context.args:
        await update.message.reply_text("Usage: /confirm <order_id>")
        return

    order_id = context.args[0]
    order = ORDERS.get(order_id)
    if not order:
        await update.message.reply_text(f"No order found with ID {order_id}.")
        return

    order["status"] = "confirmed"
    await update.message.reply_text(f"✅ Order {order_id} marked as confirmed.")

    try:
        await context.bot.send_message(
            chat_id=order["user_id"],
            text=(
                f"🎊 *Payment Confirmed!*\n\n"
                f"Your booking for *{order['spot']}* in {order['city']} is "
                f"officially locked in, madam! 🎉\n\n"
                f"Our creative team will reach out shortly to collect your "
                f"artwork/design. Welcome to the {BRAND_NAME} family — here's "
                f"to watching your business flourish! 🚀🥂"
            ),
            parse_mode=ParseMode.MARKDOWN,
        )
    except Exception as e:
        logger.warning(f"Could not notify customer: {e}")


# ---------------------------------------------------------------------------
# Fallback text handler (forwards free-text messages, e.g. proof-of-payment
# captions or "talk to team" messages, to the admin)
# ---------------------------------------------------------------------------

async def text_forward(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if ADMIN_CHAT_ID and "PASTE" not in ADMIN_CHAT_ID:
        user = update.effective_user
        try:
            await context.bot.send_message(
                chat_id=ADMIN_CHAT_ID,
                text=(
                    f"✉️ Message from @{user.username or user.first_name} "
                    f"(id: {user.id}):\n\n{update.message.text}"
                ),
            )
        except Exception as e:
            logger.warning(f"Could not forward message to admin: {e}")
    await update.message.reply_text(
        "Got it! Our team has received your message and will be in touch "
        "shortly. In the meantime, feel free to keep exploring. 😊",
        reply_markup=main_menu_keyboard(),
    )


async def photo_forward(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Forwards payment-proof screenshots to admin."""
    if ADMIN_CHAT_ID and "PASTE" not in ADMIN_CHAT_ID:
        user = update.effective_user
        try:
            await context.bot.forward_message(
                chat_id=ADMIN_CHAT_ID,
                from_chat_id=update.message.chat_id,
                message_id=update.message.message_id,
            )
            await context.bot.send_message(
                chat_id=ADMIN_CHAT_ID,
                text=f"⬆️ Payment proof from @{user.username or user.first_name} (id: {user.id})",
            )
        except Exception as e:
            logger.warning(f"Could not forward photo to admin: {e}")
    await update.message.reply_text(
        "Thank you! We've received your payment proof and our team is "
        "reviewing it now. ✅"
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    if "PASTE" in BOT_TOKEN:
        print("⚠️  Please set the BOT_TOKEN environment variable before running.")
        return

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("confirm", confirm_command))

    app.add_handler(CallbackQueryHandler(menu_callback, pattern="^menu$"))
    app.add_handler(CallbackQueryHandler(about_callback, pattern="^about$"))
    app.add_handler(CallbackQueryHandler(contact_callback, pattern="^contact$"))
    app.add_handler(CallbackQueryHandler(explore_callback, pattern="^explore$"))
    app.add_handler(CallbackQueryHandler(city_callback, pattern="^city::"))
    app.add_handler(CallbackQueryHandler(spot_callback, pattern="^spot::"))
    app.add_handler(CallbackQueryHandler(order_callback, pattern="^order::"))
    app.add_handler(CallbackQueryHandler(confirm_order_callback, pattern="^confirmorder::"))
    app.add_handler(CallbackQueryHandler(paid_callback, pattern="^paid::"))

    app.add_handler(MessageHandler(filters.PHOTO, photo_forward))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_forward))

    print(f"🤖 {BRAND_NAME} bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
