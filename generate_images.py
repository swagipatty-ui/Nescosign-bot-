"""
Generates clean, original placeholder billboard-mockup graphics for every
spot in bot.py. These are drawn from scratch with Pillow (gradients, text,
simple shapes) — NOT photos, NOT stock imagery, NOT anyone else's IP.

Why placeholders instead of real photos:
  Real billboard photos (e.g. stock photography of Piccadilly Lights,
  Sheikh Zayed Road, Times Square) are copyrighted. Using them in a live
  customer-facing bot is a real legal risk. These generated graphics give
  every spot and every country a clean, branded visual so the bot never
  breaks or shows Telegram's "content not viewable" error, while you
  swap in real photos later (your own site visits, vendor-supplied
  images, or licensed stock you've actually paid for).

Run this once (or whenever COUNTRIES changes) to (re)populate images/.
"""

import os
import hashlib
from PIL import Image, ImageDraw, ImageFont

from bot import COUNTRIES, WELCOME_IMAGE, IMAGES_DIR, spot_image_filename

W, H = 1024, 683  # 3:2 ish, good for Telegram photo previews

# A distinct gradient palette per country so the bot "feels" international
COUNTRY_PALETTES = {
    "nigeria": [(9, 82, 51), (0, 122, 61)],       # green
    "uae": [(15, 23, 65), (198, 156, 74)],         # navy -> gold
    "germany": [(20, 20, 20), (205, 30, 40)],      # black -> red
    "france": [(18, 43, 97), (200, 30, 60)],       # blue -> red
    "norway": [(10, 40, 70), (160, 200, 220)],     # deep blue -> ice
    "russia": [(30, 20, 60), (180, 30, 40)],       # purple -> red
    "monaco": [(120, 20, 30), (200, 170, 90)],     # burgundy -> gold
    "usa": [(15, 30, 70), (190, 20, 40)],          # blue -> red
}


def try_font(size, bold=False):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold else
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ]
    for path in candidates:
        if os.path.isfile(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def vertical_gradient(size, top_color, bottom_color):
    w, h = size
    base = Image.new("RGB", size, top_color)
    top_r, top_g, top_b = top_color
    bot_r, bot_g, bot_b = bottom_color
    for y in range(h):
        t = y / max(h - 1, 1)
        r = int(top_r + (bot_r - top_r) * t)
        g = int(top_g + (bot_g - top_g) * t)
        b = int(top_b + (bot_b - top_b) * t)
        ImageDraw.Draw(base).line([(0, y), (w, y)], fill=(r, g, b))
    return base


def draw_billboard_frame(draw, w, h):
    """Draws a simple stylised billboard/signpost silhouette at the
    bottom of the frame so every image reads as 'OOH advertising'
    regardless of city."""
    pole_w = int(w * 0.03)
    pole_x = w // 2 - pole_w // 2
    pole_top = int(h * 0.72)
    draw.rectangle([pole_x, pole_top, pole_x + pole_w, h], fill=(25, 25, 25))

    board_margin = int(w * 0.12)
    board_top = int(h * 0.40)
    board_bottom = int(h * 0.72)
    draw.rectangle(
        [board_margin, board_top, w - board_margin, board_bottom],
        outline=(255, 255, 255),
        width=6,
    )


def make_cover_image(path, country_name, flag, palette, subtitle):
    img = vertical_gradient((W, H), palette[0], palette[1])
    draw = ImageDraw.Draw(img)
    draw_billboard_frame(draw, W, H)

    title_font = try_font(58, bold=True)
    sub_font = try_font(30)
    brand_font = try_font(26, bold=True)

    title = f"{flag}  {country_name}"
    draw.text((W // 2, int(H * 0.20)), title, font=title_font, fill=(255, 255, 255), anchor="mm")
    draw.text((W // 2, int(H * 0.30)), subtitle, font=sub_font, fill=(230, 230, 230), anchor="mm")
    draw.text((W // 2, int(H * 0.56)), "YOUR AD HERE", font=title_font, fill=(255, 255, 255), anchor="mm")
    draw.text((W // 2, int(H * 0.92)), "GlobalSpot · by Affirmative Group", font=brand_font, fill=(255, 255, 255), anchor="mm")

    img.save(path, "JPEG", quality=90)


def make_spot_image(path, spot_name, city_name, country_name, tag, palette):
    img = vertical_gradient((W, H), palette[0], palette[1])
    draw = ImageDraw.Draw(img)
    draw_billboard_frame(draw, W, H)

    name_font = try_font(44, bold=True)
    loc_font = try_font(28)
    tag_font = try_font(24)
    brand_font = try_font(22, bold=True)

    # Wrap spot name if long
    words = spot_name.split()
    lines, current = [], ""
    for word in words:
        trial = (current + " " + word).strip()
        if len(trial) > 22:
            lines.append(current)
            current = word
        else:
            current = trial
    if current:
        lines.append(current)

    start_y = int(H * 0.50)
    for i, line in enumerate(lines):
        draw.text((W // 2, start_y + i * 50), line, font=name_font, fill=(255, 255, 255), anchor="mm")

    draw.text((W // 2, int(H * 0.20)), f"{city_name}, {country_name}", font=loc_font, fill=(235, 235, 235), anchor="mm")
    draw.text((W // 2, int(H * 0.28)), tag.upper(), font=tag_font, fill=(255, 215, 130), anchor="mm")
    draw.text((W // 2, int(H * 0.92)), "GlobalSpot · by Affirmative Group", font=brand_font, fill=(255, 255, 255), anchor="mm")

    img.save(path, "JPEG", quality=90)


def make_welcome_image(path):
    img = vertical_gradient((W, H), (10, 10, 20), (25, 25, 45))
    draw = ImageDraw.Draw(img)
    draw_billboard_frame(draw, W, H)

    title_font = try_font(60, bold=True)
    sub_font = try_font(28)

    draw.text((W // 2, int(H * 0.18)), "🌍 GlobalSpot", font=title_font, fill=(255, 255, 255), anchor="mm")
    draw.text((W // 2, int(H * 0.28)), "Big Ideas. Worldwide Impact.", font=sub_font, fill=(230, 230, 230), anchor="mm")
    draw.text((W // 2, int(H * 0.56)), "YOUR AD HERE", font=title_font, fill=(255, 255, 255), anchor="mm")
    draw.text((W // 2, int(H * 0.92)), "by Affirmative Group · YUYU Ads", font=sub_font, fill=(200, 200, 200), anchor="mm")

    img.save(path, "JPEG", quality=90)


def main():
    os.makedirs(IMAGES_DIR, exist_ok=True)

    welcome_path = os.path.join(IMAGES_DIR, WELCOME_IMAGE)
    make_welcome_image(welcome_path)
    print(f"Created {welcome_path}")

    for country_key, country in COUNTRIES.items():
        palette = COUNTRY_PALETTES.get(country_key, [(40, 40, 40), (90, 90, 90)])

        cover_path = os.path.join(IMAGES_DIR, f"{country_key}_cover.jpg")
        make_cover_image(cover_path, country["name"], country["flag"], palette, country["tagline"])
        print(f"Created {cover_path}")

        for city_key, city in country["cities"].items():
            for spot in city["spots"]:
                filename = spot_image_filename(country_key, spot["id"])
                spot_path = os.path.join(IMAGES_DIR, filename)
                make_spot_image(
                    spot_path,
                    spot["name"],
                    city["name"],
                    country["name"],
                    spot["tag"],
                    palette,
                )
                print(f"Created {spot_path}")

    print("\nDone. All placeholder images generated in images/.")
    print("Swap any file in images/ with a real photo (same filename) any time.")


if __name__ == "__main__":
    main()
