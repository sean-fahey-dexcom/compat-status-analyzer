#!/bin/bash
# Launch script for COMPAT Status Analyzer Streamlit app
# Intended for use with systemd

set -e

APP_DIR="/Users/sj75203/workspace/compat-status-analyzer"
VENV_DIR="$APP_DIR/.venv"
APP_FILE="compat_status_analyzer.py"
PORT=8505

# Kill existing streamlit process for this app if running
pkill -f "streamlit run.*$APP_FILE" || true

# Wait for process to terminate
sleep 1

# Change to app directory
cd "$APP_DIR"

# Activate virtual environment and run streamlit
source "$VENV_DIR/bin/activate"
exec streamlit run "$APP_FILE" --server.port "$PORT" --server.headless true
