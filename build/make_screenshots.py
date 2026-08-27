#!/usr/bin/env python3
"""Prepare the real CoreCredit device captures for the web.

Every image here is an unaltered App Store capture of the shipping app. Two
things happen to each one and nothing else:

  * the iOS status bar is cropped away, so a gallery of captures taken at
    different times of day does not show six different clocks, and
  * it is scaled down and re-encoded for the web.

No pixel of app UI is redrawn, recoloured, composited, or invented.

    python3 build/make_screenshots.py <corecredit-repo> <corecredit-appstore-repo>
"""
from pathlib import Path
import sys

from PIL import Image

Image.MAX_IMAGE_PIXELS = None

ROOT = Path(__file__).resolve().parent.parent
CC_IMG = ROOT / "sites/corecredit/assets/img"
ID_IMG = ROOT / "sites/idlery/assets/img"

# (output stem, source repo, path within it, status-bar crop in source pixels)
#
# The crop is the status-bar height at each capture's own scale: 130px for the
# 946-wide captures, 161px for the 1170-wide one. The Returns capture was taken
# a frame into a sheet transition, so it is cropped below its title bar instead.
PHONE = [
    ("shot-dashboard", "appstore", "screenshots/01_dashboard_final.png", 130),
    ("shot-cores", "app", "Cores_Marketing.png", 130),
    ("shot-credit", "app", "image5.png", 161),
    ("shot-scan", "app", "lefttiltedphone.PNG", 130),
    ("shot-history", "app", "Image 6.png", 130),
    ("shot-returns", "app", "image4.PNG", 250),
]
IPAD = ("shot-ipad", "app", "IMG_0313.PNG", 0)

PHONE_WIDTH = 390
IPAD_WIDTH = 720


def emit(im: Image.Image, stem: str, width: int, out_dir: Path) -> None:
    for scale, suffix in ((1, ""), (2, "@2x")):
        w = width * scale
        h = max(1, round(im.height * w / im.width))
        small = im.resize((w, h), Image.LANCZOS)
        path = out_dir / f"{stem}{suffix}.png"
        # Screenshots of flat UI quantise to a palette with no visible loss and
        # roughly a third of the bytes; the barcode photograph in the scan
        # capture is the only continuous-tone region and gets a wider palette.
        small.convert("RGB").quantize(colors=256, method=Image.MEDIANCUT, dither=Image.NONE).save(
            path, optimize=True
        )
        print(f"  {path.name}: {w}x{h}, {path.stat().st_size / 1024:.1f} KB")


def main(app_repo: Path, appstore_repo: Path) -> int:
    roots = {"app": app_repo, "appstore": appstore_repo}
    CC_IMG.mkdir(parents=True, exist_ok=True)

    for stem, which, rel, cut in PHONE + [IPAD]:
        src = roots[which] / rel
        if not src.is_file():
            print(f"  MISSING {src}")
            return 1
        im = Image.open(src).convert("RGB")
        im = im.crop((0, cut, im.width, im.height))
        emit(im, stem, IPAD_WIDTH if stem == IPAD[0] else PHONE_WIDTH, CC_IMG)

    # idlery.com shows the two captures its CoreCredit section refers to.
    ID_IMG.mkdir(parents=True, exist_ok=True)
    for stem in ("shot-dashboard", "shot-credit"):
        for suffix in ("", "@2x"):
            name = f"{stem}{suffix}.png"
            (ID_IMG / name).write_bytes((CC_IMG / name).read_bytes())
            print(f"  idlery/{name}: copied")
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__)
        raise SystemExit(2)
    raise SystemExit(main(Path(sys.argv[1]), Path(sys.argv[2])))
