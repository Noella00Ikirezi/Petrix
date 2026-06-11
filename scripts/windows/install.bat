@echo off
REM PentestAI Installation Script for Windows (CMD)
REM Run as Administrator
REM Usage: install.bat

echo ========================================
echo   PentestAI Installation for Windows
echo ========================================
echo.

REM Check Python
echo [*] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo [!] Python not found. Please install Python 3.11+
    echo     Download from: https://www.python.org/downloads/
    pause
    exit /b 1
)
python --version

REM Check nmap
echo [*] Checking nmap installation...
if exist "C:\Program Files (x86)\Nmap\nmap.exe" (
    echo     Found: C:\Program Files ^(x86^)\Nmap\nmap.exe
) else if exist "C:\Program Files\Nmap\nmap.exe" (
    echo     Found: C:\Program Files\Nmap\nmap.exe
) else (
    nmap --version >nul 2>&1
    if errorlevel 1 (
        echo [!] nmap not found. Please install nmap:
        echo     Download from: https://nmap.org/download.html
        pause
        exit /b 1
    )
)

REM Create virtual environment
echo [*] Creating virtual environment...
if not exist "venv" (
    python -m venv venv
    echo     Created: venv\
) else (
    echo     Virtual environment already exists
)

REM Activate and install
echo [*] Installing dependencies...
call venv\Scripts\activate.bat
python -m pip install --upgrade pip --quiet
pip install -e . --quiet
echo     Dependencies installed

REM Create config
echo [*] Creating configuration...
if not exist ".env" (
    copy .env.example .env >nul
    echo     Created .env (remember to update SECRET_KEY!)
) else (
    echo     .env already exists
)

REM Create directories
echo [*] Creating directories...
if not exist "data" mkdir data
if not exist "logs" mkdir logs
if not exist "reports" mkdir reports

echo.
echo ========================================
echo   Installation Complete!
echo ========================================
echo.
echo Usage:
echo   1. Activate environment:  venv\Scripts\activate.bat
echo   2. Run CLI demo:          python -m src.cli.main demo
echo   3. Scan a target:         python -m src.cli.main scan 192.168.1.1
echo   4. Start web interface:   uvicorn src.web.app:app --host 127.0.0.1 --port 8000
echo.
pause
