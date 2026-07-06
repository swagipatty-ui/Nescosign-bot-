# -*- coding: utf-8 -*-
"""
Nescosign data: categories, spots, pricing.
Format/pricing tiers modeled on industry-standard billboard formats
(Bulletin, Poster, Junior Poster, Digital variants, Wallscape).
Replace photo_url and details with your own real inventory whenever you're ready.
"""

BRAND_NAME = "Nescosign"

BANNER_IMAGE_URL = "https://i.imgur.com/8vHNQ0J.png"  # placeholder - replace with your real banner file_id or URL

# ---------------------------------------------------------------------------
# CATEGORIES
# Each category = a billboard format, matching standard industry classes.
# ---------------------------------------------------------------------------
CATEGORIES = {
    "bulletin": {
        "label": "🪧 Bulletin (Large)",
        "short": "Large static billboard — maximum roadside impact.",
    },
    "poster": {
        "label": "📋 Poster (Medium)",
        "short": "Medium static billboard — strong city visibility.",
    },
    "jr_poster": {
        "label": "📄 Jr Poster (Small)",
        "short": "Small static billboard — dense urban/local coverage.",
    },
    "bulletin_digi": {
        "label": "💡 Bulletin, Digital (Large)",
        "short": "Large digital/LED billboard — rotating full-color ads.",
    },
    "poster_digi": {
        "label": "📺 Poster, Digital (Medium)",
        "short": "Medium digital/LED billboard — flexible, fast-changing creative.",
    },
    "wallscape": {
        "label": "🏙️ Wallscape",
        "short": "Building-sized mural advertising — impossible to miss.",
    },
}

# ---------------------------------------------------------------------------
# SPOTS
# Keyed by category -> list of spot dicts.
# Each spot: id, name, location, photo_url, description, views, impressions, price
# ---------------------------------------------------------------------------
SPOTS = {
    "bulletin": [
        {
            "id": "bul_times_square",
            "name": "Times Square LED Spectacular",
            "location": "📍 New York City, USA",
            "photo_url": "https://images.unsplash.com/photo-1560807707-8cc77767d783?w=1200",
            "description": (
                "Picture your brand towering over the most photographed intersection on Earth. "
                "Over 360,000 pairs of eyes pass through Times Square every single day — tourists, "
                "executives, dreamers, all looking up. This is where global icons launch, and it "
                "could be where your business becomes one."
            ),
            "daily_views": "180,000+",
            "monthly_impressions": "5.4M+",
            "size": "48' W x 14' H",
            "price": 28000,
            "period": "4-week flight (shared rotation)",
        },
        {
            "id": "bul_sunset_strip",
            "name": "Sunset Strip Icon Board",
            "location": "📍 Los Angeles, USA",
            "photo_url": "https://images.unsplash.com/photo-1515896769750-31548aa180ed?w=1200",
            "description": (
                "The Strip has launched more brands than any stretch of road in America. Every "
                "day, industry execs, tourists and tastemakers drive this legendary corridor. "
                "Put your name where Hollywood already looks."
            ),
            "daily_views": "95,000+",
            "monthly_impressions": "2.8M+",
            "size": "48' W x 14' H",
            "price": 22000,
            "period": "4-week flight",
        },
    ],
    "poster": [
        {
            "id": "pos_downtown_chicago",
            "name": "Downtown Chicago Poster",
            "location": "📍 Chicago, USA",
            "photo_url": "https://images.unsplash.com/photo-1494522358652-f30e61a60313?w=1200",
            "description": (
                "Positioned along one of Chicago's busiest commuter corridors, this poster puts "
                "your business in front of daily foot and vehicle traffic — the kind of steady, "
                "local repetition that builds real brand memory."
            ),
            "daily_views": "14,000+",
            "monthly_impressions": "420,000+",
            "size": "22.75\" W x 10.5\" H",
            "price": 1400,
            "period": "4-week flight",
        },
    ],
    "jr_poster": [
        {
            "id": "jr_neighborhood_miami",
            "name": "Neighborhood Corner Board",
            "location": "📍 Miami, USA",
            "photo_url": "https://images.unsplash.com/photo-1506966953602-c20cc11f75e3?w=1200",
            "description": (
                "Small format, big local presence. Perfect for businesses that live and die by "
                "their neighborhood — restaurants, gyms, clinics, local services. Get seen by the "
                "same commuters, day after day, until your name sticks."
            ),
            "daily_views": "9,500+",
            "monthly_impressions": "285,000+",
            "size": "11' W x 5' H",
            "price": 550,
            "period": "4-week flight",
        },
    ],
    "bulletin_digi": [
        {
            "id": "digi_vegas_strip",
            "name": "Las Vegas Strip Digital Bulletin",
            "location": "📍 Las Vegas, USA",
            "photo_url": "https://images.unsplash.com/photo-1605833556294-ea5c7a74f57d?w=1200",
            "description": (
                "Full color, full motion-ready static creative, rotating in front of the Strip's "
                "nonstop crowd — 24 hours a day. Swap your message anytime, target events, and "
                "stay current without ever reprinting a thing."
            ),
            "daily_views": "48,000+",
            "monthly_impressions": "1.4M+",
            "size": "48' W x 14' H (1400x400px)",
            "price": 18000,
            "period": "4-week flight, ~8 sec spot / 64 sec loop",
        },
    ],
    "poster_digi": [
        {
            "id": "digi_atl_midtown",
            "name": "Midtown Atlanta Digital Poster",
            "location": "📍 Atlanta, USA",
            "photo_url": "https://images.unsplash.com/photo-1477959858617-67f85cf4f1df?w=1200",
            "description": (
                "Change your creative as often as your business needs — new promo this week, "
                "new offer next week, zero reprint cost. Midtown's dense office and residential "
                "traffic sees your brand fresh, every single day."
            ),
            "daily_views": "24,000+",
            "monthly_impressions": "720,000+",
            "size": "22.75\" W x 10.5\" H (840x400px)",
            "price": 3200,
            "period": "4-week flight, ~8 sec spot / 64 sec loop",
        },
    ],
    "wallscape": [
        {
            "id": "wall_soho_nyc",
            "name": "SoHo Building Wallscape",
            "location": "📍 New York City, USA",
            "photo_url": "https://images.unsplash.com/photo-1517502884422-41eaead166d4?w=1200",
            "description": (
                "This is the format that stops a city in its tracks. A full building face, "
                "impossible to scroll past, impossible to ignore. When brands want to make a "
                "cultural statement — not just an ad — this is where they go."
            ),
            "daily_views": "70,000+",
            "monthly_impressions": "2.1M+",
            "size": "Custom (building-scale)",
            "price": 35000,
            "period": "4-week flight",
        },
    ],
}


def get_spot(spot_id: str):
    """Find a spot dict by its id across all categories."""
    for cat_spots in SPOTS.values():
        for spot in cat_spots:
            if spot["id"] == spot_id:
                return spot
    return None


def get_category_spots(category_id: str):
    return SPOTS.get(category_id, [])
