#!/usr/bin/env python3
"""Check every foreground/background pair the two sites actually use against WCAG AA.

The palettes are read out of the stylesheets rather than copied here, so a token
that changes in CSS is checked at its new value instead of quietly drifting away
from a hard-coded duplicate.
"""
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parent.parent


def lin(c):
    c /= 255
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def lum(h):
    h = h.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)


def ratio(a, b):
    la, lb = lum(a), lum(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


TOKEN = re.compile(r"--([a-z0-9-]+)\s*:\s*(#[0-9a-fA-F]{3,8})\s*;")


def read_palettes(css: Path):
    """Return (light, dark) token maps, keyed with dashes turned into underscores."""
    text = css.read_text(encoding="utf-8")

    # The dark block is the first `@media (prefers-color-scheme: dark)` rule that
    # redefines :root. Everything before it is the light palette.
    start = text.find("@media (prefers-color-scheme: dark)")
    head = text[:start] if start != -1 else text

    light = {k.replace("-", "_"): v.lower() for k, v in TOKEN.findall(head)}

    dark = dict(light)
    if start != -1:
        depth, i = 0, text.index("{", start)
        for j in range(i, len(text)):
            if text[j] == "{":
                depth += 1
            elif text[j] == "}":
                depth -= 1
                if depth == 0:
                    break
        for k, v in TOKEN.findall(text[i:j]):
            dark[k.replace("-", "_")] = v.lower()
    return light, dark


CC_LIGHT, CC_DARK = read_palettes(ROOT / "sites/corecredit/assets/css/corecredit.css")
ID_LIGHT, ID_DARK = read_palettes(ROOT / "sites/idlery/assets/css/idlery.css")

# (label, fg, bg, minimum) — 4.5 for body text, 3.0 for large text / UI boundaries
CC_PAIRS = [
    ("ink on ground", "ink", "ground", 4.5),
    ("ink on surface", "ink", "surface", 4.5),
    ("ink on surface_2", "ink", "surface_2", 4.5),
    ("ink_mid on ground", "ink_mid", "ground", 4.5),
    ("ink_mid on surface", "ink_mid", "surface", 4.5),
    ("ink_mid on surface_2", "ink_mid", "surface_2", 4.5),
    ("ink_soft on surface", "ink_soft", "surface", 4.5),
    ("ink_soft on surface_2", "ink_soft", "surface_2", 4.5),
    ("ink_soft on ground", "ink_soft", "ground", 4.5),
    ("blue link on ground", "blue", "ground", 4.5),
    ("blue link on surface", "blue", "surface", 4.5),
    ("blue link on surface_2", "blue", "surface_2", 4.5),
    ("blue eyebrow on surface_2", "blue", "surface_2", 4.5),
    ("blue_deep on blue_wash (pill)", "blue_deep", "blue_wash", 4.5),
    ("risk tag", "risk", "risk_wash", 4.5),
    ("settled tag", "settled", "settled_wash", 4.5),
    # Launch additions.
    ("available-now pill on surface_2", "settled", "settled_wash", 4.5),
    ("plan price on surface", "ink_soft", "surface", 4.5),
    ("QR caption on white", "#55617a", "#ffffff", 4.5),
    ("focus ring vs ground", "blue", "ground", 3.0),
]

ID_PAIRS = [
    ("ink on ground", "ink", "ground", 4.5),
    ("ink on ground_tint", "ink", "ground_tint", 4.5),
    ("ink on surface", "ink", "surface", 4.5),
    ("ink_mid on ground", "ink_mid", "ground", 4.5),
    ("ink_mid on ground_tint", "ink_mid", "ground_tint", 4.5),
    ("ink_mid on surface", "ink_mid", "surface", 4.5),
    ("ink_soft on ground", "ink_soft", "ground", 4.5),
    ("ink_soft on ground_tint", "ink_soft", "ground_tint", 4.5),
    ("ink_soft on surface", "ink_soft", "surface", 4.5),
    ("teal_ink link on ground", "teal_ink", "ground", 4.5),
    ("teal_ink link on ground_tint", "teal_ink", "ground_tint", 4.5),
    ("teal_ink link on surface", "teal_ink", "surface", 4.5),
    ("teal_ink eyebrow on ground_tint", "teal_ink", "ground_tint", 4.5),
    ("teal_ink on teal_wash (badge)", "teal_ink", "teal_wash", 4.5),
    # Launch additions: the announcement band and the App Store button.
    ("launch kicker on teal_wash", "teal_ink", "teal_wash", 4.5),
    ("launch heading on teal_wash", "ink", "teal_wash", 4.5),
    ("launch sub on teal_wash", "ink_mid", "teal_wash", 4.5),
    ("live badge on surface", "teal_ink", "surface", 4.5),
    # The wordmark is supplied artwork in the brand teal (#3aa6ab, 2.91:1 on
    # white). WCAG 1.4.11 exempts a logotype from the non-text contrast
    # minimum, and the images carry alt="Idlery", so the company name is
    # available to a reader who cannot see the mark at all. The typographic
    # fallback, which *is* text, is set in --teal-ink and is covered above.
    # The brand hairline is decorative and aria-hidden; this only asserts it
    # remains plainly visible.
    ("brandline vs ground (decorative)", "teal", "ground", 2.5),
    ("focus ring vs ground", "teal_ink", "ground", 3.0),
]

CHECKS = [
    ("CoreCredit light", CC_LIGHT, CC_PAIRS + [("white on blue (button)", "#ffffff", "blue", 4.5)]),
    ("CoreCredit dark", CC_DARK, CC_PAIRS + [("dark ink on blue (button)", "#06122c", "blue", 4.5)]),
    ("Idlery light", ID_LIGHT, ID_PAIRS + [("white on teal_ink (button)", "#ffffff", "teal_ink", 4.5)]),
    ("Idlery dark", ID_DARK, ID_PAIRS + [("dark ink on teal (button)", "#062426", "teal", 4.5)]),
]

fails = 0
for name, pal, pairs in CHECKS:
    print(f"\n=== {name} ===")
    for label, fg, bg, minimum in pairs:
        f = pal.get(fg, fg)
        b = pal.get(bg, bg)
        if not f.startswith("#") or not b.startswith("#"):
            print(f"  SKIP  unresolved token in: {label} ({fg} / {bg})")
            fails += 1
            continue
        r = ratio(f, b)
        ok = r >= minimum
        if not ok:
            fails += 1
        print(f"  {'ok  ' if ok else 'FAIL'} {r:5.2f}:1  (min {minimum})  {label}")

print(f"\n{fails} failure(s)")
sys.exit(1 if fails else 0)
