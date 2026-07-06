"""Generates a clean, professional branded welcome banner for Nescosign."""

from PIL import Image, ImageDraw, ImageFilter
import math

W, H = 1280, 720

# --- Background gradient (deep navy -> electric purple, diagonal) ---
img = Image.new("RGB", (W, H), "#0B0F2C")
draw = ImageDraw.Draw(img)

top_color = (10, 14, 40)      # deep navy
bottom_color = (76, 29, 149)  # rich purple
accent_color = (236, 72, 153) # magenta accent
gold_color = (250, 204, 21)   # gold accent

for y in range(H):
    t = y / H
    r = int(top_color[0] + (bottom_color[0] - top_color[0]) * t)
    g = int(top_color[1] + (bottom_color[1] - top_color[1]) * t)
    b = int(top_color[2] + (bottom_color[2] - top_color[2]) * t)
    draw.line([(0, y), (W, y)], fill=(r, g, b))

# --- Diagonal light beams for a "spotlight/billboard" feel ---
beam_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
beam_draw = ImageDraw.Draw(beam_layer)
for i, x_off in enumerate([-100, 250, 650, 1000]):
    alpha = 26 if i % 2 == 0 else 18
    beam_draw.polygon(
        [(x_off, 0), (x_off + 180, 0), (x_off - 300, H), (x_off - 480, H)],
        fill=(255, 255, 255, alpha),
    )
beam_layer = beam_layer.filter(ImageFilter.GaussianBlur(20))
img = Image.alpha_composite(img.convert("RGBA"), beam_layer).convert("RGB")
draw = ImageDraw.Draw(img)

# --- Simple city skyline silhouette along the bottom ---
skyline = Image.new("RGBA", (W, H), (0, 0, 0, 0))
sk_draw = ImageDraw.Draw(skyline)
import random
random.seed(7)
x = 0
base_y = H - 40
building_color = (5, 8, 25, 235)
while x < W:
    bw = random.randint(50, 110)
    bh = random.randint(90, 260)
    sk_draw.rectangle([x, base_y - bh, x + bw, base_y], fill=building_color)
    # windows
    for wy in range(base_y - bh + 12, base_y - 10, 18):
        for wx in range(x + 8, x + bw - 8, 14):
            if random.random() > 0.35:
                glow = random.choice([gold_color, (255, 255, 255)])
                sk_draw.rectangle([wx, wy, wx + 6, wy + 8], fill=(*glow, 200))
    x += bw + random.randint(4, 14)
img.paste(skyline, (0, 0), skyline)
draw = ImageDraw.Draw(img)

# --- A glowing "billboard" rectangle to the right, echoing the product ---
board_x, board_y, board_w, board_h = 860, 200, 340, 210
draw.rectangle(
    [board_x - 10, board_y - 10, board_x + board_w + 10, board_y + board_h + 10],
    fill=(255, 255, 255, 255),
    outline=None,
)
draw.rectangle(
    [board_x, board_y, board_x + board_w, board_y + board_h],
    fill=(15, 20, 50),
)
draw.rectangle(
    [board_x, board_y, board_x + board_w, board_y + board_h],
    outline=gold_color,
    width=3,
)
# little "play" / ad glyph on the mini billboard
cx, cy = board_x + board_w // 2, board_y + board_h // 2 - 10
draw.polygon(
    [(cx - 30, cy - 40), (cx - 30, cy + 40), (cx + 45, cy)],
    fill=accent_color,
)
draw.text(
    (board_x + 20, board_y + board_h - 40),
    "YOUR BRAND HERE",
    fill=(255, 255, 255),
)
# stand for the mini billboard
draw.rectangle(
    [board_x + board_w // 2 - 12, board_y + board_h + 10, board_x + board_w // 2 + 12, board_y + board_h + 90],
    fill=(30, 35, 65),
)

# --- Fonts ---
from PIL import ImageFont
try:
    font_logo = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 92)
    font_tag = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 34)
    font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 22)
    font_board = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
except Exception:
    font_logo = ImageFont.load_default()
    font_tag = ImageFont.load_default()
    font_small = ImageFont.load_default()
    font_board = ImageFont.load_default()

# redraw the "YOUR BRAND HERE" text with correct font now that it's loaded
draw.rectangle([board_x + 15, board_y + board_h - 45, board_x + board_w - 15, board_y + board_h - 15], fill=(15, 20, 50))
draw.text((board_x + 20, board_y + board_h - 42), "YOUR BRAND HERE", fill=(255, 255, 255), font=font_board)

# --- Logo text ---
logo_x, logo_y = 70, 90
draw.text((logo_x, logo_y), "NESCO", fill=(255, 255, 255), font=font_logo)
# measure width of "NESCO" to place "SIGN" right after in accent color
bbox = draw.textbbox((logo_x, logo_y), "NESCO", font=font_logo)
nesco_w = bbox[2] - bbox[0]
draw.text((logo_x + nesco_w, logo_y), "SIGN", fill=accent_color, font=font_logo)

# underline accent
draw.rectangle([logo_x, logo_y + 115, logo_x + 430, logo_y + 122], fill=gold_color)

# --- Tagline ---
draw.text(
    (logo_x, logo_y + 150),
    "Put Your Brand Where The World Is Looking",
    fill=(230, 230, 245),
    font=font_tag,
)
draw.text(
    (logo_x, logo_y + 200),
    "Premium Digital Billboards  \u2022  Global Cities  \u2022  Real Results",
    fill=(180, 180, 210),
    font=font_small,
)

img.save("/home/claude/nescosign_bot/images/welcome_banner.png", quality=95)
print("Banner saved.")
