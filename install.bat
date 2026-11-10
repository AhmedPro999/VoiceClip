@echo off
cd /d "%~dp0"
echo ============================================
echo  VoiceClip - install
echo ============================================
where python >nul 2>nul
if errorlevel 1 (
  echo Python was not found. Install Python 3.11+ from https://www.python.org/downloads/
  echo and tick "Add Python to PATH" during setup, then run this file again.
  pause
  exit /b 1
)
echo [1/3] Creating virtual environment...
if not exist ".venv" python -m venv .venv
echo [2/3] Installing packages (about 150 MB, once)...
".venv\Scripts\python.exe" -m pip install --upgrade pip
".venv\Scripts\python.exe" -m pip install --timeout 60 --retries 20 --resume-retries 50 -r requirements.txt
if errorlevel 1 (
  echo.
  echo Install failed. Check your internet connection and run install.bat again - it resumes.
  pause
  exit /b 1
)
echo [3/3] Creating config.json...
if not exist "config.json" copy /y "config.example.json" "config.json" >nul
echo.
echo Done!
echo  1. Get a free Gemini API key: https://aistudio.google.com/apikey
echo  2. Open config.json and paste it into "api_key" (inside the quotes).
echo  3. Run run.bat - the mic icon appears next to the clock.
echo.
echo Offline mode (optional, ~4 GB download): run install_offline.bat later.
pause
