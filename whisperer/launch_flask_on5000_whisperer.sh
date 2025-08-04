#!/bin/bash

# --- Configuration ---
PORT=5000
VENV_DIR="venv"
PYTHON_CMD="python3"
LOG_RETENTION_DAYS=7

# --- Log File Paths ---
LOG_DIR="logs"
SERVICE_LOG="$LOG_DIR/service.log"
FLASK_LOG="$LOG_DIR/flask_app.log"
TRANSCRIPT_LOG="$LOG_DIR/transcriptions.log"
RECENT_TRANSCRIPT_LOG="$LOG_DIR/recent_transcriptions.log"

# Initialize log directory and files
mkdir -p "$LOG_DIR"
touch "$SERVICE_LOG" "$FLASK_LOG" "$TRANSCRIPT_LOG" "$RECENT_TRANSCRIPT_LOG"

# --- Function to Purge Old Transcripts ---
purge_old_transcripts() {
    if [ -s "$TRANSCRIPT_LOG" ]; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] Purging transcript logs older than $LOG_RETENTION_DAYS days" >> "$SERVICE_LOG"
        temp_file=$(mktemp)
        cutoff_date=$(date -v-${LOG_RETENTION_DAYS}d +%s)
        
        while IFS= read -r line; do
            if [[ "$line" =~ ^\[(.*)\].* ]]; then
                log_date=$(date -j -f "%Y-%m-%d %H:%M:%S" "${BASH_REMATCH[1]}" +%s 2>/dev/null)
                if [ -n "$log_date" ] && [ "$log_date" -gt "$cutoff_date" ]; then
                    echo "$line"
                fi
            fi
        done < "$TRANSCRIPT_LOG" > "$temp_file"
        
        mv "$temp_file" "$TRANSCRIPT_LOG"
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] Transcript log cleaned" >> "$SERVICE_LOG"
    else
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] No existing transcript log entries to purge" >> "$SERVICE_LOG"
    fi
}

# --- Function to Free Port ---
free_port() {
    echo -e "\n[$(date '+%Y-%m-%d %H:%M:%S')] Attempting to free port $PORT..." >> "$SERVICE_LOG"
    local pids=$(lsof -ti :$PORT)
    if [ -n "$pids" ]; then
        echo "Found processes using port $PORT: $pids" >> "$SERVICE_LOG"
        kill -9 $pids
        sleep 1
        if lsof -ti :$PORT >/dev/null; then
            echo "Failed to free port $PORT" >> "$SERVICE_LOG"
            return 1
        else
            echo "Successfully freed port $PORT" >> "$SERVICE_LOG"
            return 0
        fi
    else
        echo "No processes found using port $PORT" >> "$SERVICE_LOG"
        return 0
    fi
}

# --- Main Execution ---
{
    echo -e "\n$(date '+%Y-%m-%d %H:%M:%S') - Starting Whisper Service Launcher (Debug Mode)"
    echo -e "=============================================="

    # --- Port Handling ---
    echo -e "\nChecking port $PORT..."
    if lsof -i :$PORT >/dev/null; then
        echo -e "Port $PORT is in use - attempting to free it..."
        if ! free_port; then
            echo -e "Could not free port $PORT. Please close it manually."
            exit 1
        fi
    fi

    # --- Cleanup Previous Instances ---
    echo -e "\nStopping existing whisperer services..."
    pkill -f "python.*whisperer\.py" 2>/dev/null || true

    # --- Virtual Environment Handling ---
    if [ ! -d "$VENV_DIR" ]; then
        echo -e "\nVirtual environment not found!"
        echo -e "Please create it first with:"
        echo "python3 -m venv venv"
        echo "source venv/bin/activate"
        echo "pip install -r requirements.txt"
        exit 1
    else
        echo -e "\nActivating virtual environment..."
        source "$VENV_DIR/bin/activate"
    fi

    # --- Verify Requirements ---
    echo -e "\nChecking dependencies..."
    pip install -r requirements.txt --quiet

    # --- Purge Old Transcripts ---
    purge_old_transcripts

    # --- Service Launch ---
    echo -e "\nStarting Whisperer service in foreground..."
    
    # Create log processing function
    process_flask_output() {
        while IFS= read -r line; do
            # Print to console
            echo "$line"
            
            # Log to flask_app.log with timestamp
            echo "[$(date '+%Y-%m-%d %H:%M:%S')] $line" >> "$FLASK_LOG"
        done
    }

    # Run in foreground with output processing
    $PYTHON_CMD -u whisperer.py 2>&1 | process_flask_output

} | tee -a "$SERVICE_LOG"

exit 0
