#!/usr/bin/env python3
"""Delete image assets no page actually references, so nothing unused ships."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent

for site in ("sites/corecredit", "sites/idlery"):
    d = ROOT / site
    # Every text file that can name an image, the manifest included — scanning
    # only HTML/CSS/JS would let this delete an icon the manifest depends on.
    sources = [f for pattern in ("*.html", "*.css", "*.js", "*.webmanifest", "*.xml", "*.txt")
               for f in d.rglob(pattern)]
    text = "\n".join(f.read_text(encoding="utf-8") for f in sources)
    img_dir = d / "assets/img"
    removed = []
    for img in sorted(img_dir.iterdir()):
        if img.name not in text:
            img.unlink()
            removed.append(img.name)
    print(f"{site}: removed {len(removed)} unused image(s): {', '.join(removed) or 'none'}")
    print(f"{site}: kept {sorted(p.name for p in img_dir.iterdir())}")
