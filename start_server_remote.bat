@echo off
REM Start BoschMCP_HSWPr Server for Remote Access
echo ========================================
echo Starting BoschMCP_HSWPr Server (Remote Access Enabled)
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Check if dependencies are installed
echo Checking dependencies...
python -c "import fastapi, uvicorn" >nul 2>&1
if errorlevel 1 (
    echo Installing dependencies...
    pip install -r requirements.txt
)

REM Start server on all network interfaces for remote access
echo.
echo Starting server on http://0.0.0.0:8000
echo Accessible via:
echo   - Local: http://127.0.0.1:8000
echo   - Remote: http://10.210.60.20:8000
echo.
echo Press Ctrl+C to stop
echo.

REM Set environment variables for remote access
set MCP_HOST=0.0.0.0
set MCP_PORT=8000

python BoschMCP_HSWPr\server.py
