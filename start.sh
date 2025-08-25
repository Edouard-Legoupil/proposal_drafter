#!/bin/bash

set -euo pipefail  # Exit on error, undefined vars, pipe failures

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging configuration
LOG_DIR="logs"
LOG_FILE="$LOG_DIR/startup_$(date '+%Y%m%d_%H%M%S').log"
ERROR_LOG="$LOG_DIR/error_$(date '+%Y%m%d_%H%M%S').log"

# Create logs directory
mkdir -p "$LOG_DIR"

# Logging functions
log_info() {
    local msg="$1"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${GREEN}[INFO]${NC} $msg" | tee -a "$LOG_FILE"
}

log_warning() {
    local msg="$1"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${YELLOW}[WARN]${NC} $msg" | tee -a "$LOG_FILE"
}

log_error() {
    local msg="$1"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${RED}[ERROR]${NC} $msg" | tee -a "$LOG_FILE" | tee -a "$ERROR_LOG"
}

log_debug() {
    local msg="$1"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    if [[ "${DEBUG:-false}" == "true" ]]; then
        echo -e "${BLUE}[DEBUG]${NC} $msg" | tee -a "$LOG_FILE"
    else
        echo "[$timestamp] [DEBUG] $msg" >> "$LOG_FILE"
    fi
}

# Global variables for process tracking
BACKEND_PID=""
FRONTEND_PID=""
STARTUP_FAILED=false

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if port is available
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 1  # Port is busy
    else
        return 0  # Port is available
    fi
}

# Function to wait for service to be ready
wait_for_service() {
    local url=$1
    local service_name=$2
    local max_attempts=30
    local attempt=0
    
    log_info "Waiting for $service_name to be ready at $url..."
    
    while [ $attempt -lt $max_attempts ]; do
        if curl -f -s "$url" >/dev/null 2>&1; then
            log_info "$service_name is ready!"
            return 0
        fi
        
        attempt=$((attempt + 1))
        log_debug "Attempt $attempt/$max_attempts: $service_name not ready yet..."
        sleep 2
    done
    
    log_error "$service_name failed to start within $(($max_attempts * 2)) seconds"
    return 1
}

# Function to gracefully shutdown services
graceful_shutdown() {
    local exit_code=${1:-0}
    
    log_info "Initiating graceful shutdown..."
    
    # Stop frontend first (usually faster to stop)
    if [[ -n "$FRONTEND_PID" ]] && kill -0 "$FRONTEND_PID" 2>/dev/null; then
        log_info "Stopping frontend server (PID: $FRONTEND_PID)..."
        kill -TERM "$FRONTEND_PID" 2>/dev/null || true
        
        # Wait for graceful shutdown
        local count=0
        while kill -0 "$FRONTEND_PID" 2>/dev/null && [ $count -lt 10 ]; do
            sleep 1
            count=$((count + 1))
        done
        
        # Force kill if still running
        if kill -0 "$FRONTEND_PID" 2>/dev/null; then
            log_warning "Force killing frontend server..."
            kill -KILL "$FRONTEND_PID" 2>/dev/null || true
        fi
        
        log_info "Frontend server stopped"
    fi
    
    # Stop backend
    if [[ -n "$BACKEND_PID" ]] && kill -0 "$BACKEND_PID" 2>/dev/null; then
        log_info "Stopping backend server (PID: $BACKEND_PID)..."
        kill -TERM "$BACKEND_PID" 2>/dev/null || true
        
        # Wait for graceful shutdown
        local count=0
        while kill -0 "$BACKEND_PID" 2>/dev/null && [ $count -lt 15 ]; do
            sleep 1
            count=$((count + 1))
        done
        
        # Force kill if still running
        if kill -0 "$BACKEND_PID" 2>/dev/null; then
            log_warning "Force killing backend server..."
            kill -KILL "$BACKEND_PID" 2>/dev/null || true
        fi
        
        log_info "Backend server stopped"
    fi
    
    # Clean up any remaining processes
    pkill -f "python.*run.py" 2>/dev/null || true
    pkill -f "npm.*start" 2>/dev/null || true
    
    if [ $exit_code -eq 0 ]; then
        log_info "Shutdown completed successfully"
    else
        log_error "Shutdown completed with errors (exit code: $exit_code)"
    fi
    
    log_info "Logs saved to: $LOG_FILE"
    if [ -f "$ERROR_LOG" ]; then
        log_info "Error logs saved to: $ERROR_LOG"
    fi
    
    exit $exit_code
}

# Error handler
error_handler() {
    local line_number=$1
    local command="$2"
    log_error "Script failed at line $line_number: $command"
    STARTUP_FAILED=true
    graceful_shutdown 1
}

# Set up error handling
trap 'error_handler ${LINENO} "$BASH_COMMAND"' ERR
trap 'graceful_shutdown 0' INT TERM




# Main startup process
main() {
    log_info "🤖 Starting Proposal Generator..."
    log_info "Startup log: $LOG_FILE"
    log_debug "Debug mode: ${DEBUG:-false}"
    
    # System information
    log_debug "System: $(uname -a)"
    log_debug "Shell: $SHELL"
    log_debug "User: $(whoami)"
    log_debug "Working directory: $(pwd)"
    
    # Check prerequisites
    log_info "📋 Checking prerequisites..."
    
    if ! command_exists python3; then
        log_error "Python 3 is not installed"
        graceful_shutdown 1
    fi
    
    if ! command_exists node; then
        log_error "Node.js is not installed"
        graceful_shutdown 1
    fi
    
    if ! command_exists npm; then
        log_error "npm is not installed"
        graceful_shutdown 1
    fi
    
    if ! command_exists curl; then
        log_error "curl is not installed (required for health checks)"
        graceful_shutdown 1
    fi
    
    # Version information
    local python_version=$(python3 --version 2>&1)
    local node_version=$(node --version 2>&1)
    local npm_version=$(npm --version 2>&1)
    
    log_info "✅ Prerequisites check passed"
    log_debug "Python: $python_version"
    log_debug "Node.js: $node_version"
    log_debug "npm: $npm_version"
    
    # Check ports
    log_info "🔍 Checking port availability..."
    



    if ! check_port 8502; then
        log_error "Port 8502 is already in use (required for backend)"
        log_info "Please stop the service using port 8502 or change the backend port"
        graceful_shutdown 1
    fi
    
    if ! check_port 8503; then
        log_error "Port 8503 is already in use (required for frontend)"
        log_info "Please stop the service using port 8503 or change the frontend port"
        graceful_shutdown 1
    fi
    
    log_info "✅ Ports 8502 and 8503 are available"
    
    # Check project structure
    log_info "📁 Validating project structure..."
    
    if [ ! -d "backend" ]; then
        log_error "Backend directory not found"
        graceful_shutdown 1
    fi
    
    if [ ! -d "frontend" ]; then
        log_error "Frontend directory not found"
        graceful_shutdown 1
    fi
    
    if [ ! -f "backend/main.py" ]; then
        log_error "Backend startup script (main.py) not found"
        graceful_shutdown 1
    fi
    
    if [ ! -f "frontend/package.json" ]; then
        log_error "Frontend package.json not found"
        graceful_shutdown 1
    fi
    
    log_info "✅ Project structure is valid"
    
    # Check environment configuration
    if [ ! -f "backend/.env" ]; then
        log_warning "backend/.env file not found"
        log_info "Please create it with your API keys:"
        log_info ""
        
        if [[ "${INTERACTIVE:-true}" == "true" ]]; then
            read -p "Press Enter to continue anyway, or Ctrl+C to exit..."
        else
            log_warning "Running in non-interactive mode, continuing without .env file..."
        fi
    else
        log_info "✅ Environment file found"
        
    fi
    
    # Check dependencies
    log_info "📦 Checking dependencies..."
    
    if [ ! -f "backend/requirements.txt" ]; then
        log_error "Backend requirements.txt not found"
        graceful_shutdown 1
    fi
    
    if [ ! -d "frontend/node_modules" ]; then
        log_warning "Frontend node_modules not found, running npm install..."
        cd frontend
        if ! npm install >> "../$LOG_FILE" 2>&1; then
            log_error "Failed to install frontend dependencies"
            cd ..
            graceful_shutdown 1
        fi
        cd ..
        log_info "✅ Frontend dependencies installed"
    else
        log_info "✅ Frontend dependencies found"
    fi
    



    # Start backend server
    log_info "🚀 Starting backend server..."
    cd backend
    
    # Create a virtual environment                                                                                                                                                             
    python3 -m venv venv                                                                                                                                                                       
                                                                                                                                                                                                
    # Activate the virtual environment                                                                                                                                                         
    source venv/bin/activate                                                                                                                                                                   
                                                                                                                                                                                                
    # Install dependencies (example)                                                                                                                                                           
    pip install -r requirements.txt 


    # Start backend with enhanced logging
    uvicorn main:app --host 0.0.0.0 --port 8502 --reload  >> "../$LOG_FILE" 2>&1 &
    BACKEND_PID=$!
    cd ..
    
    log_info "Backend server started with PID: $BACKEND_PID"
    log_debug "Backend logs are being written to $LOG_FILE"
    
    # Wait for backend to be ready
    # if ! wait_for_service "http://localhost:8502/health" "Backend"; then
    #     log_error "Backend failed to start properly"
    #     graceful_shutdown 1
    # fi
    
    # Start frontend server
    log_info "🌐 Starting frontend server..."
    cd frontend
    npm install
    # Set environment variable to suppress browser opening
    export BROWSER=none
    
    npm run build >> "../$LOG_FILE" 2>&1 &
    FRONTEND_PID=$!
    cd ..
    
    log_info "Frontend server started with PID: $FRONTEND_PID"
    log_debug "Frontend logs are being written to $LOG_FILE"
    
    # # Wait for frontend to be ready
    # if ! wait_for_service "http://localhost:8503" "Frontend"; then
    #     log_error "Frontend failed to start properly"
    #     graceful_shutdown 1
    # fi
    
    # Success!
    log_info "🎉 CrewAI Blog Generator is now running!"
    log_info ""
    log_info "📍 Frontend App: http://localhost:8502" 
    log_info "📍 API Documentation: http://localhost:8502/docs"
    log_info ""
    log_info "📊 System Status:"
    log_info "  - Backend PID: $BACKEND_PID"
    log_info "  - Frontend PID: $FRONTEND_PID"
    log_info "  - Log file: $LOG_FILE"
    log_info ""
    log_info "Press Ctrl+C to stop both servers"
    
    # Monitor processes
    while true; do
        # Check if backend is still running
        if ! kill -0 "$BACKEND_PID" 2>/dev/null; then
            log_error "Backend process died unexpectedly"
            graceful_shutdown 1
        fi
        
        # # Check if frontend is still running
        # if ! kill -0 "$FRONTEND_PID" 2>/dev/null; then
        #     log_error "Frontend process died unexpectedly"
        #     graceful_shutdown 1
        # fi
        
        sleep 5
    done
}

# Run main function
main "$@"
