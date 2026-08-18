#!/usr/bin/env python3
"""Check every foreground/background pair the two sites actually use against WCAG AA."""

def lin(c):
    c /= 255
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

def lum(h):
    h = h.lstrip("#")
    r, g, b = (int(h[i:i+2], 16) for i in (0, 2, 4))
    return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)

def ratio(a, b):
    la, lb = lum(a), lum(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)

CC_LIGHT = dict(blue="#0053fd", blue_deep="#0039b0", blue_wash="#eaf0ff", ground="#f4f6fb",
                surface="#ffffff", surface2="#f8fafd", ink="#0b1220", ink_mid="#3d4a63",
                ink_soft="#55617a", risk="#a4331f", risk_wash="#fdeeea", settled="#12693f",
                settled_wash="#e6f4ec")
CC_DARK = dict(blue="#6f9dff", blue_deep="#a8c4ff", blue_wash="#14203a", ground="#080b12",
               surface="#131a26", surface2="#182131", ink="#f2f5fa", ink_mid="#b9c4d6",
               ink_soft="#a4b0c4", risk="#ffa695", risk_wash="#2c1512", settled="#74d6a3",
               settled_wash="#0f2419")
ID_LIGHT = dict(teal_ink="#0a737d", teal="#0f96a1", teal_wash="#e8f7f8", ground="#ffffff",
                ground_tint="#f2fafb", surface="#ffffff", ink="#10222b", ink_mid="#3d5560",
                ink_soft="#55707b")
ID_DARK = dict(teal_ink="#5fd8e0", teal="#46ccd5", teal_wash="#102c31", ground="#0e1820",
               ground_tint="#121e27", surface="#16232e", ink="#eef7f8", ink_mid="#b3c6cd",
               ink_soft="#9db2bb")

# (label, fg, bg, minimum) — 4.5 for body text, 3.0 for large text / UI boundaries
CHECKS = [
    ("CC light", CC_LIGHT, [
        ("ink on ground", "ink", "ground", 4.5), ("ink on surface", "ink", "surface", 4.5),
        ("ink on surface2", "ink", "surface2", 4.5),
        ("ink_mid on ground", "ink_mid", "ground", 4.5),
        ("ink_mid on surface", "ink_mid", "surface", 4.5),
        ("ink_mid on surface2", "ink_mid", "surface2", 4.5),
        ("ink_soft on surface", "ink_soft", "surface", 4.5),
        ("ink_soft on surface2", "ink_soft", "surface2", 4.5),
        ("ink_soft on ground", "ink_soft", "ground", 4.5),
        ("blue link on ground", "blue", "ground", 4.5),
        ("blue link on surface", "blue", "surface", 4.5),
        ("blue link on surface2", "blue", "surface2", 4.5),
        ("blue eyebrow on surface2", "blue", "surface2", 4.5),
        ("blue_deep on blue_wash (pill)", "blue_deep", "blue_wash", 4.5),
        ("white on blue (button)", "#ffffff", "blue", 4.5),
        ("risk tag", "risk", "risk_wash", 4.5),
        ("settled tag", "settled", "settled_wash", 4.5),
        ("focus ring vs ground", "blue", "ground", 3.0),
    ]),
    ("CC dark", CC_DARK, [
        ("ink on ground", "ink", "ground", 4.5), ("ink on surface", "ink", "surface", 4.5),
        ("ink on surface2", "ink", "surface2", 4.5),
        ("ink_mid on surface", "ink_mid", "surface", 4.5),
        ("ink_mid on surface2", "ink_mid", "surface2", 4.5),
        ("ink_soft on surface", "ink_soft", "surface", 4.5),
        ("ink_soft on surface2", "ink_soft", "surface2", 4.5),
        ("ink_soft on ground", "ink_soft", "ground", 4.5),
        ("blue link on ground", "blue", "ground", 4.5),
        ("blue link on surface", "blue", "surface", 4.5),
        ("blue link on surface2", "blue", "surface2", 4.5),
        ("blue_deep on blue_wash (pill)", "blue_deep", "blue_wash", 4.5),
        ("dark button ink on blue", "#06122c", "blue", 4.5),
        ("risk tag", "risk", "risk_wash", 4.5),
        ("settled tag", "settled", "settled_wash", 4.5),
        ("focus ring vs ground", "blue", "ground", 3.0),
    ]),
    ("Idlery light", ID_LIGHT, [
        ("ink on ground", "ink", "ground", 4.5),
        ("ink on ground_tint", "ink", "ground_tint", 4.5),
        ("ink_mid on ground", "ink_mid", "ground", 4.5),
        ("ink_mid on ground_tint", "ink_mid", "ground_tint", 4.5),
        ("ink_soft on ground", "ink_soft", "ground", 4.5),
        ("ink_soft on ground_tint", "ink_soft", "ground_tint", 4.5),
        ("teal_ink link on ground", "teal_ink", "ground", 4.5),
        ("teal_ink link on ground_tint", "teal_ink", "ground_tint", 4.5),
        ("teal_ink eyebrow on ground_tint", "teal_ink", "ground_tint", 4.5),
        ("teal_ink on teal_wash (badge)", "teal_ink", "teal_wash", 4.5),
        ("white on teal_ink (button)", "#ffffff", "teal_ink", 4.5),
        ("wordmark teal on ground", "teal", "ground", 3.0),
        ("focus ring vs ground", "teal_ink", "ground", 3.0),
    ]),
    ("Idlery dark", ID_DARK, [
        ("ink on ground", "ink", "ground", 4.5),
        ("ink on surface", "ink", "surface", 4.5),
        ("ink_mid on ground", "ink_mid", "ground", 4.5),
        ("ink_mid on surface", "ink_mid", "surface", 4.5),
        ("ink_soft on ground", "ink_soft", "ground", 4.5),
        ("ink_soft on surface", "ink_soft", "surface", 4.5),
        ("teal_ink link on ground", "teal_ink", "ground", 4.5),
        ("teal_ink link on surface", "teal_ink", "surface", 4.5),
        ("teal_ink on teal_wash (badge)", "teal_ink", "teal_wash", 4.5),
        ("dark button ink on teal", "#062026", "teal", 4.5),
        ("wordmark teal on ground", "teal", "ground", 3.0),
        ("focus ring vs ground", "teal_ink", "ground", 3.0),
    ]),
]

fails = 0
for name, pal, pairs in CHECKS:
    print(f"\n=== {name} ===")
    for label, fg, bg, minimum in pairs:
        f = pal.get(fg, fg)
        b = pal.get(bg, bg)
        r = ratio(f, b)
        ok = r >= minimum
        if not ok:
            fails += 1
        print(f"  {'ok  ' if ok else 'FAIL'} {r:5.2f}:1  (min {minimum})  {label}")
print(f"\n{fails} failure(s)")
raise SystemExit(1 if fails else 0)
