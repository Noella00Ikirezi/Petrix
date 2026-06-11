@echo off
REM PentestAI Build Script for Windows
REM Creates standalone executable

echo ========================================
echo   PentestAI Build for Windows
echo ========================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [!] Python not found
    pause
    exit /b 1
)

REM Activate venv if exists
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

REM Run build script
python build.py

echo.
pause
