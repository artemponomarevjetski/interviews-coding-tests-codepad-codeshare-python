# Sync toolkit

This drops in two scripts + a Makefile to run a dry-run simulation first, then apply.

## Files
- `sync_by_rules.py` — core logic (Python 3.8+). Default: top-level only, ignores dotfiles.
- `sim_sync.sh` — dry-run wrapper that writes `dry_run_*.txt` and `dry_run_*.csv` logs.
- `apply_sync.sh` — apply wrapper (by default deletes older source copies when target wins; remove the flag if you want to keep them).
- `Makefile` — `make dry-run`, `make apply`, `make apply-delete` convenience targets.

## Usage
From your repo root (e.g. `/Users/artem.ponomarev/interviews-coding-tests-codepad-codeshare-python`):

```bash
# Dry-run with defaults (SRC=., DST=..)
./sim_sync.sh

# Dry-run but include dotfiles
python3 sync_by_rules.py --dry-run --include-hidden

# Apply (safe; no deletes of source)
python3 sync_by_rules.py --apply

# Apply and delete older source copies (or send to trash)
python3 sync_by_rules.py --apply --delete-older-source
python3 sync_by_rules.py --apply --delete-older-source --trash   # -> ./.sync-trash/

# Recursive mode
python3 sync_by_rules.py --apply --recursive
```

Each run prints a human log like:
```
WOULD MOVE (no conflict): ./file -> ../file
WOULD OVERWRITE (source newer): ./file -> ../file
WOULD SKIP (target newer): ./file (keeping ../file)
WOULD DELETE (older source): ./file
```
and then a summary, with optional CSV for scripting.
