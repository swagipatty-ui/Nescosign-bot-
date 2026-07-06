# -*- coding: utf-8 -*-
"""
Nescosign Telegram Bot
Browse billboard spots -> view photo/audience/price -> place order ->
admin gets notified -> customer pays manually via TON wallet -> admin confirms.
"""

import os
import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

from data import BRAND_NAME, BANNER_IMAGE_URL, CATEGORIES, get_category_spots, get_spot

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN", "PASTE_YOUR_TOKEN_HERE")
ADMIN_CHAT_ID = os.environ.get("ADMIN_CHAT_ID", "")
TON_WALLET_ADDRESS = os.environ.get("TON_WALLET_ADDRESS", "PASTE_YOUR_TON_WALLET_ADDRESS_HERE")

# Conversation states for the order flow
ORDER_NAME, ORDER_CONTACT = range(2)


# ---------------------------------------------------------------------------
# START / MENU
# ---------------------------------------------------------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    caption = (
        f"✨ *{BRAND_NAME}* — Billboard Advertising\n\n"
        "BIG IDEAS. BIGGER IMPACT.\n"
        "We turn spaces into impact — premium billboard placements across "
        "static and digital formats, in the locations that actually move your business.\n\n"
        "Tap below to explore available spots."
    )
    keyboard = [[InlineKeyboardButton("🔎 Explore Spots", callback_data="menu:explore")],
                [InlineKeyboardButton("ℹ️ About Us", callback_data="menu:about")],
                [InlineKeyboardButton("📞 Contact", callback_data="menu:contact")]]

    if update.message:
        await update.message.reply_photo(
            photo=BANNER_IMAGE_URL,
            caption=caption,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
    else:
        await update.callback_query.message.reply_photo(
            photo=BANNER_IMAGE_URL,
            caption=caption,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )


async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    action = query.data.split(":", 1)[1]

    if action == "explore":
        await show_categories(update, context)
    elif action == "about":
        text = (
            f"🏢 *About {BRAND_NAME}*\n\n"
            "We connect businesses with premium billboard advertising — static and "
            "digital — in the locations that get seen. Big ideas. Bigger impact.\n\n"
            "Your brand. Everywhere it matters."
        )
        keyboard = [[InlineKeyboardButton("⬅️ Back to Menu", callback_data="menu:home")]]
        await query.message.reply_text(text, parse_mode="Markdown",
                                        reply_markup=InlineKeyboardMarkup(keyboard))
    elif action == "contact":
        text = (
            "📞 *Contact Us*\n\n"
            "Have questions or want a custom quote? Message us here anytime and our "
            "team will get back to you directly."
        )
        keyboard = [[InlineKeyboardButton("⬅️ Back to Menu", callback_data="menu:home")]]
        await query.message.reply_text(text, parse_mode="Markdown",
                                        reply_markup=InlineKeyboardMarkup(keyboard))
    elif action == "home":
        await start(update, context)


# ---------------------------------------------------------------------------
# CATEGORY BROWSING
# ---------------------------------------------------------------------------
async def show_categories(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "🗂️ *Choose a billboard format to explore:*"
    keyboard = []
    for cat_id, cat in CATEGORIES.items():
        keyboard.append([InlineKeyboardButton(cat["label"], callback_data=f"cat:{cat_id}")])
    keyboard.append([InlineKeyboardButton("⬅️ Back to Menu", callback_data="menu:home")])

    query = update.callback_query
    if query:
        await query.message.reply_text(text, parse_mode="Markdown",
                                        reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.message.reply_text(text, parse_mode="Markdown",
                                         reply_markup=InlineKeyboardMarkup(keyboard))


async def category_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    cat_id = query.data.split(":", 1)[1]
    cat = CATEGORIES.get(cat_id)
    spots = get_category_spots(cat_id)

    if not cat or not spots:
        await query.message.reply_text(
            "No spots are currently listed in this format. Check back soon, or contact us "
            "for a custom placement.",
        )
        return

    text = f"{cat['label']}\n_{cat['short']}_\n\n*Available spots:*"
    keyboard = []
    for spot in spots:
        keyboard.append([InlineKeyboardButton(spot["name"], callback_data=f"spot:{spot['id']}")])
    keyboard.append([InlineKeyboardButton("⬅️ Back to Formats", callback_data="menu:explore")])

    await query.message.reply_text(text, parse_mode="Markdown",
                                    reply_markup=InlineKeyboardMarkup(keyboard))


# ---------------------------------------------------------------------------
# SPOT DETAIL
# ---------------------------------------------------------------------------
async def spot_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    spot_id = query.data.split(":", 1)[1]
    spot = get_spot(spot_id)

    if not spot:
        await query.message.reply_text("Sorry, that spot is no longer available.")
        return

    caption = (
        f"🖼️ *{spot['name']}*\n"
        f"{spot['location']}\n\n"
        f"{spot['description']}\n\n"
        f"👀 *{spot['daily_views']}* daily views\n"
        f"📊 *{spot['monthly_impressions']}* monthly impressions\n"
        f"📐 Size: {spot['size']}\n"
        f"💰 *${spot['price']:,}* — {spot['period']}\n\n"
        "Ready to make it yours?"
    )
    keyboard = [
        [InlineKeyboardButton("🛒 Order This Spot", callback_data=f"order:{spot_id}")],
        [InlineKeyboardButton("⬅️ Back to Spots", callback_data=f"backcat:{find_spot_category(spot_id)}")],
    ]

    await query.message.reply_photo(
        photo=spot["photo_url"],
        caption=caption,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


def find_spot_category(spot_id: str):
    """Look up which category a spot belongs to, so 'Back to Spots' returns to the right list."""
    from data import SPOTS
    for cat_id, spots in SPOTS.items():
        for spot in spots:
            if spot["id"] == spot_id:
                return cat_id
    return ""


async def back_to_category_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles 'Back to Spots' — re-shows the category list for the spot's format."""
    query = update.callback_query
    await query.answer()
    cat_id = query.data.split(":", 1)[1]
    # Reuse the same rendering as category_callback by faking the callback data
    query.data = f"cat:{cat_id}"
    await category_callback(update, context)


# ---------------------------------------------------------------------------
# ORDER FLOW (ConversationHandler)
# ---------------------------------------------------------------------------
async def order_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    spot_id = query.data.split(":", 1)[1]
    spot = get_spot(spot_id)

    if not spot:
        await query.message.reply_text("Sorry, that spot is no longer available.")
        return ConversationHandler.END

    context.user_data["order_spot_id"] = spot_id
    await query.message.reply_text(
        f"🧾 *Ordering:* {spot['name']}\n\n"
        "What's your business name?",
        parse_mode="Markdown",
    )
    return ORDER_NAME


async def order_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["order_business_name"] = update.message.text
    await update.message.reply_text(
        "Great. What's the best phone number or email to reach you at?"
    )
    return ORDER_CONTACT


async def order_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["order_contact"] = update.message.text
    spot_id = context.user_data.get("order_spot_id")
    spot = get_spot(spot_id)
    business_name = context.user_data.get("order_business_name")
    contact = context.user_data.get("order_contact")
    user = update.effective_user

    # Notify admin
    if ADMIN_CHAT_ID:
        admin_text = (
            "🆕 *New Order Request*\n\n"
            f"Spot: {spot['name']} ({spot['location']})\n"
            f"Price: ${spot['price']:,} — {spot['period']}\n\n"
            f"Business: {business_name}\n"
            f"Contact: {contact}\n"
            f"Telegram user: @{user.username or 'N/A'} (id: {user.id})"
        )
        try:
            await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=admin_text, parse_mode="Markdown")
        except Exception as e:
            logger.error(f"Failed to notify admin: {e}")

    # Show payment info to customer
    pay_text = (
        f"✅ *Order received!*\n\n"
        f"Spot: {spot['name']}\n"
        f"Total: *${spot['price']:,}*\n\n"
        "💎 To pay via TON/Telegram Wallet, send the equivalent amount to:\n"
        f"`{TON_WALLET_ADDRESS}`\n\n"
        "Once you've sent payment, tap the button below and our team will confirm "
        "and activate your spot."
    )
    keyboard = [[InlineKeyboardButton("✅ I've Paid", callback_data=f"paid:{spot_id}")]]
    await update.message.reply_text(pay_text, parse_mode="Markdown",
                                     reply_markup=InlineKeyboardMarkup(keyboard))
    return ConversationHandler.END


async def order_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Order cancelled. Type /start to browse spots again.")
    return ConversationHandler.END


# ---------------------------------------------------------------------------
# PAID CONFIRMATION
# ---------------------------------------------------------------------------
async def paid_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("Thanks! We'll confirm shortly.")
    spot_id = query.data.split(":", 1)[1]
    spot = get_spot(spot_id)
    user = update.effective_user

    if ADMIN_CHAT_ID:
        admin_text = (
            "💰 *Customer marked payment as SENT*\n\n"
            f"Spot: {spot['name'] if spot else spot_id}\n"
            f"Telegram user: @{user.username or 'N/A'} (id: {user.id})\n\n"
            "Please verify the TON wallet and confirm with the customer."
        )
        try:
            await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=admin_text, parse_mode="Markdown")
        except Exception as e:
            logger.error(f"Failed to notify admin: {e}")

    await query.message.reply_text(
        "🙏 Thank you! We've notified our team to verify your payment. "
        "You'll hear from us shortly to confirm your billboard launch."
    )


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------
def main():
    if "PASTE" in BOT_TOKEN:
        print("⚠️  Please set the BOT_TOKEN environment variable.")
        return

    app = Application.builder().token(BOT_TOKEN).build()

    order_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(order_start, pattern=r"^order:")],
        states={
            ORDER_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, order_name)],
            ORDER_CONTACT: [MessageHandler(filters.TEXT & ~filters.COMMAND, order_contact)],
        },
        fallbacks=[CommandHandler("cancel", order_cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(order_conv)
    app.add_handler(CallbackQueryHandler(menu_callback, pattern=r"^menu:"))
    app.add_handler(CallbackQueryHandler(category_callback, pattern=r"^cat:"))
    app.add_handler(CallbackQueryHandler(back_to_category_callback, pattern=r"^backcat:"))
    app.add_handler(CallbackQueryHandler(spot_callback, pattern=r"^spot:"))
    app.add_handler(CallbackQueryHandler(paid_callback, pattern=r"^paid:"))

    print(f"🤖 {BRAND_NAME} bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
