@echo off
cd /d "%~dp0"
set SHORTCUT=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\VoiceClip.lnk
powershell -NoProfile -Command ^
  "$s=(New-Object -ComObject WScript.Shell).CreateShortcut('%SHORTCUT%');" ^
  "$s.TargetPath='%~dp0.venv\Scripts\pythonw.exe';" ^
  "$s.Arguments='app.py';" ^
  "$s.WorkingDirectory='%~dp0';" ^
  "$s.Description='VoiceClip';" ^
  "$s.Save()"
echo VoiceClip will now start with Windows.
echo To remove: delete "%SHORTCUT%"
pause
