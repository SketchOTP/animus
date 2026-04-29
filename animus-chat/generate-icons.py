#!/usr/bin/env python3
"""Generate PNG icons for Android PWA install. Run once."""
from pathlib import Path

try:
    from PIL import Image, ImageDraw
except ImportError:
    raise SystemExit("Run: pip install pillow (inside your venv)")

OUT = Path(__file__).parent / "app"

def draw_ghost(draw, size):
    x0 = int(size * 0.23)
    x1 = int(size * 0.77)
    y0 = int(size * 0.18)
    y1 = int(size * 0.76)

    # Main rounded body.
    draw.rounded_rectangle([x0, y0, x1, y1], radius=int(size * 0.18), fill="white")

    # Scalloped ghost feet.
    foot_r = int(size * 0.07)
    foot_centers = (
        int(x0 + (x1 - x0) * 0.16),
        int(x0 + (x1 - x0) * 0.50),
        int(x0 + (x1 - x0) * 0.84),
    )
    for cx in foot_centers:
        draw.ellipse([cx - foot_r, y1 - foot_r, cx + foot_r, y1 + foot_r], fill="white")

    # Cut small notches between feet to keep a ghost-like silhouette.
    notch_r = int(size * 0.045)
    for cx in (
        int((foot_centers[0] + foot_centers[1]) / 2),
        int((foot_centers[1] + foot_centers[2]) / 2),
    ):
        draw.ellipse(
            [cx - notch_r, y1 - notch_r // 2, cx + notch_r, y1 + notch_r * 2],
            fill="#7c3aed",
        )

    # Eyes.
    eye_r = max(2, int(size * 0.045))
    eye_y = int(size * 0.42)
    draw.ellipse(
        [int(size * 0.42) - eye_r, eye_y - eye_r, int(size * 0.42) + eye_r, eye_y + eye_r],
        fill="#7c3aed",
    )
    draw.ellipse(
        [int(size * 0.58) - eye_r, eye_y - eye_r, int(size * 0.58) + eye_r, eye_y + eye_r],
        fill="#7c3aed",
    )

for sz in (192, 512):
    img = Image.new("RGBA", (sz, sz), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    r = int(sz * 0.22)
    d.rounded_rectangle([0, 0, sz - 1, sz - 1], radius=r, fill="#7c3aed")
    draw_ghost(d, sz)
    img.save(OUT / f"icon-{sz}.png")
    print(f"Created app/icon-{sz}.png ({sz}x{sz})")

print("Done.")
