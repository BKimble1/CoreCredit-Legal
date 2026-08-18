#!/usr/bin/env python3
"""Delete image assets no page actually references, so nothing unused ships."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent

for site in ("sites/corecredit", "sites/idlery"):
    d = ROOT / site
    text = "\n".join(
        f.read_text(encoding="utf-8")
        for f in list(d.rglob("*.html")) + list(d.rglob("*.css")) + list(d.rglob("*.js"))
    )
    img_dir = d / "assets/img"
    removed = []
    for img in sorted(img_dir.iterdir()):
        if img.name not in text:
            img.unlink()
            removed.append(img.name)
    print(f"{site}: removed {len(removed)} unused image(s): {', '.join(removed) or 'none'}")
    print(f"{site}: kept {sorted(p.name for p in img_dir.iterdir())}")
