#!/usr/bin/env python3
"""Generate the App Store QR code as a self-contained SVG, and prove it decodes.

The SVG is written from the QR matrix directly — one <rect> per run of dark
modules — so it stays a few kilobytes, scales without blurring, and carries no
external reference. Verification rasterises the *written file* and decodes it,
rather than trusting the encoder.
"""
from pathlib import Path
import sys

import segno

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "sites/corecredit/assets/img/appstore-qr.svg"
URL = "https://apps.apple.com/app/corecredit-core-return-ledger/id6802336957"

QUIET = 4  # modules of quiet zone; the QR specification requires at least 4


def build(url: str) -> tuple[str, int]:
    qr = segno.make(url, error="m")
    matrix = [[bool(m) for m in row] for row in qr.matrix]
    n = len(matrix)
    side = n + QUIET * 2

    rects = []
    for y, row in enumerate(matrix):
        x = 0
        while x < n:
            if not row[x]:
                x += 1
                continue
            run = x
            while run < n and row[run]:
                run += 1
            rects.append(f'<rect x="{x + QUIET}" y="{y + QUIET}" width="{run - x}" height="1"/>')
            x = run

    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {side} {side}" '
        f'width="{side * 4}" height="{side * 4}" role="img" '
        f'aria-label="QR code linking to the CoreCredit listing on the App Store">'
        f'<rect width="{side}" height="{side}" fill="#ffffff"/>'
        f'<g fill="#0b1220" shape-rendering="crispEdges">{"".join(rects)}</g>'
        "</svg>"
    )
    return svg, side


def verify(svg_path: Path, expected: str) -> bool:
    """Rasterise the written SVG in headless Chromium and decode the result."""
    import os
    import subprocess
    import tempfile

    import cv2

    with tempfile.TemporaryDirectory() as tmp:
        png = Path(tmp) / "qr.png"
        # A directory that resolves the globally installed Playwright.
        work = Path("/home/user/.webtools")
        script = work / "qr-shot.mjs"
        script.write_text(
            "import { chromium } from 'playwright';\n"
            "const b = await chromium.launch();\n"
            "const p = await b.newPage({ viewport: { width: 640, height: 640 } });\n"
            f"await p.goto('file://{svg_path}');\n"
            f"await p.screenshot({{ path: '{png}' }});\n"
            "await b.close();\n"
        )
        r = subprocess.run(["node", str(script)], capture_output=True, text=True,
                           cwd=str(work), env=dict(os.environ))
        if r.returncode != 0:
            print("  rasterisation failed:", r.stderr.strip()[:400])
            return False
        image = cv2.imread(str(png))
        decoded, *_ = cv2.QRCodeDetector().detectAndDecode(image)

    if decoded == expected:
        print(f"  decoded from the rendered SVG: {decoded}")
        return True
    print(f"  DECODE MISMATCH: got {decoded!r}, expected {expected!r}")
    return False


if __name__ == "__main__":
    svg, side = build(URL)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(svg, encoding="utf-8")
    print(f"  {OUT.name}: {side}x{side} modules, {OUT.stat().st_size} bytes")
    sys.exit(0 if verify(OUT.resolve(), URL) else 1)
