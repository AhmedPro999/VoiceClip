@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Run install.bat first.
  pause
  exit /b 1
)
echo This downloads about 4 GB of packages. Safe to re-run: it resumes where it stopped.
echo [1/2] Whisper, CUDA libs, translation libs...
".venv\Scripts\python.exe" -m pip install --timeout 60 --retries 20 --resume-retries 50 -r requirements-offline.txt
echo [2/2] PyTorch (CUDA 12.6 build)...
".venv\Scripts\python.exe" -m pip install --timeout 60 --retries 20 --resume-retries 50 torch --index-url https://download.pytorch.org/whl/cu126
echo.
echo Done. Switch "mode" to "offline" from the tray menu. Models download on first use.
pause
