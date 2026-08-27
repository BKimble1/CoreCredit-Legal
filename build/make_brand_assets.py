#!/usr/bin/env python3
"""Derive the Idlery brand assets from the real Idlery wordmark artwork.

The wordmark supplied with the company's other projects is a solid-colour
letterform composited on white. Everything here is derived from that single
file: the transparent wordmark used in the header and footer, the square mark
used for the favicon and touch icon (the wordmark's own "i", knocked out of a
brand-teal tile), and the social-preview image.

Nothing is drawn by hand and no letterform is redrawn — the glyph shapes come
straight out of the artwork's alpha channel.

    python3 build/make_brand_assets.py <path-to-IdleryWordmark.png>
"""
from pathlib import Path
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "sites/idlery/assets/img"
BOLD = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
REG = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"

# Sampled from the artwork itself (the modal non-white colour), confirmed
# against a second copy of the same wordmark in another repository.
BRAND = (0x3A, 0xA6, 0xAB)
# The light end of the same hue, for the wordmark shown on a dark ground.
BRAND_ON_DARK = (0x6F, 0xD3, 0xD8)
INK = "#10222b"
INK_MID = "#3d5560"
RULE = "#c3d4d7"


def key_out_white(path: Path) -> Image.Image:
    """Recover the wordmark's alpha channel from a solid-colour-on-white render.

    A pixel of a solid ink `k` composited on white at coverage `a` is
    `k*a + 255*(1-a)`, so `a = (255 - pixel) / (255 - k)`. The red channel has
    the largest delta for this teal, which makes it the least noisy estimator.
    """
    src = Image.open(path).convert("RGB")
    r = src.split()[0]
    denom = 255 - BRAND[0]
    alpha = r.point(lambda v: max(0, min(255, round((255 - v) * 255 / denom))))
    out = Image.new("RGBA", src.size, BRAND + (0,))
    out.putalpha(alpha)
    return out.crop(out.getbbox())


def recolour(mark: Image.Image, rgb) -> Image.Image:
    solid = Image.new("RGBA", mark.size, tuple(rgb) + (255,))
    solid.putalpha(mark.getchannel("A"))
    return solid


def fit_width(im: Image.Image, width: int) -> Image.Image:
    height = max(1, round(im.height * width / im.width))
    return im.resize((width, height), Image.LANCZOS)


def square_mark(glyph: Image.Image, size: int) -> Image.Image:
    """A brand-teal rounded tile with the wordmark's own "i" knocked out of it."""
    ss = 4
    n = size * ss
    tile = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    ImageDraw.Draw(tile).rounded_rectangle(
        (0, 0, n - 1, n - 1), radius=int(n * 0.225), fill=BRAND + (255,)
    )

    # Scale the glyph to sit on the tile's optical centre with generous margins.
    g = glyph.getchannel("A")
    g = g.crop(g.getbbox())
    target_h = int(n * 0.52)
    g = g.resize((max(1, round(g.width * target_h / g.height)), target_h), Image.LANCZOS)

    knock = Image.new("L", (n, n), 0)
    knock.paste(g, ((n - g.width) // 2, (n - g.height) // 2))

    # Set the glyph in white on the tile. A knockout to transparency would let
    # whatever sits behind the icon show through, which a touch icon cannot rely on.
    white = Image.new("RGBA", (n, n), (255, 255, 255, 255))
    tile = Image.composite(white, tile, knock)
    return tile.resize((size, size), Image.LANCZOS)


def flatten(im: Image.Image, bg="#ffffff") -> Image.Image:
    ground = Image.new("RGBA", im.size, bg)
    ground.alpha_composite(im)
    return ground.convert("RGB")


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


def og(wordmark: Image.Image, icon_path: Path, out: Path):
    W, H = 1200, 630
    img = Image.new("RGB", (W, H), "#ffffff")
    wash = Image.new("RGB", (W, H), "#ffffff")
    wd = ImageDraw.Draw(wash)
    wd.ellipse((W - 540, -430, W + 340, 450), fill="#ddf2f3")
    wd.ellipse((-320, H - 300, 300, H + 320), fill="#e9f9fa")
    wash = wash.filter(ImageFilter.GaussianBlur(95))
    img = Image.blend(img, wash, 0.92)
    d = ImageDraw.Draw(img)
    d.rectangle((0, 0, W, 10), fill=BRAND)

    word = fit_width(wordmark, 300)
    img.paste(word, (84, 96), word)

    f_head = ImageFont.truetype(BOLD, 56)
    f_sub = ImageFont.truetype(REG, 30)
    f_foot = ImageFont.truetype(REG, 24)

    y = 268
    for line in wrap(d, "Focused apps that make everyday work easier.", f_head, 1020):
        d.text((84, y), line, font=f_head, fill=INK)
        y += 72

    icon = Image.open(icon_path).convert("RGBA").resize((104, 104), Image.LANCZOS)
    mask = Image.new("L", (416, 416), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, 415, 415), radius=94, fill=255)
    icon.putalpha(mask.resize((104, 104), Image.LANCZOS))
    img.paste(icon, (84, y + 24), icon)
    d.text((208, y + 40), "CoreCredit — now on the App Store", font=f_sub, fill=INK_MID)

    d.line((84, H - 96, W - 84, H - 96), fill=RULE, width=2)
    d.text((84, H - 74), "idlery.com", font=f_foot, fill=INK_MID)
    right = "Idlery Services LLC"
    d.text((W - 84 - d.textlength(right, font=f_foot), H - 74), right, font=f_foot, fill=INK_MID)

    img.quantize(colors=128, method=Image.MEDIANCUT, dither=Image.NONE).save(out, optimize=True)
    print(f"  {out.name}: {out.stat().st_size / 1024:.1f} KB")


def main(source: Path) -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    mark = key_out_white(source)
    print(f"keyed wordmark: {mark.size} from {source}")

    # The wordmark, at the two densities the header and footer ask for.
    for name, rgb in (("light", BRAND), ("dark", BRAND_ON_DARK)):
        coloured = recolour(mark, rgb)
        for width, suffix in ((360, ""), (720, "@2x")):
            path = OUT / f"idlery-wordmark-{name}{suffix}.png"
            fit_width(coloured, width).save(path, optimize=True)
            print(f"  {path.name}: {path.stat().st_size / 1024:.1f} KB")

    # The "i" is the first glyph: take the leftmost connected slice of the mark.
    alpha = mark.getchannel("A")
    columns = [x for x in range(mark.width)
               if any(alpha.getpixel((x, y)) > 24 for y in range(0, mark.height, 3))]
    gap = next((i for i in range(1, len(columns)) if columns[i] - columns[i - 1] > 4), len(columns))
    glyph = mark.crop((columns[0], 0, columns[gap - 1] + 1, mark.height))
    glyph = glyph.crop(glyph.getbbox())
    print(f"  'i' glyph isolated: {glyph.size}")

    # Only the sizes the pages ask for; build/prune_assets.py deletes the rest.
    for size in (512, 256, 192, 180):
        square_mark(glyph, size).save(OUT / f"idlery-mark-{size}.png", optimize=True)
    flatten(square_mark(glyph, 32)).save(OUT / "favicon-32.png", optimize=True)
    print("  square-mark derivatives: 512, 256, 192, 180 + favicon-32")

    og(recolour(mark, BRAND), OUT / "corecredit-icon-192.png", OUT / "idlery-og.png")
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        raise SystemExit(2)
    raise SystemExit(main(Path(sys.argv[1])))
