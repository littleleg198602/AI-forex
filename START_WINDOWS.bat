@echo off
setlocal
cd /d "%~dp0"
echo FOREX AI LAB - Windows launcher
echo.

where python >nul 2>nul
if errorlevel 1 (
    echo Python was not found. Please install Python 3.11+ from https://www.python.org/downloads/ and enable "Add Python to PATH".
    echo.
    pause
    exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
    echo Creating local virtual environment...
    python -m venv .venv
    if errorlevel 1 (
        echo Failed to create .venv.
        pause
        exit /b 1
    )
)

call ".venv\Scripts\activate.bat"
if errorlevel 1 (
    echo Failed to activate .venv.
    pause
    exit /b 1
)

python -m pip install -r requirements.txt
if errorlevel 1 (
    echo Dependency installation failed.
    pause
    exit /b 1
)

python run_menu.py

echo.
echo Launcher finished. Press any key to close this window.
pause >nul
endlocal
