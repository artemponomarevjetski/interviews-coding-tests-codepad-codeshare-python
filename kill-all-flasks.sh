#!/bin/bash
# kill-all-repo-apps.sh - Ultimate kill script for ALL apps in this repository
# Location: apps/flasks/kill-all-repo-apps.sh

# Color codes for better UX
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
PURPLE='\033[0;35m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Get repository root directory (3 levels up from script location)
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

# ---------------------------------------------------------------------------
#  ASCII HEADER – Hangman + Pac-Man + Ghost
# ---------------------------------------------------------------------------
echo -e "${CYAN}"
cat << "EOF"
   ▄▄▄▄▄▄▄▄▄▄▄  ▄▄▄▄▄▄▄▄▄▄▄  ▄▄▄▄▄▄▄▄▄▄▄  ▄▄▄▄▄▄▄▄▄▄▄  ▄▄▄▄▄▄▄▄▄▄▄ 
  ▐░░░░░░░░░░░▌▐░░░░░░░░░░░▌▐░░░░░░░░░░░▌▐░░░░░░░░░░░▌▐░░░░░░░░░░░▌
  ▐░█▀▀▀▀▀▀▀▀▀ ▐░█▀▀▀▀▀▀▀█░▌▐░█▀▀▀▀▀▀▀█░▌▐░█▀▀▀▀▀▀▀█░▌▐░█▀▀▀▀▀▀▀▀▀ 
  ▐░▌          ▐░▌       ▐░▌▐░▌       ▐░▌▐░▌       ▐░▌▐░▌          
  ▐░▌          ▐░▌       ▐░▌▐░▌       ▐░▌▐░▌       ▐░▌▐░▌          
  ▐░▌          ▐░▌       ▐░▌▐░▌       ▐░▌▐░▌       ▐░▌▐░▌          
  ▐░▌          ▐░▌       ▐░▌▐░▌       ▐░▌▐░▌       ▐░▌▐░▌          
  ▐░▌          ▐░▌       ▐░▌▐░▌       ▐░▌▐░▌       ▐░▌▐░▌          
  ▐░█▄▄▄▄▄▄▄▄▄ ▐░█▄▄▄▄▄▄▄█░▌▐░█▄▄▄▄▄▄▄█░▌▐░█▄▄▄▄▄▄▄█░▌▐░█▄▄▄▄▄▄▄▄▄ 
  ▐░░░░░░░░░░░▌▐░░░░░░░░░░░▌▐░░░░░░░░░░░▌▐░░░░░░░░░░░▌▐░░░░░░░░░░░▌
   ▀▀▀▀▀▀▀▀▀▀▀  ▀▀▀▀▀▀▀▀▀▀▀  ▀▀▀▀▀▀▀▀▀▀▀  ▀▀▀▀▀▀▀▀▀▀▀  ▀▀▀▀▀▀▀▀▀▀▀ 
EOF
echo -e "${YELLOW}"
cat << "EOF"
       ____      _           _    _            ____  
      / ___|    | |         | |  | |          / ___| 
     | |  _  ___| | __  _ __| |__| |__   ___ | |  _  
     | |_| |/ __| |/ / | '__|  __  '_ \ / _ \| |_| | 
      \____|\___|   <  | |  | |  | |_) | (_) |\____| 
      |_____|       |_| |_|  |_|  |_.__/ \___/|_____| 
              ___  ___  ___  ___  ___  ___  ___  ___ 
             |   \|   \|   \|   \|   \|   \|   \|   \ 
             |_|\_|_|\_|_|\_|_|\_|_|\_|_|\_|_|\_|_|\_| 
                                                       
EOF
echo -e "${PURPLE}"
cat << "EOF"
       ╔══════════════════════════════════════════════════════╗
       ║     🚀 REPOSITORY APP KILLER v3.0  🚀              ║
       ║   Kills ALL apps from this repository               ║
       ╚══════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"
echo -e "${BOLD}Repository root:${NC} $REPO_ROOT"
echo -e "${BOLD}Script location:${NC} $(dirname "${BASH_SOURCE[0]}")"
echo ""

# ---------------------------------------------------------------------------
#  FUNCTION: show_processes
# ---------------------------------------------------------------------------
show_processes() {
    echo -e "\n${YELLOW}🔍 Scanning for running processes from this repository...${NC}"
    echo -e "${BLUE}══════════════════════════════════════════════════════${NC}"
    
    local pid_files_found=0
    for app_dir in whisperer-external whisperer-internal avatar solver; do
        if [ -f "$app_dir/whisperer.pid" ] || [ -f "$app_dir/avatar.pid" ] || [ -f "$app_dir/solver.pid" ]; then
            pid_files_found=1
            for pidfile in "$app_dir"/*.pid; do
                if [ -f "$pidfile" ]; then
                    PID=$(cat "$pidfile" 2>/dev/null)
                    echo -e "${BOLD}📄 Found PID file:${NC} $pidfile (PID: $PID)"
                    if ps -p $PID >/dev/null 2>&1; then
                        echo -e "   Status: ${GREEN}✅ RUNNING${NC}"
                        ps -o pid,user,%cpu,%mem,start,command -p $PID | tail -1
                    else
                        echo -e "   Status: ${RED}❌ NOT RUNNING (stale PID file)${NC}"
                    fi
                fi
            done
        fi
    done
    if [ $pid_files_found -eq 0 ]; then
        echo -e "${YELLOW}📄 No PID files found${NC}"
    fi
    
    echo -e "\n${BOLD}🔌 Checking ports 5000-5010:${NC}"
    local port_found=0
    for PORT in {5000..5010}; do
        PIDS=$(lsof -ti:$PORT 2>/dev/null)
        if [ ! -z "$PIDS" ]; then
            port_found=1
            echo -e "   Port ${CYAN}$PORT${NC}: ${RED}IN USE${NC} by PIDs: $PIDS"
            for pid in $PIDS; do
                echo -e "   └── PID $pid: $(ps -o command= -p $pid 2>/dev/null | head -c 60)"
            done
        fi
    done
    if [ $port_found -eq 0 ]; then
        echo -e "   ${GREEN}✅ All ports 5000-5010 are free${NC}"
    fi
    
    echo -e "\n${BOLD}👤 Checking process names from repository:${NC}"
    local processes_found=0
    
    # Check for whisperer processes
    whisperer_pids=$(pgrep -f "python.*whisperer" 2>/dev/null)
    if [ ! -z "$whisperer_pids" ]; then
        processes_found=1
        echo -e "   ${YELLOW}Whisperer processes:${NC} $whisperer_pids"
        for pid in $whisperer_pids; do
            echo -e "   └── PID $pid: $(ps -o command= -p $pid 2>/dev/null)"
        done
    fi
    
    # Check for avatar processes
    avatar_pids=$(pgrep -f "python.*avatar" 2>/dev/null)
    if [ ! -z "$avatar_pids" ]; then
        processes_found=1
        echo -e "   ${YELLOW}Avatar processes:${NC} $avatar_pids"
        for pid in $avatar_pids; do
            echo -e "   └── PID $pid: $(ps -o command= -p $pid 2>/dev/null)"
        done
    fi
    
    # Check for solver processes
    solver_pids=$(pgrep -f "python.*solver" 2>/dev/null)
    if [ ! -z "$solver_pids" ]; then
        processes_found=1
        echo -e "   ${YELLOW}Solver processes:${NC} $solver_pids"
        for pid in $solver_pids; do
            echo -e "   └── PID $pid: $(ps -o command= -p $pid 2>/dev/null)"
        done
    fi
    
    # Check for snapshot processes
    snapshot_pids=$(pgrep -f "python.*snapshot" 2>/dev/null)
    if [ ! -z "$snapshot_pids" ]; then
        processes_found=1
        echo -e "   ${YELLOW}Snapshot processes:${NC} $snapshot_pids"
        for pid in $snapshot_pids; do
            echo -e "   └── PID $pid: $(ps -o command= -p $pid 2>/dev/null)"
        done
    fi
    
    # Check for Flask processes
    flask_pids=$(pgrep -f "flask" 2>/dev/null)
    if [ ! -z "$flask_pids" ]; then
        processes_found=1
        echo -e "   ${YELLOW}Flask processes:${NC} $flask_pids"
        for pid in $flask_pids; do
            echo -e "   └── PID $pid: $(ps -o command= -p $pid 2>/dev/null)"
        done
    fi
    
    # Check for any Python app from this repo
    repo_python_pids=$(pgrep -f "python.*$REPO_ROOT" 2>/dev/null)
    if [ ! -z "$repo_python_pids" ]; then
        processes_found=1
        echo -e "   ${YELLOW}Python processes from repo:${NC} $repo_python_pids"
        for pid in $repo_python_pids; do
            echo -e "   └── PID $pid: $(ps -o command= -p $pid 2>/dev/null | head -c 60)"
        done
    fi
    
    if [ $processes_found -eq 0 ]; then
        echo -e "   ${GREEN}✅ No running repository app processes found${NC}"
    fi
    
    echo -e "${BLUE}══════════════════════════════════════════════════════${NC}"
}

# ---------------------------------------------------------------------------
#  FUNCTION: check_status
# ---------------------------------------------------------------------------
check_status() {
    echo -e "\n${PURPLE}📊 REPOSITORY APP STATUS CHECK${NC}"
    echo -e "${BLUE}══════════════════════════════════════════════════════${NC}"
    
    echo -e "${BOLD}🌐 Web Interfaces:${NC}"
    local any_responding=0
    
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/ 2>/dev/null || echo "000")
    if [ "$HTTP_CODE" = "200" ]; then
        any_responding=1
        echo -e "   ${GREEN}✅ http://localhost:5000 is responding${NC}"
    elif [ "$HTTP_CODE" = "000" ]; then
        echo -e "   ${RED}❌ http://localhost:5000 is not responding${NC}"
    else
        echo -e "   ${YELLOW}⚠️  http://localhost:5000 returned HTTP $HTTP_CODE${NC}"
    fi
    
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5001/ 2>/dev/null || echo "000")
    if [ "$HTTP_CODE" = "200" ]; then
        any_responding=1
        echo -e "   ${GREEN}✅ http://localhost:5001 is responding${NC}"
    elif [ "$HTTP_CODE" = "000" ]; then
        echo -e "   ${RED}❌ http://localhost:5001 is not responding${NC}"
    else
        echo -e "   ${YELLOW}⚠️  http://localhost:5001 returned HTTP $HTTP_CODE${NC}"
    fi
    
    echo -e "\n${BOLD}📋 Recent Logs:${NC}"
    local logs_found=0
    for logdir in whisperer-external/logs whisperer-internal/logs avatar/logs solver/logs ../../flask/log; do
        if [ -f "$logdir/flask_app.log" ] || [ -f "$logdir/flask.log" ]; then
            logs_found=1
            echo -e "   ${CYAN}$logdir${NC}:"
            if [ -f "$logdir/flask_app.log" ]; then
                tail -2 "$logdir/flask_app.log" 2>/dev/null | while read line; do
                    echo -e "   📄 ${line:0:77}..."
                done
            elif [ -f "$logdir/flask.log" ]; then
                tail -2 "$logdir/flask.log" 2>/dev/null | while read line; do
                    echo -e "   📄 ${line:0:77}..."
                done
            fi
        fi
    done
    if [ $logs_found -eq 0 ]; then
        echo -e "   ${YELLOW}No recent log files found${NC}"
    fi
    
    echo -e "\n${BOLD}⚙️  System Check:${NC}"
    for PORT in 5000 5001 5002; do
        if lsof -ti:$PORT >/dev/null 2>&1; then
            PORT_PIDS=$(lsof -ti:$PORT | tr '\n' ' ')
            echo -e "   ${YELLOW}Port $PORT: IN USE by PIDs: $PORT_PIDS${NC}"
        else
            echo -e "   ${GREEN}Port $PORT: FREE${NC}"
        fi
    done
    echo -e "${BLUE}══════════════════════════════════════════════════════${NC}"
}

# ---------------------------------------------------------------------------
#  FUNCTION: kill_all_repo_processes
# ---------------------------------------------------------------------------
kill_all_repo_processes() {
    local kill_mode=$1
    
    echo -e "\n${RED}⚠️  WARNING: This will kill ALL processes from the repository!${NC}"
    echo -e "${RED}   Including: whisperer, avatar, solver, snapshot, flask apps${NC}"
    
    if [ "$kill_mode" != "force" ]; then
        read -p "Are you sure you want to proceed? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo -e "${YELLOW}❌ Operation cancelled${NC}"
            exit 0
        fi
    fi
    
    echo -e "\n${RED}🛑 Killing ALL repository processes...${NC}"
    
    echo -e "${YELLOW}📄 Killing processes from PID files...${NC}"
    for app_dir in whisperer-external whisperer-internal avatar solver ../../flask; do
        for pidfile in "$app_dir"/*.pid; do
            if [ -f "$pidfile" ]; then
                PID=$(cat "$pidfile" 2>/dev/null)
                echo -e "   Killing PID from $pidfile: $PID"
                kill -9 $PID 2>/dev/null
                rm -f "$pidfile"
            fi
        done
    done
    
    echo -e "\n${YELLOW}🔌 Clearing common ports (5000-5010)...${NC}"
    for PORT in {5000..5010}; do
        PIDS=$(lsof -ti:$PORT 2>/dev/null)
        if [ ! -z "$PIDS" ]; then
            echo -e "   Killing processes on port ${CYAN}$PORT${NC}: $PIDS"
            kill -9 $PIDS 2>/dev/null
        fi
    done
    
    echo -e "\n${YELLOW}👤 Killing by process name patterns...${NC}"
    
    whisperer_pids=$(pgrep -f "python.*whisperer" 2>/dev/null)
    if [ ! -z "$whisperer_pids" ]; then
        echo -e "   Killing whisperer processes: $whisperer_pids"
        kill -9 $whisperer_pids 2>/dev/null
    fi
    
    avatar_pids=$(pgrep -f "python.*avatar" 2>/dev/null)
    if [ ! -z "$avatar_pids" ]; then
        echo -e "   Killing avatar processes: $avatar_pids"
        kill -9 $avatar_pids 2>/dev/null
    fi
    
    solver_pids=$(pgrep -f "python.*solver" 2>/dev/null)
    if [ ! -z "$solver_pids" ]; then
        echo -e "   Killing solver processes: $solver_pids"
        kill -9 $solver_pids 2>/dev/null
    fi
    
    snapshot_pids=$(pgrep -f "python.*snapshot" 2>/dev/null)
    if [ ! -z "$snapshot_pids" ]; then
        echo -e "   Killing snapshot processes: $snapshot_pids"
        kill -9 $snapshot_pids 2>/dev/null
    fi
    
    flask_pids=$(pgrep -f "flask" 2>/dev/null)
    if [ ! -z "$flask_pids" ]; then
        echo -e "   Killing Flask processes: $flask_pids"
        kill -9 $flask_pids 2>/dev/null
    fi
    
    repo_python_pids=$(pgrep -f "python.*$REPO_ROOT" 2>/dev/null)
    if [ ! -z "$repo_python_pids" ]; then
        echo -e "   Killing Python processes from repo: $repo_python_pids"
        kill -9 $repo_python_pids 2>/dev/null
    fi
    
    echo -e "\n${GREEN}✅ All repository processes killed${NC}"
    echo -e "${GREEN}✅ All common ports cleared${NC}"
    
    echo -e "\n${YELLOW}🔍 Verifying cleanup...${NC}"
    sleep 2
    
    remaining_pids=$(pgrep -f "python.*($REPO_ROOT|whisperer|avatar|solver|snapshot|flask)" 2>/dev/null)
    if [ ! -z "$remaining_pids" ]; then
        echo -e "${RED}⚠️  Some processes still running: $remaining_pids${NC}"
        echo -e "${YELLOW}   Attempting final force kill...${NC}"
        kill -9 $remaining_pids 2>/dev/null
    else
        echo -e "${GREEN}✅ No remaining processes found${NC}"
    fi
    
    remaining_ports=""
    for PORT in 5000 5001 5002; do
        if lsof -ti:$PORT >/dev/null 2>&1; then
            remaining_ports="$remaining_ports $PORT"
        fi
    done
    if [ ! -z "$remaining_ports" ]; then
        echo -e "${RED}⚠️  Ports still in use:$remaining_ports${NC}"
        echo -e "${YELLOW}   You may need to kill them manually:${NC}"
        for PORT in $remaining_ports; do
            echo -e "   sudo lsof -ti:$PORT | xargs sudo kill -9"
        done
    else
        echo -e "${GREEN}✅ All ports are free${NC}"
    fi
}

# ---------------------------------------------------------------------------
#  FUNCTION: show_menu
# ---------------------------------------------------------------------------
show_menu() {
    echo -e "\n${CYAN}╔══════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║                 MAIN MENU                            ║${NC}"
    echo -e "${CYAN}╚══════════════════════════════════════════════════════╝${NC}"
    echo -e ""
    echo -e "${BOLD}1.${NC} 🔍 Scan & Show running processes from repo"
    echo -e "${BOLD}2.${NC} 📊 Check status of all apps (web, logs)"
    echo -e "${BOLD}3.${NC} 🛑 Kill ALL repo apps (with confirmation)"
    echo -e "${BOLD}4.${NC} 💀 Force kill ALL repo apps (no confirmation)"
    echo -e "${BOLD}5.${NC} 🎯 Kill specific process by PID"
    echo -e "${BOLD}6.${NC} 🚪 Exit"
    echo -e ""
    echo -e "${BLUE}══════════════════════════════════════════════════════${NC}"
}

# ---------------------------------------------------------------------------
#  FUNCTION: kill_specific_pid
# ---------------------------------------------------------------------------
kill_specific_pid() {
    echo -e "\n${YELLOW}🎯 Kill specific process${NC}"
    read -p "Enter PID to kill: " pid_to_kill
    
    if [[ ! "$pid_to_kill" =~ ^[0-9]+$ ]]; then
        echo -e "${RED}❌ Invalid PID format${NC}"
        return
    fi
    
    if ps -p $pid_to_kill >/dev/null 2>&1; then
        echo -e "Process found: $(ps -o command= -p $pid_to_kill)"
        read -p "Are you sure you want to kill PID $pid_to_kill? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            kill -9 $pid_to_kill 2>/dev/null
            if [ $? -eq 0 ]; then
                echo -e "${GREEN}✅ Successfully killed PID $pid_to_kill${NC}"
            else
                echo -e "${RED}❌ Failed to kill PID $pid_to_kill${NC}"
            fi
        else
            echo -e "${YELLOW}❌ Operation cancelled${NC}"
        fi
    else
        echo -e "${RED}❌ Process with PID $pid_to_kill not found${NC}"
    fi
}

# ---------------------------------------------------------------------------
#  MAIN INTERACTIVE LOOP
# ---------------------------------------------------------------------------
while true; do
    show_menu
    echo -n "Select option (1-6): "
    read choice
    
    case $choice in
        1)
            show_processes
            ;;
        2)
            check_status
            ;;
        3)
            show_processes
            kill_all_repo_processes "interactive"
            ;;
        4)
            show_processes
            kill_all_repo_processes "force"
            ;;
        5)
            kill_specific_pid
            ;;
        6)
            echo -e "\n${GREEN}👋 Goodbye!${NC}"
            exit 0
            ;;
        *)
            echo -e "${RED}❌ Invalid option. Please select 1-6${NC}"
            ;;
    esac
    
    echo -e "\n${YELLOW}Press Enter to continue...${NC}"
    read
done
