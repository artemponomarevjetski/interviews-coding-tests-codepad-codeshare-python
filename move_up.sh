#!/usr/bin/env bash
# Move all items from SRC into DST (merging directories when needed).
# Default: DRY RUN. Use --apply to make changes.
# Usage: ./move_up.sh [--apply|--dry-run] [--no-clobber] [SRC [DST]]
set -Eeuo pipefail

usage() { cat <<'USAGE'
Usage: move_up.sh [--apply|--dry-run] [--no-clobber] [SRC [DST]]
Moves everything inside SRC into DST (merging directories when needed).
Defaults: SRC="."  DST="..", mode=DRY RUN.

Options:
  --apply        Actually make changes (default is dry run).
  --dry-run      Print the plan, but don't change anything.
  --no-clobber   Do not overwrite existing files; skip with a warning.
  -h, --help     Show this help.
USAGE
}

# Defaults
DRY_RUN=1
NO_CLOBBER=0

# Parse options
ARGS=()
while (($#)); do
  case "$1" in
    --apply) DRY_RUN=0 ;;
    --dry-run|--plan|-n) DRY_RUN=1 ;;
    --no-clobber) NO_CLOBBER=1 ;;
    -h|--help) usage; exit 0 ;;
    --) shift; break ;;
    -*) printf 'Error: unknown option: %s\n' "$1" >&2; usage; exit 2 ;;
    *) ARGS+=("$1") ;;
  esac
  shift
done
# Collect any remaining args after `--`
while (($#)); do ARGS+=("$1"); shift; done

# Positional defaults
SRC="${ARGS[0]:-.}"
DST="${ARGS[1]:-..}"

die()  { printf 'Error: %s\n' "$*" >&2; exit 1; }
log()  { printf '%s\n' "$*"; }
warn() { printf 'WARNING: %s\n' "$*" >&2; }

# Resolve script path to avoid moving ourselves
script_path="${BASH_SOURCE[0]}"
[[ "$script_path" != /* ]] && script_path="$PWD/${script_path#./}"
script_base="${script_path##*/}"

[[ -d "$SRC" ]] || die "Source '$SRC' is not a directory."
[[ -d "$DST" ]] || die "Destination '$DST' is not a directory."

# Absolute paths
abs_src="$(cd "$SRC" && pwd -P)"
abs_dst="$(cd "$DST" && pwd -P)"

[[ "$abs_src" != "$abs_dst" ]] || die "Source and destination resolve to the same directory."
case "$abs_dst/" in
  "$abs_src/"*) die "Destination ('$abs_dst') is inside source ('$abs_src'); refusing to proceed." ;;
esac

# Announce
log "Source: $SRC"
log "Dest:   $DST"
if (( DRY_RUN )); then
  log "Mode:   DRY RUN (no changes)"
else
  log "Mode:   APPLY (changes will be made)"
fi

# Runner that preserves arguments; logs safely in dry-run
run() {
  if (( DRY_RUN )); then
    printf "DRY: "
    printf "%q " "$@"
    printf "\n"
  else
    command "$@"
  fi
}

# Decide whether to skip a path
should_skip() {
  local p="$1"
  local b="${p##*/}"
  [[ "$p" == "$script_path" ]] && return 0
  [[ "$b" == "$script_base" ]] && return 0
  [[ "$b" == move_*.log ]] && return 0
  return 1
}

# -------- Portable stat helpers (GNU vs BSD/macOS) --------
stat_mtime() {  # modification time (epoch seconds)
  if stat -c %Y "$1" >/dev/null 2>&1; then stat -c %Y "$1"; else stat -f %m "$1"; fi
}
stat_size() {   # size in bytes
  if stat -c %s "$1" >/dev/null 2>&1; then stat -c %s "$1"; else stat -f %z "$1"; fi
}

# -------- Collision policy (files): newer wins; if same time, larger wins --------
move_file() {
  local src="$1" dest_dir="$2"
  local base="${src##*/}"
  local dest="$dest_dir/$base"

  if [[ ! -e "$dest" ]]; then
    log "NEW: $dest  <-- $src"
    run mv -f "$src" "$dest"
    return 0
  fi

  if (( NO_CLOBBER )); then
    warn "exists, skipping (no-clobber): $dest"
    return 0
  fi

  if [[ -f "$src" && -f "$dest" ]]; then
    local sm dm ss ds
    sm=$(stat_mtime "$src") || sm=0
    dm=$(stat_mtime "$dest") || dm=0

    if (( sm > dm )); then
      log "REPLACE (src newer): $dest  <-- $src"
      run mv -f "$src" "$dest"
      return 0
    elif (( sm < dm )); then
      log "KEEP (dest newer), drop src: $dest  [src=$src]"
      run rm -f "$src"
      return 0
    fi

    ss=$(stat_size "$src") || ss=0
    ds=$(stat_size "$dest") || ds=0
    if   (( ss > ds )); then
      log "REPLACE (same time, src larger): $dest  <-- $src"
      run mv -f "$src" "$dest"
    elif (( ss < ds )); then
      log "KEEP (same time, dest larger), drop src: $dest  [src=$src]"
      run rm -f "$src"
    else
      if cmp -s "$src" "$dest"; then
        log "SKIP (identical), drop src duplicate: $dest"
      else
        log "KEEP (same time & size but different; conservative), drop src: $dest"
      fi
      run rm -f "$src"
    fi
    return 0
  fi

  if [[ -d "$dest" ]]; then
    log "INTO DIR: $dest/$base  <-- $src"
  else
    log "REPLACE (fallback type): $dest  <-- $src"
  fi
  run mv -f "$src" "$dest"
}

move_dir() {
  local src="$1" parent_dest="$2"
  local base="${src##*/}"
  local dest="$parent_dest/$base"

  if [[ ! -e "$dest" ]]; then
    log "NEW DIR: $dest  <-- $src"
    run mv -f "$src" "$dest"
    return 0
  fi
  if [[ ! -d "$dest" ]]; then
    warn "destination exists and is not a directory, skipping dir: $dest"
    return 0
  fi

  shopt -s dotglob nullglob
  local p
  for p in "$src"/*; do
    [[ -e "$p" ]] || continue
    if should_skip "$p"; then
      continue
    fi
    if [[ -d "$p" && ! -L "$p" ]]; then
      move_dir "$p" "$dest"
    else
      move_file "$p" "$dest"
    fi
  done
  shopt -u dotglob nullglob

  run rmdir "$src" 2>/dev/null || true
}

# Clean top-level macOS junk file if present
if [[ -e "$abs_src/.DS_Store" ]]; then
  run rm -f "$abs_src/.DS_Store"
fi

# Main loop: move everything from SRC into DST
shopt -s dotglob nullglob
for path in "$abs_src"/*; do
  [[ -e "$path" ]] || continue
  if should_skip "$path"; then
    continue
  fi
  if [[ -d "$path" && ! -L "$path" ]]; then
    move_dir "$path" "$abs_dst"
  else
    move_file "$path" "$abs_dst"
  fi
done
shopt -u dotglob nullglob

log "Done."

