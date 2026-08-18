#!/usr/bin/env python3
"""Generate the interim Idlery brand mark, favicons and Open Graph image.

INTERIM ONLY. These are simple, on-brand stand-ins so the site ships with a real
local favicon and a real social preview. They are deliberately plainer than the
Idlery square brand mark rather than an imitation of it: when the brand artwork
is supplied, regenerate these from that artwork and replace the files in
sites/idlery/assets/img/.
"""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "sites/idlery/assets/img"
BOLD = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
REG = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"

TEAL_TOP = (0x17, 0xBF, 0xD1)
TEAL_BOTTOM = (0x45, 0xD6, 0xD8)
TEAL_INK = "#0a737d"
TEAL = "#0f96a1"
INK = "#10222b"
INK_MID = "#3d5560"
RULE = "#c3d4d7"
TINT = "#f2fafb"


def mark(size: int) -> Image.Image:
    """Teal gradient rounded square carrying a white lowercase i."""
    ss = 8  # supersample
    n = size * ss
    img = Image.new("RGBA", (n, n), (0, 0, 0, 0))

    grad = Image.new("RGB", (1, n))
    gd = ImageDraw.Draw(grad)
    for y in range(n):
        t = y / max(1, n - 1)
        gd.point(
            (0, y),
            fill=tuple(round(a + (b - a) * t) for a, b in zip(TEAL_TOP, TEAL_BOTTOM)),
        )
    grad = grad.resize((n, n))

    mask = Image.new("L", (n, n), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, n - 1, n - 1), radius=int(n * 0.225), fill=255)
    img.paste(grad, (0, 0), mask)

    d = ImageDraw.Draw(img)
    stem_w = n * 0.155
    cx = n * 0.5
    dot_r = stem_w * 0.62
    dot_cy = n * 0.265
    d.ellipse((cx - dot_r, dot_cy - dot_r, cx + dot_r, dot_cy + dot_r), fill=(255, 255, 255, 255))
    top, bottom = n * 0.415, n * 0.775
    d.rounded_rectangle(
        (cx - stem_w / 2, top, cx + stem_w / 2, bottom),
        radius=stem_w * 0.32,
        fill=(255, 255, 255, 255),
    )
    return img.resize((size, size), Image.LANCZOS)


def og(out: Path):
    W, H = 1200, 630
    img = Image.new("RGB", (W, H), "#ffffff")
    wash = Image.new("RGB", (W, H), "#ffffff")
    wd = ImageDraw.Draw(wash)
    wd.ellipse((W - 540, -430, W + 340, 450), fill="#dff5f6")
    wd.ellipse((-320, H - 300, 300, H + 320), fill="#e9f9fa")
    wash = wash.filter(ImageFilter.GaussianBlur(95))
    img = Image.blend(img, wash, 0.92)
    d = ImageDraw.Draw(img)

    d.rectangle((0, 0, W, 10), fill=TEAL)

    m = mark(120)
    img.paste(m, (84, 92), m)

    f_word = ImageFont.truetype(BOLD, 76)
    f_head = ImageFont.truetype(BOLD, 56)
    f_foot = ImageFont.truetype(REG, 24)

    d.text((228, 108), "idlery", font=f_word, fill=TEAL)

    y = 300
    words = "Focused apps that make everyday work easier.".split()
    line = ""
    lines = []
    for w in words:
        trial = f"{line} {w}".strip()
        if d.textlength(trial, font=f_head) <= 1020:
            line = trial
        else:
            lines.append(line)
            line = w
    lines.append(line)
    for ln in lines:
        d.text((84, y), ln, font=f_head, fill=INK)
        y += 72

    d.line((84, H - 96, W - 84, H - 96), fill=RULE, width=2)
    d.text((84, H - 74), "idlery.com", font=f_foot, fill=INK_MID)
    right = "Idlery Services LLC"
    d.text((W - 84 - d.textlength(right, font=f_foot), H - 74), right, font=f_foot, fill=INK_MID)

    img.quantize(colors=128, method=Image.MEDIANCUT, dither=Image.NONE).save(out, optimize=True)
    print("wrote", out.name, out.stat().st_size, "bytes")


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    for size in (512, 256, 192, 180, 96, 48, 32):
        m = mark(size)
        m.save(OUT / f"idlery-mark-{size}.png", optimize=True)
    mark(32).save(OUT / "favicon-32.png", optimize=True)
    print("wrote brand-mark derivatives")
    og(OUT / "idlery-og.png")
