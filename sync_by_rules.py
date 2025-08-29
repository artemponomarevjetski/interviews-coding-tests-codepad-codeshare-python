#!/usr/bin/env python3

"""
Sync files from SRC to DST using rules:

1) If filename exists in both places: newer timestamp wins.
2) If timestamps tie: larger file wins.
3) If the winner is the source -> overwrite/move into target.
4) If the winner is the target -> leave target as-is; optionally delete or trash the older source copy.
5) If filename exists only in source -> move (no conflict).

By default compares only top-level files (non-recursive) and ignores hidden dotfiles.
Use flags to tweak.

Examples:
  Dry-run (default):   python3 sync_by_rules.py --src . --dst .. --dry-run
  Apply safely:        python3 sync_by_rules.py --src . --dst .. --apply
  Apply & delete olds: python3 sync_by_rules.py --src . --dst .. --apply --delete-older-source
  Include dotfiles:    python3 sync_by_rules.py --include-hidden
  Recursive:           python3 sync_by_rules.py --recursive

Exit codes: 0 OK, non-zero on failures.
"""
from __future__ import annotations

import argparse
import csv
import errno
import os
import shutil
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

@dataclass(frozen=True)
class FileInfo:
    path: Path
    name: str
    size: int
    mtime_ns: int

def is_hidden(p: Path) -> bool:
    return p.name.startswith(".")

def scan(dirpath: Path, recursive: bool, include_hidden: bool) -> Dict[str, FileInfo]:
    files: Dict[str, FileInfo] = {}
    if recursive:
        it = dirpath.rglob("*")
    else:
        it = dirpath.glob("*")
    for p in it:
        if not p.is_file():
            continue
        if not include_hidden and is_hidden(p):
            continue
        # Only compare by filename (basename), ignoring subdir structure for conflicts.
        name = p.name
        try:
            st = p.stat()
        except FileNotFoundError:
            # Race condition; skip
            continue
        files[name] = FileInfo(path=p, name=name, size=st.st_size, mtime_ns=st.st_mtime_ns)
    return files

@dataclass
class Action:
    kind: str        # MOVE | OVERWRITE | SKIP | DELETE
    reason: str
    src: Optional[Path] = None
    dst: Optional[Path] = None

def format_line(prefix: str, a: Action, src_root: Path, dst_root: Path) -> str:
    def rel(p: Optional[Path], root: Path) -> str:
        if p is None:
            return ""
        try:
            return "./" + str(p.relative_to(root).as_posix())
        except Exception:
            # Fallback: show basename if not relative
            return "./" + p.name if root in p.parents else str(p)
    if a.kind in ("MOVE", "OVERWRITE"):
        return f'{prefix} {a.kind} ({a.reason}): {rel(a.src, src_root)} -> {rel(a.dst, dst_root)}'
    elif a.kind == "DELETE":
        return f'{prefix} DELETE ({a.reason}): {rel(a.src, src_root)}'
    elif a.kind == "SKIP":
        return f'{prefix} SKIP ({a.reason}): {rel(a.src, src_root)} (keeping {rel(a.dst, dst_root).replace("./","../",1)})'
    else:
        return f'{prefix} {a.kind} ({a.reason})'

def plan_actions(
    src_dir: Path,
    dst_dir: Path,
    recursive: bool = False,
    include_hidden: bool = False,
    delete_older_source: bool = False,
) -> Tuple[List[Action], Dict[str, FileInfo], Dict[str, FileInfo]]:
    src = scan(src_dir, recursive=recursive, include_hidden=include_hidden)
    dst = scan(dst_dir, recursive=recursive, include_hidden=include_hidden)

    actions: List[Action] = []

    for name, s in sorted(src.items(), key=lambda kv: kv[0]):
        d = dst.get(name)
        if d is None:
            actions.append(Action("MOVE", "no conflict", s.path, dst_dir / name))
            continue

        if s.mtime_ns > d.mtime_ns:
            actions.append(Action("OVERWRITE", "source newer", s.path, d.path))
        elif s.mtime_ns < d.mtime_ns:
            actions.append(Action("SKIP", "target newer", s.path, d.path))
            if delete_older_source:
                actions.append(Action("DELETE", "older source", s.path, None))
        else:
            # Same timestamp — compare sizes
            if s.size > d.size:
                actions.append(Action("OVERWRITE", "same time, larger source", s.path, d.path))
            elif s.size < d.size:
                actions.append(Action("SKIP", "same time, larger target", s.path, d.path))
                if delete_older_source:
                    actions.append(Action("DELETE", "smaller source (same time)", s.path, None))
            else:
                actions.append(Action("SKIP", "identical", s.path, d.path))

    return actions, src, dst

def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

def move_replace(src: Path, dst: Path) -> None:
    """Move src to dst, overwriting atomically when possible, cross-device safe."""
    ensure_parent(dst)
    try:
        os.replace(src, dst)  # atomic on same filesystem
    except OSError as e:
        if e.errno == errno.EXDEV:
            # cross-device: copy then atomic replace
            tmp = dst.with_suffix(dst.suffix + ".tmp_sync")
            shutil.copy2(src, tmp)
            os.replace(tmp, dst)
            try:
                os.unlink(src)
            except FileNotFoundError:
                pass
        else:
            raise

def trash_file(p: Path, trash_dir: Path) -> Path:
    trash_dir.mkdir(parents=True, exist_ok=True)
    ts = time.strftime("%Y%m%d-%H%M%S")
    candidate = trash_dir / f"{p.name}.{ts}"
    i = 0
    out = candidate
    while out.exists():
        i += 1
        out = trash_dir / f"{p.name}.{ts}.{i}"
    shutil.move(str(p), str(out))
    return out

def apply_actions(
    actions: Iterable[Action],
    src_dir: Path,
    dst_dir: Path,
    delete_older_source: bool = False,
    use_trash: bool = False,
) -> Tuple[int,int,int,int]:
    moved = overwritten = skipped = deleted = 0
    trash_dir = src_dir / ".sync-trash"
    for a in actions:
        if a.kind == "MOVE":
            move_replace(a.src, a.dst)
            moved += 1
        elif a.kind == "OVERWRITE":
            move_replace(a.src, a.dst)
            overwritten += 1
        elif a.kind == "SKIP":
            skipped += 1
        elif a.kind == "DELETE" and delete_older_source:
            if use_trash:
                trash_file(a.src, trash_dir)
            else:
                try:
                    a.src.unlink()
                except FileNotFoundError:
                    pass
            deleted += 1
    return moved, overwritten, skipped, deleted

def write_csv(path: Path, rows: List[dict]) -> None:
    if not rows:
        path.write_text("")
        return
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

def to_rows(actions: List[Action], src_dir: Path, dst_dir: Path) -> List[dict]:
    rows = []
    for a in actions:
        rows.append({
            "kind": a.kind,
            "reason": a.reason,
            "src": str(a.src.relative_to(src_dir)) if a.src and a.src.is_relative_to(src_dir) else (str(a.src) if a.src else ""),
            "dst": str(a.dst.relative_to(dst_dir)) if a.dst and a.dst.is_relative_to(dst_dir) else (str(a.dst) if a.dst else ""),
        })
    return rows

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Sync SRC -> DST applying timestamp/size rules.")
    ap.add_argument("--src", default=".", help="Source directory (default: .)")
    ap.add_argument("--dst", default="..", help="Target directory (default: ..)")
    ap.add_argument("--recursive", action="store_true", help="Recurse into subdirectories")
    ap.add_argument("--include-hidden", action="store_true", help="Include hidden dotfiles")
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="Only simulate (default)")
    mode.add_argument("--apply", action="store_true", help="Apply changes")
    ap.add_argument("--delete-older-source", action="store_true", help="When target wins, delete the older/smaller source copy")
    ap.add_argument("--trash", action="store_true", help="Send deletions to .sync-trash instead of rm")
    ap.add_argument("--log", default="", help="Optional path to write the line-by-line log")
    ap.add_argument("--csv", default="", help="Optional path to write actions as CSV")
    ap.add_argument("--quiet", action="store_true", help="Suppress line-by-line output")
    args = ap.parse_args(argv)

    src_dir = Path(args.src).resolve()
    dst_dir = Path(args.dst).resolve()

    if not src_dir.is_dir() or not dst_dir.is_dir():
        print(f"ERR: src ({src_dir}) or dst ({dst_dir}) is not a directory", file=sys.stderr)
        return 2

    actions, src_map, dst_map = plan_actions(
        src_dir=src_dir,
        dst_dir=dst_dir,
        recursive=args.recursive,
        include_hidden=args.include_hidden,
        delete_older_source=args.delete_older_source,
    )

    prefix = "WOULD" if (args.dry_run or not args.apply) else "DO"
    lines = [format_line(prefix, a, src_dir, dst_dir) for a in actions]

    # Write outputs
    if not args.quiet:
        for ln in lines:
            print(ln)

    if args.log:
        Path(args.log).write_text("\n".join(lines), encoding="utf-8")

    if args.csv:
        write_csv(Path(args.csv), to_rows(actions, src_dir, dst_dir))

    # Summary
    totals = {"MOVE":0,"OVERWRITE":0,"SKIP":0,"DELETE":0}
    for a in actions:
        totals[a.kind] = totals.get(a.kind,0) + 1

    print(f"\nSummary: MOVE={totals['MOVE']} OVERWRITE={totals['OVERWRITE']} "
          f"SKIP={totals['SKIP']} DELETE={totals['DELETE']}", file=sys.stderr)

    if args.apply:
        moved, overwritten, skipped, deleted = apply_actions(
            actions, src_dir, dst_dir,
            delete_older_source=args.delete_older_source,
            use_trash=args.trash,
        )
        print(f"Applied: moved={moved} overwritten={overwritten} skipped={skipped} deleted={deleted}", file=sys.stderr)

    return 0

if __name__ == "__main__":
    raise SystemExit(main())
