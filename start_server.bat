@echo off
REM Start BoschMCP_HSWPr Server
echo ========================================
echo Starting BoschMCP_HSWPr Server
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

REM Start server
echo.
echo Starting server on http://127.0.0.1:8000
echo Press Ctrl+C to stop
echo.
python BoschMCP_HSWPr\server.py
