#!/bin/bash
# Start BoschMCP_HSWPr Server

echo "========================================"
echo "Starting BoschMCP_HSWPr Server"
echo "========================================"
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed or not in PATH"
    exit 1
fi

# Check if dependencies are installed
echo "Checking dependencies..."
python3 -c "import fastapi, uvicorn" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Installing dependencies..."
    pip3 install -r requirements.txt
fi

# Start server
echo ""
echo "Starting server on http://127.0.0.1:8000"
echo "Press Ctrl+C to stop"
echo ""
python3 server.py
