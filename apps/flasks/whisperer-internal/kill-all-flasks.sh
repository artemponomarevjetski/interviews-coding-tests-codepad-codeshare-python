#!/bin/bash
# kill-all-flasks.sh - Interactive kill script for all Flask apps

# Color codes for better UX
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# ASCII Art for header
echo -e "${CYAN}"
echo "╔══════════════════════════════════════════════════════╗"
echo "║      🛑 WHISPERER PROCESS KILLER - INTERACTIVE       ║"
echo "╚══════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Function to display process info
show_processes() {
    echo -e "\n${YELLOW}🔍 Scanning for running processes...${NC}"
    echo -e "${BLUE}══════════════════════════════════════════════════════${NC}"
    
    # Check PID file
    if [ -f "whisperer.pid" ]; then
        PID=$(cat whisperer.pid)
        echo -e "${BOLD}📄 Found PID file:${NC} whisperer.pid (PID: $PID)"
        ps -p $PID >/dev/null 2>&1
        if [ $? -eq 0 ]; then
            echo -e "   Status: ${GREEN}✅ RUNNING${NC}"
            ps -o pid,user,%cpu,%mem,start,command -p $PID | tail -1
        else
            echo -e "   Status: ${RED}❌ NOT RUNNING (stale PID file)${NC}"
        fi
    else
        echo -e "${YELLOW}📄 No whisperer.pid file found${NC}"
    fi
    
    echo -e "\n${BOLD}🔌 Checking ports 5000-5010:${NC}"
    local port_found=0
    for PORT in {5000..5010}; do
        PIDS=$(lsof -ti:$PORT 2>/dev/null)
        if [ ! -z "$PIDS" ]; then
            port_found=1
            echo -e "   Port ${CYAN}$PORT${NC}: ${RED}IN USE${NC} by PIDs: $PIDS"
            for pid in $PIDS; do
                echo -e "   └── PID $pid: $(ps -o command= -p $pid 2>/dev/null | head -c 50)"
            done
        fi
    done
    if [ $port_found -eq 0 ]; then
        echo -e "   ${GREEN}✅ All ports 5000-5010 are free${NC}"
    fi
    
    echo -e "\n${BOLD}👤 Checking process names:${NC}"
    local processes_found=0
    
    # Check for whisperer processes
    whisperer_pids=$(pgrep -f "python.*whisperer")
    if [ ! -z "$whisperer_pids" ]; then
        processes_found=1
        echo -e "   ${YELLOW}Whisperer processes:${NC} $whisperer_pids"
        for pid in $whisperer_pids; do
            echo -e "   └── PID $pid: $(ps -o command= -p $pid 2>/dev/null)"
        done
    fi
    
    # Check for Flask processes
    flask_pids=$(pgrep -f "flask")
    if [ ! -z "$flask_pids" ]; then
        processes_found=1
        echo -e "   ${YELLOW}Flask processes:${NC} $flask_pids"
        for pid in $flask_pids; do
            echo -e "   └── PID $pid: $(ps -o command= -p $pid 2>/dev/null)"
        done
    fi
    
    # Check for Python app processes
    python_pids=$(pgrep -f "python.*app")
    if [ ! -z "$python_pids" ]; then
        processes_found=1
        echo -e "   ${YELLOW}Python app processes:${NC} $python_pids"
        for pid in $python_pids; do
            echo -e "   └── PID $pid: $(ps -o command= -p $pid 2>/dev/null | head -c 60)"
        done
    fi
    
    if [ $processes_found -eq 0 ]; then
        echo -e "   ${GREEN}✅ No running whisperer/Flask/Python app processes found${NC}"
    fi
    
    echo -e "${BLUE}══════════════════════════════════════════════════════${NC}"
}

# Function to kill processes
kill_processes() {
    local kill_mode=$1
    
    echo -e "\n${RED}⚠️  WARNING: This will kill processes!${NC}"
    
    if [ "$kill_mode" != "force" ]; then
        read -p "Are you sure you want to proceed? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo -e "${YELLOW}❌ Operation cancelled${NC}"
            exit 0
        fi
    fi
    
    echo -e "\n${RED}🛑 Killing processes...${NC}"
    
    # Kill by PID file
    if [ -f "whisperer.pid" ]; then
        PID=$(cat whisperer.pid)
        echo -e "${YELLOW}📄 Killing PID from file: $PID${NC}"
        kill -9 $PID 2>/dev/null
        if [ $? -eq 0 ]; then
            echo -e "   ${GREEN}✅ Successfully killed PID $PID${NC}"
        else
            echo -e "   ${YELLOW}⚠️  Process $PID not found or already terminated${NC}"
        fi
        rm -f whisperer.pid
    fi
    
    # Kill by port
    echo -e "\n${YELLOW}🔌 Clearing ports 5000-5010...${NC}"
    for PORT in {5000..5010}; do
        PIDS=$(lsof -ti:$PORT 2>/dev/null)
        if [ ! -z "$PIDS" ]; then
            echo -e "   Killing processes on port ${CYAN}$PORT${NC}: $PIDS"
            kill -9 $PIDS 2>/dev/null
        fi
    done
    
    # Kill by name
    echo -e "\n${YELLOW}👤 Killing by process name...${NC}"
    
    # Whisperer processes
    whisperer_pids=$(pgrep -f "python.*whisperer")
    if [ ! -z "$whisperer_pids" ]; then
        echo -e "   Killing whisperer processes: $whisperer_pids"
        kill -9 $whisperer_pids 2>/dev/null
    fi
    
    # Flask processes
    flask_pids=$(pgrep -f "flask")
    if [ ! -z "$flask_pids" ]; then
        echo -e "   Killing Flask processes: $flask_pids"
        kill -9 $flask_pids 2>/dev/null
    fi
    
    # Python app processes
    python_pids=$(pgrep -f "python.*app")
    if [ ! -z "$python_pids" ]; then
        echo -e "   Killing Python app processes: $python_pids"
        kill -9 $python_pids 2>/dev/null
    fi
    
    echo -e "\n${GREEN}✅ All whisperer processes killed${NC}"
    echo -e "${GREEN}✅ Ports 5000-5010 cleared${NC}"
    
    # Verify cleanup
    echo -e "\n${YELLOW}🔍 Verifying cleanup...${NC}"
    sleep 1
    show_processes | tail -20
}

# Function to display menu
show_menu() {
    echo -e "\n${CYAN}╔══════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║                    MAIN MENU                         ║${NC}"
    echo -e "${CYAN}╚══════════════════════════════════════════════════════╝${NC}"
    echo -e ""
    echo -e "${BOLD}1.${NC} 🔍 Scan & Show running processes"
    echo -e "${BOLD}2.${NC} 🛑 Kill all whisperer/Flask processes (with confirmation)"
    echo -e "${BOLD}3.${NC} 💀 Force kill all processes (no confirmation)"
    echo -e "${BOLD}4.${NC} 🎯 Kill specific process by PID"
    echo -e "${BOLD}5.${NC} 🚪 Exit"
    echo -e ""
    echo -e "${BLUE}══════════════════════════════════════════════════════${NC}"
}

# Function to kill specific PID
kill_specific_pid() {
    echo -e "\n${YELLOW}🎯 Kill specific process${NC}"
    read -p "Enter PID to kill: " pid_to_kill
    
    # Validate input
    if [[ ! "$pid_to_kill" =~ ^[0-9]+$ ]]; then
        echo -e "${RED}❌ Invalid PID format${NC}"
        return
    fi
    
    # Check if process exists
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

# Main interactive loop
while true; do
    show_menu
    echo -n "Select option (1-5): "
    read choice
    
    case $choice in
        1)
            show_processes
            ;;
        2)
            show_processes
            kill_processes "interactive"
            ;;
        3)
            show_processes
            kill_processes "force"
            ;;
        4)
            kill_specific_pid
            ;;
        5)
            echo -e "\n${GREEN}👋 Goodbye!${NC}"
            exit 0
            ;;
        *)
            echo -e "${RED}❌ Invalid option. Please select 1-5${NC}"
            ;;
    esac
    
    echo -e "\n${YELLOW}Press Enter to continue...${NC}"
    read
done
