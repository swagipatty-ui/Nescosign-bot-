# ======================================================================
# GLOBALSPOT
# Interactive Telegram brokerage bot for international OOH/billboard spots
# ======================================================================
#
# BUSINESS MODEL (read this before editing prices):
#   This bot is a BROKERAGE, not a media owner. Every price shown is:
#     base_vendor_price + 10% brokerage margin (YUYU's cut)
#   Base prices come from real published vendor/market rate ranges
#   researched for each city (JCDecaux, Alliance Media, Ströer, RMAA,
#   OAU Dubai, AdQuick, etc — see PRICE_SOURCES below). They are
#   presented as indicative "starting from" prices, NOT locked quotes,
#   because OOH pricing always depends on exact dates, duration and
#   availability. The bot's job is to capture the lead and route it to
#   a human (you) who confirms the real quote with the vendor.
#
#   Every country here is marked either:
#     status = "brokerage"   -> you have/are building real vendor
#                                relationships, bot treats it as a
#                                genuine bookable lead
#     status = "network"     -> aspirational / expansion market, bot
#                                still shows real market-rate pricing
#                                for credibility, but funnels to a
#                                "Request Introduction" flow instead of
#                                a hard "Book Now", so you're never
#                                promising fulfillment you can't yet
#                                back up with a signed vendor contact.
#
#   You can flip any market from "network" to "brokerage" the moment
#   you've actually got a vendor contact confirmed for it — just
#   change the status field in COUNTRIES below.
#
# ======================================================================
# PRICE_SOURCES (researched, real published ranges as of mid-2026):
#   Dubai/UAE   : OAU (outdooradvertisinguae.com), Leads Dubai,
#                 Media World, Dubai Advertising, AdQuick
#   Germany     : Statista, Alliance Media, AdQuick (Berlin DOOH),
#                 draussenwerber.de, 123Plakat, One Day Agency
#   France      : AdQuick (Paris DOOH), Alliance Media, Adintime,
#                 AdvertiseMint, One Day Agency
#   Norway      : Empire Group, wtm Outdoor, One Day Agency, Masscom
#   Monaco      : Omdat Marketing (JCDecaux Monaco agent), Sortlist
#   Russia      : Promaco.fi, RMAA Group, russia-promo.com
#   USA         : AdQuick, DASH TWO, Blindspot, Influize, management.org
#
# ======================================================================

import os
import logging
from datetime import datetime

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputFile,
)
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    ConversationHandler,
    filters,
)

# ----------------------------------------------------------------------
# CONFIG
# ----------------------------------------------------------------------

BOT_TOKEN = os.environ.get("GLOBALSPOT_BOT_TOKEN", "PUT_YOUR_NEW_REVOKED_TOKEN_HERE")

ADMIN_CONTACT_USERNAME = os.environ.get("GLOBALSPOT_ADMIN_USERNAME", "@your_yuyu_username")
ADMIN_CONTACT_PHONE = os.environ.get("GLOBALSPOT_ADMIN_PHONE", "+234 800 000 0000")
ADMIN_CHAT_ID = os.environ.get("GLOBALSPOT_ADMIN_CHAT_ID", "")  # numeric telegram id, leads get forwarded here if set

BROKERAGE_MARKUP = 0.10  # your 10% on top of every base vendor price

IMAGES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "images")
WELCOME_IMAGE = "welcome.jpg"

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("globalspot")

# Conversation states for the lead-capture flow
ASK_NAME, ASK_CONTACT, ASK_DATES, ASK_NOTES = range(4)


# ----------------------------------------------------------------------
# HELPER — apply brokerage markup and format currency nicely
# ----------------------------------------------------------------------

def marked_up(amount: int) -> int:
    """Apply YUYU's 10% brokerage margin on top of the base vendor price."""
    return round(amount * (1 + BROKERAGE_MARKUP))


def fmt_money(amount: int, currency: str) -> str:
    return f"{currency} {amount:,.0f}".replace(".0", "")


def price_range_line(low: int, high: int, currency: str, period: str = "month") -> str:
    low_m = marked_up(low)
    high_m = marked_up(high)
    return f"{fmt_money(low_m, currency)} – {fmt_money(high_m, currency)} / {period}"


# ----------------------------------------------------------------------
# DATA — Countries → Cities → Spots
# All base prices below are REAL researched market ranges (2026), before
# markup. marked_up() adds your 10% at display time — never hardcode
# the marked-up number here, always the raw base figure.
# ----------------------------------------------------------------------

COUNTRIES = {
    "uae": {
        "flag": "🇦🇪",
        "name": "UAE — Dubai",
        "status": "brokerage",
        "currency": "AED",
        "tagline": "Iconic skyline inventory — Sheikh Zayed Road, Downtown, Marina.",
        "cities": {
            "dubai": {
                "name": "Dubai",
                "spots": [
                    {
                        "id": "ae_szr_unipole",
                        "name": "Sheikh Zayed Road Unipole",
                        "tag": "Iconic · Highway",
                        "desc": "Dubai's busiest commercial corridor — 500,000+ vehicles daily. The single most requested OOH address in the UAE.",
                        "price_low": 35000, "price_high": 300000, "period": "month",
                    },
                    {
                        "id": "ae_szr_digital",
                        "name": "SZR Digital LED Spectacular",
                        "tag": "Digital · Premium",
                        "desc": "Full-motion 4K LED along Sheikh Zayed Road — dynamic creative rotation, day/night visibility, top-tier brand association.",
                        "price_low": 80000, "price_high": 400000, "period": "month",
                    },
                    {
                        "id": "ae_downtown",
                        "name": "Downtown Dubai Billboard",
                        "tag": "Global prestige",
                        "desc": "In view of Burj Khalifa and Dubai Mall — global brand prestige with heavy tourist and luxury-shopper footfall.",
                        "price_low": 40000, "price_high": 200000, "period": "month",
                    },
                    {
                        "id": "ae_marina_jbr",
                        "name": "Dubai Marina / JBR Spot",
                        "tag": "Tourist · Lifestyle",
                        "desc": "High-spending tourist and resident demographic along the Marina walk and JBR beachfront strip.",
                        "price_low": 25000, "price_high": 150000, "period": "month",
                    },
                    {
                        "id": "ae_business_bay",
                        "name": "Business Bay Digital Screen",
                        "tag": "Digital · Corporate",
                        "desc": "Reaches Dubai's dense corporate and finance crowd — ideal for B2B, fintech, and professional services brands.",
                        "price_low": 25000, "price_high": 120000, "period": "month",
                    },
                    {
                        "id": "ae_al_khail",
                        "name": "Al Khail Road Billboard",
                        "tag": "Premium highway",
                        "desc": "Second only to SZR in traffic volume — strong reach across Dubai Hills, a magnet for luxury retail campaigns.",
                        "price_low": 40000, "price_high": 120000, "period": "month",
                    },
                    {
                        "id": "ae_bridge_banner",
                        "name": "SZR Bridge Banner",
                        "tag": "High-visibility",
                        "desc": "Spans the road itself for a viewing angle no roadside unipole can match — constant exposure from both directions.",
                        "price_low": 225000, "price_high": 350000, "period": "month",
                    },
                ],
            },
        },
    },
    "germany": {
        "flag": "🇩🇪",
        "name": "Germany",
        "status": "network",
        "currency": "€",
        "tagline": "Europe's largest advertising economy — Berlin, Munich, Hamburg.",
        "cities": {
            "berlin": {
                "name": "Berlin",
                "spots": [
                    {
                        "id": "de_alexanderplatz",
                        "name": "Alexanderplatz LED Spectacular",
                        "tag": "Digital · Landmark",
                        "desc": "Germany's largest 3D anamorphic LED display — Berlin's flagship digital OOH landmark, unmissable foot and transit traffic.",
                        "price_low": 3000, "price_high": 15000, "period": "month",
                    },
                    {
                        "id": "de_kudamm",
                        "name": "Kurfürstendamm Billboard",
                        "tag": "Premium shopping strip",
                        "desc": "Berlin's answer to the Champs-Élysées — high-end retail corridor with strong affluent footfall.",
                        "price_low": 2500, "price_high": 12000, "period": "month",
                    },
                    {
                        "id": "de_potsdamer",
                        "name": "Potsdamer Platz Digital",
                        "tag": "Digital · Business hub",
                        "desc": "Modern business and entertainment district — reaches office workers, tourists, and event-goers alike.",
                        "price_low": 2500, "price_high": 12000, "period": "month",
                    },
                    {
                        "id": "de_hauptbahnhof",
                        "name": "Berlin Hauptbahnhof Digital Panel",
                        "tag": "Digital · Transit",
                        "desc": "Berlin's central train station, one of Europe's busiest transit hubs, with massive daily commuter and traveler footfall.",
                        "price_low": 2000, "price_high": 10000, "period": "month",
                    },
                    {
                        "id": "de_ber_airport",
                        "name": "Berlin Brandenburg Airport (BER) Display",
                        "tag": "Digital · Airport",
                        "desc": "Terminal 1/2 digital placements reaching international business and leisure travelers arriving in the capital.",
                        "price_low": 3500, "price_high": 18000, "period": "month",
                    },
                    {
                        "id": "de_metro_billboard",
                        "name": "U-Bahn Metro Billboard",
                        "tag": "Transit · High dwell-time",
                        "desc": "Large-format posters behind the tracks in premium U-Bahn stations, impossible to miss during the average 5-minute wait.",
                        "price_low": 500, "price_high": 3000, "period": "month",
                    },
                    {
                        "id": "de_mall_berlin",
                        "name": "Mall of Berlin Digital Screen",
                        "tag": "Retail · Indoor",
                        "desc": "Premium indoor placement in one of Berlin's largest shopping destinations, with direct exposure to active shoppers.",
                        "price_low": 1500, "price_high": 8000, "period": "month",
                    },
                ],
            },
            "munich": {
                "name": "Munich",
                "spots": [
                    {
                        "id": "de_munich_marienplatz",
                        "name": "Marienplatz City Centre Billboard",
                        "tag": "Iconic · City centre",
                        "desc": "The heart of Munich, facing the historic Neues Rathaus, with constant tourist and local footfall in Bavaria's capital.",
                        "price_low": 2500, "price_high": 12000, "period": "month",
                    },
                    {
                        "id": "de_munich_airport",
                        "name": "Munich Airport Digital Display",
                        "tag": "Digital · Airport",
                        "desc": "One of Germany's busiest airports, offering premium exposure to business travelers and Bavaria's affluent commuter base.",
                        "price_low": 3500, "price_high": 18000, "period": "month",
                    },
                    {
                        "id": "de_munich_autobahn",
                        "name": "Munich Autobahn Junction Billboard",
                        "tag": "Highway",
                        "desc": "A key motorway junction near the city, ideal for automotive, logistics, and B2B brands targeting Bavaria's industrial belt.",
                        "price_low": 2000, "price_high": 9000, "period": "month",
                    },
                ],
            },
        },
    },
    "france": {
        "flag": "🇫🇷",
        "name": "France",
        "status": "network",
        "currency": "€",
        "tagline": "Home of JCDecaux — Paris, Champs-Élysées, La Défense.",
        "cities": {
            "paris": {
                "name": "Paris",
                "spots": [
                    {
                        "id": "fr_champs_elysees",
                        "name": "Champs-Élysées Billboard",
                        "tag": "Iconic · Global prestige",
                        "desc": "The world's most famous avenue — 16M+ annual tourists pass through, unmatched global brand prestige.",
                        "price_low": 4400, "price_high": 20000, "period": "month",
                    },
                    {
                        "id": "fr_la_defense",
                        "name": "La Défense Digital Spectacular",
                        "tag": "Digital · Business district",
                        "desc": "Paris's premier business district, with dense daily footfall of finance and corporate professionals.",
                        "price_low": 3000, "price_high": 18000, "period": "month",
                    },
                    {
                        "id": "fr_avenue_montaigne",
                        "name": "Avenue Montaigne Luxury Billboard",
                        "tag": "Ultra-luxury retail",
                        "desc": "Paris's flagship haute-couture avenue, home to the world's top fashion houses and their wealthiest clientele.",
                        "price_low": 3500, "price_high": 20000, "period": "month",
                    },
                    {
                        "id": "fr_cdg_airport",
                        "name": "Charles de Gaulle Airport Panel",
                        "tag": "Digital · Airport",
                        "desc": "Europe's second-largest airport hub, with 72 million annual passengers passing through.",
                        "price_low": 3000, "price_high": 16000, "period": "month",
                    },
                    {
                        "id": "fr_chatelet_metro",
                        "name": "Châtelet-Les Halles Metro Screen",
                        "tag": "Digital · Transit",
                        "desc": "Europe's busiest underground interchange, delivering massive daily commuter reach in the heart of Paris.",
                        "price_low": 2000, "price_high": 12000, "period": "month",
                    },
                    {
                        "id": "fr_haussmann",
                        "name": "Boulevard Haussmann Billboard",
                        "tag": "Premium retail",
                        "desc": "Home to Galeries Lafayette and Printemps, two of the world's most visited department stores.",
                        "price_low": 2500, "price_high": 15000, "period": "month",
                    },
                    {
                        "id": "fr_westfield_4temps",
                        "name": "Westfield Les 4 Temps Mall Screen",
                        "tag": "Retail · Indoor",
                        "desc": "One of the largest shopping centres in Europe, located in the La Défense business district.",
                        "price_low": 1500, "price_high": 9000, "period": "month",
                    },
                ],
            },
        },
    },
    "norway": {
        "flag": "🇳🇴",
        "name": "Norway",
        "status": "network",
        "currency": "NOK",
        "tagline": "High-affluence Nordic market — Oslo, Bergen, Trondheim.",
        "cities": {
            "oslo": {
                "name": "Oslo",
                "spots": [
                    {
                        "id": "no_oslo_central",
                        "name": "Oslo Central Station Digital Panel",
                        "tag": "Digital · Transit",
                        "desc": "High dwell-time transit location in the heart of Oslo — reaches commuters and travelers daily.",
                        "price_low": 40000, "price_high": 150000, "period": "month",
                    },
                    {
                        "id": "no_oslo_city",
                        "name": "Oslo City Centre Billboard",
                        "tag": "Premium urban",
                        "desc": "Positioned in Oslo's high-footfall commercial core, with strong reach among Norway's financially stable, design-conscious consumers.",
                        "price_low": 30000, "price_high": 120000, "period": "month",
                    },
                    {
                        "id": "no_gardermoen_airport",
                        "name": "Oslo Airport (Gardermoen) Display",
                        "tag": "Digital · Airport",
                        "desc": "Norway's biggest airport, serving 104 destinations, reaching frequent flyers and business lounge travelers.",
                        "price_low": 35000, "price_high": 140000, "period": "month",
                    },
                    {
                        "id": "no_karl_johan",
                        "name": "Karl Johans Gate Billboard",
                        "tag": "Iconic · Main street",
                        "desc": "Oslo's main boulevard connecting the Royal Palace to the Central Station, with heavy pedestrian traffic year-round.",
                        "price_low": 28000, "price_high": 110000, "period": "month",
                    },
                    {
                        "id": "no_storsenter_mall",
                        "name": "Storsenter Mall Digital Screen",
                        "tag": "Retail · Indoor",
                        "desc": "Placement in one of Norway's largest shopping centre networks, reaching active retail shoppers.",
                        "price_low": 20000, "price_high": 90000, "period": "month",
                    },
                    {
                        "id": "no_tram_advertising",
                        "name": "Oslo Tramway Digital Screen",
                        "tag": "Digital · Transit",
                        "desc": "Onboard screens across Oslo's extensive tram network, popular with the university student demographic.",
                        "price_low": 15000, "price_high": 70000, "period": "month",
                    },
                    {
                        "id": "no_business_region",
                        "name": "Oslo Business Region Billboard",
                        "tag": "Corporate",
                        "desc": "Targets investors, executives, and professionals in Oslo's core business and finance district.",
                        "price_low": 25000, "price_high": 100000, "period": "month",
                    },
                ],
            },
        },
    },
    "russia": {
        "flag": "🇷🇺",
        "name": "Russia",
        "status": "network",
        "currency": "₽",
        "tagline": "One of the world's fastest-growing OOH markets — Moscow, St. Petersburg.",
        "cities": {
            "moscow": {
                "name": "Moscow",
                "spots": [
                    {
                        "id": "ru_moscow_billboard",
                        "name": "Moscow Standard Billboard (6×3m)",
                        "tag": "Classic format",
                        "desc": "Moscow's most common large-format billboard — broad city-wide reach across major roads.",
                        "price_low": 29000, "price_high": 116000, "period": "month",
                    },
                    {
                        "id": "ru_moscow_supersite",
                        "name": "Moscow Supersite (12×5m)",
                        "tag": "Extra-large highway",
                        "desc": "Massive-format installation on Moscow's main highways, delivering maximum scale and visual dominance.",
                        "price_low": 120000, "price_high": 360000, "period": "month",
                    },
                    {
                        "id": "ru_moscow_cityboard",
                        "name": "Moscow Cityboard (3×7m)",
                        "tag": "Elevated · Urban",
                        "desc": "Elevated billboard visible to both pedestrians and drivers, combining compact size with high effectiveness.",
                        "price_low": 60000, "price_high": 180000, "period": "month",
                    },
                    {
                        "id": "ru_metro_digital",
                        "name": "Moscow Metro Digital Screen",
                        "tag": "Digital · Transit",
                        "desc": "Reaches 7 million daily metro riders — one of the highest-traffic transit networks in the world.",
                        "price_low": 40000, "price_high": 150000, "period": "month",
                    },
                    {
                        "id": "ru_city_format",
                        "name": "Moscow City Format Panel (1.2×1.8m)",
                        "tag": "Pedestrian · Compact",
                        "desc": "Compact static or dynamic pylons near bus stations and in the historic city centre, offering high-frequency exposure.",
                        "price_low": 25000, "price_high": 90000, "period": "month",
                    },
                    {
                        "id": "ru_bus_shelter",
                        "name": "Moscow Bus Shelter Advertising",
                        "tag": "Street furniture",
                        "desc": "High-frequency street-level exposure along daily commuting routes across the capital.",
                        "price_low": 20000, "price_high": 75000, "period": "month",
                    },
                    {
                        "id": "ru_network_campaign",
                        "name": "Citywide Network Campaign",
                        "tag": "Multi-site · Half-month",
                        "desc": "A bundled network of billboards across multiple Moscow districts for maximum citywide coverage.",
                        "price_low": 300000, "price_high": 1300000, "period": "half-month",
                    },
                ],
            },
        },
    },
    "monaco": {
        "flag": "🇲🇨",
        "name": "Monaco",
        "status": "network",
        "currency": "€",
        "tagline": "Ultra-premium luxury placements — Monte Carlo, Casino Square.",
        "cities": {
            "monte_carlo": {
                "name": "Monte Carlo",
                "spots": [
                    {
                        "id": "mc_casino_square",
                        "name": "Casino Square Triptych Display",
                        "tag": "Ultra-luxury · Iconic",
                        "desc": "Beside the Hôtel de Paris and Monte-Carlo Casino — the single most prestigious OOH address in Europe, reaching ultra-high-net-worth visitors.",
                        "price_low": 15000, "price_high": 60000, "period": "month",
                    },
                    {
                        "id": "mc_hermitage",
                        "name": "Hôtel Hermitage Panoramic Display",
                        "tag": "Ultra-luxury",
                        "desc": "Facing the 5-star Hôtel Hermitage, delivering premium visibility to Monaco's most affluent residents and jet-set visitors.",
                        "price_low": 12000, "price_high": 50000, "period": "month",
                    },
                    {
                        "id": "mc_ostende_totem",
                        "name": "Avenue de Ostende Totem",
                        "tag": "Ultra-luxury · Landmark",
                        "desc": "A 250sqm landmark advertising totem, one of the largest and most visible display formats in the Principality.",
                        "price_low": 18000, "price_high": 65000, "period": "month",
                    },
                    {
                        "id": "mc_grand_prix",
                        "name": "Monaco Grand Prix Circuit Billboard",
                        "tag": "Event-tied · Global broadcast",
                        "desc": "Trackside placement along the legendary F1 circuit, with global broadcast exposure during Grand Prix week.",
                        "price_low": 25000, "price_high": 90000, "period": "event week",
                    },
                    {
                        "id": "mc_yacht_show",
                        "name": "Port Hercules Yacht Show Display",
                        "tag": "Event-tied · Ultra-HNWI",
                        "desc": "Positioned along the harbour during the Monaco Yacht Show, reaching the world's ultra-high-net-worth yacht buyers.",
                        "price_low": 20000, "price_high": 80000, "period": "event week",
                    },
                    {
                        "id": "mc_casino_banner",
                        "name": "Place du Casino Banner Display",
                        "tag": "Ultra-luxury",
                        "desc": "Next to the Hôtel de Paris and Café de Paris, right at the centre of Monaco's most photographed square.",
                        "price_low": 14000, "price_high": 55000, "period": "month",
                    },
                    {
                        "id": "mc_larvotto",
                        "name": "Larvotto Beach Digital Display",
                        "tag": "Lifestyle · Beachfront",
                        "desc": "Monaco's premier beach district, reaching affluent residents and tourists enjoying the Mediterranean coastline.",
                        "price_low": 10000, "price_high": 40000, "period": "month",
                    },
                ],
            },
        },
    },
    "usa": {
        "flag": "🇺🇸",
        "name": "USA",
        "status": "network",
        "currency": "$",
        "tagline": "The world's most-watched billboard market — Times Square, LA, Chicago.",
        "cities": {
            "new_york": {
                "name": "New York City",
                "spots": [
                    {
                        "id": "us_times_square",
                        "name": "Times Square Digital Billboard",
                        "tag": "Iconic · Global stage",
                        "desc": "The most photographed advertising real estate on Earth, offering global media visibility for brands with ambition to match.",
                        "price_low": 20000, "price_high": 50000, "period": "month",
                    },
                    {
                        "id": "us_one_times_square",
                        "name": "One Times Square Flagship Takeover",
                        "tag": "Ultra-premium · Exclusive",
                        "desc": "The single most iconic billboard in the world — full-screen exclusive takeover for brands with global ambition and budget.",
                        "price_low": 50000, "price_high": 250000, "period": "month",
                    },
                    {
                        "id": "us_brooklyn",
                        "name": "Brooklyn Digital Billboard",
                        "tag": "Digital · Commuter",
                        "desc": "A more affordable yet effective NYC option, ideal for targeting commuters and local businesses across the boroughs.",
                        "price_low": 3000, "price_high": 12000, "period": "month",
                    },
                ],
            },
            "los_angeles": {
                "name": "Los Angeles",
                "spots": [
                    {
                        "id": "us_sunset_strip",
                        "name": "Sunset Strip Spectacular",
                        "tag": "Entertainment industry",
                        "desc": "Hollywood's most iconic advertising strip, the address every entertainment brand wants to be seen on.",
                        "price_low": 5000, "price_high": 25000, "period": "month",
                    },
                    {
                        "id": "us_la_downtown",
                        "name": "Downtown LA Billboard",
                        "tag": "Urban commuter",
                        "desc": "High-visibility placement for LA's downtown commuter and business crowd.",
                        "price_low": 2500, "price_high": 15000, "period": "month",
                    },
                    {
                        "id": "us_405_freeway",
                        "name": "405 Freeway Digital Billboard",
                        "tag": "Highway · High traffic",
                        "desc": "One of the busiest freeways in America, delivering daily exposure to thousands of drivers.",
                        "price_low": 3000, "price_high": 18000, "period": "month",
                    },
                    {
                        "id": "us_lax_airport",
                        "name": "LAX Airport Digital Display",
                        "tag": "Digital · Airport",
                        "desc": "Reaches millions of international and domestic travelers passing through one of the world's busiest airports.",
                        "price_low": 4000, "price_high": 20000, "period": "month",
                    },
                ],
            },
            "chicago": {
                "name": "Chicago",
                "spots": [
                    {
                        "id": "us_chicago_loop",
                        "name": "The Loop Digital Billboard",
                        "tag": "Business district",
                        "desc": "Chicago's central business district, reaching a dense daytime population of professionals and shoppers.",
                        "price_low": 3000, "price_high": 15000, "period": "month",
                    },
                ],
            },
        },
    },
}


# ----------------------------------------------------------------------
# IMAGE HELPERS
# ----------------------------------------------------------------------

def image_path(filename: str) -> str:
    return os.path.join(IMAGES_DIR, filename)


def image_exists(filename: str) -> bool:
    path = image_path(filename)
    return os.path.isfile(path) and os.path.getsize(path) > 0


def spot_image_filename(country_key: str, spot_id: str) -> str:
    return f"{country_key}_{spot_id}.jpg"


# ----------------------------------------------------------------------
# CORE HELPER — send a fresh photo+caption+keyboard screen
# (Telegram cannot edit a text message into a photo message cleanly, so
# every screen change sends a brand-new message rather than editing.)
# ----------------------------------------------------------------------

async def send_photo_screen(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    image_filename: str,
    caption: str,
    keyboard: InlineKeyboardMarkup,
):
    chat_id = update.effective_chat.id
    path = image_path(image_filename)

    if image_exists(image_filename):
        with open(path, "rb") as photo_file:
            await context.bot.send_photo(
                chat_id=chat_id,
                photo=InputFile(photo_file, filename=image_filename),
                caption=caption,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard,
            )
    else:
        # Graceful fallback: no crash, no "content not viewable" — just
        # send the text screen if an image hasn't been generated yet.
        await context.bot.send_message(
            chat_id=chat_id,
            text=caption,
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard,
        )


async def answer_callback(update: Update):
    if update.callback_query:
        await update.callback_query.answer()


# ----------------------------------------------------------------------
# SCREENS
# ----------------------------------------------------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await answer_callback(update)
    caption = (
        "🌍 <b>GlobalSpot</b>\n\n"
        "<b>BIG IDEAS. WORLDWIDE IMPACT.</b>\n\n"
        "We broker premium billboard and digital OOH placements across "
        "the UAE and an expanding global network spanning "
        "Germany, France, Norway, Russia, Monaco, and the USA.\n\n"
        "Real vendor-backed pricing. Real locations. One point of contact.\n\n"
        "Tap a country below to explore available spots. 👇"
    )
    keyboard_rows = []
    row = []
    for key, country in COUNTRIES.items():
        row.append(InlineKeyboardButton(f"{country['flag']} {country['name']}", callback_data=f"country:{key}"))
        if len(row) == 2:
            keyboard_rows.append(row)
            row = []
    if row:
        keyboard_rows.append(row)
    keyboard_rows.append([InlineKeyboardButton("ℹ️ About GlobalSpot", callback_data="about")])
    keyboard_rows.append([InlineKeyboardButton("📞 Talk to a Human", callback_data="contact")])

    keyboard = InlineKeyboardMarkup(keyboard_rows)
    await send_photo_screen(update, context, WELCOME_IMAGE, caption, keyboard)


async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await answer_callback(update)
    caption = (
        "ℹ️ <b>About GlobalSpot</b>\n\n"
        "GlobalSpot is an international billboard brokerage desk.\n\n"
        "🇦🇪 <b>UAE</b> — active brokerage. We connect you "
        "directly with vendor partners and manage your booking end to end.\n\n"
        "🌍 <b>Germany, France, Norway, Russia, Monaco, USA</b> — our growing "
        "global network. Pricing shown reflects real current market rates "
        "from local OOH operators. Reach out and we'll personally introduce "
        "you to a vetted partner in that market.\n\n"
        "All prices include our brokerage service — no hidden fees, "
        "no surprises. What you see is what you'll be quoted, subject to "
        "final vendor confirmation on exact dates and availability."
    )
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("⬅️ Back to Countries", callback_data="home")],
        [InlineKeyboardButton("📞 Talk to a Human", callback_data="contact")],
    ])
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=caption,
        parse_mode=ParseMode.HTML,
        reply_markup=keyboard,
    )


async def contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await answer_callback(update)
    caption = (
        "📞 <b>Talk to a Human</b>\n\n"
        f"WhatsApp / Telegram: {ADMIN_CONTACT_USERNAME}\n"
        f"Phone: {ADMIN_CONTACT_PHONE}\n\n"
        "Or tap <b>Request a Quote</b> on any spot and we'll message you "
        "directly with next steps."
    )
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("⬅️ Back to Countries", callback_data="home")],
    ])
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=caption,
        parse_mode=ParseMode.HTML,
        reply_markup=keyboard,
    )


async def show_country(update: Update, context: ContextTypes.DEFAULT_TYPE, country_key: str):
    await answer_callback(update)
    country = COUNTRIES[country_key]
    status_line = (
        "✅ <b>Active brokerage market</b> — book with confidence."
        if country["status"] == "brokerage"
        else "🌐 <b>Global network market</b> — request an introduction to our local partner."
    )
    caption = (
        f"{country['flag']} <b>{country['name']}</b>\n"
        f"<i>{country['tagline']}</i>\n\n"
        f"{status_line}\n\n"
        "Choose a city to view available spots:"
    )
    keyboard_rows = []
    for city_key, city in country["cities"].items():
        keyboard_rows.append([
            InlineKeyboardButton(f"📍 {city['name']} ({len(city['spots'])} spots)",
                                  callback_data=f"city:{country_key}:{city_key}")
        ])
    keyboard_rows.append([InlineKeyboardButton("⬅️ Back to Countries", callback_data="home")])
    keyboard = InlineKeyboardMarkup(keyboard_rows)

    country_image = f"{country_key}_cover.jpg"
    await send_photo_screen(update, context, country_image, caption, keyboard)


async def show_city(update: Update, context: ContextTypes.DEFAULT_TYPE, country_key: str, city_key: str):
    await answer_callback(update)
    country = COUNTRIES[country_key]
    city = country["cities"][city_key]

    caption = (
        f"{country['flag']} <b>{city['name']}, {country['name']}</b>\n\n"
        f"{len(city['spots'])} premium spots available. Tap any spot for full details, "
        "pricing, and a photo of the location.\n"
    )
    keyboard_rows = []
    for spot in city["spots"]:
        keyboard_rows.append([
            InlineKeyboardButton(f"📌 {spot['name']}", callback_data=f"spot:{country_key}:{city_key}:{spot['id']}")
        ])
    keyboard_rows.append([InlineKeyboardButton(f"⬅️ Back to {country['name']}", callback_data=f"country:{country_key}")])
    keyboard_rows.append([InlineKeyboardButton("🏠 Home", callback_data="home")])
    keyboard = InlineKeyboardMarkup(keyboard_rows)

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=caption,
        parse_mode=ParseMode.HTML,
        reply_markup=keyboard,
    )


async def show_spot(update: Update, context: ContextTypes.DEFAULT_TYPE, country_key: str, city_key: str, spot_id: str):
    await answer_callback(update)
    country = COUNTRIES[country_key]
    city = country["cities"][city_key]
    spot = next(s for s in city["spots"] if s["id"] == spot_id)

    price_line = price_range_line(spot["price_low"], spot["price_high"], country["currency"], spot.get("period", "month"))

    cta_label = "✅ Request to Book" if country["status"] == "brokerage" else "🤝 Request Introduction"
    cta_data = f"lead:{country_key}:{city_key}:{spot_id}"

    caption = (
        f"📌 <b>{spot['name']}</b>\n"
        f"{country['flag']} {city['name']}, {country['name']}\n"
        f"<i>{spot['tag']}</i>\n\n"
        f"{spot['desc']}\n\n"
        f"💰 <b>{price_line}</b>\n"
        f"<i>(incl. brokerage service — final quote confirmed with vendor)</i>\n\n"
        "Ready to move on this spot?"
    )
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(cta_label, callback_data=cta_data)],
        [InlineKeyboardButton(f"⬅️ Back to {city['name']}", callback_data=f"city:{country_key}:{city_key}")],
        [InlineKeyboardButton("🏠 Home", callback_data="home")],
    ])

    spot_image = spot_image_filename(country_key, spot_id)
    await send_photo_screen(update, context, spot_image, caption, keyboard)


# ----------------------------------------------------------------------
# LEAD CAPTURE CONVERSATION
# ----------------------------------------------------------------------

async def start_lead(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await answer_callback(update)
    query = update.callback_query
    _, country_key, city_key, spot_id = query.data.split(":")
    context.user_data["lead"] = {
        "country_key": country_key,
        "city_key": city_key,
        "spot_id": spot_id,
    }
    country = COUNTRIES[country_key]
    city = country["cities"][city_key]
    spot = next(s for s in city["spots"] if s["id"] == spot_id)
    context.user_data["lead"]["spot_name"] = spot["name"]
    context.user_data["lead"]["country_name"] = country["name"]
    context.user_data["lead"]["city_name"] = city["name"]

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=(
            f"Great choice — <b>{spot['name']}</b>, {city['name']}.\n\n"
            "What's your name or company name?"
        ),
        parse_mode=ParseMode.HTML,
    )
    return ASK_NAME


async def lead_ask_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["lead"]["name"] = update.message.text
    await update.message.reply_text(
        "Thanks! Best WhatsApp number or email to reach you on?"
    )
    return ASK_CONTACT


async def lead_ask_dates(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["lead"]["contact"] = update.message.text
    await update.message.reply_text(
        "When would you like the campaign to run? (e.g. 'August 2026, 1 month')"
    )
    return ASK_DATES


async def lead_ask_notes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["lead"]["dates"] = update.message.text
    await update.message.reply_text(
        "Anything else we should know? (budget, creative ready, brand name — or just type 'none')"
    )
    return ASK_NOTES


async def lead_finish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["lead"]["notes"] = update.message.text
    lead = context.user_data["lead"]

    summary = (
        "🎯 <b>New GlobalSpot Lead</b>\n\n"
        f"Spot: {lead['spot_name']}\n"
        f"Location: {lead['city_name']}, {lead['country_name']}\n"
        f"Name: {lead['name']}\n"
        f"Contact: {lead['contact']}\n"
        f"Dates: {lead['dates']}\n"
        f"Notes: {lead['notes']}\n"
        f"Timestamp: {datetime.utcnow().isoformat()} UTC\n"
        f"Telegram user: @{update.effective_user.username or update.effective_user.id}"
    )

    logger.info("NEW LEAD: %s", summary.replace("\n", " | "))

    if ADMIN_CHAT_ID:
        try:
            await context.bot.send_message(
                chat_id=ADMIN_CHAT_ID,
                text=summary,
                parse_mode=ParseMode.HTML,
            )
        except Exception as e:
            logger.warning("Could not forward lead to admin chat: %s", e)

    await update.message.reply_text(
        "🙌 Got it! Your request has been sent to the GlobalSpot team.\n\n"
        f"We'll reach out on {lead['contact']} within 24 hours with a confirmed "
        "quote and next steps.\n\n"
        f"In the meantime, you can reach us directly: {ADMIN_CONTACT_USERNAME}",
    )

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Want to explore more spots?",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🏠 Back to Home", callback_data="home")]
        ]),
    )
    context.user_data.pop("lead", None)
    return ConversationHandler.END


async def lead_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.pop("lead", None)
    await update.message.reply_text("No problem — request cancelled. Type /start to browse again.")
    return ConversationHandler.END


# ----------------------------------------------------------------------
# CALLBACK ROUTER
# ----------------------------------------------------------------------

async def button_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data

    if data == "home":
        await start(update, context)
    elif data == "about":
        await about(update, context)
    elif data == "contact":
        await contact(update, context)
    elif data.startswith("country:"):
        _, country_key = data.split(":")
        await show_country(update, context, country_key)
    elif data.startswith("city:"):
        _, country_key, city_key = data.split(":")
        await show_city(update, context, country_key, city_key)
    elif data.startswith("spot:"):
        _, country_key, city_key, spot_id = data.split(":")
        await show_spot(update, context, country_key, city_key, spot_id)
    else:
        await answer_callback(update)


# ----------------------------------------------------------------------
# MAIN
# ----------------------------------------------------------------------

def main():
    os.makedirs(IMAGES_DIR, exist_ok=True)

    if BOT_TOKEN == "PUT_YOUR_NEW_REVOKED_TOKEN_HERE":
        logger.warning(
            "No bot token set! Export GLOBALSPOT_BOT_TOKEN or edit BOT_TOKEN in this file."
        )

    if not image_exists(WELCOME_IMAGE):
        logger.warning(
            "%s not found in %s — welcome screen will fall back to text-only "
            "until you add real images. Run generate_images.py to create "
            "placeholder graphics for every spot.",
            WELCOME_IMAGE,
            IMAGES_DIR,
        )

    app = Application.builder().token(BOT_TOKEN).build()

    lead_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_lead, pattern=r"^lead:")],
        states={
            ASK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, lead_ask_contact)],
            ASK_CONTACT: [MessageHandler(filters.TEXT & ~filters.COMMAND, lead_ask_dates)],
            ASK_DATES: [MessageHandler(filters.TEXT & ~filters.COMMAND, lead_ask_notes)],
            ASK_NOTES: [MessageHandler(filters.TEXT & ~filters.COMMAND, lead_finish)],
        },
        fallbacks=[CommandHandler("cancel", lead_cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(lead_conv)
    app.add_handler(CallbackQueryHandler(button_router))

    logger.info("GlobalSpot bot starting...")
    app.run_polling()


if __name__ == "__main__":
    main()
