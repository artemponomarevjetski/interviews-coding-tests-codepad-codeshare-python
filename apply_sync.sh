#!/usr/bin/env bash
set -euo pipefail
SRC="${1:-.}"
DST="${2:-..}"
TS="$(date +%Y%m%d_%H%M%S)"
# Apply the planned actions. Remove --delete-older-source if you don't want to delete source copies when target wins.
python3 "$(dirname "$0")/sync_by_rules.py" --src "$SRC" --dst "$DST" --apply --delete-older-source --log "apply_$TS.txt" --csv "apply_$TS.csv"
echo "Apply complete. Logs: apply_$TS.txt, apply_$TS.csv"
