#!/bin/bash

# CrewAI Blog Generator - Debug Script
# This script helps diagnose issues with the application

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Create logs directory
mkdir -p logs

echo -e "${BLUE}🔍 CrewAI Blog Generator - Debug Information${NC}"
echo "=================================================="
echo ""

# System Information
echo -e "${GREEN}📊 System Information${NC}"
echo "Date: $(date)"
echo "System: $(uname -a)"
echo "Shell: $SHELL"
echo "User: $(whoami)"
echo "Working Directory: $(pwd)"
echo ""

# Check prerequisites
echo -e "${GREEN}🔧 Prerequisites Check${NC}"
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

check_command() {
    local cmd=$1
    if command_exists "$cmd"; then
        local version=$($cmd --version 2>&1 | head -n1)
        echo -e "  ✅ $cmd: $version"
    else
        echo -e "  ❌ $cmd: Not installed"
    fi
}

check_command python3
check_command node
check_command npm
check_command curl
check_command lsof
check_command git
echo ""

# Port availability
echo -e "${GREEN}🌐 Port Availability${NC}"
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo -e "  ❌ Port $port: In use"
        lsof -Pi :$port -sTCP:LISTEN
    else
        echo -e "  ✅ Port $port: Available"
    fi
}

check_port 8000
check_port 3000
echo ""

# Project Structure
echo -e "${GREEN}📁 Project Structure${NC}"
check_file() {
    local file=$1
    local desc=$2
    if [ -f "$file" ]; then
        local size=$(ls -lah "$file" | awk '{print $5}')
        echo -e "  ✅ $desc: $file ($size)"
    elif [ -d "$file" ]; then
        local count=$(ls -1 "$file" 2>/dev/null | wc -l)
        echo -e "  ✅ $desc: $file ($count items)"
    else
        echo -e "  ❌ $desc: $file (missing)"
    fi
}

check_file "backend" "Backend Directory"
check_file "frontend" "Frontend Directory"
check_file "backend/main.py" "Backend Startup Script" 
check_file "backend/requirements.txt" "Backend Requirements"
check_file "frontend/package.json" "Frontend Package Config"
check_file "frontend/src/App.jsx" "Frontend Application"
check_file "backend/.env" "Environment Variables"
check_file "start.sh" "Startup Script"
echo ""

# Python Environment
echo -e "${GREEN}🐍 Python Environment${NC}"
if command_exists python3; then
    echo "Python executable: $(which python3)"
    echo "Python version: $(python3 --version)"
    echo "Python path: $(python3 -c 'import sys; print(sys.executable)')"
    
    # Check if we can access the backend directory
    cd backend 2>/dev/null || { echo -e "  ❌ Cannot access backend directory"; exit 1; }
    
    echo ""
    echo "Python modules check:"
    
    check_python_module() {
        local module=$1
        python3 -c "import $module; print(f'  ✅ $module: {$module.__version__ if hasattr($module, \"__version__\") else \"installed\"}')" 2>/dev/null || echo -e "  ❌ $module: Not installed"
    }
    
    check_python_module fastapi
    check_python_module uvicorn
    check_python_module pydantic
    check_python_module crewai
    check_python_module langchain_google_genai
    check_python_module dotenv
    check_python_module axios
    
    cd ..
fi
echo ""

# Node.js Environment
echo -e "${GREEN}📦 Node.js Environment${NC}"
if command_exists node; then
    echo "Node executable: $(which node)"
    echo "Node version: $(node --version)"
    echo "npm version: $(npm --version)"
    
    if [ -d "frontend" ]; then
        cd frontend
        echo ""
        echo "Frontend dependencies:"
        if [ -f "package.json" ]; then
            echo "  Package.json found"
            if [ -d "node_modules" ]; then
                modules_count=$(ls -1 node_modules 2>/dev/null | wc -l)
                echo -e "  ✅ node_modules: $modules_count packages installed"
            else
                echo -e "  ❌ node_modules: Not found (run npm install)"
            fi
        else
            echo -e "  ❌ package.json: Not found"
        fi
        cd ..
    fi
fi
echo ""

# Environment Variables
echo -e "${GREEN}🔐 Environment Variables${NC}"
if [ -f "backend/.env" ]; then
    echo "  ✅ .env file found"
    
    # Check for required variables without showing values
    check_env_var() {
        local var=$1
        if grep -q "^$var=" "backend/.env" 2>/dev/null; then
            echo -e "  ✅ $var: Configured"
        else
            echo -e "  ❌ $var: Not found"
        fi
    }
    
else
    echo -e "  ❌ .env file not found in backend directory"
    echo "     Create backend/.env "
fi
echo ""

# Recent Logs
echo -e "${GREEN}📄 Recent Logs${NC}"
if [ -d "logs" ]; then
    log_count=$(ls -1 logs 2>/dev/null | wc -l)
    if [ $log_count -gt 0 ]; then
        echo "  Found $log_count log files:"
        ls -lt logs | head -5 | while read line; do
            echo "    $line"
        done
        
        # Show last few lines of most recent log
        latest_log=$(ls -t logs/*.log 2>/dev/null | head -1)
        if [ -n "$latest_log" ]; then
            echo ""
            echo "  Last 10 lines from: $latest_log"
            echo "  ----------------------------------------"
            tail -10 "$latest_log" 2>/dev/null || echo "    (Could not read log file)"
        fi
    else
        echo "  No log files found"
    fi
else
    echo "  No logs directory found"
fi
echo ""

# Running Processes
echo -e "${GREEN}🏃 Running Processes${NC}"
check_process() {
    local pattern=$1
    local desc=$2
    local pids=$(pgrep -f "$pattern" 2>/dev/null || true)
    if [ -n "$pids" ]; then
        echo -e "  ✅ $desc:"
        echo "$pids" | while read pid; do
            local cmd=$(ps -p $pid -o command= 2>/dev/null || echo "Unknown")
            echo "    PID $pid: $cmd"
        done
    else
        echo -e "  ❌ $desc: Not running"
    fi
}



# Network Connectivity
echo -e "${GREEN}🌍 Network Connectivity${NC}"
check_url() {
    local url=$1
    local desc=$2
    if curl -f -s --connect-timeout 5 "$url" >/dev/null 2>&1; then
        echo -e "  ✅ $desc: $url"
    else
        echo -e "  ❌ $desc: $url (not reachable)"
    fi
}

check_url "http://localhost:8052" "Frontend"
check_url "http://localhost:8052/health" "Backend Health"
check_url "http://localhost:8052/docs" "API Documentation"
echo ""

# Disk Space
echo -e "${GREEN}💾 Disk Space${NC}"
df -h . | head -2
echo ""

# Memory Usage
echo -e "${GREEN}🧠 Memory Usage${NC}"
free -h
echo ""

echo -e "${BLUE}🎯 Quick Troubleshooting Tips:${NC}"
echo "1. If ports are in use: kill the processes or use different ports"
echo "2. If modules are missing: run 'pip install -r backend/requirements.txt'"
echo "3. If frontend deps missing: run 'cd frontend && npm install'"
echo "4. If .env is missing: create backend/.env with your API keys"
echo "5. Check recent logs in the logs/ directory for detailed errors"
echo "6. Use 'DEBUG=true ./start.sh' for verbose startup logging"
echo ""

echo -e "${GREEN}✅ Debug information collected successfully!${NC}"
