@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\streamlit.exe" (
  echo Run setup_windows.bat first.
  pause
  exit /b 1
)
if "%TWIN_APP_PASSWORD%"=="" (
  echo WARNING: TWIN_APP_PASSWORD is not set. Dashboard is not password protected by the app.
  echo For internet access, set a strong password and use Cloudflare Access Tunnel as documented in README.
  echo Example for this terminal only: set TWIN_APP_PASSWORD=use-a-long-unique-password
)
if "%OLLAMA_MODEL%"=="" set OLLAMA_MODEL=llama3.2:3b
if "%OLLAMA_HOST%"=="" set OLLAMA_HOST=http://127.0.0.1:11434
call .venv\Scripts\python.exe -m streamlit run app.py --server.address 127.0.0.1 --server.port 8501
pause
