#!/usr/bin/env python3
"""Generate the Open Graph social-preview images from local artwork only."""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BOLD = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
REG = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"


def rounded_icon(path, size, radius_ratio=0.225):
    icon = Image.open(path).convert("RGBA").resize((size, size), Image.LANCZOS)
    mask = Image.new("L", (size * 4, size * 4), 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        (0, 0, size * 4 - 1, size * 4 - 1), radius=int(size * 4 * radius_ratio), fill=255
    )
    icon.putalpha(mask.resize((size, size), Image.LANCZOS))
    return icon


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


def corecredit_og(out: Path):
    W, H = 1200, 630
    img = Image.new("RGB", (W, H), "#f4f6fb")
    d = ImageDraw.Draw(img)

    # soft brand wash in the top-right corner
    wash = Image.new("RGB", (W, H), "#f4f6fb")
    wd = ImageDraw.Draw(wash)
    wd.ellipse((W - 560, -460, W + 320, 420), fill="#dfe8ff")
    wash = wash.filter(ImageFilter.GaussianBlur(90))
    img = Image.blend(img, wash, 0.9)
    d = ImageDraw.Draw(img)

    d.rectangle((0, 0, W, 10), fill="#0053fd")

    icon = rounded_icon(ROOT / "sites/corecredit/assets/img/corecredit-icon-384.png", 132)
    img.paste(icon, (84, 96), icon)

    f_kicker = ImageFont.truetype(BOLD, 26)
    f_head = ImageFont.truetype(BOLD, 58)
    f_sub = ImageFont.truetype(REG, 28)
    f_foot = ImageFont.truetype(REG, 24)

    d.text((240, 128), "CORECREDIT", font=f_kicker, fill="#0053fd")
    d.text((240, 168), "Now on the App Store for iPhone", font=f_sub, fill="#55617a")

    y = 300
    for line in wrap(d, "Know exactly how much core-credit money is still at risk.", f_head, 1030):
        d.text((84, y), line, font=f_head, fill="#0b1220")
        y += 74

    d.line((84, H - 96, W - 84, H - 96), fill="#c9d3e6", width=2)
    d.text((84, H - 74), "corecredit.idlery.com", font=f_foot, fill="#3d4a63")
    right = "Idlery Services LLC"
    d.text((W - 84 - d.textlength(right, font=f_foot), H - 74), right, font=f_foot, fill="#55617a")

    img.quantize(colors=128, method=Image.MEDIANCUT, dither=Image.NONE).save(out, optimize=True)
    print("wrote", out, out.stat().st_size, "bytes")


if __name__ == "__main__":
    corecredit_og(ROOT / "sites/corecredit/assets/img/corecredit-og.png")
