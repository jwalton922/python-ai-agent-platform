@echo off
REM Windows batch startup script for AI Agent Platform

REM Get the directory of this script
set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"

REM Set Python path
set PYTHONPATH=%SCRIPT_DIR%;%PYTHONPATH%

echo 🚀 Starting AI Agent Platform
echo 📁 Project root: %SCRIPT_DIR%
echo 🐍 PYTHONPATH: %PYTHONPATH%

REM Check if virtual environment exists
if exist "venv\Scripts\activate.bat" (
    echo 🌐 Activating virtual environment...
    call venv\Scripts\activate.bat
) else if exist ".venv\Scripts\activate.bat" (
    echo 🌐 Activating virtual environment...
    call .venv\Scripts\activate.bat
)

REM Install dependencies if needed
if not exist ".last_install" (
    echo 📦 Installing dependencies...
    pip install -r requirements.txt
    echo. > .last_install
)

REM Run the application
echo 🎯 Starting unified server...
python run_unified.py

pause