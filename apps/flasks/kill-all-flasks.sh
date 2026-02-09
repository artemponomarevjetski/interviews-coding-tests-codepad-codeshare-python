#!/bin/bash
# kill-all-flasks.sh - Interactive kill script for all Flask apps

# Color codes for better UX
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
PURPLE='\033[0;35m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# ASCII Art for header
echo -e "${CYAN}"
echo "╔══════════════════════════════════════════════════════╗"
echo "║           WHISPERER CONTROL PANEL                    ║"
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

# Function to check whisperer status
check_status() {
    echo -e "\n${PURPLE}📊 WHISPERER STATUS CHECK${NC}"
    echo -e "${BLUE}══════════════════════════════════════════════════════${NC}"
    
    # Check PID file
    if [ -f "whisperer.pid" ]; then
        PID=$(cat whisperer.pid)
        echo -e "${BOLD}📄 PID File:${NC} whisperer.pid (PID: ${CYAN}$PID${NC})"
        
        if ps -p $PID >/dev/null 2>&1; then
            echo -e "   Status: ${GREEN}✅ RUNNING${NC}"
            
            # Show process details
            echo -e "   ${BOLD}📈 Resource Usage:${NC}"
            ps -o pid,user,%cpu,%mem,etime,command -p $PID | tail -1 | while read line; do
                echo "   $line" | awk '{printf "   CPU: %s%%  MEM: %s%%  UPTIME: %s\n   CMD: %s %s %s\n", $3, $4, $5, $6, $7, $8}'
            done
            
            # Check if it's using audio
            echo -e "\n   ${BOLD}🎤 Audio Status:${NC}"
            if lsof -p $PID 2>/dev/null | grep -q -i "sounddevice\|portaudio\|coreaudio"; then
                echo -e "   ${GREEN}✅ Audio device is active${NC}"
            else
                echo -e "   ${YELLOW}⚠️  Audio device may not be active${NC}"
            fi
        else
            echo -e "   Status: ${RED}❌ NOT RUNNING (stale PID file)${NC}"
        fi
    else
        echo -e "${YELLOW}📄 No PID file found${NC}"
    fi
    
    # Check web interface
    echo -e "\n${BOLD}🌐 Web Interface:${NC}"
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/ 2>/dev/null || echo "000")
    
    if [ "$HTTP_CODE" = "200" ]; then
        echo -e "   ${GREEN}✅ http://localhost:5000 is responding${NC}"
        
        # Try to get recent transcriptions
        echo -e "   ${BOLD}📝 Recent Transcriptions:${NC}"
        curl -s http://localhost:5000/ 2>/dev/null | grep -o '>[^<]*<' | sed 's/[<>]//g' | grep -v 'Live Number' | head -5 | while read line; do
            if [ -n "$line" ]; then
                echo -e "   📄 $line"
            fi
        done
        
        if [ $? -ne 0 ]; then
            echo -e "   ${YELLOW}No transcriptions displayed on page${NC}"
        fi
    elif [ "$HTTP_CODE" = "000" ]; then
        echo -e "   ${RED}❌ http://localhost:5000 is not responding (connection refused)${NC}"
    else
        echo -e "   ${YELLOW}⚠️  http://localhost:5000 returned HTTP $HTTP_CODE${NC}"
    fi
    
    # Check log file
    echo -e "\n${BOLD}📋 Recent Logs:${NC}"
    if [ -f "logs/flask_app.log" ]; then
        LOG_SIZE=$(stat -f%z "logs/flask_app.log" 2>/dev/null || echo "0")
        if [ "$LOG_SIZE" -gt 1000 ]; then
            echo -e "   Last 3 log entries:"
            tail -3 "logs/flask_app.log" | while read line; do
                # Truncate long lines
                if [ ${#line} -gt 80 ]; then
                    echo -e "   📄 ${line:0:77}..."
                else
                    echo -e "   📄 $line"
                fi
            done
        else
            echo -e "   ${YELLOW}Log file exists but is small or empty${NC}"
        fi
    else
        echo -e "   ${YELLOW}No log file found at logs/flask_app.log${NC}"
    fi
    
    # Quick system check
    echo -e "\n${BOLD}⚙️  System Check:${NC}"
    
    # Check if port 5000 is in use
    if lsof -ti:5000 >/dev/null 2>&1; then
        PORT_PIDS=$(lsof -ti:5000 | tr '\n' ' ')
        echo -e "   ${YELLOW}Port 5000: IN USE by PIDs: $PORT_PIDS${NC}"
    else
        echo -e "   ${GREEN}Port 5000: FREE${NC}"
    fi
    
    # Check Python environment
    if [ -d "venv" ]; then
        echo -e "   ${GREEN}Virtual environment: EXISTS${NC}"
    else
        echo -e "   ${YELLOW}Virtual environment: NOT FOUND${NC}"
    fi
    
    echo -e "\n${BOLD}🎯 Recommended Action:${NC}"
    if [ -f "whisperer.pid" ] && ps -p $(cat whisperer.pid 2>/dev/null) >/dev/null 2>&1; then
        echo -e "   💡 App appears to be running."
        echo -e "   💡 To stop gracefully: ${CYAN}Choose option 3${NC}"
        echo -e "   💡 To force stop: ${CYAN}Choose option 4${NC}"
        echo -e "   💡 To view live logs: ${CYAN}tail -f logs/flask_app.log${NC}"
    else
        echo -e "   💡 App does not appear to be running."
        echo -e "   💡 To start: ${CYAN}./set-up-and-launch-whisperer-internal.sh${NC}"
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
    echo -e "${BOLD}2.${NC} 📊 Check whisperer status (web, logs, audio)"
    echo -e "${BOLD}3.${NC} 🛑 Kill all whisperer/Flask processes (with confirmation)"
    echo -e "${BOLD}4.${NC} 💀 Force kill all processes (no confirmation)"
    echo -e "${BOLD}5.${NC} 🎯 Kill specific process by PID"
    echo -e "${BOLD}6.${NC} 🚪 Exit"
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
            kill_processes "interactive"
            ;;
        4)
            show_processes
            kill_processes "force"
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