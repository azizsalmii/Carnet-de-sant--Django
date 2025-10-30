@echo off
REM ==========================================
REM Start Django with ngrok tunnel
REM ==========================================

echo.
echo ========================================
echo   Django + ngrok Quick Start
echo ========================================
echo.

REM Check if ngrok is installed
where ngrok >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] ngrok is not installed!
    echo.
    echo Please install ngrok:
    echo   1. Download from https://ngrok.com/download
    echo   2. Extract to a folder in your PATH
    echo   3. Run: ngrok config add-authtoken YOUR_TOKEN
    echo.
    pause
    exit /b 1
)

REM Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo [ERROR] Virtual environment not found!
    echo.
    echo Please create it first:
    echo   python -m venv venv
    echo   venv\Scripts\activate
    echo   pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

echo [1/3] Activating virtual environment...
call venv\Scripts\activate.bat

echo [2/3] Setting environment variables...
set NGROK=true
set DEBUG=True
set ENABLE_HF_MODELS=0

echo [3/3] Starting Django server...
echo.
echo ========================================
echo   Django server starting on port 8000
echo ========================================
echo.
echo Open a NEW terminal and run:
echo   ngrok http 8000
echo.
echo Then visit the ngrok URL shown!
echo.
echo Press Ctrl+C to stop the server
echo ========================================
echo.

python manage.py runserver 0.0.0.0:8000
