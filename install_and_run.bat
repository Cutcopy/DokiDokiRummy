@echo off
echo ========================================
echo  Rummy 500 - Setup and Launch
echo ========================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed.
    echo.
    echo Please install Python 3.8+ from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

echo Installing pygame-ce (Python 3.14 compatible)...
python -m pip install pygame-ce --quiet
if errorlevel 1 (
    echo Failed to install pygame. Try running as administrator.
    pause
    exit /b 1
)

echo Launching Rummy 500...
python main.py
