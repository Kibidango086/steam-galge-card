#!/usr/bin/env python3
"""Generate Steam grid artwork for a non-Steam galgame.

Requires Pillow. Outputs standard Steam library slots under a prefix that the
sync script later renames to the real appid.

Example:
    python3 build_artwork.py --cover cover.png --hero ogp.png \
        --logo logo.png --icon icon.png --prefix game --out-dir out
"""

import argparse
import sys
from pathlib import Path

from PIL import Image, ImageFilter, ImageOps

PORTRAIT = (600, 900)
CAPSULE = (920, 430)
HEADER = (460, 215)
HERO_DEFAULT = (1920, 620)
LOGO_CANVAS = (1280, 720)
ICON_CANVAS = (512, 512)


def parse_size(text):
    try:
        width, height = (int(part) for part in text.lower().split("x"))
    except ValueError:
        sys.exit(f"Invalid size: {text!r} (expected WxH)")
    if width <= 0 or height <= 0:
        sys.exit(f"Invalid size: {text!r}")
    return width, height


def open_image(path):
    image = Image.open(path)
    image.load()
    return image


def crop_to(image, size):
    """Resize and center-crop an image to an exact size."""
    src = image.convert("RGB")
    scale = max(size[0] / src.width, size[1] / src.height)
    resized = src.resize(
        (max(1, round(src.width * scale)), max(1, round(src.height * scale))),
        Image.LANCZOS,
    )
    left = (resized.width - size[0]) // 2
    top = (resized.height - size[1]) // 2
    return resized.crop((left, top, left + size[0], top + size[1]))


def blurred_wide(cover, size):
    """Build a wide banner from a portrait cover with a blurred backdrop."""
    src = cover.convert("RGB")
    bg = src.resize(size, Image.LANCZOS).filter(ImageFilter.GaussianBlur(18))
    fitted = ImageOps.contain(src, size)
    bg.paste(fitted, ((size[0] - fitted.width) // 2, (size[1] - fitted.height) // 2))
    return bg


def wide_image(hero, cover, size):
    if hero is not None:
        return crop_to(hero, size)
    return blurred_wide(cover, size)


def on_canvas(image, canvas_size):
    """Center an RGBA image on a transparent canvas."""
    fitted = ImageOps.contain(image.convert("RGBA"), canvas_size)
    canvas = Image.new("RGBA", canvas_size, (0, 0, 0, 0))
    canvas.paste(
        fitted,
        ((canvas_size[0] - fitted.width) // 2, (canvas_size[1] - fitted.height) // 2),
    )
    return canvas


def save_jpg(image, path, quality):
    image.convert("RGB").save(path, "JPEG", quality=quality, optimize=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cover", required=True, help="Portrait cover or key visual")
    parser.add_argument("--hero", help="Optional wide hero source (OGP/screenshot)")
    parser.add_argument("--logo", help="Optional transparent logo PNG")
    parser.add_argument("--icon", help="Optional icon PNG")
    parser.add_argument("--prefix", required=True, help="Output filename prefix")
    parser.add_argument("--out-dir", required=True, help="Output directory")
    parser.add_argument(
        "--hero-size",
        default="1920x620",
        help="Hero size as WxH (official is 3840x1240)",
    )
    parser.add_argument("--quality", type=int, default=92, help="JPEG quality")
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    cover = open_image(args.cover)
    hero = open_image(args.hero) if args.hero else None
    logo = open_image(args.logo) if args.logo else None
    icon = open_image(args.icon) if args.icon else None
    hero_size = parse_size(args.hero_size)
    prefix = args.prefix

    portrait = crop_to(cover, PORTRAIT)
    capsule = wide_image(hero, cover, CAPSULE)
    header = wide_image(hero, cover, HEADER)
    hero_image = wide_image(hero, cover, hero_size)

    save_jpg(portrait, out_dir / f"{prefix}_library_600x900.jpg", args.quality)
    save_jpg(portrait, out_dir / f"{prefix}p.jpg", args.quality)
    save_jpg(capsule, out_dir / f"{prefix}_library_capsule.jpg", args.quality)
    save_jpg(hero_image, out_dir / f"{prefix}_library_hero.jpg", args.quality)
    save_jpg(header, out_dir / f"{prefix}_header.jpg", args.quality)
    header.convert("RGB").save(out_dir / f"{prefix}.png", "PNG")
    header.convert("RGB").save(out_dir / f"{prefix}_grid.png", "PNG")

    if logo is not None:
        on_canvas(logo, LOGO_CANVAS).save(out_dir / f"{prefix}_logo.png", "PNG")
    if icon is not None:
        on_canvas(icon, ICON_CANVAS).save(out_dir / f"{prefix}_icon.png", "PNG")

    print(f"Artwork written to {out_dir} (prefix {prefix})")


if __name__ == "__main__":
    main()
