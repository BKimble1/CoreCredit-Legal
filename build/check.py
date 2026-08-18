#!/usr/bin/env python3
"""Structural checks over the built sites: parse every page, verify every local
reference resolves, and report anything a browser would silently tolerate."""
from html.parser import HTMLParser
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
VOID = {"area","base","br","col","embed","hr","img","input","link","meta","param","source","track","wbr"}


class Checker(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.refs = []       # (attr, value)
        self.ids = set()
        self.problems = []
        self.headings = []
        self.imgs = []
        self.title = None
        self._in_title = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "id" in a:
            if a["id"] in self.ids:
                self.problems.append(f"duplicate id: {a['id']}")
            self.ids.add(a["id"])
        for key in ("href", "src"):
            if key in a:
                self.refs.append((tag, a[key]))
        if "srcset" in a:
            for part in a["srcset"].split(","):
                url = part.strip().split(" ")[0]
                if url:
                    self.refs.append((tag, url))
        if tag == "img":
            self.imgs.append(a)
        if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self.headings.append(int(tag[1]))
        if tag == "title":
            self._in_title = True
        if tag not in VOID:
            self.stack.append(tag)

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False
        if tag in VOID:
            return
        if not self.stack:
            self.problems.append(f"stray </{tag}>")
            return
        if self.stack[-1] != tag:
            self.problems.append(f"mismatched </{tag}> (open: {self.stack[-1]})")
            while self.stack and self.stack[-1] != tag:
                self.stack.pop()
            if self.stack:
                self.stack.pop()
        else:
            self.stack.pop()

    def handle_data(self, data):
        if self._in_title:
            self.title = (self.title or "") + data


def check_site(site: Path, label: str):
    print(f"\n=== {label} ===")
    pages = sorted(site.rglob("*.html"))
    fail = 0
    page_ids = {}
    for page in pages:
        c = Checker()
        c.feed(page.read_text(encoding="utf-8"))
        rel = page.relative_to(site)
        page_ids[("/" + str(rel.parent).replace("\\", "/")).replace("/.", "/")] = c.ids
        if c.stack:
            c.problems.append(f"unclosed tags: {c.stack}")
        if not c.title:
            c.problems.append("no <title>")
        # heading order
        prev = 0
        for h in c.headings:
            if prev and h > prev + 1:
                c.problems.append(f"heading jump h{prev} -> h{h}")
            prev = h
        if c.headings.count(1) != 1:
            c.problems.append(f"expected exactly one <h1>, found {c.headings.count(1)}")
        # images
        for img in c.imgs:
            if "alt" not in img:
                c.problems.append(f"img without alt: {img.get('src')}")
            if not (img.get("width") and img.get("height")):
                c.problems.append(f"img without width/height: {img.get('src')}")
        # local references resolve
        for tag, ref in c.refs:
            if ref.startswith(("http://", "https://", "mailto:", "tel:", "data:")):
                continue
            if ref.startswith("#"):
                if ref[1:] and ref[1:] not in c.ids:
                    c.problems.append(f"anchor not found on page: {ref}")
                continue
            path, _, frag = ref.partition("#")
            if not path:
                continue
            target = (site / path.lstrip("/")) if path.startswith("/") else (page.parent / path)
            resolved = None
            for cand in (target, target / "index.html", target.with_suffix(".html")):
                if cand.is_file():
                    resolved = cand
                    break
            if resolved is None:
                c.problems.append(f"broken local {tag} reference: {ref}")
            elif frag:
                body = resolved.read_text(encoding="utf-8")
                if f'id="{frag}"' not in body:
                    c.problems.append(f"fragment not found in {path}: #{frag}")
        status = "ok " if not c.problems else "FAIL"
        print(f"  [{status}] {rel}")
        for p in c.problems:
            print(f"          - {p}")
            fail += 1
    return fail


total = check_site(ROOT / "sites/corecredit", "corecredit.idlery.com")
total += check_site(ROOT / "sites/idlery", "idlery.com")
print(f"\n{total} problem(s)")
sys.exit(1 if total else 0)
