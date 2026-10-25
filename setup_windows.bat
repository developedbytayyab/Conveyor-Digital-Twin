@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if errorlevel 1 (
  echo Python launcher not found. Install Python 3.11 or 3.12 from https://www.python.org/downloads/windows/
  echo During install, enable "Add Python to PATH".
  pause
  exit /b 1
)
py -3.11 -m venv .venv 2>nul
if errorlevel 1 py -3.12 -m venv .venv
if errorlevel 1 (
  echo Could not create virtual environment. Install Python 3.11 or 3.12.
  pause
  exit /b 1
)
call .venv\Scripts\python.exe -m pip install --upgrade pip
call .venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 (
  echo Dependency installation failed.
  pause
  exit /b 1
)
echo.
echo Setup complete. Next run start_dashboard.bat
pause
