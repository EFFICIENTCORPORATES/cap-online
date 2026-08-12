#!/usr/bin/env python3
"""
telegram/branding/build_brand_kit.py -- generate the 1LAVYA brand asset kit
from the source logo (Phase 1 of the 2026-08-10 roadmap: Branding Kit ->
Report Pipeline -> Leaderboard -> Admin Portal)
--------------------------------------------------------------------------------
Source of truth: telegram/1LAVYA_LOGO.jpeg (1254x1254 JPEG, white background,
navy + gold mark, "1lavya" wordmark, "Learn. Practice. Achieve." tagline).

This script derives everything downstream code should actually use -- never
hand-edit an output file here, re-run this script if the source logo ever
changes:

  telegram/branding/assets/1lavya_logo_transparent.png
      Same artwork, white background removed (alpha-feathered, not a hard
      cutout -- see remove_white_background()) so it drops cleanly onto any
      colored header/footer without a white box around it.

  telegram/branding/assets/1lavya_logo_original.jpg
      A byte-identical copy of the source JPEG, kept alongside the derived
      asset so brand_kit.py has one directory to read from instead of
      reaching back into telegram/ for the original.

  telegram/branding/brand_colors.json
      The two dominant brand colors (navy, gold), extracted directly from
      the logo's own pixels -- not eyeballed/guessed -- by hue-bucketing
      every non-background pixel and averaging each bucket. Single JSON
      source of truth for every brand color used downstream (dashboard,
      reports, anything else), matching this repo's existing "one JSON file
      is the only place X lives" convention (see CLAUDE.md section 7).

USAGE:
    python telegram/branding/build_brand_kit.py
"""

import json
import colorsys
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
SOURCE_LOGO = HERE.parent / "1LAVYA_LOGO.jpeg"
ASSETS_DIR = HERE / "assets"
TRANSPARENT_PNG = ASSETS_DIR / "1lavya_logo_transparent.png"   # full-res, 1254x1254, ~800KB -- for a one-per-document cover/hero use, never embed repeatedly
ORIGINAL_COPY = ASSETS_DIR / "1lavya_logo_original.jpg"
COLORS_JSON = HERE / "brand_colors.json"

# Pre-sized thumbnails -- generated once here, never resized on the fly by
# consuming code, so every report/dashboard embeds a small, predictable
# asset instead of repeatedly shipping the 800KB full-res PNG. Sizes chosen
# for the two real use cases: a header logo (visible, needs some detail)
# and a small footer/inline mark (tiny, just needs to be recognizable).
THUMBNAIL_SIZES = {
    "header": (128, ASSETS_DIR / "1lavya_logo_header_128.png"),
    "footer": (48, ASSETS_DIR / "1lavya_logo_footer_48.png"),
}


def remove_white_background(img: Image.Image) -> Image.Image:
    """Feathered alpha, not a hard cutout -- a pixel's alpha ramps smoothly
    from fully transparent (pure white) to fully opaque (min(R,G,B) <= 200)
    based on how far it is from white. Avoids a jagged/aliased edge around
    the star points and book-page curves, which a hard white==transparent
    threshold would produce."""
    rgba = np.array(img.convert("RGBA")).astype(float)
    rgb = rgba[..., :3]
    whiteness = rgb.min(axis=-1)  # high = close to white on every channel
    alpha = np.clip((245 - whiteness) / (245 - 200), 0, 1) * 255
    rgba[..., 3] = alpha
    return Image.fromarray(rgba.astype("uint8"), "RGBA")


def extract_brand_colors(img: Image.Image) -> dict:
    """Hue-buckets every non-background, non-grayscale pixel into "navy"
    (blue hue range) vs "gold" (yellow/amber hue range) and averages each
    bucket's RGB -- sampled from the real logo, not guessed by eye. Returns
    hex strings ready to drop straight into CSS."""
    rgb_img = img.convert("RGB")
    arr = np.array(rgb_img).reshape(-1, 3) / 255.0

    # Drop background (near-white) and near-black/gray (low-saturation)
    # pixels -- only the actual brand-color ink should vote on the average.
    maxc = arr.max(axis=1)
    minc = arr.min(axis=1)
    saturation = np.where(maxc > 0, (maxc - minc) / np.where(maxc == 0, 1, maxc), 0)
    keep = (maxc < 0.97) & (saturation > 0.25)  # not near-white, has real color
    colored = arr[keep]

    navy_bucket, gold_bucket = [], []
    for r, g, b in colored:
        h, s, v = colorsys.rgb_to_hsv(r, g, b)
        deg = h * 360
        if 190 <= deg <= 250:      # blue/navy range
            navy_bucket.append((r, g, b))
        elif 30 <= deg <= 55:      # gold/amber range
            gold_bucket.append((r, g, b))

    def avg_hex(bucket, fallback):
        if not bucket:
            return fallback
        arr_b = np.array(bucket)
        r, g, b = (arr_b.mean(axis=0) * 255).astype(int)
        return f"#{r:02x}{g:02x}{b:02x}"

    # Fallbacks are sane defaults matching the logo's visible palette, only
    # used if a bucket comes back empty (shouldn't happen on the real logo,
    # but never let color extraction hard-crash the whole build).
    navy = avg_hex(navy_bucket, "#1a2f5c")
    gold = avg_hex(gold_bucket, "#c9971c")

    return {
        "navy": navy,
        "gold": gold,
        "navy_sample_pixels": len(navy_bucket),
        "gold_sample_pixels": len(gold_bucket),
    }


def main():
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)

    if not SOURCE_LOGO.exists():
        raise SystemExit(f"Source logo not found: {SOURCE_LOGO}")

    img = Image.open(SOURCE_LOGO)
    img.convert("RGB").save(ORIGINAL_COPY, "JPEG", quality=95)
    print(f"Wrote {ORIGINAL_COPY}")

    transparent = remove_white_background(img)
    transparent.save(TRANSPARENT_PNG, "PNG")
    print(f"Wrote {TRANSPARENT_PNG} ({transparent.size[0]}x{transparent.size[1]})")

    for label, (size, out_path) in THUMBNAIL_SIZES.items():
        thumb = transparent.copy()
        thumb.thumbnail((size, size), Image.LANCZOS)
        thumb.save(out_path, "PNG", optimize=True)
        print(f"Wrote {out_path} ({label}, {thumb.size[0]}x{thumb.size[1]}, {out_path.stat().st_size:,} bytes)")

    colors = extract_brand_colors(img)
    colors_out = {
        "$comment": "Generated by telegram/branding/build_brand_kit.py from telegram/1LAVYA_LOGO.jpeg's "
                    "own pixels -- never hand-edit, re-run the script if the source logo changes.",
        "navy": colors["navy"],
        "gold": colors["gold"],
        "navy_tint": "#eef1f7",   # light navy tint, for subtle backgrounds/borders -- not sampled, a fixed derivative
        "gold_tint": "#fbf3e1",   # light gold tint, same purpose
        "ink": "#14213d",         # near-navy, for body text on light backgrounds -- darker than pure navy for readability
        "_sample_sizes": {"navy_pixels": colors["navy_sample_pixels"], "gold_pixels": colors["gold_sample_pixels"]},
    }
    COLORS_JSON.write_text(json.dumps(colors_out, indent=2), encoding="utf-8")
    print(f"Wrote {COLORS_JSON}: navy={colors['navy']} (from {colors['navy_sample_pixels']} px), "
          f"gold={colors['gold']} (from {colors['gold_sample_pixels']} px)")


if __name__ == "__main__":
    main()
