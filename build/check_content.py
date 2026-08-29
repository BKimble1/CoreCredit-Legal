#!/usr/bin/env python3
"""Content and metadata checks over both sites.

Structure is `build/check.py`'s job; this one is about what the pages *say* and
what they point at: no stale launch language, one App Store URL and one App
Store ID, valid JSON-LD, a canonical and a social card on every page, and every
address in `_redirects` and `sitemap.xml` pointing at something real.
"""
from html.parser import HTMLParser
from pathlib import Path
import json
import re
import sys

ROOT = Path(__file__).resolve().parent.parent
SITES = {
    "idlery.com": (ROOT / "sites/idlery", "https://idlery.com"),
    "corecredit.idlery.com": (ROOT / "sites/corecredit", "https://corecredit.idlery.com"),
}

APP_ID = "6802336957"
APP_STORE_URL = f"https://apps.apple.com/app/corecredit-core-return-ledger/id{APP_ID}"

# Phrases that must not survive the launch, and stand-ins that must never ship.
FORBIDDEN = [
    r"coming soon",
    r"pre-?order",
    r"waitlist",
    r"\bexample\.com\b",
    r"\bexample\.org\b",
    r"\bTODO\b",
    r"\bFIXME\b",
    r"lorem ipsum",
    r"\bplaceholder\b",
    r"your-?email@",
    r"\bXXX\b",
    r"not yet available",
    r"launching soon",
]

# Every off-site host either site is allowed to link to.
ALLOWED_HOSTS = {"idlery.com", "corecredit.idlery.com", "apps.apple.com", "schema.org", "www.w3.org"}

problems = []


def fail(where, msg):
    problems.append(f"{where}: {msg}")


class Meta(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.meta = {}
        self.links = {}
        self.hrefs = []
        self.jsonld = []
        self._ld = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "meta":
            key = a.get("name") or a.get("property")
            if key:
                self.meta.setdefault(key, []).append(a.get("content", ""))
        elif tag == "link":
            self.links.setdefault(a.get("rel", ""), []).append(a.get("href", ""))
        elif tag == "a" and "href" in a:
            self.hrefs.append((a["href"], a.get("target"), a.get("rel")))
        elif tag == "script" and a.get("type") == "application/ld+json":
            self._ld = True

    def handle_endtag(self, tag):
        if tag == "script":
            self._ld = False

    def handle_data(self, data):
        if self._ld:
            self.jsonld.append(data)


def walk_json(node, visit):
    if isinstance(node, dict):
        for k, v in node.items():
            visit(k, v)
            walk_json(v, visit)
    elif isinstance(node, list):
        for v in node:
            walk_json(v, visit)


for label, (root, origin) in SITES.items():
    print(f"\n=== {label} ===")
    for page in sorted(root.rglob("*.html")):
        rel = "/" + str(page.relative_to(root)).replace("\\", "/")
        text = page.read_text(encoding="utf-8")
        where = f"{label}{rel}"

        for pattern in FORBIDDEN:
            for m in re.finditer(pattern, text, re.I):
                line = text[: m.start()].count("\n") + 1
                fail(where, f"forbidden phrase {m.group(0)!r} on line {line}")

        # Every App Store reference is the one listing.
        for m in re.finditer(r"https://apps\.apple\.com/\S*?(?=[\"'\s<])", text):
            if m.group(0) != APP_STORE_URL:
                fail(where, f"unexpected App Store URL: {m.group(0)}")
        for m in re.finditer(r"\bid(\d{9,10})\b", text):
            if m.group(1) != APP_ID:
                fail(where, f"unexpected App Store ID: {m.group(1)}")

        p = Meta()
        p.feed(text)

        is404 = rel.endswith("404.html")
        if not is404:
            canonical = p.links.get("canonical", [])
            if len(canonical) != 1:
                fail(where, f"expected exactly one canonical link, found {len(canonical)}")
            else:
                expected = origin + ("/" if rel == "/index.html" else rel.replace("/index.html", ""))
                if canonical[0] != expected:
                    fail(where, f"canonical is {canonical[0]}, expected {expected}")
            for key in ("description", "og:title", "og:description", "og:image", "og:url",
                        "og:image:width", "og:image:height", "og:image:alt", "twitter:card"):
                if key not in p.meta:
                    fail(where, f"missing <meta> {key}")
            if p.meta.get("og:url", [""])[0] != (canonical[0] if canonical else ""):
                fail(where, "og:url does not match the canonical URL")
        else:
            if "noindex" not in " ".join(p.meta.get("robots", [])):
                fail(where, "404 page is not marked noindex")

        if "icon" not in p.links:
            fail(where, "no favicon link")
        if "apple-touch-icon" not in p.links:
            fail(where, "no apple-touch-icon link")
        if p.links.get("manifest") != ["/site.webmanifest"]:
            fail(where, f"manifest link is {p.links.get('manifest')}, expected ['/site.webmanifest']")
        if "og:locale" not in p.meta and not is404:
            fail(where, "missing <meta> og:locale")

        # The Smart App Banner belongs on the product site only.
        banner = p.meta.get("apple-itunes-app", [])
        if label == "corecredit.idlery.com":
            if banner != [f"app-id={APP_ID}"]:
                fail(where, f"Smart App Banner is {banner}, expected ['app-id={APP_ID}']")
        elif banner:
            fail(where, "Smart App Banner on the company site, where it does not belong")

        for raw in p.jsonld:
            try:
                data = json.loads(raw)
            except json.JSONDecodeError as e:
                fail(where, f"JSON-LD does not parse: {e}")
                continue
            if data.get("@context") != "https://schema.org":
                fail(where, "JSON-LD @context is not https://schema.org")
            types = []
            walk_json(data, lambda k, v: types.append(v) if k == "@type" else None)
            if not types:
                fail(where, "JSON-LD declares no @type")
            bad = []
            walk_json(
                data,
                lambda k, v: bad.append(v)
                if isinstance(v, str) and v.startswith("http://")
                else None,
            )
            for b in bad:
                fail(where, f"JSON-LD carries a plain-http URL: {b}")

        for href, target, rel_attr in p.hrefs:
            if href.startswith("mailto:"):
                if href != "mailto:support@idlery.com":
                    fail(where, f"unexpected mail address: {href}")
                continue
            if not href.startswith("http"):
                continue
            host = href.split("/")[2]
            if host not in ALLOWED_HOSTS:
                fail(where, f"link to an unexpected host: {href}")
            if target == "_blank" and (not rel_attr or "noopener" not in rel_attr):
                fail(where, f'target="_blank" without rel="noopener": {href}')

    # The web app manifest: valid JSON, and every icon it names must exist at
    # exactly the size it claims. A wrong `sizes` is silent — the browser simply
    # picks a different icon, or none.
    manifest = root / "site.webmanifest"
    if not manifest.is_file():
        fail(label, "no site.webmanifest, but the pages link one")
    else:
        try:
            data = json.loads(manifest.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            fail(f"{label}/site.webmanifest", f"does not parse: {e}")
            data = None
        if data is not None:
            for key in ("name", "short_name", "start_url", "scope", "icons", "theme_color"):
                if key not in data:
                    fail(f"{label}/site.webmanifest", f"missing key: {key}")
            if not re.fullmatch(r"#[0-9a-fA-F]{6}", str(data.get("theme_color", ""))):
                fail(f"{label}/site.webmanifest", f"theme_color is not a 6-digit hex: {data.get('theme_color')}")
            for icon in data.get("icons", []):
                src = icon.get("src", "")
                target = root / src.lstrip("/")
                if not target.is_file():
                    fail(f"{label}/site.webmanifest", f"icon does not exist: {src}")
                    continue
                with target.open("rb") as fh:
                    head = fh.read(26)
                if head[:8] == b"\x89PNG\r\n\x1a\n":
                    import struct
                    w, h = struct.unpack(">II", head[16:24])
                    if icon.get("sizes") != f"{w}x{h}":
                        fail(f"{label}/site.webmanifest",
                             f"{src} is {w}x{h} but the manifest says {icon.get('sizes')}")
            print("  [ok ] site.webmanifest icons exist at the sizes declared")

    # Redirect targets and sitemap entries must point at something real.
    redirects = root / "_redirects"
    if redirects.is_file():
        for line in redirects.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) < 2:
                fail(f"{label}/_redirects", f"malformed rule: {line}")
                continue
            source, dest = parts[0], parts[1]
            forced = any(part.endswith("!") for part in parts[2:])
            if (source.startswith("/") and not source.startswith("/*")
                    and "*" not in source and not forced):
                target = root / source.lstrip("/")
                if target.is_file() or (target / "index.html").is_file():
                    fail(f"{label}/_redirects",
                         f"{source} is redirected but also exists as a file, and the rule is not "
                         f"forced with `!`, so the file wins and the redirect never runs")
            if dest.startswith("/") and not dest.startswith("/#") and "*" not in dest:
                target = root / dest.lstrip("/")
                if not (target.is_file() or (target / "index.html").is_file()):
                    fail(f"{label}/_redirects", f"{source} redirects to a missing page: {dest}")
        print("  [ok ] _redirects targets resolve")

    sitemap = root / "sitemap.xml"
    if sitemap.is_file():
        for loc in re.findall(r"<loc>(.*?)</loc>", sitemap.read_text(encoding="utf-8")):
            if not loc.startswith(origin):
                fail(f"{label}/sitemap.xml", f"{loc} is not on {origin}")
                continue
            path = loc[len(origin):].strip("/")
            target = root / path if path else root
            if not ((target / "index.html").is_file() or target.is_file()):
                fail(f"{label}/sitemap.xml", f"{loc} has no page behind it")
        print("  [ok ] sitemap entries resolve")

    # Nothing in the CSS may reach off-site: the CSP would block it anyway.
    for css in root.rglob("*.css"):
        for url in re.findall(r"url\(([^)]*)\)", css.read_text(encoding="utf-8")):
            if "//" in url:
                fail(f"{label}/{css.name}", f"external url() in CSS: {url}")
    print("  [ok ] no external references in CSS")

# The App Store QR code has to encode exactly the listing the buttons point at.
qr = ROOT / "sites/corecredit/assets/img/appstore-qr.svg"
if qr.is_file():
    index = (ROOT / "sites/corecredit/index.html").read_text(encoding="utf-8")
    if "appstore-qr.svg" not in index:
        fail("corecredit.idlery.com", "the QR code asset ships but no page uses it")
    print("  [ok ] QR asset is referenced (decoded end-to-end by build/make_qr.py)")

print()
for p in problems:
    print(f"  FAIL {p}")
print(f"{len(problems)} problem(s)")
sys.exit(1 if problems else 0)
