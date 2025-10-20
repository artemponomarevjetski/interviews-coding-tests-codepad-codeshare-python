#!/usr/bin/env python3
"""
dedupe_suffixes.py — Canonicalize files that have copy‑number suffixes.

Find groups like:
  - "report.pdf", "report (1).pdf", "report (2).pdf"
  - "photo.jpg",  "photo 2.jpg",   "photo 3.jpg"
Ensure the canonical base ("report.pdf"/"photo.jpg") holds the newest content,
remove exact duplicates, and keep different versions.

Winner policy (per dir, per (stem, ext)):
  1) Newer mtime wins; 2) larger size ties; 3) prefer base name.

Actions (printed in dry‑run):
  - RENAME_TO_BASE         base missing → rename winner to base
  - OVERWRITE_BASE         base exists → replace base with winner’s bytes
  - REMOVE_DUP_IDENTICAL   delete/trash files byte‑identical to winner
  - KEEP_DIFFERENT         leave differing versions

Safety:
  - DRY RUN BY DEFAULT (prints plan). Use --apply to make changes.
  - With --trash, deletions go to "<root>/.dedupe-trash" (timestamped).

Patterns matched:
  - "name (N).ext"  (Finder/Chrome)
  - "name N.ext"    (alternate)
Canonical base: "name.ext". The “name” may include spaces/parentheses.

Fast mode:
  - --fast uses sampled comparison (first/middle/last chunks) to avoid
    reading whole large files; much faster with a tiny risk of false positives.
  - --skip-ext and --max-size let you *treat* huge/specified files as
    different (so they are never deleted in dry‑run).

VCS data:
  - Skips anything inside ".git" directories and files starting with ".git"
    (e.g., .gitignore, .gitattributes).

Examples:
  python3 dedupe_suffixes.py --root ~/Desktop/TetraMem                  # dry-run
  python3 dedupe_suffixes.py --root ~/Desktop/TetraMem --fast           # faster dry-run
  python3 dedupe_suffixes.py --root ~/Downloads --apply --trash --fast  # apply
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import time
from pathlib import Path

# Read buffer for exact byte‑wise comparison (1 MiB).
READ_CHUNK = 1024 * 1024

# VCS exclusions
GIT_DIRS = {".git"}
GIT_FILE_PREFIXES = (".git",)


def is_git_related(p: Path) -> bool:
    """Return True if path is inside a .git dir or filename starts with '.git'."""
    return any(part in GIT_DIRS for part in p.parts) or p.name.startswith(GIT_FILE_PREFIXES)


def iter_files(root: Path, recursive: bool):
    """Yield files under root, skipping .git dirs and .git* files."""
    if not recursive:
        for p in root.iterdir():
            if p.is_file() and not is_git_related(p):
                yield p
        return

    for dirpath, dirnames, filenames in os.walk(root):
        # prevent descending into .git
        dirnames[:] = [d for d in dirnames if d not in GIT_DIRS]
        for name in filenames:
            p = Path(dirpath) / name
            if not is_git_related(p):
                yield p


# Match either "name (N).ext" OR "name N.ext".
SUFFIX_RE = re.compile(
    r'^(?P<stem>.+?)\s+(?:\((?P<num1>\d+)\)|(?P<num2>\d+))(?P<ext>\.[^.]+)?$'
)


def same_file(a: Path, b: Path) -> bool:
    """Return True iff files are byte‑identical (exact, full read)."""
    try:
        if a.stat().st_size != b.stat().st_size:
            return False
    except FileNotFoundError:
        return False

    with a.open("rb") as fa, b.open("rb") as fb:
        while True:
            ba = fa.read(READ_CHUNK)
            bb = fb.read(READ_CHUNK)
            if ba != bb:
                return False
            if not ba:  # EOF on both
                return True


def same_file_sampled(a: Path, b: Path, sample: int = 256 * 1024) -> bool:
    """
    Heuristic: compare first/middle/last 'sample' bytes. Much faster for big files.
    Exact for small files (< 3*sample). Returns False if sizes differ.
    """
    try:
        sa = a.stat()
        sb = b.stat()
    except FileNotFoundError:
        return False
    if sa.st_size != sb.st_size:
        return False
    size = sa.st_size
    if size == 0:
        return True
    if size <= sample * 3:
        return same_file(a, b)

    with a.open("rb") as fa, b.open("rb") as fb:
        # start
        fa.seek(0); fb.seek(0)
        if fa.read(sample) != fb.read(sample):
            return False
        # middle
        mid = max(0, (size // 2) - (sample // 2))
        fa.seek(mid); fb.seek(mid)
        if fa.read(sample) != fb.read(sample):
            return False
        # end
        end = max(0, size - sample)
        fa.seek(end); fb.seek(end)
        if fa.read(sample) != fb.read(sample):
            return False
    return True


def move_replace(src: Path, dst: Path) -> None:
    """Atomically move/replace 'src' to 'dst', creating parent dirs."""
    dst.parent.mkdir(parents=True, exist_ok=True)
    os.replace(src, dst)


def to_trash(p: Path, trash_root: Path) -> Path:
    """Move 'p' to trash_root with timestamped suffix; return final path."""
    trash_root.mkdir(parents=True, exist_ok=True)
    ts = time.strftime("%Y%m%d-%H%M%S")
    out = trash_root / f"{p.name}.{ts}"
    i = 0
    while out.exists():
        i += 1
        out = trash_root / f"{p.name}.{ts}.{i}"
    shutil.move(str(p), str(out))
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="Dedupe '(n)' and ' n' suffixed files by ensuring base names "
                    "hold the newest content and removing exact duplicates."
    )
    ap.add_argument("--root", default=".", help="Root folder to scan (default: .)")
    ap.add_argument("--apply", action="store_true",
                    help="Apply changes (default: dry run).")
    ap.add_argument("--trash", action="store_true",
                    help="Move deletions to <root>/.dedupe-trash.")
    ap.add_argument("--recursive", action="store_true", default=True,
                    help="Scan subdirectories (default: on).")

    # Performance/heuristics
    ap.add_argument("--fast", action="store_true",
                    help="Use sampled comparison (first/middle/last chunks).")
    ap.add_argument("--sample", type=int, default=256 * 1024,
                    help="Sample size in bytes for --fast (default: 262144).")
    ap.add_argument("--max-size", type=int, default=None,
                    help="Skip byte compares for files larger than this many MiB "
                         "(treat as different; they will NOT be deleted).")
    ap.add_argument("--skip-ext", action="append", default=[],
                    help="Never byte-compare these extensions (e.g., --skip-ext .zip).")
    ap.add_argument("--verbose", action="store_true",
                    help="Print each group being processed.")
    args = ap.parse_args(argv)

    root = Path(args.root).resolve()
    trash_root = root / ".dedupe-trash"
    skip_exts = {e.lower() for e in args.skip_ext}
    max_bytes = None if args.max_size is None else args.max_size * 1024 * 1024

    # Build groups keyed by (directory, stem, ext).
    groups: dict[tuple[Path, str, str], set[Path]] = {}
    for p in iter_files(root, args.recursive):
        if not p.is_file():
            continue
        m = SUFFIX_RE.match(p.name)
        if not m:
            continue
        stem = m.group("stem")
        ext = (m.group("ext") or "")
        base = p.with_name(stem + ext)
        key = (p.parent, stem, ext)
        s = groups.setdefault(key, set())
        s.add(p)
        if base.exists():
            s.add(base)

    # Decide actions per group.
    actions: list[tuple[str, Path, Path | None]] = []
    for (parent, stem, ext), paths in sorted(groups.items()):
        paths = sorted(paths)
        base = parent / (stem + ext)
        if args.verbose:
            print(f"[GROUP] {parent} :: '{stem}{ext}' ({len(paths)} files)")

        # Winner: newer mtime, then larger size, then prefer base path.
        def score(p: Path):
            st = p.stat()
            return (st.st_mtime_ns, st.st_size, 2 if p == base else 1)

        winner = max(paths, key=score)

        # Ensure base ends up holding the winner bytes.
        if base.exists() and winner != base:
            actions.append(("OVERWRITE_BASE", winner, base))
        elif not base.exists():
            actions.append(("RENAME_TO_BASE", winner, base))

        # Others: remove exact duplicates of winner; keep different ones.
        for p in paths:
            if p == winner or p == base:
                continue

            # Heuristics to avoid heavy reads
            if (max_bytes is not None and p.stat().st_size > max_bytes) or \
               (p.suffix.lower() in skip_exts or winner.suffix.lower() in skip_exts):
                actions.append(("KEEP_DIFFERENT", p, None))
                continue

            identical = (same_file_sampled(p, winner, args.sample)
                         if args.fast else same_file(p, winner))

            if identical:
                actions.append(("REMOVE_DUP_IDENTICAL", p, None))
            else:
                actions.append(("KEEP_DIFFERENT", p, None))

    # Execute / print the plan.
    dry = not args.apply
    for kind, src, dst in actions:
        if kind == "OVERWRITE_BASE":
            print(f"{'WOULD' if dry else 'DO'} REPLACE: {dst} <-- {src}")
            if not dry:
                move_replace(src, dst)
        elif kind == "RENAME_TO_BASE":
            print(f"{'WOULD' if dry else 'DO'} RENAME:  {src} -> {dst}")
            if not dry:
                move_replace(src, dst)
        elif kind == "REMOVE_DUP_IDENTICAL":
            if args.trash:
                print(f"{'WOULD' if dry else 'DO'} TRASH:   {src}")
                if not dry:
                    to_trash(src, trash_root)
            else:
                print(f"{'WOULD' if dry else 'DO'} DELETE:  {src}")
                if not dry:
                    try:
                        src.unlink()
                    except FileNotFoundError:
                        pass
        elif kind == "KEEP_DIFFERENT":
            print(f"SKIP (different content): {src}")

    # Summary.
    counts: dict[str, int] = {}
    for k, _, _ in actions:
        counts[k] = counts.get(k, 0) + 1
    print("Summary:", " ".join(f"{k}={v}" for k, v in sorted(counts.items())))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
