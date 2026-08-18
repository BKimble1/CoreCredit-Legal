#!/usr/bin/env python3
"""Build the two drag-and-drop Netlify archives.

Each archive holds the deployable site and nothing else: index.html sits at the
archive root, and development files, VCS history, caches, source maps and OS
metadata are excluded by construction (only the sites/ trees are ever copied).
"""
from pathlib import Path
import shutil
import zipfile

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"

EXCLUDE_NAMES = {".DS_Store", "Thumbs.db", "desktop.ini", "__MACOSX", ".git", ".gitignore",
                 "node_modules", ".cache", ".netlify"}
EXCLUDE_SUFFIXES = {".map", ".zip", ".docx", ".pyc", ".log", ".bak", ".orig"}


def keep(path: Path) -> bool:
    if any(part in EXCLUDE_NAMES for part in path.parts):
        return False
    if path.suffix.lower() in EXCLUDE_SUFFIXES:
        return False
    if path.name.startswith("._"):
        return False
    return True


def build(site: str, archive: str) -> Path:
    src = ROOT / "sites" / site
    out = DIST / archive
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)

    files = []
    for path in sorted(src.rglob("*")):
        if path.is_dir() or not keep(path.relative_to(src)):
            continue
        rel = path.relative_to(src)
        dest = out / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, dest)
        files.append(rel.as_posix())

    zip_path = DIST / f"{archive}.zip"
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for rel in files:
            # deterministic timestamps keep the archive reproducible
            info = zipfile.ZipInfo(rel, date_time=(2026, 8, 18, 12, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            z.writestr(info, (out / rel).read_bytes())

    size = zip_path.stat().st_size
    print(f"{zip_path.name}: {len(files)} files, {size / 1024:.1f} KB")
    return zip_path


def verify(zip_path: Path):
    with zipfile.ZipFile(zip_path) as z:
        names = z.namelist()
        bad = z.testzip()
    problems = []
    if "index.html" not in names:
        problems.append("index.html is NOT at the archive root")
    if bad:
        problems.append(f"corrupt entry: {bad}")
    for n in names:
        if n.startswith("/") or ".." in n.split("/"):
            problems.append(f"unsafe path: {n}")
        if any(part in EXCLUDE_NAMES for part in n.split("/")):
            problems.append(f"excluded item present: {n}")
    print(f"  root index.html: {'yes' if 'index.html' in names else 'NO'}")
    print(f"  entries: {', '.join(sorted(names))}")
    if problems:
        for p in problems:
            print(f"  PROBLEM: {p}")
    return problems


if __name__ == "__main__":
    DIST.mkdir(exist_ok=True)
    issues = []
    for site, archive in (("idlery", "idlery-netlify"), ("corecredit", "corecredit-netlify")):
        z = build(site, archive)
        issues += verify(z)
    print(f"\n{len(issues)} packaging problem(s)")
    raise SystemExit(1 if issues else 0)
