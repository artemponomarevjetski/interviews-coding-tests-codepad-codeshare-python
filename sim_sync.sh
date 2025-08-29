#!/usr/bin/env bash
set -euo pipefail
SRC="${1:-.}"
DST="${2:-..}"
# Run a dry-run and save logs
TS="$(date +%Y%m%d_%H%M%S)"
python3 "$(dirname "$0")/sync_by_rules.py" --src "$SRC" --dst "$DST" --dry-run --log "dry_run_$TS.txt" --csv "dry_run_$TS.csv"
echo "Dry-run complete. Logs: dry_run_$TS.txt, dry_run_$TS.csv"
