#!/usr/bin/env python3
"""Inject shared HTML partials into the static pages, in place.

The pages in sites/ are always complete, deployable HTML. This script only keeps the
repeated header/footer blocks identical across them; it is an authoring aid, not a
build step the sites depend on.
"""
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parent.parent
PARTIALS = Path(__file__).resolve().parent / "partials"


def inject(page: Path, marker: str, partial: str) -> bool:
    html = page.read_text(encoding="utf-8")
    body = (PARTIALS / partial).read_text(encoding="utf-8").rstrip("\n")
    start = f"<!-- {marker}:start -->"
    end = f"<!-- {marker}:end -->"
    block = f"{start}\n{body}\n{end}"
    placeholder = f"<!-- {marker} -->"

    if placeholder in html:
        new = html.replace(placeholder, block)
    else:
        pattern = re.compile(re.escape(start) + r".*?" + re.escape(end), re.S)
        if not pattern.search(html):
            return False
        new = pattern.sub(lambda _: block, html)

    if new != html:
        page.write_text(new, encoding="utf-8")
        return True
    return False


def main() -> int:
    jobs = [
        ("sites/corecredit", "SITE-FOOTER", "cc-footer.html"),
        ("sites/idlery", "SITE-HEADER", "idlery-header.html"),
        ("sites/idlery", "SITE-FOOTER", "idlery-footer.html"),
    ]
    touched = 0
    for folder, marker, partial in jobs:
        if not (PARTIALS / partial).exists():
            continue
        for page in sorted((ROOT / folder).rglob("*.html")):
            if inject(page, marker, partial):
                print(f"  updated {page.relative_to(ROOT)}  [{marker}]")
                touched += 1
    print(f"{touched} file(s) updated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
