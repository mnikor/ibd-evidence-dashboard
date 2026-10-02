@echo off
REM Double-click to start the IBD Evidence Intelligence dashboard on Windows.
cd /d "%~dp0"
py -3 --version >nul 2>&1
if %errorlevel%==0 (set PY=py -3) else (set PY=python)
%PY% --version >nul 2>&1
if errorlevel 1 (
  echo Python 3 was not found.
  echo Install it from https://www.python.org/downloads/windows/ ^(tick "Add python.exe to PATH"^)
  echo or from the Microsoft Store, then run this file again.
  pause
  exit /b 1
)
echo Starting the dashboard... a browser window will open.
echo Keep this window open while you use the dashboard. Close it or press Ctrl+C to stop.
start "" http://127.0.0.1:8765
%PY% scripts\serve.py
pause
