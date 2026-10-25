@echo off
cd /d "%~dp0"
call .venv\Scripts\python.exe -m pytest -q
pause
