"""
S04-T09: Generate AdAssistant internal test brand icon.
Produces icon.png (128x128) and icon.ico (multi-size).
Uses only stdlib + Pillow — no new dependencies.
"""
from PIL import Image, ImageDraw, ImageFont
import math
import os

OUT_DIR = os.path.dirname(os.path.abspath(__file__))

# ── Design constants ──────────────────────────────────────────────
SIZES_PNG = [128]          # primary PNG
SIZES_ICO = [16, 24, 32, 48, 64, 128, 256]

# App dark background
BG_COLOR = (7, 17, 31)           # #07111f
# AI accent gradient (cyan-blue)
ACCENT_START = (0, 180, 216)     # #00b4d8
ACCENT_END = (72, 149, 239)      # #4895ef
# Subtle ring
RING_COLOR = (30, 60, 100)       # semi-transparent feel border

# ── Helpers ───────────────────────────────────────────────────────

def blend(c1, c2, t):
    """Linear blend between two RGB tuples."""
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))


def draw_stylized_A(draw, size, offset=(0, 0)):
    """
    Draw a geometric stylized "A" that reads as a modern tech/ai mark.
    The A is drawn as an outlined triangle-like shape with a horizontal
    crossbar, created from polygons.
    """
    w, h = size, size
    ox, oy = offset
    margin = w * 0.15
    stroke = max(2, int(w * 0.10))  # line thickness

    # Outer A shape
    left_x = ox + margin
    right_x = ox + w - margin
    top_y = oy + margin * 1.2
    bottom_y = oy + h - margin * 1.1
    crossbar_y = top_y + (bottom_y - top_y) * 0.60

    # The A is formed from three filled polygons:
    # left leg, right leg, and the hollow interior

    # Left leg (thick angled bar)
    left_outer = [
        (left_x, bottom_y),
        (left_x + stroke, bottom_y),
        (ox + w * 0.44, top_y + stroke * 0.7),
        (ox + w * 0.35, top_y),
    ]
    # Right leg (thick angled bar)
    right_outer = [
        (right_x, bottom_y),
        (right_x - stroke, bottom_y),
        (ox + w * 0.56, top_y + stroke * 0.7),
        (ox + w * 0.65, top_y),
    ]
    # Crossbar
    crossbar = [
        (ox + w * 0.38, crossbar_y),
        (ox + w * 0.62, crossbar_y),
        (ox + w * 0.62, crossbar_y + stroke),
        (ox + w * 0.38, crossbar_y + stroke),
    ]

    # Draw legs
    draw.polygon(left_outer, fill=ACCENT_START)
    draw.polygon(right_outer, fill=ACCENT_END)
    draw.polygon(crossbar, fill=blend(ACCENT_START, ACCENT_END, 0.5))

    # Inner cutout for A (the triangular hole)
    inner_left_x = left_x + stroke * 1.8
    inner_right_x = right_x - stroke * 1.8
    inner_top_y = top_y + stroke * 1.8
    inner_bottom_y = bottom_y - stroke * 0.3

    cutout = [
        (inner_left_x, inner_bottom_y),
        (ox + w * 0.44, inner_top_y + stroke * 1.2),
        (ox + w * 0.50, inner_top_y),
        (ox + w * 0.56, inner_top_y + stroke * 1.2),
        (inner_right_x, inner_bottom_y),
        (inner_right_x - stroke, inner_bottom_y),
        (ox + w * 0.53, inner_top_y + stroke * 1.8),
        (ox + w * 0.50, inner_top_y + stroke * 1.9),
        (ox + w * 0.47, inner_top_y + stroke * 1.8),
        (inner_left_x + stroke, inner_bottom_y),
    ]
    draw.polygon(cutout, fill=BG_COLOR)


def draw_icon(size):
    """Draw a single icon frame at the given size."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))

    # Rounded rect background using a mask
    mask = Image.new("L", (size, size), 0)
    mask_draw = ImageDraw.Draw(mask)
    radius = int(size * 0.18)
    mask_draw.rounded_rectangle(
        [(0, 0), (size - 1, size - 1)],
        radius=radius,
        fill=255,
    )

    bg = Image.new("RGBA", (size, size), BG_COLOR + (255,))
    img = Image.composite(bg, img, mask)

    draw = ImageDraw.Draw(img)

    # Subtle outer ring
    ring_r = int(size * 0.40)
    center = size // 2
    # Draw a subtle circular accent ring behind the A
    ring_inner = int(ring_r * 0.82)
    for y in range(size):
        for x in range(size):
            dx = x - center
            dy = y - center
            dist = math.sqrt(dx * dx + dy * dy)
            if ring_inner <= dist <= ring_r:
                # Gradient ring: top cyan, bottom blue
                angle = (math.atan2(dy, dx) + math.pi) / (2 * math.pi)
                color = blend(ACCENT_START, ACCENT_END, angle)
                alpha = int(40 + 20 * (1 - abs(dist - (ring_r + ring_inner) / 2) / ((ring_r - ring_inner) / 2)))
                alpha = max(10, min(60, alpha))
                r, g, b = color
                existing = img.getpixel((x, y))
                # blend
                new_r = int(existing[0] * (1 - alpha / 255) + r * (alpha / 255))
                new_g = int(existing[1] * (1 - alpha / 255) + g * (alpha / 255))
                new_b = int(existing[2] * (1 - alpha / 255) + b * (alpha / 255))
                img.putpixel((x, y), (new_r, new_g, new_b, 255))

    draw = ImageDraw.Draw(img)

    # Draw the stylized A, scaled to fit
    a_size = int(size * 0.55)
    a_offset_x = (size - a_size) // 2
    a_offset_y = int(size * 0.22)
    draw_stylized_A(draw, a_size, (a_offset_x, a_offset_y))

    # Small dot accent (AI hint) — a small triangle/dot near the apex
    dot_x = size // 2
    dot_y = int(size * 0.20)
    dot_r = max(1.5, size * 0.025)
    draw.ellipse(
        [(dot_x - dot_r, dot_y - dot_r), (dot_x + dot_r, dot_y + dot_r)],
        fill=ACCENT_START,
    )

    return img


# ── Generate ──────────────────────────────────────────────────────

def main():
    # PNG
    png_path = os.path.join(OUT_DIR, "icon.png")
    png_img = draw_icon(128)
    png_img.save(png_path, "PNG")
    print(f"[OK] {png_path} ({png_img.size[0]}x{png_img.size[1]} PNG)")

    # ICO (multi-size)
    # Generate highest-res frame, let Pillow resize down via `sizes`
    ico_path = os.path.join(OUT_DIR, "icon.ico")
    largest = draw_icon(256)
    largest.save(
        ico_path,
        format="ICO",
        sizes=[(s, s) for s in SIZES_ICO],
    )
    print(f"[OK] {ico_path} (ICO with sizes: {SIZES_ICO})")

    # Verify
    print(f"\nAll done. Icon files ready for packaging.")


if __name__ == "__main__":
    main()
