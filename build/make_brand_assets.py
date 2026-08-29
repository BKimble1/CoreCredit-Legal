#!/usr/bin/env python3
"""Derive every Idlery brand asset from the artwork in brand/.

Two source files, both committed here so the sites can be rebuilt from this
repository alone:

  brand/idlery-app-icon-1024.png   the Idlery app icon — a vertical teal
                                   gradient with a white "i". This is the
                                   primary mark and the anchor for the whole
                                   colour system.
  brand/idlery-wordmark-source.png the "idlery" logotype, solid ink on white.

Nothing is drawn by hand and no letterform is redrawn. The wordmark's glyph
shapes come out of the artwork's own alpha, recovered from its white ground;
the square mark is the app icon itself, resampled.

    python3 build/make_brand_assets.py
"""
from pathlib import Path
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent.parent
BRAND = ROOT / "brand"
OUT = ROOT / "sites/idlery/assets/img"
ICON = BRAND / "idlery-app-icon-1024.png"
WORDMARK = BRAND / "idlery-wordmark-source.png"
BOLD = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
REG = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"

# Sampled from the app icon's gradient: the top of the tile, its mid tone, and
# the bottom. Every teal in assets/css/idlery.css is this hue family, and the
# wordmark is painted in the top tone so the logotype and the icon are one
# colour system rather than two — the supplied wordmark render is a duller
# teal (#3aa6ab), far enough from the icon (dE76 ≈ 12) to read as a different
# colour when the two sit together in the header.
BRAND_INK = (0x18, 0x9B, 0xBA)
BRAND_ON_DARK = (0x77, 0xD7, 0xE2)
INK = "#10222b"
INK_MID = "#3d5560"
RULE = "#c3d4d7"

# iOS masks a touch icon itself and a manifest icon is used at many shapes, so
# those ship full-bleed and square. Only the favicon gets corners baked in,
# because nothing rounds a favicon for you.
CORNER_RATIO = 0.225


def key_out_white(path: Path) -> Image.Image:
    """Recover the wordmark's alpha from a solid-ink-on-white render.

    A pixel of ink `k` composited on white at coverage `a` is
    `k*a + 255*(1-a)`, so `a = (255 - pixel) / (255 - k)`. The red channel has
    the largest delta for this teal, which makes it the least noisy estimator.
    """
    src = Image.open(path).convert("RGB")
    red = src.split()[0]
    # The render's own ink, not the brand ink we are about to paint it with.
    denom = 255 - 0x3A
    alpha = red.point(lambda v: max(0, min(255, round((255 - v) * 255 / denom))))
    out = Image.new("RGBA", src.size, (0, 0, 0, 0))
    out.putalpha(alpha)
    return out.crop(out.getbbox())


def paint(mask: Image.Image, rgb) -> Image.Image:
    solid = Image.new("RGBA", mask.size, tuple(rgb) + (255,))
    solid.putalpha(mask.getchannel("A"))
    return solid


def fit_width(im: Image.Image, width: int) -> Image.Image:
    height = max(1, round(im.height * width / im.width))
    return im.resize((width, height), Image.LANCZOS)


def rounded(im: Image.Image, ratio: float = CORNER_RATIO) -> Image.Image:
    """Round an icon's corners, anti-aliased, on transparency."""
    im = im.convert("RGBA")
    n = im.width * 4
    mask = Image.new("L", (n, n), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, n - 1, n - 1), radius=int(n * ratio), fill=255)
    im.putalpha(mask.resize(im.size, Image.LANCZOS))
    return im


def wrap(draw, text, font, max_width):
    words, lines, line = text.split(), [], ""
    for w in words:
        trial = f"{line} {w}".strip()
        if draw.textlength(trial, font=font) <= max_width:
            line = trial
        else:
            if line:
                lines.append(line)
            line = w
    if line:
        lines.append(line)
    return lines


def og(wordmark: Image.Image, icon: Image.Image, out: Path):
    W, H = 1200, 630
    img = Image.new("RGB", (W, H), "#ffffff")
    wash = Image.new("RGB", (W, H), "#ffffff")
    wd = ImageDraw.Draw(wash)
    wd.ellipse((W - 540, -430, W + 340, 450), fill="#dcf4f7")
    wd.ellipse((-320, H - 300, 300, H + 320), fill="#e9fafb")
    wash = wash.filter(ImageFilter.GaussianBlur(95))
    img = Image.blend(img, wash, 0.92)
    d = ImageDraw.Draw(img)

    # The card's top rule is the icon's own gradient, read left to right: the
    # tile's top tone, its mid tone, its bottom tone.
    ramp = Image.new("RGB", (W, 1))
    stops = [(0.0, icon.getpixel((6, 6))), (0.55, icon.getpixel((6, icon.height // 2))),
             (1.0, icon.getpixel((6, icon.height - 7)))]
    for x in range(W):
        t = x / (W - 1)
        for (t0, c0), (t1, c1) in zip(stops, stops[1:]):
            if t0 <= t <= t1:
                k = 0 if t1 == t0 else (t - t0) / (t1 - t0)
                ramp.putpixel((x, 0), tuple(round(a + (b - a) * k) for a, b in zip(c0, c1)))
                break
    img.paste(ramp.resize((W, 10)), (0, 0))

    word = fit_width(wordmark, 288)
    img.paste(word, (84, 88), word)

    f_head = ImageFont.truetype(BOLD, 56)
    f_sub = ImageFont.truetype(REG, 29)
    f_foot = ImageFont.truetype(REG, 24)

    y = 252
    for line in wrap(d, "Focused apps that make everyday work easier.", f_head, 1020):
        d.text((84, y), line, font=f_head, fill=INK)
        y += 72

    # The launch line sits under the headline, and the rule sits under that —
    # measured rather than assumed, so nothing can collide as copy changes.
    icon_px = 96
    icon_y = y + 26
    cc = rounded(Image.open(OUT / "corecredit-icon-192.png").convert("RGBA").resize((icon_px, icon_px), Image.LANCZOS))
    img.paste(cc, (84, icon_y), cc)
    d.text((84 + icon_px + 28, icon_y + (icon_px - 34) // 2),
           "CoreCredit — now on the App Store", font=f_sub, fill=INK_MID)

    rule_y = max(icon_y + icon_px + 30, H - 96)
    d.line((84, rule_y, W - 84, rule_y), fill=RULE, width=2)
    d.text((84, rule_y + 22), "idlery.com", font=f_foot, fill=INK_MID)
    right = "Idlery Services LLC"
    d.text((W - 84 - d.textlength(right, font=f_foot), rule_y + 22), right, font=f_foot, fill=INK_MID)

    img.quantize(colors=192, method=Image.MEDIANCUT, dither=Image.NONE).save(out, optimize=True)
    print(f"  {out.name}: {out.stat().st_size / 1024:.1f} KB")


def main() -> int:
    for src in (ICON, WORDMARK):
        if not src.is_file():
            print(f"missing brand source: {src}")
            return 1
    OUT.mkdir(parents=True, exist_ok=True)

    icon = Image.open(ICON).convert("RGB")
    if icon.size != (1024, 1024):
        print(f"the app icon should be 1024x1024, got {icon.size}")
        return 1

    # Square mark: the app icon itself, full-bleed.
    for size in (512, 256, 192, 180):
        path = OUT / f"idlery-mark-{size}.png"
        icon.resize((size, size), Image.LANCZOS).save(path, optimize=True)
        print(f"  {path.name}: {size}x{size}, {path.stat().st_size / 1024:.1f} KB")

    # The CoreCredit site credits its parent company in the footer, so it needs
    # the Idlery mark too.
    cc = ROOT / "sites/corecredit/assets/img"
    if cc.is_dir():
        for size in (96, 192):
            path = cc / f"idlery-mark-{size}.png"
            icon.resize((size, size), Image.LANCZOS).save(path, optimize=True)
            print(f"  corecredit/{path.name}: {size}x{size}, {path.stat().st_size / 1024:.1f} KB")

    fav = OUT / "favicon-32.png"
    rounded(icon.resize((128, 128), Image.LANCZOS)).resize((32, 32), Image.LANCZOS).save(fav, optimize=True)
    print(f"  {fav.name}: 32x32 rounded, {fav.stat().st_size / 1024:.1f} KB")

    mask = key_out_white(WORDMARK)
    print(f"  wordmark keyed from its white ground: {mask.size}")
    for name, rgb in (("light", BRAND_INK), ("dark", BRAND_ON_DARK)):
        coloured = paint(mask, rgb)
        for width, suffix in ((360, ""), (720, "@2x")):
            path = OUT / f"idlery-wordmark-{name}{suffix}.png"
            fit_width(coloured, width).save(path, optimize=True)
            print(f"  {path.name}: {path.stat().st_size / 1024:.1f} KB")

    og(paint(mask, BRAND_INK), icon, OUT / "idlery-og.png")
    return 0


if __name__ == "__main__":
    sys.exit(main())
