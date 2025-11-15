#!/bin/bash

TEMP_DIR="$HOME/temp"
WIN_DIR="$HOME/win_x"
LOG_DIR="$HOME/log"
SNAPSHOT_PY="$HOME/snapshot.py"
RSYNC_PATTERN="rsync -a --delete"
PYTHON_PATTERN="python3.*snapshot.py"
SMB_USER="v-aponomarev"
SMB_PASS=$(<"$HOME/.password")
SMB_HOST="192.168.0.191"
SMB_SHARE="x"

mkdir -p "$TEMP_DIR" "$WIN_DIR" "$LOG_DIR"

check_status() {
  RSYNC_RUNNING=$(pgrep -f "$RSYNC_PATTERN")
  PYTHON_RUNNING=$(pgrep -f "$PYTHON_PATTERN")
}

announce_status() {
  echo "📷 snapshot.py loop:   ${PYTHON_RUNNING:+RUNNING ($PYTHON_RUNNING)}${PYTHON_RUNNING:-NOT AVAILABLE}"
  echo "🔁 rsync loop:         ${RSYNC_RUNNING:+RUNNING ($RSYNC_RUNNING)}${RSYNC_RUNNING:-NOT AVAILABLE}"
}

show_menu() {
  echo "–––––––––––––––––––––––––––––––––––––––––––––"
  echo "Commands:"
  echo "  l or [Enter] → Lookup (show status)"
  echo "  s → Start or Restart snapshot.py and rsync"
  echo "  f → Show files in ~/temp"
  echo "  g → Show logs from snapshot.py"
  echo "  t → Terminate all loops"
  echo "  h → Show this help menu"
  echo "  q → Quit"
  echo "–––––––––––––––––––––––––––––––––––––––––––––"
}

mount_share_explicit() {
  echo "🔐 Mounting Windows share explicitly..."
  mount | grep -q "$WIN_DIR" && umount "$WIN_DIR"
  if echo "$SMB_PASS" | mount_smbfs "//$SMB_USER@$SMB_HOST/$SMB_SHARE" "$WIN_DIR" 2>/dev/null; then
    echo "✅ SMB share mounted successfully."
  else
    echo "❌ SMB share mount failed!"
    return 1
  fi
}

start_services() {
  echo "🧹 Flushing ~/temp directory completely..."
  rm -rf "${TEMP_DIR:?}/"*

  mount_share_explicit || return

  echo "🔄 Performing initial sync with SMB share..."
  rsync -av --delete "$TEMP_DIR/" "$WIN_DIR/" && echo "✅ Initial sync completed."

  check_status

  if [[ -n "$PYTHON_RUNNING" ]]; then
    echo "📷 snapshot.py already RUNNING (PID: $PYTHON_RUNNING)"
  else
    echo "🚀 Starting snapshot.py loop..."
    nohup bash -c "while true; do python3 '$SNAPSHOT_PY'; sleep 10; done" > "$LOG_DIR/snapshot_stdout.log" 2>&1 &
    echo "✅ snapshot.py loop STARTED"
  fi

  if [[ -n "$RSYNC_RUNNING" ]]; then
    echo "🔁 rsync already RUNNING (PID: $RSYNC_RUNNING)"
  else
    echo "🔁 Starting rsync loop..."
    nohup bash -c "while true; do rsync -a --delete --exclude='*.log' '$TEMP_DIR/' '$WIN_DIR/'; sleep 5; done" > "$LOG_DIR/rsync_stdout.log" 2>&1 &
    echo "✅ rsync loop STARTED"
  fi
}

stop_services() {
  echo "🛑 Terminating all snapshot.py and rsync loops..."
  pkill -f "$RSYNC_PATTERN" 2>/dev/null && echo "🔁 rsync KILLED" || echo "🔁 rsync NOT AVAILABLE"
  pkill -f "$PYTHON_PATTERN" 2>/dev/null && echo "📷 snapshot.py KILLED" || echo "📷 snapshot.py NOT AVAILABLE"
}

show_files() {
  echo "📂 Contents of ~/temp:"
  ls -lh "$TEMP_DIR"
}

show_logs() {
  echo "📄 Last 10 lines of snapshot.log"
  tail -n 10 "$LOG_DIR/snapshot.log" 2>/dev/null
}

controller_loop() {
  while true; do
    clear
    check_status
    announce_status
    echo "–––––––––––––––––––––––––––––––––––––––––––––"
    echo "[Press 'h' for help]"
    echo -n "🟢 Command (l/s/f/g/t/h/q or Enter to refresh): "
    IFS= read -rsn1 cmd
    echo ""
    case "$cmd" in
      "" | l | L) check_status; announce_status; sleep 1 ;;
      s|S) start_services; sleep 2 ;;
      f|F) show_files; read -rp "🔁 Press Enter to continue..." ;;
      g|G) show_logs; read -rp "🔁 Press Enter to continue..." ;;
      t|T) stop_services; sleep 1 ;;
      h|H) show_menu; read -rp "📋 Press Enter to continue..." ;;
      q|Q) echo "👋 EXITING"; exit 0 ;;
      *) echo "❌ Invalid input. Only l, s, f, g, t, h, or q allowed."; sleep 1 ;;
    esac
  done
}

controller_loop
